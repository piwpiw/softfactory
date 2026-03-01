"""
CooCook Feed Service - User activity feed and social features
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from backend.models import db, User, Recipe, RecipeReview, Feed, UserFollow, RecipeLike
from backend.auth import require_auth

feed_bp = Blueprint('feed', __name__, url_prefix='/api/coocook/feed')


@feed_bp.route('/activity/<int:user_id>', methods=['GET'])
@require_auth
def get_user_activity(user_id):
    """Get activity feed for a specific user

    Query parameters:
        - limit: max number of items (default: 20)
        - offset: pagination offset (default: 0)
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Get feed entries
    feed_entries = Feed.query.filter_by(user_id=user_id).order_by(
        desc(Feed.created_at)
    ).limit(limit).offset(offset).all()

    return jsonify({
        'success': True,
        'count': len(feed_entries),
        'activities': [entry.to_dict() for entry in feed_entries]
    }), 200


@feed_bp.route('/timeline', methods=['GET'])
@require_auth
def get_user_timeline(current_user):
    """Get personalized timeline for current user based on follows

    Shows activities from users they follow
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Get users that current user follows
    following = db.session.query(UserFollow.following_id).filter_by(
        follower_id=current_user.id
    ).all()
    following_ids = [f[0] for f in following] + [current_user.id]

    # Get feed for followed users
    timeline = Feed.query.filter(
        Feed.user_id.in_(following_ids)
    ).order_by(desc(Feed.created_at)).limit(limit).offset(offset).all()

    return jsonify({
        'success': True,
        'count': len(timeline),
        'activities': [entry.to_dict() for entry in timeline]
    }), 200


@feed_bp.route('/recipe-published/<int:recipe_id>', methods=['POST'])
@require_auth
def log_recipe_published(current_user, recipe_id):
    """Log when a recipe is published"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    if recipe.chef_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Create feed entry
    feed = Feed(
        user_id=current_user.id,
        activity_type='recipe_published',
        content_json={
            'recipe_id': recipe_id,
            'recipe_name': recipe.name,
            'recipe_cuisine': recipe.cuisine,
            'recipe_image_url': None
        }
    )
    db.session.add(feed)
    db.session.commit()

    return jsonify({
        'success': True,
        'activity': feed.to_dict()
    }), 201


@feed_bp.route('/recipe-liked/<int:recipe_id>', methods=['POST'])
@require_auth
def log_recipe_liked(current_user, recipe_id):
    """Log when a recipe is liked"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    # Check if already liked
    existing_like = RecipeLike.query.filter_by(
        recipe_id=recipe_id,
        user_id=current_user.id
    ).first()

    if existing_like:
        return jsonify({'error': 'Recipe already liked'}), 400

    # Create like
    like = RecipeLike(recipe_id=recipe_id, user_id=current_user.id)
    db.session.add(like)

    # Create feed entry
    feed = Feed(
        user_id=current_user.id,
        activity_type='recipe_liked',
        content_json={
            'recipe_id': recipe_id,
            'recipe_name': recipe.name,
        }
    )
    db.session.add(feed)

    # Update recipe like count
    recipe.like_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'activity': feed.to_dict(),
        'like_count': recipe.like_count
    }), 201


@feed_bp.route('/recipe-unliked/<int:recipe_id>', methods=['POST'])
@require_auth
def log_recipe_unliked(current_user, recipe_id):
    """Remove like from a recipe"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    # Check if liked
    like = RecipeLike.query.filter_by(
        recipe_id=recipe_id,
        user_id=current_user.id
    ).first()

    if not like:
        return jsonify({'error': 'Recipe not liked'}), 400

    db.session.delete(like)
    recipe.like_count = max(0, recipe.like_count - 1)
    db.session.commit()

    return jsonify({
        'success': True,
        'like_count': recipe.like_count
    }), 200


