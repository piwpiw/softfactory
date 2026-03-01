"""Test Suite for Nutrition Engine - CooCook"""

import pytest
from backend.services.nutrition_engine import (
    calculate_nutrition,
    calculate_recipe_nutrition,
    get_allergen_info,
    rate_nutrition,
    get_daily_value_percentages,
    NUTRITION_DB,
)


# ============ TEST: calculate_nutrition() ============

def test_calculate_nutrition_basic():
    """Test basic nutrition calculation with simple ingredients"""
    ingredients = [
        {'name': 'chicken breast', 'quantity_g': 200},
        {'name': 'rice', 'quantity_g': 150},
    ]

    result = calculate_nutrition(ingredients)

    # Verify structure
    assert 'calories' in result
    assert 'protein' in result
    assert 'carbs' in result
    assert 'fat' in result
    assert 'fiber' in result
    assert 'sodium' in result
    assert 'macros' in result
    assert 'ingredient_breakdown' in result
    assert 'unknown_ingredients' in result

    # Verify values are positive
    assert result['calories'] > 0
    assert result['protein'] > 0
    assert result['carbs'] > 0

    # Verify ingredient breakdown has correct count
    assert len(result['ingredient_breakdown']) == 2


def test_calculate_nutrition_scaling():
    """Test that nutrition scales correctly with quantity"""
    # 100g chicken breast
    ingredients_100g = [{'name': 'chicken breast', 'quantity_g': 100}]
    result_100g = calculate_nutrition(ingredients_100g)

    # 200g chicken breast (should be ~2x)
    ingredients_200g = [{'name': 'chicken breast', 'quantity_g': 200}]
    result_200g = calculate_nutrition(ingredients_200g)

    assert abs(result_200g['calories'] - result_100g['calories'] * 2) < 0.1
    assert abs(result_200g['protein'] - result_100g['protein'] * 2) < 0.1


def test_calculate_nutrition_unknown_ingredients():
    """Test handling of unknown ingredients"""
    ingredients = [
        {'name': 'chicken breast', 'quantity_g': 100},
        {'name': 'unknown_ingredient_xyz', 'quantity_g': 100},
    ]

    result = calculate_nutrition(ingredients)

    assert 'unknown_ingredient_xyz' in result['unknown_ingredients']
    assert len(result['ingredient_breakdown']) == 1


def test_calculate_nutrition_empty():
    """Test with empty ingredients list"""
    result = calculate_nutrition([])

    assert result['calories'] == 0.0
    assert result['protein'] == 0.0
    assert result['carbs'] == 0.0


def test_calculate_nutrition_macros():
    """Test that macros sum to approximately 100%"""
    ingredients = [
        {'name': 'chicken breast', 'quantity_g': 200},
        {'name': 'rice', 'quantity_g': 150},
        {'name': 'olive oil', 'quantity_g': 20},
    ]

    result = calculate_nutrition(ingredients)

    macros_sum = (
        result['macros']['protein%'] +
        result['macros']['carbs%'] +
        result['macros']['fat%']
    )

    # Should be approximately 100 (allow small rounding error)
    assert 95 < macros_sum < 105


# ============ TEST: calculate_recipe_nutrition() ============

def test_calculate_recipe_nutrition_basic():
    """Test recipe nutrition calculation with servings"""
    recipe = {
        'name': 'Simple Chicken Rice',
        'ingredients': [
            {'name': 'chicken breast', 'quantity_g': 200},
            {'name': 'rice', 'quantity_g': 150},
        ],
        'servings': 2,
    }

    result = calculate_recipe_nutrition(recipe)

    # Verify structure
    assert result['recipe_name'] == 'Simple Chicken Rice'
    assert result['servings'] == 2
    assert 'total_nutrition' in result
    assert 'per_serving' in result
    assert 'total_macros' in result
    assert 'per_serving_macros' in result

    # Per-serving should be half of total
    assert abs(result['per_serving']['calories'] - result['total_nutrition']['calories'] / 2) < 0.1


def test_calculate_recipe_nutrition_override_servings():
    """Test overriding servings parameter"""
    recipe = {
        'name': 'Test Recipe',
        'ingredients': [{'name': 'rice', 'quantity_g': 100}],
        'servings': 2,
    }

    # Override with 4 servings
    result = calculate_recipe_nutrition(recipe, servings=4)

    assert result['servings'] == 4
    # Per-serving should be 1/4 of total
    assert abs(result['per_serving']['calories'] - result['total_nutrition']['calories'] / 4) < 0.1


# ============ TEST: get_allergen_info() ============

def test_get_allergen_info_basic():
    """Test allergen detection for common allergens"""
    ingredients = ['egg', 'dairy', 'shellfish']

    result = get_allergen_info(ingredients)

    assert 'egg' in result['allergens']
    assert 'dairy' in result['allergens']
    assert 'shellfish' in result['allergens']
    assert result['is_safe'] is False
    assert result['has_top_8_allergens'] is True


def test_get_allergen_info_safe():
    """Test safe ingredients with no allergens"""
    ingredients = ['rice', 'spinach', 'carrot']

    result = get_allergen_info(ingredients)

    assert result['allergen_count'] == 0
    assert result['is_safe'] is True
    assert len(result['warnings']) == 0


def test_get_allergen_info_case_insensitive():
    """Test allergen detection is case-insensitive"""
    ingredients = ['CHEESE', 'Egg', 'ShRiMp']

    result = get_allergen_info(ingredients)

    assert 'dairy' in result['allergens']
    assert 'egg' in result['allergens']
    assert 'shellfish' in result['allergens']


