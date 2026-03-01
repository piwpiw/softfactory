"""CooCook Feed Service — Social Feed, Reviews, Recommendations"""
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_, func
from ..models import (
    db, User, Chef, Recipe, RecipeReview, RecipeLike, UserFollow, Feed,
    CookingSession
)
from typing import List, Dict, Optional, Tuple
import json


class FeedService:
    """Manages user feed, social interactions, and recommendations"""

    @staticmethod
    def get_user_feed(user_id: int, limit: int = 20, offset: int = 0) -> Dict:
        """
        Get personalized feed for user combining:
        - New recipes from followed chefs
        - Activity from followed users (reviews, likes)
        - AI-powered recommendations
        - Popular recipes

        Args:
            user_id: Target user ID
            limit: Number of feed items (default 20)
            offset: Pagination offset

        Returns:
            {
                'feed': [Feed items with user/chef/recipe info],
                'total': Total count,
                'next_offset': Offset for next page,
                'timestamp': Current timestamp
            }
        """
        try:
            # Get followed chef IDs
            followed_chef_ids = db.session.query(UserFollow.following_id).filter(
                UserFollow.follower_id == user_id
            ).subquery()

            # Build feed query combining multiple sources
            feed_query = db.session.query(Feed).filter(
                Feed.user_id == user_id
            ).order_by(
                desc(Feed.created_at)
            ).offset(offset).limit(limit).all()

            # Fallback: If no feed items, generate from followed content
            if not feed_query:
                feed_query = FeedService._generate_personalized_feed(
                    user_id, limit, offset
                )

            feed_items = [FeedService._serialize_feed_item(item) for item in feed_query]
            total_count = db.session.query(func.count(Feed.id)).filter(
                Feed.user_id == user_id
            ).scalar()

            return {
                'feed': feed_items,
                'total': total_count,
                'next_offset': offset + limit,
                'has_more': (offset + limit) < total_count,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': f'Feed generation failed: {str(e)}',
                'feed': [],
                'total': 0
            }

    @staticmethod
    def _generate_personalized_feed(user_id: int, limit: int, offset: int) -> List:
        """Generate personalized feed from followed chefs and users"""
        try:
            # Get followed users and chefs
            following = db.session.query(UserFollow.following_id).filter(
                UserFollow.follower_id == user_id
            ).all()
            following_ids = [f[0] for f in following]

            # Recent recipes from followed chefs
            feed_items = []
            if following_ids:
                recent_recipes = db.session.query(Recipe).filter(
                    Recipe.chef_id.in_(following_ids)
                ).order_by(desc(Recipe.created_at)).limit(limit // 2).all()

                for recipe in recent_recipes:
                    feed_item = Feed(
                        user_id=user_id,
                        activity_type='new_recipe',
                        content_json=json.dumps({
                            'recipe_id': recipe.id,
                            'title': recipe.title,
                            'chef_id': recipe.chef_id,
                            'chef_name': recipe.chef.name if recipe.chef else 'Unknown'
                        })
                    )
                    feed_items.append(feed_item)

            # Recent reviews from followed users
            if following_ids:
                recent_reviews = db.session.query(RecipeReview).filter(
                    RecipeReview.user_id.in_(following_ids)
                ).order_by(desc(RecipeReview.created_at)).limit(limit // 4).all()

                for review in recent_reviews:
                    feed_item = Feed(
                        user_id=user_id,
                        activity_type='review',
                        content_json=json.dumps({
                            'review_id': review.id,
                            'recipe_id': review.recipe_id,
                            'rating': review.rating,
                            'user_id': review.user_id,
                            'user_name': review.user.name if review.user else 'Unknown'
                        })
                    )
                    feed_items.append(feed_item)

            return sorted(feed_items, key=lambda x: x.created_at, reverse=True)
        except Exception as e:
            print(f"Feed generation error: {e}")
            return []

    @staticmethod
    def _serialize_feed_item(feed: 'Feed') -> Dict:
        """Convert Feed object to JSON-serializable dict"""
        try:
            content = json.loads(feed.content_json) if feed.content_json else {}
            return {
                'id': feed.id,
                'activity_type': feed.activity_type,
                'content': content,
                'created_at': feed.created_at.isoformat() if feed.created_at else None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception:
            return {
                'id': feed.id,
                'activity_type': feed.activity_type,
                'content': {},
                'created_at': None
            }

    @staticmethod
    def post_review(
        recipe_id: int,
        user_id: int,
        rating: int,
        text: str,
        photos: Optional[List[str]] = None
    ) -> Dict:
        """
        Post a review for a recipe

        Args:
            recipe_id: Recipe being reviewed
            user_id: User posting review
            rating: 1-5 star rating
            text: Review text (max 500 chars)
            photos: Optional list of photo URLs

        Returns:
            {'success': bool, 'review_id': int, 'message': str}
        """
        try:
            # Validate inputs
            if not (1 <= rating <= 5):
                return {'success': False, 'message': 'Rating must be 1-5'}
            if len(text) > 500:
                return {'success': False, 'message': 'Review text too long (max 500)'}

            # Check recipe exists
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {'success': False, 'message': 'Recipe not found'}

            # Create review
            review = RecipeReview(
                recipe_id=recipe_id,
                user_id=user_id,
                rating=rating,
                text=text,
                photos=json.dumps(photos) if photos else None
            )
            db.session.add(review)

            # Update recipe rating
            recipe.update_rating()

            # Create feed entry
            feed = Feed(
                user_id=user_id,
                activity_type='review',
                content_json=json.dumps({
                    'review_id': None,  # Will be populated after flush
                    'recipe_id': recipe_id,
                    'rating': rating,
                    'text': text[:100]  # Summary
                })
            )
            db.session.add(feed)
            db.session.commit()

            review_id = review.id
            feed.content_json = json.dumps({
                'review_id': review_id,
                'recipe_id': recipe_id,
                'rating': rating,
                'text': text[:100]
            })
            db.session.commit()

            return {
                'success': True,
                'review_id': review_id,
                'message': 'Review posted successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Review creation failed: {str(e)}'}

    @staticmethod
    def get_reviews(
        recipe_id: int,
        page: int = 1,
        per_page: int = 10,
        sort: str = 'recent'
    ) -> Dict:
        """
        Get reviews for a recipe with pagination and sorting

        Args:
            recipe_id: Recipe ID
            page: Page number (1-indexed)
            per_page: Reviews per page
            sort: 'recent', 'helpful', 'rating_high', 'rating_low'

        Returns:
            {
                'reviews': [Review objects],
                'total': Total count,
                'page': Current page,
                'total_pages': Total pages,
                'average_rating': float,
                'rating_distribution': {1: count, 2: count, ...}
            }
        """
        try:
            offset = (page - 1) * per_page

            # Build base query
            query = RecipeReview.query.filter_by(recipe_id=recipe_id)

            # Apply sorting
            if sort == 'helpful':
                query = query.order_by(desc(RecipeReview.helpful_count))
            elif sort == 'rating_high':
                query = query.order_by(desc(RecipeReview.rating))
            elif sort == 'rating_low':
                query = query.order_by(RecipeReview.rating)
            else:  # 'recent'
                query = query.order_by(desc(RecipeReview.created_at))

            total = query.count()
            reviews = query.offset(offset).limit(per_page).all()

            # Calculate statistics
            all_reviews = RecipeReview.query.filter_by(recipe_id=recipe_id).all()
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0

            rating_dist = {i: 0 for i in range(1, 6)}
            for review in all_reviews:
                rating_dist[review.rating] += 1

            return {
                'reviews': [FeedService._serialize_review(r) for r in reviews],
                'total': total,
                'page': page,
                'total_pages': (total + per_page - 1) // per_page,
                'average_rating': round(avg_rating, 2),
                'rating_distribution': rating_dist,
                'has_more': (page * per_page) < total
            }
        except Exception as e:
            return {
                'error': f'Review retrieval failed: {str(e)}',
                'reviews': [],
                'total': 0
            }

    @staticmethod
    def _serialize_review(review: 'RecipeReview') -> Dict:
        """Convert RecipeReview to JSON-serializable dict"""
        try:
            photos = json.loads(review.photos) if review.photos else []
            return {
                'id': review.id,
                'recipe_id': review.recipe_id,
                'user_id': review.user_id,
                'user_name': review.user.name if review.user else 'Anonymous',
                'rating': review.rating,
                'text': review.text,
                'photos': photos,
                'helpful_count': review.helpful_count,
                'unhelpful_count': review.unhelpful_count,
                'created_at': review.created_at.isoformat() if review.created_at else None
            }
        except Exception:
            return {}

    @staticmethod
    def like_recipe(recipe_id: int, user_id: int) -> Dict:
        """
        Like or unlike a recipe

        Args:
            recipe_id: Recipe ID
            user_id: User ID

        Returns:
            {'success': bool, 'liked': bool, 'message': str}
        """
        try:
            # Check if already liked
            existing = RecipeLike.query.filter_by(
                recipe_id=recipe_id,
                user_id=user_id
            ).first()

            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {'success': False, 'message': 'Recipe not found'}

            if existing:
                # Unlike
                db.session.delete(existing)
                recipe.like_count = max(0, (recipe.like_count or 1) - 1)
                db.session.commit()
                return {
                    'success': True,
                    'liked': False,
                    'message': 'Recipe unliked',
                    'like_count': recipe.like_count
                }
            else:
                # Like
                like = RecipeLike(recipe_id=recipe_id, user_id=user_id)
                db.session.add(like)
                recipe.like_count = (recipe.like_count or 0) + 1
                db.session.commit()

                # Create feed entry
                feed = Feed(
                    user_id=user_id,
                    activity_type='like',
                    content_json=json.dumps({
                        'recipe_id': recipe_id,
                        'recipe_title': recipe.title
                    })
                )
                db.session.add(feed)
                db.session.commit()

                return {
                    'success': True,
                    'liked': True,
                    'message': 'Recipe liked',
                    'like_count': recipe.like_count
                }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Like action failed: {str(e)}'}

    @staticmethod
    def follow_chef(chef_id: int, user_id: int) -> Dict:
        """
        Follow or unfollow a chef

        Args:
            chef_id: Chef to follow
            user_id: User following

        Returns:
            {'success': bool, 'following': bool, 'follower_count': int}
        """
        try:
            # Check if already following
            existing = UserFollow.query.filter_by(
                follower_id=user_id,
                following_id=chef_id
            ).first()

            chef = Chef.query.get(chef_id)
            if not chef:
                return {'success': False, 'message': 'Chef not found'}

            if existing:
                # Unfollow
                db.session.delete(existing)
                db.session.commit()
                return {
                    'success': True,
                    'following': False,
                    'message': 'Chef unfollowed'
                }
            else:
                # Follow
                follow = UserFollow(follower_id=user_id, following_id=chef_id)
                db.session.add(follow)
                db.session.commit()

                # Create feed entry
                feed = Feed(
                    user_id=user_id,
                    activity_type='follow',
                    content_json=json.dumps({
                        'chef_id': chef_id,
                        'chef_name': chef.name
                    })
                )
                db.session.add(feed)
                db.session.commit()

                return {
                    'success': True,
                    'following': True,
                    'message': 'Chef followed'
                }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Follow action failed: {str(e)}'}

    @staticmethod
    def get_user_profile(user_id: int) -> Dict:
        """
        Get user profile with statistics and achievements

        Args:
            user_id: User ID

        Returns:
            {
                'user': User object,
                'stats': {
                    'cooking_sessions': count,
                    'saved_recipes': count,
                    'followers': count,
                    'following': count,
                    'reviews_posted': count,
                    'recipes_liked': count,
                    'activity_level': 'active'|'moderate'|'inactive'
                },
                'recent_activity': [Feed items]
            }
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}

            # Count statistics
            cooking_sessions = db.session.query(func.count(CookingSession.id)).filter(
                CookingSession.user_id == user_id
            ).scalar()

            saved_recipes = db.session.query(func.count(RecipeLike.id)).filter(
                RecipeLike.user_id == user_id
            ).scalar()

            followers = db.session.query(func.count(UserFollow.id)).filter(
                UserFollow.following_id == user_id
            ).scalar()

            following = db.session.query(func.count(UserFollow.id)).filter(
                UserFollow.follower_id == user_id
            ).scalar()

            reviews = db.session.query(func.count(RecipeReview.id)).filter(
                RecipeReview.user_id == user_id
            ).scalar()

            # Recent activity
            recent_feed = Feed.query.filter_by(user_id=user_id).order_by(
                desc(Feed.created_at)
            ).limit(5).all()

            # Determine activity level
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_activity = Feed.query.filter(
                and_(
                    Feed.user_id == user_id,
                    Feed.created_at >= recent_date
                )
            ).count()

            if recent_activity > 10:
                activity_level = 'active'
            elif recent_activity > 3:
                activity_level = 'moderate'
            else:
                activity_level = 'inactive'

            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'avatar_url': user.avatar_url,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                },
                'stats': {
                    'cooking_sessions': cooking_sessions,
                    'saved_recipes': saved_recipes,
                    'followers': followers,
                    'following': following,
                    'reviews_posted': reviews,
                    'recipes_liked': saved_recipes,
                    'activity_level': activity_level
                },
                'recent_activity': [
                    FeedService._serialize_feed_item(f) for f in recent_feed
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Profile retrieval failed: {str(e)}'
            }

    @staticmethod
    def share_recipe(recipe_id: int, user_id: int, platform: str = 'generic') -> Dict:
        """
        Track recipe share events

        Args:
            recipe_id: Recipe being shared
            user_id: User sharing
            platform: 'facebook', 'twitter', 'whatsapp', 'email', 'generic'

        Returns:
            {'success': bool, 'share_count': int}
        """
        try:
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {'success': False, 'message': 'Recipe not found'}

            # Increment share count
            recipe.share_count = (recipe.share_count or 0) + 1
            db.session.add(recipe)

            # Create feed entry
            feed = Feed(
                user_id=user_id,
                activity_type='share',
                content_json=json.dumps({
                    'recipe_id': recipe_id,
                    'platform': platform,
                    'recipe_title': recipe.title
                })
            )
            db.session.add(feed)
            db.session.commit()

            return {
                'success': True,
                'share_count': recipe.share_count,
                'message': 'Recipe shared successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Share failed: {str(e)}'}
