"""Nutrition Engine - CooCook Nutritional Analysis Service

Core functions for calculating nutritional values, macro ratios, allergen detection,
and nutrition scoring. Integrates with NUTRITION_DB from coocook.py.

Total lines: ~360 | Updated: 2026-02-26
"""

from typing import List, Dict, Optional
from datetime import datetime


# ============ NUTRITION DATABASE (Reference) ============

NUTRITION_DB = {
    'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28.2, 'fat': 0.3, 'fiber': 0.4, 'sodium': 1},
    'chicken breast': {'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6, 'fiber': 0.0, 'sodium': 74},
    'salmon': {'calories': 208, 'protein': 20.4, 'carbs': 0.0, 'fat': 13.4, 'fiber': 0.0, 'sodium': 59},
    'tofu': {'calories': 76, 'protein': 8.0, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3, 'sodium': 7},
    'egg': {'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0, 'fiber': 0.0, 'sodium': 124},
    'pasta': {'calories': 131, 'protein': 5.0, 'carbs': 25.0, 'fat': 1.1, 'fiber': 1.8, 'sodium': 1},
    'beef': {'calories': 250, 'protein': 26.0, 'carbs': 0.0, 'fat': 15.0, 'fiber': 0.0, 'sodium': 72},
    'shrimp': {'calories': 99, 'protein': 24.0, 'carbs': 0.2, 'fat': 0.3, 'fiber': 0.0, 'sodium': 111},
    'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4, 'fiber': 2.6, 'sodium': 33},
    'kimchi': {'calories': 15, 'protein': 1.1, 'carbs': 2.4, 'fat': 0.5, 'fiber': 1.6, 'sodium': 498},
    'mushroom': {'calories': 22, 'protein': 3.1, 'carbs': 3.3, 'fat': 0.3, 'fiber': 1.0, 'sodium': 5},
    'spinach': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2, 'sodium': 79},
    'onion': {'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1, 'fiber': 1.7, 'sodium': 4},
    'garlic': {'calories': 149, 'protein': 6.4, 'carbs': 33.1, 'fat': 0.5, 'fiber': 2.1, 'sodium': 17},
    'olive oil': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'fiber': 0.0, 'sodium': 2},
    'soy sauce': {'calories': 53, 'protein': 8.1, 'carbs': 4.9, 'fat': 0.6, 'fiber': 0.8, 'sodium': 5493},
    'butter': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81.0, 'fiber': 0.0, 'sodium': 11},
    'potato': {'calories': 77, 'protein': 2.0, 'carbs': 17.5, 'fat': 0.1, 'fiber': 2.2, 'sodium': 6},
    'carrot': {'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2, 'fiber': 2.8, 'sodium': 69},
    'cheese': {'calories': 402, 'protein': 25.0, 'carbs': 1.3, 'fat': 33.1, 'fiber': 0.0, 'sodium': 621},
}

# Allergen mapping: ingredient -> list of allergens
ALLERGEN_MAP = {
    'peanut': ['peanut'],
    'peanuts': ['peanut'],
    'tree nuts': ['tree nuts'],
    'almonds': ['tree nuts'],
    'walnuts': ['tree nuts'],
    'cashew': ['tree nuts'],
    'pistachio': ['tree nuts'],
    'hazelnut': ['tree nuts'],
    'pecan': ['tree nuts'],
    'macadamia': ['tree nuts'],
    'milk': ['dairy'],
    'dairy': ['dairy'],
    'cheese': ['dairy'],
    'butter': ['dairy'],
    'yogurt': ['dairy'],
    'cream': ['dairy'],
    'whey': ['dairy'],
    'milk powder': ['dairy'],
    'wheat': ['gluten'],
    'barley': ['gluten'],
    'rye': ['gluten'],
    'oat': ['gluten'],
    'flour': ['gluten'],
    'bread': ['gluten'],
    'pasta': ['gluten'],
    'cereal': ['gluten'],
    'fish': ['fish'],
    'salmon': ['fish'],
    'tuna': ['fish'],
    'cod': ['fish'],
    'trout': ['fish'],
    'shellfish': ['shellfish'],
    'shrimp': ['shellfish'],
    'prawn': ['shellfish'],
    'crab': ['shellfish'],
    'lobster': ['shellfish'],
    'oyster': ['shellfish'],
    'clam': ['shellfish'],
    'mussel': ['shellfish'],
    'scallop': ['shellfish'],
    'egg': ['egg'],
    'eggs': ['egg'],
    'sesame': ['sesame'],
    'sesame oil': ['sesame'],
    'soy': ['soy'],
    'soy sauce': ['soy'],
    'tofu': ['soy'],
    'tempeh': ['soy'],
    'edamame': ['soy'],
}

# Daily value reference (US FDA)
DAILY_VALUES = {
    'calories': 2000,
    'protein': 50,
    'carbs': 300,
    'fat': 65,
    'fiber': 25,
    'sodium': 2300,
}


# ============ FUNCTION 1: Calculate Nutrition from Ingredients List ============

def calculate_nutrition(ingredients: List[Dict]) -> Dict:
    """
    Calculate total nutrition from a list of ingredients.

    Args:
        ingredients: List of dicts with 'name' (str) and 'quantity_g' (float)
                    Example: [{'name': 'rice', 'quantity_g': 200}, ...]

    Returns:
        dict with keys:
            - calories (float): Total calories
            - protein (float): Grams of protein
            - carbs (float): Grams of carbs
            - fat (float): Grams of fat
            - fiber (float): Grams of fiber
            - sodium (float): Mg of sodium
            - macros (dict): {'protein%', 'carbs%', 'fat%'}
            - ingredient_breakdown (list): Per-ingredient nutrition
            - unknown_ingredients (list): Ingredients not in database
    """
    total_nutrition = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'fiber': 0.0,
        'sodium': 0.0,
    }

    ingredient_breakdown = []
    unknown_ingredients = []

    # Process each ingredient
    for item in ingredients:
        name = item.get('name', '').strip().lower()
        quantity_g = item.get('quantity_g', 100.0)

        # Look up in database
        nutrition_per_100g = NUTRITION_DB.get(name)

        if nutrition_per_100g:
            # Scale by actual quantity
            scale_factor = quantity_g / 100.0

            item_nutrition = {}
            for nutrient, value in nutrition_per_100g.items():
                scaled_value = round(value * scale_factor, 1)
                item_nutrition[nutrient] = scaled_value
                total_nutrition[nutrient] += scaled_value

            ingredient_breakdown.append({
                'name': name,
                'quantity_g': quantity_g,
                'nutrition': item_nutrition,
            })
        else:
            unknown_ingredients.append(name)

    # Round all totals
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)

    # Calculate macro percentages
    total_calories = total_nutrition['calories']
    if total_calories > 0:
        protein_calories = total_nutrition['protein'] * 4  # 4 cal/g
        carbs_calories = total_nutrition['carbs'] * 4
        fat_calories = total_nutrition['fat'] * 9  # 9 cal/g

        macros = {
            'protein%': round((protein_calories / total_calories) * 100, 1),
            'carbs%': round((carbs_calories / total_calories) * 100, 1),
            'fat%': round((fat_calories / total_calories) * 100, 1),
        }
    else:
        macros = {'protein%': 0.0, 'carbs%': 0.0, 'fat%': 0.0}

    return {
        'calories': total_nutrition['calories'],
        'protein': total_nutrition['protein'],
        'carbs': total_nutrition['carbs'],
        'fat': total_nutrition['fat'],
        'fiber': total_nutrition['fiber'],
        'sodium': total_nutrition['sodium'],
        'macros': macros,
        'ingredient_breakdown': ingredient_breakdown,
        'unknown_ingredients': unknown_ingredients,
        'calculated_at': datetime.utcnow().isoformat(),
    }