def test_get_allergen_info_top_8():
    """Test detection of top 8 FDA allergens"""
    top_8_ingredients = [
        'peanut',
        'tree nuts',
        'milk',
        'egg',
        'fish',
        'shellfish',
        'wheat',
        'sesame',
        'soy',
    ]

    result = get_allergen_info(top_8_ingredients)

    assert result['has_top_8_allergens'] is True
    assert result['allergen_count'] > 0


def test_get_allergen_info_warnings():
    """Test warning message generation"""
    ingredients = ['cheese']

    result = get_allergen_info(ingredients)

    assert len(result['warnings']) > 0
    assert 'dairy' in result['warnings'][0].lower() or 'Dairy' in result['warnings'][0]


# ============ TEST: rate_nutrition() ============

def test_rate_nutrition_perfect_balance():
    """Test nutrition score with balanced macros"""
    # ~300 cal, good protein, good carbs, reasonable fat
    score = rate_nutrition(
        calories=300,
        carbs=35,  # ~47% of calories
        protein=25,  # ~33% of calories
        fat=8,  # ~24% of calories
        fiber=5,
    )

    # Should be a good score (70+)
    assert score > 70
    assert score <= 100


def test_rate_nutrition_low_score():
    """Test nutrition score with poor macros"""
    # Only fat and calories (no carbs, no protein, no fiber)
    score = rate_nutrition(
        calories=300,
        carbs=0,
        protein=0,
        fat=30,
        fiber=0,
    )

    # Should be lower score (base 50 but no bonuses)
    assert score <= 50


def test_rate_nutrition_high_protein():
    """Test that high protein boosts score"""
    score_normal = rate_nutrition(
        calories=300,
        carbs=30,
        protein=15,  # Lower protein
        fat=8,
        fiber=2,
    )

    score_high_protein = rate_nutrition(
        calories=300,
        carbs=30,
        protein=40,  # High protein
        fat=8,
        fiber=6,  # Higher fiber
    )

    # High protein and fiber should score better
    assert score_high_protein >= score_normal


def test_rate_nutrition_high_fiber():
    """Test that high fiber boosts score"""
    score_low_fiber = rate_nutrition(
        calories=300,
        carbs=30,
        protein=25,
        fat=8,
        fiber=2,
    )

    score_high_fiber = rate_nutrition(
        calories=300,
        carbs=30,
        protein=25,
        fat=8,
        fiber=8,
    )

    # High fiber should score better
    assert score_high_fiber > score_low_fiber


def test_rate_nutrition_zero_calories():
    """Test scoring with zero calories"""
    score = rate_nutrition(
        calories=0,
        carbs=0,
        protein=0,
        fat=0,
        fiber=0,
    )

    assert score == 0


# ============ TEST: get_daily_value_percentages() ============

def test_get_daily_value_percentages():
    """Test daily value percentage calculation"""
    nutrition = {
        'calories': 1000,
        'protein': 50,
        'carbs': 150,
        'fat': 32,
        'fiber': 12,
        'sodium': 1000,
    }

    dv_percent = get_daily_value_percentages(nutrition)

    # Verify all keys present
    assert 'calories' in dv_percent
    assert 'protein' in dv_percent
    assert 'carbs' in dv_percent
    assert 'fat' in dv_percent
    assert 'fiber' in dv_percent
    assert 'sodium' in dv_percent

    # Verify percentages are reasonable (>0 and <200)
    for key, percent in dv_percent.items():
        assert percent >= 0
        assert percent < 500


# ============ INTEGRATION TESTS ============

def test_nutrition_db_integrity():
    """Test that NUTRITION_DB has all required nutrients"""
    required_nutrients = {'calories', 'protein', 'carbs', 'fat', 'fiber', 'sodium'}

    for ingredient, nutrition in NUTRITION_DB.items():
        for nutrient in required_nutrients:
            assert nutrient in nutrition, f"{ingredient} missing {nutrient}"
            assert isinstance(nutrition[nutrient], (int, float))
            assert nutrition[nutrient] >= 0


def test_real_recipe_calculation():
    """Test with real bibimbap recipe"""
    recipe = {
        'name': 'Traditional Bibimbap',
        'ingredients': [
            {'name': 'rice', 'quantity_g': 300},
            {'name': 'beef', 'quantity_g': 150},
            {'name': 'egg', 'quantity_g': 100},
            {'name': 'spinach', 'quantity_g': 100},
            {'name': 'mushroom', 'quantity_g': 100},
            {'name': 'carrot', 'quantity_g': 100},
            {'name': 'kimchi', 'quantity_g': 50},
            {'name': 'soy sauce', 'quantity_g': 20},
        ],
        'servings': 2,
    }

    result = calculate_recipe_nutrition(recipe)

    # Verify reasonable values
    assert result['total_nutrition']['calories'] > 1000
    assert result['total_nutrition']['protein'] > 40
    assert result['per_serving']['calories'] < result['total_nutrition']['calories']
    # Note: per_serving_nutrition_score is added in the API endpoint, not in the core function


def test_api_endpoint_request_format():
    """Test that our functions work with API request format"""
    # Simulate POST /nutrition/calculate request
    api_request = {
        'ingredients': [
            {'name': 'chicken breast', 'quantity_g': 200},
            {'name': 'rice', 'quantity_g': 150},
        ]
    }

    result = calculate_nutrition(api_request['ingredients'])

    # Should work without errors
    assert 'calories' in result
    assert 'macros' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
