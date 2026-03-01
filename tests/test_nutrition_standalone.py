"""Standalone Test Suite for Nutrition Engine - No Flask dependency"""

import pytest
from backend.services.nutrition_engine import (
    calculate_nutrition,
    calculate_recipe_nutrition,
    get_allergen_info,
    rate_nutrition,
    get_daily_value_percentages,
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
    print(f"✓ Basic nutrition calculation: {result['calories']} cal, {result['protein']}g protein")


def test_calculate_nutrition_scaling():
    """Test that nutrition scales correctly with quantity"""
    ingredients_100g = [{'name': 'chicken breast', 'quantity_g': 100}]
    result_100g = calculate_nutrition(ingredients_100g)

    ingredients_200g = [{'name': 'chicken breast', 'quantity_g': 200}]
    result_200g = calculate_nutrition(ingredients_200g)

    assert abs(result_200g['calories'] - result_100g['calories'] * 2) < 0.1
    assert abs(result_200g['protein'] - result_100g['protein'] * 2) < 0.1
    print(f"✓ Scaling test: 100g={result_100g['calories']} cal, 200g={result_200g['calories']} cal")


def test_calculate_nutrition_unknown_ingredients():
    """Test handling of unknown ingredients"""
    ingredients = [
        {'name': 'chicken breast', 'quantity_g': 100},
        {'name': 'unknown_xyz', 'quantity_g': 100},
    ]

    result = calculate_nutrition(ingredients)

    assert 'unknown_xyz' in result['unknown_ingredients']
    assert len(result['ingredient_breakdown']) == 1
    print(f"✓ Unknown ingredient handling: found {len(result['unknown_ingredients'])} unknown")


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

    assert 95 < macros_sum < 105
    print(f"✓ Macro percentages: P={result['macros']['protein%']}%, C={result['macros']['carbs%']}%, F={result['macros']['fat%']}%")


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

    assert result['recipe_name'] == 'Simple Chicken Rice'
    assert result['servings'] == 2
    assert 'total_nutrition' in result
    assert 'per_serving' in result
    assert abs(result['per_serving']['calories'] - result['total_nutrition']['calories'] / 2) < 0.1
    print(f"✓ Recipe nutrition: {result['total_nutrition']['calories']} cal total, {result['per_serving']['calories']} per serving")


def test_calculate_recipe_nutrition_override_servings():
    """Test overriding servings parameter"""
    recipe = {
        'name': 'Test Recipe',
        'ingredients': [{'name': 'rice', 'quantity_g': 100}],
        'servings': 2,
    }

    result = calculate_recipe_nutrition(recipe, servings=4)

    assert result['servings'] == 4
    assert abs(result['per_serving']['calories'] - result['total_nutrition']['calories'] / 4) < 0.1
    print(f"✓ Servings override: 4 servings, {result['per_serving']['calories']} cal per serving")


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
    print(f"✓ Allergen detection: {len(result['allergens'])} allergens found")


def test_get_allergen_info_safe():
    """Test safe ingredients with no allergens"""
    ingredients = ['rice', 'spinach', 'carrot']

    result = get_allergen_info(ingredients)

    assert result['allergen_count'] == 0
    assert result['is_safe'] is True
    assert len(result['warnings']) == 0
    print("✓ Safe ingredients test passed")


def test_get_allergen_info_top_8():
    """Test detection of top 8 FDA allergens"""
    top_8_ingredients = [
        'peanut', 'tree nuts', 'milk', 'egg',
        'fish', 'shellfish', 'wheat', 'sesame'
    ]

    result = get_allergen_info(top_8_ingredients)

    assert result['has_top_8_allergens'] is True
    assert result['allergen_count'] > 0
    print(f"✓ Top 8 allergens detected: {result['allergen_count']} unique allergens")


# ============ TEST: rate_nutrition() ============

def test_rate_nutrition_perfect_balance():
    """Test nutrition score with balanced macros"""
    score = rate_nutrition(
        calories=300,
        carbs=35,
        protein=25,
        fat=8,
        fiber=5,
    )

    assert score > 70
    assert score <= 100
    print(f"✓ Balanced nutrition score: {score}/100")


def test_rate_nutrition_high_fiber():
    """Test that high fiber boosts score"""
    score_low = rate_nutrition(calories=300, carbs=30, protein=25, fat=8, fiber=2)
    score_high = rate_nutrition(calories=300, carbs=30, protein=25, fat=8, fiber=8)

    assert score_high >= score_low
    print(f"✓ Fiber effect: Low fiber={score_low}, High fiber={score_high}")


def test_rate_nutrition_zero_calories():
    """Test scoring with zero calories"""
    score = rate_nutrition(calories=0, carbs=0, protein=0, fat=0, fiber=0)
    assert score == 0
    print("✓ Zero calorie test passed")


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

    assert 'calories' in dv_percent
    assert 'protein' in dv_percent
    for key, percent in dv_percent.items():
        assert percent >= 0
    print(f"✓ Daily values calculated: {len(dv_percent)} nutrients")


# ============ INTEGRATION TEST ============

def test_full_workflow():
    """Test complete nutrition calculation workflow"""
    # Step 1: Calculate from ingredients
    ingredients = [
        {'name': 'chicken breast', 'quantity_g': 150},
        {'name': 'rice', 'quantity_g': 100},
        {'name': 'broccoli', 'quantity_g': 100},
    ]
    nutrition = calculate_nutrition(ingredients)

    # Step 2: Check allergens
    allergens = get_allergen_info(['chicken breast', 'rice', 'broccoli'])

    # Step 3: Rate nutrition
    score = rate_nutrition(
        nutrition['calories'],
        nutrition['carbs'],
        nutrition['protein'],
        nutrition['fat'],
        nutrition['fiber']
    )

    # Step 4: Calculate daily values
    dv = get_daily_value_percentages(nutrition)

    print(f"\n✓ Full workflow test:")
    print(f"  - Nutrition: {nutrition['calories']} cal, {nutrition['protein']}g protein")
    print(f"  - Allergens: {len(allergens['allergens'])} found, Safe={allergens['is_safe']}")
    print(f"  - Score: {score}/100")
    print(f"  - Daily values: {len(dv)} metrics calculated")

    assert nutrition['calories'] > 0
    assert allergens['is_safe'] is True
    assert score > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