@feed_bp.route('/recipe-reviewed/<int:recipe_id>', methods=['POST'])
@require_auth
def log_recipe_reviewed(current_user, recipe_id):
    """Log when a recipe is reviewed"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    data = request.get_json()
    rating = data.get('rating')
    review_text = data.get('text', '')

    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Invalid rating (1-5)'}), 400

    # Create review
    review = RecipeReview(
        recipe_id=recipe_id,
        user_id=current_user.id,
        rating=rating,
        text=review_text,
        photos_json=data.get('photos', [])
    )
    db.session.add(review)

    # Create feed entry
    feed = Feed(
        user_id=current_user.id,
        activity_type='recipe_reviewed',
        content_json={
            'recipe_id': recipe_id,
            'recipe_name': recipe.name,
            'rating': rating,
            'review_text': review_text[:100] if review_text else None
        }
    )
    db.session.add(feed)

    # Update recipe stats
    recipe.review_count += 1
    # Recalculate average rating
    all_ratings = db.session.query(func.avg(RecipeReview.rating)).filter_by(
        recipe_id=recipe_id
    ).scalar()
    recipe.rating = float(all_ratings) if all_ratings else 0

    db.session.commit()

    return jsonify({
        'success': True,
        'activity': feed.to_dict(),
        'review_count': recipe.review_count,
        'rating': recipe.rating
    }), 201


@feed_bp.route('/user-followed/<int:following_id>', methods=['POST'])
@require_auth
def log_user_followed(current_user, following_id):
    """Log when user follows another user"""
    target_user = User.query.get(following_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    if following_id == current_user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    # Check if already following
    existing_follow = UserFollow.query.filter_by(
        follower_id=current_user.id,
        following_id=following_id
    ).first()

    if existing_follow:
        return jsonify({'error': 'Already following this user'}), 400

    # Create follow
    follow = UserFollow(
        follower_id=current_user.id,
        following_id=following_id
    )
    db.session.add(follow)

    # Create feed entry
    feed = Feed(
        user_id=current_user.id,
        activity_type='user_followed',
        content_json={
            'user_id': following_id,
            'user_name': target_user.name,
        }
    )
    db.session.add(feed)

    db.session.commit()

    return jsonify({
        'success': True,
        'activity': feed.to_dict()
    }), 201


@feed_bp.route('/user-unfollowed/<int:following_id>', methods=['POST'])
@require_auth
def log_user_unfollowed(current_user, following_id):
    """Log when user unfollows another user"""
    follow = UserFollow.query.filter_by(
        follower_id=current_user.id,
        following_id=following_id
    ).first()

    if not follow:
        return jsonify({'error': 'Not following this user'}), 400

    db.session.delete(follow)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Unfollowed successfully'
    }), 200


@feed_bp.route('/followers/<int:user_id>', methods=['GET'])
def get_followers(user_id):
    """Get list of followers for a user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    followers = db.session.query(User).join(
        UserFollow, UserFollow.follower_id == User.id
    ).filter(UserFollow.following_id == user_id).all()

    return jsonify({
        'success': True,
        'user_id': user_id,
        'follower_count': len(followers),
        'followers': [
            {
                'id': f.id,
                'name': f.name,
                'avatar_url': f.avatar_url
            }
            for f in followers
        ]
    }), 200


@feed_bp.route('/following/<int:user_id>', methods=['GET'])
def get_following(user_id):
    """Get list of users that a user is following"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    following = db.session.query(User).join(
        UserFollow, UserFollow.following_id == User.id
    ).filter(UserFollow.follower_id == user_id).all()

    return jsonify({
        'success': True,
        'user_id': user_id,
        'following_count': len(following),
        'following': [
            {
                'id': f.id,
                'name': f.name,
                'avatar_url': f.avatar_url
            }
            for f in following
        ]
    }), 200


@feed_bp.route('/trending-recipes', methods=['GET'])
def get_trending_recipes():
    """Get trending recipes based on likes and reviews"""
    limit = request.args.get('limit', 10, type=int)
    days = request.args.get('days', 30, type=int)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    trending = Recipe.query.filter(
        Recipe.created_at >= cutoff_date
    ).order_by(
        desc(Recipe.like_count + Recipe.review_count)
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'count': len(trending),
        'recipes': [recipe.to_dict() for recipe in trending]
    }), 200


@feed_bp.route('/top-chefs', methods=['GET'])
def get_top_chefs():
    """Get top chefs by number of recipes and followers"""
    limit = request.args.get('limit', 10, type=int)

    top_chefs = db.session.query(
        User.id,
        User.name,
        User.avatar_url,
        func.count(Recipe.id).label('recipe_count'),
        func.count(UserFollow.id).label('follower_count')
    ).join(
        Recipe, Recipe.chef_id == User.id, isouter=True
    ).join(
        UserFollow, UserFollow.following_id == User.id, isouter=True
    ).group_by(User.id).order_by(
        desc(func.count(Recipe.id)),
        desc(func.count(UserFollow.id))
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'count': len(top_chefs),
        'chefs': [
            {
                'id': chef[0],
                'name': chef[1],
                'avatar_url': chef[2],
                'recipe_count': chef[3] or 0,
                'follower_count': chef[4] or 0
            }
            for chef in top_chefs
        ]
    }), 200