# ============ FUNCTION 2: Calculate Recipe Nutrition (with servings) ============

def calculate_recipe_nutrition(
    recipe: Dict,
    servings: Optional[int] = None
) -> Dict:
    """
    Calculate nutrition for a complete recipe with servings.

    Args:
        recipe: Dict with keys:
            - 'name': str
            - 'ingredients': List[{'name': str, 'quantity_g': float}]
            - 'servings': int (optional, defaults to 1)
        servings: int (optional, overrides recipe['servings'])

    Returns:
        dict with keys:
            - total_nutrition: Full recipe nutrition
            - per_serving: Nutrition per serving
            - macros: Macro percentages
            - servings: Number of servings
            - (all other fields from calculate_nutrition)
    """
    # Get ingredients from recipe
    ingredients = recipe.get('ingredients', [])
    if not servings:
        servings = recipe.get('servings', 1)

    # Calculate total nutrition
    result = calculate_nutrition(ingredients)

    # Divide by servings for per-serving values
    per_serving = {
        'calories': round(result['calories'] / servings, 1),
        'protein': round(result['protein'] / servings, 1),
        'carbs': round(result['carbs'] / servings, 1),
        'fat': round(result['fat'] / servings, 1),
        'fiber': round(result['fiber'] / servings, 1),
        'sodium': round(result['sodium'] / servings, 1),
    }

    # Recalculate macros for per-serving
    total_cal = per_serving['calories']
    if total_cal > 0:
        per_serving_macros = {
            'protein%': round((per_serving['protein'] * 4 / total_cal) * 100, 1),
            'carbs%': round((per_serving['carbs'] * 4 / total_cal) * 100, 1),
            'fat%': round((per_serving['fat'] * 9 / total_cal) * 100, 1),
        }
    else:
        per_serving_macros = {'protein%': 0.0, 'carbs%': 0.0, 'fat%': 0.0}

    return {
        'recipe_name': recipe.get('name', 'Unknown Recipe'),
        'servings': servings,
        'total_nutrition': {
            'calories': result['calories'],
            'protein': result['protein'],
            'carbs': result['carbs'],
            'fat': result['fat'],
            'fiber': result['fiber'],
            'sodium': result['sodium'],
        },
        'total_macros': result['macros'],
        'per_serving': per_serving,
        'per_serving_macros': per_serving_macros,
        'ingredient_breakdown': result['ingredient_breakdown'],
        'unknown_ingredients': result['unknown_ingredients'],
        'calculated_at': datetime.utcnow().isoformat(),
    }


