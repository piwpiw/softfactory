"""Shopping List Service - Recipe-based Shopping Management (CooCook v3)"""
from datetime import datetime
from sqlalchemy import desc
from flask import Blueprint, jsonify, request
from ..models import db, ShoppingList, ShoppingListItem, Recipe
from ..auth import require_auth
from collections import defaultdict

# Create blueprint
shopping_bp = Blueprint('shopping', __name__, url_prefix='/api/coocook/shopping')


# Estimated ingredient prices (per standard unit)
INGREDIENT_PRICES = {
    'rice': 2.50,  # per kg
    'chicken breast': 8.99,  # per lb
    'salmon': 12.99,  # per lb
    'tofu': 3.49,  # per block
    'egg': 0.30,  # per unit
    'pasta': 1.99,  # per box
    'beef': 7.99,  # per lb
    'shrimp': 14.99,  # per lb
    'broccoli': 2.49,  # per bunch
    'kimchi': 5.99,  # per jar
    'mushroom': 4.99,  # per lb
    'spinach': 3.49,  # per bunch
    'onion': 0.99,  # per unit
    'garlic': 0.50,  # per bulb
    'olive oil': 8.99,  # per bottle
    'soy sauce': 3.99,  # per bottle
    'butter': 4.49,  # per lb
    'potato': 1.99,  # per lb
    'carrot': 0.79,  # per lb
    'cheese': 6.99,  # per lb
}


class ShoppingListService:
    """Service for managing shopping lists with recipe-based auto-generation"""

    @staticmethod
    def create_list(user_id, name, recipe_ids=None, serving_sizes=None):
        """
        Create a shopping list from recipes with automatic ingredient merging.

        Args:
            user_id: User creating the list
            name: Display name for the shopping list
            recipe_ids: List of recipe/menu IDs to merge
            serving_sizes: Dict of {recipe_id: serving_size}

        Returns:
            ShoppingList object
        """
        # Import here to avoid circular imports
        from .coocook import MOCK_MENUS

        items_dict = defaultdict(lambda: {'quantity': 0, 'unit': None, 'checked': False})

        # Merge ingredients from multiple recipes
        if recipe_ids:
            serving_sizes = serving_sizes or {}

            for recipe_id in recipe_ids:
                menu = MOCK_MENUS.get(recipe_id)
                if not menu:
                    continue

                multiplier = serving_sizes.get(recipe_id, 1)

                for ingredient in menu.get('ingredients', []):
                    ingredient_lower = ingredient.lower()

                    if ingredient_lower not in items_dict:
                        items_dict[ingredient_lower] = {
                            'name': ingredient,
                            'quantity': 0,
                            'unit': 'pack',
                            'checked': False,
                            'category': ShoppingListService._ingredient_category(ingredient),
                            'estimated_price': INGREDIENT_PRICES.get(ingredient_lower, 0),
                        }

                    # Sum quantities
                    items_dict[ingredient_lower]['quantity'] += multiplier

        # Convert to list format
        items = []
        for key, item in items_dict.items():
            items.append(item)

        # Create shopping list
        shopping_list = ShoppingList(
            user_id=user_id,
            name=name,
            items=items,
        )

        db.session.add(shopping_list)
        db.session.commit()

        return shopping_list

    @staticmethod
    def get_user_lists(user_id):
        """Get all shopping lists for a user"""
        return ShoppingList.query.filter_by(
            user_id=user_id
        ).order_by(
            desc(ShoppingList.created_at)
        ).all()

    @staticmethod
    def get_list_details(list_id, user_id):
        """
        Get detailed shopping list with price estimates

        Args:
            list_id: Shopping list ID
            user_id: User ID (for auth check)

        Returns:
            ShoppingList dict or None if not found
        """
        shopping_list = ShoppingList.query.get(list_id)

        if not shopping_list or shopping_list.user_id != user_id:
            return None

        return shopping_list.to_dict()

    @staticmethod
    def add_item(list_id, ingredient, quantity, unit, user_id):
        """
        Add an item to a shopping list

        Args:
            list_id: Shopping list ID
            ingredient: Ingredient name
            quantity: Quantity value
            unit: Unit of measurement
            user_id: User ID (for auth check)

        Returns:
            Updated ShoppingList or None
        """
        shopping_list = ShoppingList.query.get(list_id)

        if not shopping_list or shopping_list.user_id != user_id:
            return None

        ingredient_lower = ingredient.lower()
        estimated_price = INGREDIENT_PRICES.get(ingredient_lower, 0)

        items = shopping_list.items or []

        # Check if item already exists
        for item in items:
            if item.get('name', '').lower() == ingredient_lower:
                item['quantity'] += quantity
                shopping_list.updated_at = datetime.utcnow()
                db.session.commit()
                return shopping_list

        # Add new item
        new_item = {
            'name': ingredient,
            'quantity': quantity,
            'unit': unit,
            'checked': False,
            'category': ShoppingListService._ingredient_category(ingredient),
            'estimated_price': estimated_price,
        }

        items.append(new_item)
        shopping_list.items = items
        shopping_list.updated_at = datetime.utcnow()
        db.session.commit()

        return shopping_list

    @staticmethod
    def update_item(list_id, item_index, quantity=None, is_checked=None, user_id=None):
        """
        Update an item in the shopping list

        Args:
            list_id: Shopping list ID
            item_index: Index of item to update
            quantity: New quantity (optional)
            is_checked: New checked status (optional)
            user_id: User ID (for auth check)

        Returns:
            Updated ShoppingList or None
        """
        shopping_list = ShoppingList.query.get(list_id)

        if not shopping_list or (user_id and shopping_list.user_id != user_id):
            return None

        items = shopping_list.items or []

        if item_index < 0 or item_index >= len(items):
            return None

        if quantity is not None:
            items[item_index]['quantity'] = quantity

        if is_checked is not None:
            items[item_index]['checked'] = is_checked

        shopping_list.items = items
        shopping_list.updated_at = datetime.utcnow()
        db.session.commit()

        return shopping_list

    @staticmethod
    def delete_item(list_id, item_index, user_id):
        """
        Delete an item from the shopping list

        Args:
            list_id: Shopping list ID
            item_index: Index of item to delete
            user_id: User ID (for auth check)

        Returns:
            Updated ShoppingList or None
        """
        shopping_list = ShoppingList.query.get(list_id)

        if not shopping_list or shopping_list.user_id != user_id:
            return None

        items = shopping_list.items or []

        if item_index < 0 or item_index >= len(items):
            return None

        items.pop(item_index)
        shopping_list.items = items
        shopping_list.updated_at = datetime.utcnow()
        db.session.commit()

        return shopping_list

    @staticmethod
    def calculate_total_price(list_id, user_id):
        """
        Calculate total estimated price for all items in shopping list

        Args:
            list_id: Shopping list ID
            user_id: User ID (for auth check)

        Returns:
            Dict with breakdown and total, or None if not found
        """
        shopping_list = ShoppingList.query.get(list_id)

        if not shopping_list or shopping_list.user_id != user_id:
            return None

        items = shopping_list.items or []
        breakdown = []
        total = 0

        for item in items:
            name = item.get('name', '').lower()
            quantity = item.get('quantity', 1)
            unit = item.get('unit', 'pack')

            # Get price per unit
            unit_price = INGREDIENT_PRICES.get(name, 0)
            item_total = unit_price * quantity

            breakdown.append({
                'name': item.get('name'),
                'quantity': quantity,
                'unit': unit,
                'unit_price': unit_price,
                'total_price': round(item_total, 2),
            })

            total += item_total

        return {
            'list_id': list_id,
            'list_name': shopping_list.name,
            'item_breakdown': breakdown,
            'total_items': len(items),
            'estimated_total': round(total, 2),
            'currency': 'USD',
        }

    @staticmethod
    def _ingredient_category(name):
        """Categorize ingredient for grouping in shopping list"""
        categories = {
            'produce': ['broccoli', 'spinach', 'onion', 'garlic', 'carrot', 'mushroom', 'potato'],
            'protein': ['chicken breast', 'beef', 'salmon', 'shrimp', 'tofu', 'egg'],
            'grain': ['rice', 'pasta'],
            'dairy': ['cheese', 'butter'],
            'condiment': ['soy sauce', 'olive oil', 'kimchi'],
        }

        name_lower = name.lower()
        for category, items in categories.items():
            if name_lower in items:
                return category

        return 'other'


