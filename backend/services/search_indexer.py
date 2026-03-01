"""Search Indexer - Bulk index database records into Elasticsearch
Provides utilities to sync SQLAlchemy models with Elasticsearch indices
"""

from ..models import db, Recipe, SNSPost, User
from .elasticsearch_service import get_search_manager
import logging

logger = logging.getLogger(__name__)


def index_recipes():
    """Index all recipes from database into Elasticsearch"""
    try:
        search_manager = get_search_manager()

        # Fetch all recipes in batches to avoid memory issues
        recipes = db.session.query(Recipe).all()

        documents = []
        for recipe in recipes:
            doc = {
                'id': recipe.id,
                'title': recipe.title or '',
                'description': recipe.description or '',
                'content': recipe.instructions or '',
                'tags': recipe.tags or [],
                'ingredients': ','.join([ing.get('name', '') for ing in (recipe.ingredients or [])]),
                'difficulty': recipe.difficulty_level or 'medium',
                'cooking_time': recipe.cooking_time_minutes or 30,
                'servings': recipe.servings or 4,
                'calories': recipe.calories or 0,
                'protein': recipe.protein_g or 0,
                'carbs': recipe.carbs_g or 0,
                'fat': recipe.fat_g or 0,
                'rating': recipe.average_rating or 0,
                'review_count': recipe.review_count or 0,
                'views': recipe.view_count or 0,
                'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
                'updated_at': recipe.updated_at.isoformat() if recipe.updated_at else None,
                'user_id': recipe.user_id,
                'is_public': recipe.is_public if hasattr(recipe, 'is_public') else True
            }
            documents.append(doc)

        if documents:
            success, errors = search_manager.es.bulk_index('recipes', documents)
            logger.info(f"Indexed {success} recipes into Elasticsearch")
            if errors:
                logger.warning(f"Errors during recipe indexing: {len(errors)}")
            return success
        return 0

    except Exception as e:
        logger.error(f"Failed to index recipes: {str(e)}")
        return 0


def index_sns_posts():
    """Index all SNS posts from database into Elasticsearch"""
    try:
        search_manager = get_search_manager()

        posts = db.session.query(SNSPost).all()

        documents = []
        for post in posts:
            # Calculate engagement rate
            total_engagement = (post.likes_count or 0) + (post.comments_count or 0) + (post.shares or 0)
            engagement_rate = total_engagement / max(post.views_count or 1, 1) if post.views_count else 0

            doc = {
                'id': post.id,
                'content': post.content or '',
                'caption': post.caption or '',
                'hashtags': post.hashtags or [],
                'platform': post.platform or 'unknown',
                'likes': post.likes_count or 0,
                'comments': post.comments_count or 0,
                'shares': post.shares or 0,
                'engagement_rate': engagement_rate,
                'posted_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'user_id': post.user_id,
                'user_name': post.user.name if post.user else 'unknown'
            }
            documents.append(doc)

        if documents:
            success, errors = search_manager.es.bulk_index('sns_posts', documents)
            logger.info(f"Indexed {success} SNS posts into Elasticsearch")
            if errors:
                logger.warning(f"Errors during SNS post indexing: {len(errors)}")
            return success
        return 0

    except Exception as e:
        logger.error(f"Failed to index SNS posts: {str(e)}")
        return 0


def index_users():
    """Index all users from database into Elasticsearch"""
    try:
        search_manager = get_search_manager()

        users = db.session.query(User).all()

        documents = []
        for user in users:
            doc = {
                'id': user.id,
                'name': user.name or '',
                'email': user.email or '',
                'bio': getattr(user, 'bio', '') or '',
                'role': user.role or 'user',
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_active': user.is_active
            }
            documents.append(doc)

        if documents:
            success, errors = search_manager.es.bulk_index('users', documents)
            logger.info(f"Indexed {success} users into Elasticsearch")
            if errors:
                logger.warning(f"Errors during user indexing: {len(errors)}")
            return success
        return 0

    except Exception as e:
        logger.error(f"Failed to index users: {str(e)}")
        return 0