# ============ FUNCTION 3: Allergen Detection ============

def get_allergen_info(ingredients: List[str]) -> Dict:
    """
    Detect allergens in a list of ingredient names.

    Args:
        ingredients: List of ingredient name strings

    Returns:
        dict with keys:
            - allergens: List[str] of detected allergens
            - allergen_count: int
            - ingredients_with_allergens: List[{'name': str, 'allergens': List[str]}]
            - warnings: List[str] of human-readable warnings
            - is_safe: bool (True if no allergens detected)
    """
    detected_allergens = set()
    ingredients_with_allergens = []
    warnings = []

    for ingredient in ingredients:
        ingredient_lower = ingredient.strip().lower()

        # Check allergen map
        allergens_found = []
        for allergen_name, allergen_list in ALLERGEN_MAP.items():
            if allergen_name in ingredient_lower:
                allergens_found.extend(allergen_list)

        if allergens_found:
            # Remove duplicates and add to tracking
            unique_allergens = list(set(allergens_found))
            detected_allergens.update(unique_allergens)

            ingredients_with_allergens.append({
                'name': ingredient,
                'allergens': unique_allergens,
            })

    # Generate warnings
    if detected_allergens:
        for allergen in sorted(detected_allergens):
            allergen_upper = allergen.title()
            warnings.append(f'Contains {allergen_upper} - may cause allergic reaction')

    # Check for top 8 allergens (US FDA definition)
    top_8_allergens = {'dairy', 'egg', 'fish', 'shellfish', 'tree nuts', 'peanut', 'wheat', 'sesame', 'soy'}
    has_top_8 = bool(detected_allergens & top_8_allergens)

    return {
        'allergens': sorted(list(detected_allergens)),
        'allergen_count': len(detected_allergens),
        'has_top_8_allergens': has_top_8,
        'ingredients_with_allergens': ingredients_with_allergens,
        'warnings': warnings,
        'is_safe': len(detected_allergens) == 0,
    }


# ============ FUNCTION 4: Nutrition Score (0-100) ============