# ============ BLUEPRINT ROUTES ============

@shopping_bp.route('/lists', methods=['GET'])
@require_auth
def get_shopping_lists(current_user):
    """Get all shopping lists for current user"""
    lists = ShoppingList.query.filter_by(user_id=current_user.id).all()

    return jsonify({
        'success': True,
        'count': len(lists),
        'lists': [
            {
                'id': l.id,
                'name': l.name,
                'is_shared': l.is_shared,
                'item_count': len(l.items),
                'created_at': l.created_at.isoformat() if l.created_at else None
            }
            for l in lists
        ]
    }), 200


@shopping_bp.route('/lists', methods=['POST'])
@require_auth
def create_shopping_list(current_user):
    """Create a new shopping list

    Request body:
        {
            "name": "Weekly Groceries",
            "is_shared": false
        }
    """
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    shopping_list = ShoppingList(
        user_id=current_user.id,
        name=name,
        is_shared=data.get('is_shared', False)
    )
    db.session.add(shopping_list)
    db.session.commit()

    return jsonify({
        'success': True,
        'list': shopping_list.to_dict()
    }), 201


@shopping_bp.route('/lists/<int:list_id>', methods=['GET'])
@require_auth
def get_shopping_list(current_user, list_id):
    """Get a specific shopping list with items"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        return jsonify({'error': 'Shopping list not found'}), 404

    if shopping_list.user_id != current_user.id and not shopping_list.is_shared:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({
        'success': True,
        'list': {
            'id': shopping_list.id,
            'name': shopping_list.name,
            'is_shared': shopping_list.is_shared,
            'created_at': shopping_list.created_at.isoformat() if shopping_list.created_at else None,
            'items': [item.to_dict() for item in shopping_list.items]
        }
    }), 200


@shopping_bp.route('/lists/<int:list_id>', methods=['DELETE'])
@require_auth
def delete_shopping_list(current_user, list_id):
    """Delete a shopping list"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        return jsonify({'error': 'Shopping list not found'}), 404

    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(shopping_list)
    db.session.commit()

    return jsonify({'success': True}), 200


