"""
CooCook Nutrition Engine Blueprint - Nutritional Analysis API
"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
from backend.models import db, Recipe, RecipeReview
from backend.auth import require_auth
from .nutrition_engine import calculate_nutrition, get_allergens, score_nutrition

nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/api/coocook/nutrition')


@nutrition_bp.route('/calculate', methods=['POST'])
@require_auth
def calculate_recipe_nutrition(current_user):
    """Calculate nutritional values for ingredients

    Request body:
        {
            "ingredients": [
                {"name": "chicken breast", "amount": 200, "unit": "g"},
                {"name": "rice", "amount": 1, "unit": "cup"}
            ]
        }

    Returns:
        {
            "success": true,
            "nutrition": {
                "calories": 450,
                "protein": 35,
                "carbs": 45,
                "fat": 12,
                ...
            },
            "macros": {...}
        }
    """
    data = request.get_json()
    ingredients = data.get('ingredients', [])

    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400

    try:
        nutrition = calculate_nutrition(ingredients)
        return jsonify({
            'success': True,
            'nutrition': nutrition
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@nutrition_bp.route('/allergens', methods=['POST'])
@require_auth
def detect_allergens(current_user):
    """Detect allergens in ingredients

    Request body:
        {
            "ingredients": [
                {"name": "peanuts"},
                {"name": "milk"},
                {"name": "shrimp"}
            ]
        }

    Returns:
        {
            "success": true,
            "allergens": ["peanut", "dairy", "shellfish"],
            "ingredients_with_allergens": [...]
        }
    """
    data = request.get_json()
    ingredients = data.get('ingredients', [])

    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400

    try:
        allergens = get_allergens(ingredients)
        return jsonify({
            'success': True,
            'allergens': allergens['allergen_list'],
            'ingredients_with_allergens': allergens['ingredients_with_allergens']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@nutrition_bp.route('/score', methods=['POST'])
@require_auth
def score_nutrition_values(current_user):
    """Calculate nutrition score (0-100)

    Request body:
        {
            "nutrition": {
                "calories": 450,
                "protein": 35,
                "carbs": 45,
                "fat": 12,
                "fiber": 4,
                "sodium": 800
            }
        }

    Returns:
        {
            "success": true,
            "score": 85,
            "grade": "A",
            "feedback": [...]
        }
    """
    data = request.get_json()
    nutrition = data.get('nutrition', {})

    if not nutrition:
        return jsonify({'error': 'No nutrition data provided'}), 400

    try:
        score = score_nutrition(nutrition)
        grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 50 else 'D'

        return jsonify({
            'success': True,
            'score': score,
            'grade': grade,
            'feedback': _get_nutrition_feedback(score, nutrition)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@nutrition_bp.route('/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe_nutrition(recipe_id):
    """Get nutritional information for a recipe

    Query parameters:
        - servings: adjust nutrition for specific servings (default: recipe servings)
    """
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    servings = request.args.get('servings', recipe.servings, type=int)

    if not recipe.nutrition_json:
        return jsonify({
            'error': 'Nutrition data not available for this recipe'
        }), 404

    # Adjust nutrition per serving
    nutrition = recipe.nutrition_json.copy()
    if servings != recipe.servings:
        factor = servings / recipe.servings
        nutrition['calories'] = round(nutrition.get('calories', 0) * factor)
        nutrition['protein'] = round(nutrition.get('protein', 0) * factor, 1)
        nutrition['carbs'] = round(nutrition.get('carbs', 0) * factor, 1)
        nutrition['fat'] = round(nutrition.get('fat', 0) * factor, 1)

    return jsonify({
        'success': True,
        'recipe_id': recipe_id,
        'recipe_name': recipe.name,
        'servings': servings,
        'nutrition': nutrition,
        'score': score_nutrition(nutrition),
        'allergens': get_allergens(recipe.ingredients_json)
    }), 200


@nutrition_bp.route('/compare-recipes', methods=['POST'])
@require_auth
def compare_recipe_nutrition(current_user):
    """Compare nutritional values between multiple recipes

    Request body:
        {
            "recipe_ids": [1, 2, 3]
        }

    Returns:
        {
            "success": true,
            "recipes": [
                {
                    "id": 1,
                    "name": "Spaghetti Carbonara",
                    "nutrition": {...},
                    "score": 75
                },
                ...
            ]
        }
    """
    data = request.get_json()
    recipe_ids = data.get('recipe_ids', [])

    if not recipe_ids:
        return jsonify({'error': 'No recipe IDs provided'}), 400

    recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()

    if not recipes:
        return jsonify({'error': 'No recipes found'}), 404

    comparison = []
    for recipe in recipes:
        if recipe.nutrition_json:
            comparison.append({
                'id': recipe.id,
                'name': recipe.name,
                'cuisine': recipe.cuisine,
                'nutrition': recipe.nutrition_json,
                'score': score_nutrition(recipe.nutrition_json)
            })

    return jsonify({
        'success': True,
        'count': len(comparison),
        'recipes': comparison
    }), 200


@nutrition_bp.route('/recommendations/<int:recipe_id>', methods=['GET'])
def get_nutrition_recommendations(recipe_id):
    """Get nutrition improvement recommendations for a recipe

    Returns:
        {
            "success": true,
            "recipe_id": 1,
            "current_score": 75,
            "recommendations": [...]
        }
    """
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    if not recipe.nutrition_json:
        return jsonify({'error': 'Nutrition data not available'}), 404

    nutrition = recipe.nutrition_json
    score = score_nutrition(nutrition)
    recommendations = _get_nutrition_recommendations(nutrition, score)

    return jsonify({
        'success': True,
        'recipe_id': recipe_id,
        'recipe_name': recipe.name,
        'current_score': score,
        'recommendations': recommendations
    }), 200


def _get_nutrition_feedback(score: int, nutrition: Dict) -> List[str]:
    """Generate feedback based on nutrition score"""
    feedback = []

    if score >= 85:
        feedback.append("Excellent nutritional balance!")
    elif score >= 70:
        feedback.append("Good nutritional profile with minor improvements possible.")
    elif score >= 50:
        feedback.append("Moderate nutrition - consider increasing certain nutrients.")
    else:
        feedback.append("Nutrition could be significantly improved.")

    # Specific feedback
    protein = nutrition.get('protein', 0)
    carbs = nutrition.get('carbs', 0)
    fat = nutrition.get('fat', 0)
    fiber = nutrition.get('fiber', 0)
    sodium = nutrition.get('sodium', 0)
    calories = nutrition.get('calories', 1)

    if protein < (calories / 300) * 12:
        feedback.append("Consider adding more protein sources.")

    if fiber < 3:
        feedback.append("This recipe is low in fiber. Add vegetables or whole grains.")

    if sodium > 2000:
        feedback.append("This recipe is high in sodium. Consider reducing salt.")

    carbs_percent = (carbs * 4 / calories) * 100 if calories > 0 else 0
    if carbs_percent > 60:
        feedback.append("This recipe is high in carbohydrates.")
    elif carbs_percent < 30:
        feedback.append("This recipe is low in carbohydrates.")

    fat_percent = (fat * 9 / calories) * 100 if calories > 0 else 0
    if fat_percent > 40:
        feedback.append("This recipe is high in fat. Consider healthier cooking methods.")

    return feedback


def _get_nutrition_recommendations(nutrition: Dict, current_score: int) -> List[Dict]:
    """Generate specific recommendations for nutrition improvement"""
    recommendations = []

    protein = nutrition.get('protein', 0)
    carbs = nutrition.get('carbs', 0)
    fat = nutrition.get('fat', 0)
    fiber = nutrition.get('fiber', 0)
    sodium = nutrition.get('sodium', 0)
    calories = nutrition.get('calories', 1)

    if protein < (calories / 300) * 12:
        recommendations.append({
            'area': 'Protein',
            'current': round(protein, 1),
            'target': round((calories / 300) * 15, 1),
            'suggestion': 'Add lean meat, fish, eggs, or legumes'
        })

    if fiber < 3:
        recommendations.append({
            'area': 'Fiber',
            'current': round(fiber, 1),
            'target': 5,
            'suggestion': 'Include whole grains, vegetables, or fruits'
        })

    if sodium > 2000:
        recommendations.append({
            'area': 'Sodium',
            'current': round(sodium),
            'target': 1500,
            'suggestion': 'Reduce salt and use herbs/spices for flavor'
        })

    fat_percent = (fat * 9 / calories) * 100 if calories > 0 else 0
    if fat_percent > 35:
        recommendations.append({
            'area': 'Fat',
            'current': round(fat_percent, 1),
            'target': 25,
            'suggestion': 'Use healthier cooking methods (bake, grill, steam)'
        })

    if current_score < 70:
        recommendations.append({
            'area': 'Overall Balance',
            'current': current_score,
            'target': 85,
            'suggestion': 'Implement multiple recommendations above to improve overall nutrition'
        })

    return recommendations