def index_all():
    """Index all searchable content into Elasticsearch"""
    try:
        logger.info("Starting full indexing...")

        recipe_count = index_recipes()
        post_count = index_sns_posts()
        user_count = index_users()

        logger.info(f"Indexing complete: {recipe_count} recipes, {post_count} posts, {user_count} users")
        return {
            'recipes': recipe_count,
            'posts': post_count,
            'users': user_count,
            'total': recipe_count + post_count + user_count
        }
    except Exception as e:
        logger.error(f"Full indexing failed: {str(e)}")
        return None


def sync_single_recipe(recipe_id: int):
    """Index or update a single recipe"""
    try:
        search_manager = get_search_manager()
        recipe = db.session.query(Recipe).get(recipe_id)

        if not recipe:
            logger.warning(f"Recipe {recipe_id} not found")
            return False

        doc = {
            'id': recipe.id,
            'title': recipe.title or '',
            'description': recipe.description or '',
            'content': recipe.instructions or '',
            'tags': recipe.tags or [],
            'ingredients': ','.join([ing.get('name', '') for ing in (recipe.ingredients or [])]),
            'difficulty': recipe.difficulty_level or 'medium',
            'cooking_time': recipe.cooking_time_minutes or 30,
            'servings': recipe.servings or 4,
            'calories': recipe.calories or 0,
            'protein': recipe.protein_g or 0,
            'carbs': recipe.carbs_g or 0,
            'fat': recipe.fat_g or 0,
            'rating': recipe.average_rating or 0,
            'review_count': recipe.review_count or 0,
            'views': recipe.view_count or 0,
            'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
            'updated_at': recipe.updated_at.isoformat() if recipe.updated_at else None,
            'user_id': recipe.user_id,
            'is_public': recipe.is_public if hasattr(recipe, 'is_public') else True
        }

        return search_manager.index_document('recipes', recipe.id, doc)
    except Exception as e:
        logger.error(f"Failed to sync recipe {recipe_id}: {str(e)}")
        return False


def sync_single_post(post_id: int):
    """Index or update a single SNS post"""
    try:
        search_manager = get_search_manager()
        post = db.session.query(SNSPost).get(post_id)

        if not post:
            logger.warning(f"Post {post_id} not found")
            return False

        total_engagement = (post.likes_count or 0) + (post.comments_count or 0) + (post.shares or 0)
        engagement_rate = total_engagement / max(post.views_count or 1, 1) if post.views_count else 0

        doc = {
            'id': post.id,
            'content': post.content or '',
            'caption': post.caption or '',
            'hashtags': post.hashtags or [],
            'platform': post.platform or 'unknown',
            'likes': post.likes_count or 0,
            'comments': post.comments_count or 0,
            'shares': post.shares or 0,
            'engagement_rate': engagement_rate,
            'posted_at': post.published_at.isoformat() if post.published_at else None,
            'created_at': post.created_at.isoformat() if post.created_at else None,
            'user_id': post.user_id,
            'user_name': post.user.name if post.user else 'unknown'
        }

        return search_manager.index_document('sns_posts', post.id, doc)
    except Exception as e:
        logger.error(f"Failed to sync post {post_id}: {str(e)}")
        return False


def delete_recipe_from_index(recipe_id: int):
    """Remove a recipe from Elasticsearch index"""
    try:
        search_manager = get_search_manager()
        search_manager.es.es.delete(index='recipes', id=recipe_id)
        logger.info(f"Deleted recipe {recipe_id} from index")
        return True
    except Exception as e:
        logger.error(f"Failed to delete recipe {recipe_id}: {str(e)}")
        return False


def delete_post_from_index(post_id: int):
    """Remove an SNS post from Elasticsearch index"""
    try:
        search_manager = get_search_manager()
        search_manager.es.es.delete(index='sns_posts', id=post_id)
        logger.info(f"Deleted post {post_id} from index")
        return True
    except Exception as e:
        logger.error(f"Failed to delete post {post_id}: {str(e)}")
        return False