@shopping_bp.route('/lists/<int:list_id>/items', methods=['POST'])
@require_auth
def add_shopping_list_item(current_user, list_id):
    """Add item to shopping list

    Request body:
        {
            "ingredient": "Chicken Breast",
            "quantity": 500,
            "unit": "g",
            "estimated_price": 8.99
        }
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        return jsonify({'error': 'Shopping list not found'}), 404

    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    ingredient = data.get('ingredient')
    quantity = data.get('quantity')
    unit = data.get('unit', 'pcs')

    if not ingredient or not quantity:
        return jsonify({'error': 'Ingredient and quantity are required'}), 400

    item = ShoppingListItem(
        list_id=list_id,
        ingredient=ingredient,
        quantity=quantity,
        unit=unit,
        estimated_price=data.get('estimated_price'),
        is_checked=False
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item': item.to_dict()
    }), 201


@shopping_bp.route('/items/<int:item_id>', methods=['PUT'])
@require_auth
def update_shopping_item(current_user, item_id):
    """Update shopping list item"""
    item = ShoppingListItem.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Check authorization
    shopping_list = ShoppingList.query.get(item.list_id)
    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    if 'ingredient' in data:
        item.ingredient = data['ingredient']
    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'unit' in data:
        item.unit = data['unit']
    if 'estimated_price' in data:
        item.estimated_price = data['estimated_price']
    if 'is_checked' in data:
        item.is_checked = data['is_checked']

    db.session.commit()

    return jsonify({
        'success': True,
        'item': item.to_dict()
    }), 200


@shopping_bp.route('/items/<int:item_id>', methods=['DELETE'])
@require_auth
def delete_shopping_item(current_user, item_id):
    """Delete item from shopping list"""
    item = ShoppingListItem.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Check authorization
    shopping_list = ShoppingList.query.get(item.list_id)
    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True}), 200


@shopping_bp.route('/from-recipes', methods=['POST'])
@require_auth
def create_from_recipes(current_user):
    """Create shopping list from recipe ingredients

    Request body:
        {
            "name": "Dinner Party",
            "recipe_ids": [1, 2, 3]
        }
    """
    data = request.get_json()
    name = data.get('name')
    recipe_ids = data.get('recipe_ids', [])

    if not name or not recipe_ids:
        return jsonify({'error': 'Name and recipe_ids are required'}), 400

    # Get recipes
    recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()

    if not recipes:
        return jsonify({'error': 'No recipes found'}), 404

    # Create shopping list
    shopping_list = ShoppingList(
        user_id=current_user.id,
        name=name,
        is_shared=False
    )
    db.session.add(shopping_list)
    db.session.flush()

    # Add ingredients from recipes
    ingredient_totals = {}
    for recipe in recipes:
        if recipe.ingredients_json:
            for ingredient in recipe.ingredients_json:
                name_lower = ingredient.get('name', '').lower()
                quantity = ingredient.get('amount', 0)
                unit = ingredient.get('unit', 'pcs')

                key = (name_lower, unit)
                if key not in ingredient_totals:
                    ingredient_totals[key] = {
                        'name': ingredient.get('name'),
                        'quantity': 0,
                        'unit': unit,
                        'estimated_price': None
                    }
                ingredient_totals[key]['quantity'] += quantity

    # Create items
    for (name_lower, unit), data in ingredient_totals.items():
        item = ShoppingListItem(
            list_id=shopping_list.id,
            ingredient=data['name'],
            quantity=data['quantity'],
            unit=data['unit'],
            is_checked=False
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({
        'success': True,
        'list': shopping_list.to_dict(),
        'item_count': len(ingredient_totals)
    }), 201


@shopping_bp.route('/lists/<int:list_id>/estimate', methods=['GET'])
@require_auth
def estimate_cost(current_user, list_id):
    """Get cost estimate for shopping list"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        return jsonify({'error': 'Shopping list not found'}), 404

    if shopping_list.user_id != current_user.id and not shopping_list.is_shared:
        return jsonify({'error': 'Unauthorized'}), 403

    total = 0
    breakdown = []

    for item in shopping_list.items:
        item_price = item.estimated_price or 0
        item_total = item_price * item.quantity

        breakdown.append({
            'ingredient': item.ingredient,
            'quantity': item.quantity,
            'unit': item.unit,
            'unit_price': item_price,
            'total': round(item_total, 2)
        })

        total += item_total

    return jsonify({
        'success': True,
        'list_id': list_id,
        'breakdown': breakdown,
        'estimated_total': round(total, 2),
        'currency': 'USD'
    }), 200