def rate_nutrition(
    calories: float,
    carbs: float,
    protein: float,
    fat: float = 0.0,
    fiber: float = 0.0
) -> int:
    """
    Calculate nutrition score (0-100) based on macro balance and nutrient density.

    Scoring criteria:
    - Base: 50 points
    - Protein adequacy: +20 (if >15g per 300 cal serving)
    - Carb quality: +15 (if 40-50% of calories)
    - Fat quality: +10 (if <30% of calories)
    - Fiber content: +5 (if >3g)

    Args:
        calories: Total calories
        carbs: Grams of carbs
        protein: Grams of protein
        fat: Grams of fat (optional)
        fiber: Grams of fiber (optional)

    Returns:
        int score from 0-100
    """
    score = 50  # Base score

    # Skip if no calories
    if calories == 0:
        return 0

    # 1. Protein scoring (20 points max)
    # ~15g protein per 300 calories is adequate
    protein_target = (calories / 300) * 15
    protein_ratio = protein / protein_target if protein_target > 0 else 0

    if protein_ratio >= 0.8:  # At least 80% of target
        score += 20
    elif protein_ratio >= 0.5:
        score += 10
    elif protein_ratio >= 0.2:
        score += 5

    # 2. Carbohydrate scoring (15 points max)
    # Optimal: 40-50% of calories from carbs
    carbs_calories = carbs * 4
    carbs_percent = (carbs_calories / calories) * 100 if calories > 0 else 0

    if 40 <= carbs_percent <= 50:
        score += 15
    elif 35 <= carbs_percent <= 55:
        score += 12
    elif 30 <= carbs_percent <= 60:
        score += 8
    elif carbs_percent > 0:
        score += 4

    # 3. Fat scoring (10 points max)
    # Optimal: <30% of calories from fat
    fat_calories = fat * 9
    fat_percent = (fat_calories / calories) * 100 if calories > 0 else 0

    if fat_percent < 20:
        score += 10
    elif fat_percent < 30:
        score += 8
    elif fat_percent < 40:
        score += 4

    # 4. Fiber scoring (5 points max)
    # Good: >3g, Excellent: >5g
    if fiber >= 5:
        score += 5
    elif fiber >= 3:
        score += 3
    elif fiber > 0:
        score += 1

    # Cap score at 100
    score = min(100, max(0, score))

    return int(score)


# ============ HELPER FUNCTION: Daily Value Percentages ============

def get_daily_value_percentages(nutrition: Dict) -> Dict:
    """
    Calculate daily value percentages for a nutrition dict.

    Args:
        nutrition: Dict with keys: calories, protein, carbs, fat, fiber, sodium

    Returns:
        dict with DV% for each nutrient
    """
    dv_percent = {}
    for nutrient, daily_value in DAILY_VALUES.items():
        if nutrient in nutrition and daily_value > 0:
            value = nutrition[nutrient]
            percent = round((value / daily_value) * 100, 1)
            dv_percent[nutrient] = percent
    return dv_percent


# ============ HELPER FUNCTION: Format Nutrition Summary ============

def format_nutrition_summary(nutrition: Dict, serving_size: str = '1 serving') -> str:
    """
    Format nutrition data into human-readable summary.

    Args:
        nutrition: Nutrition dict from calculate_nutrition()
        serving_size: Optional serving size label

    Returns:
        Formatted string for display
    """
    lines = [
        f"Nutrition Summary ({serving_size})",
        f"================================",
        f"Calories: {nutrition['calories']} kcal",
        f"Protein:  {nutrition['protein']}g ({nutrition['macros']['protein%']}%)",
        f"Carbs:    {nutrition['carbs']}g ({nutrition['macros']['carbs%']}%)",
        f"Fat:      {nutrition['fat']}g ({nutrition['macros']['fat%']}%)",
        f"Fiber:    {nutrition['fiber']}g",
        f"Sodium:   {nutrition['sodium']}mg",
    ]
    return "\n".join(lines)


# ============ BACKWARD COMPATIBILITY ALIASES ============

def get_allergens(ingredients: List[str]) -> Dict:
    """Backward compatibility alias for get_allergen_info"""
    return get_allergen_info(ingredients)


def score_nutrition(calories: float, carbs: float, protein: float, fat: float = 0.0) -> int:
    """Backward compatibility alias for rate_nutrition"""
    return rate_nutrition(calories, carbs, protein, fat)
