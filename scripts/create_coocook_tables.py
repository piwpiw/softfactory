#!/usr/bin/env python
"""
Script to create CooCook database tables and seed test data.

Usage:
    python scripts/create_coocook_tables.py
"""
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app import create_app, db
from backend.models import User, Recipe, RecipeReview, ShoppingList, ShoppingListItem, UserFollow, Feed, RecipeLike


def create_tables():
    """Create all CooCook tables"""
    app = create_app()

    with app.app_context():
        # Create tables
        print("Creating CooCook tables...")
        db.create_all()
        print("[OK] Tables created successfully")

        # Commit changes
        db.session.commit()
        print("[OK] Changes committed to database")


def seed_test_data():
    """Seed test data for CooCook"""
    app = create_app()

    with app.app_context():
        # Check if test data already exists
        existing_recipes = Recipe.query.count()
        if existing_recipes > 0:
            print(f"[OK] Test data already exists ({existing_recipes} recipes found). Skipping seed.")
            return

        print("\nSeeding test data...")

        # Create test users (chefs)
        chef1 = User.query.filter_by(email='chef1@coocook.com').first()
        if not chef1:
            chef1 = User(
                email='chef1@coocook.com',
                name='Gordon Ramsay',
                role='user',
                is_active=True
            )
            chef1.set_password('password123')
            db.session.add(chef1)
            db.session.flush()

        chef2 = User.query.filter_by(email='chef2@coocook.com').first()
        if not chef2:
            chef2 = User(
                email='chef2@coocook.com',
                name='Julia Child',
                role='user',
                is_active=True
            )
            chef2.set_password('password123')
            db.session.add(chef2)
            db.session.flush()

        # Test recipes data
        recipes_data = [
            {
                'name': 'Spaghetti Carbonara',
                'cuisine': 'Italian',
                'difficulty': 'medium',
                'prep_time': 20,
                'servings': 4,
                'ingredients': [
                    {'name': 'spaghetti', 'amount': 400, 'unit': 'g'},
                    {'name': 'eggs', 'amount': 4, 'unit': 'pcs'},
                    {'name': 'bacon', 'amount': 200, 'unit': 'g'},
                    {'name': 'parmesan cheese', 'amount': 100, 'unit': 'g'},
                    {'name': 'black pepper', 'amount': 1, 'unit': 'tsp'},
                ],
                'nutrition': {'calories': 450, 'protein': 25, 'carbs': 50, 'fat': 18},
                'description': 'Authentic Italian pasta with crispy bacon and creamy sauce',
                'price': 12.99,
            },
            {
                'name': 'Thai Green Curry',
                'cuisine': 'Thai',
                'difficulty': 'medium',
                'prep_time': 30,
                'servings': 4,
                'ingredients': [
                    {'name': 'coconut milk', 'amount': 400, 'unit': 'ml'},
                    {'name': 'green curry paste', 'amount': 3, 'unit': 'tbsp'},
                    {'name': 'chicken breast', 'amount': 500, 'unit': 'g'},
                    {'name': 'thai basil', 'amount': 1, 'unit': 'cup'},
                    {'name': 'lime juice', 'amount': 2, 'unit': 'tbsp'},
                ],
                'nutrition': {'calories': 320, 'protein': 28, 'carbs': 12, 'fat': 20},
                'description': 'Creamy Thai curry with aromatic basil and tender chicken',
                'price': 14.99,
            },
            {
                'name': 'Chocolate Chip Cookies',
                'cuisine': 'American',
                'difficulty': 'easy',
                'prep_time': 25,
                'servings': 24,
                'ingredients': [
                    {'name': 'butter', 'amount': 225, 'unit': 'g'},
                    {'name': 'sugar', 'amount': 200, 'unit': 'g'},
                    {'name': 'eggs', 'amount': 2, 'unit': 'pcs'},
                    {'name': 'flour', 'amount': 280, 'unit': 'g'},
                    {'name': 'chocolate chips', 'amount': 2, 'unit': 'cup'},
                    {'name': 'vanilla extract', 'amount': 2, 'unit': 'tsp'},
                ],
                'nutrition': {'calories': 210, 'protein': 2, 'carbs': 28, 'fat': 10},
                'description': 'Classic crispy-edged, chewy chocolate chip cookies',
                'price': None,
            },
            {
                'name': 'Korean Bibimbap',
                'cuisine': 'Korean',
                'difficulty': 'hard',
                'prep_time': 45,
                'servings': 2,
                'ingredients': [
                    {'name': 'white rice', 'amount': 2, 'unit': 'cup'},
                    {'name': 'beef ribeye', 'amount': 200, 'unit': 'g'},
                    {'name': 'spinach', 'amount': 200, 'unit': 'g'},
                    {'name': 'zucchini', 'amount': 1, 'unit': 'pcs'},
                    {'name': 'gochujang', 'amount': 3, 'unit': 'tbsp'},
                    {'name': 'egg', 'amount': 2, 'unit': 'pcs'},
                ],
                'nutrition': {'calories': 580, 'protein': 32, 'carbs': 65, 'fat': 22},
                'description': 'Mixed vegetables and beef over steamed rice with gochujang sauce',
                'price': 11.99,
            },
            {
                'name': 'Caesar Salad',
                'cuisine': 'Italian',
                'difficulty': 'easy',
                'prep_time': 15,
                'servings': 2,
                'ingredients': [
                    {'name': 'romaine lettuce', 'amount': 1, 'unit': 'head'},
                    {'name': 'parmesan cheese', 'amount': 50, 'unit': 'g'},
                    {'name': 'croutons', 'amount': 1, 'unit': 'cup'},
                    {'name': 'caesar dressing', 'amount': 100, 'unit': 'ml'},
                ],
                'nutrition': {'calories': 250, 'protein': 12, 'carbs': 20, 'fat': 14},
                'description': 'Crisp romaine lettuce with tangy Caesar dressing and crunchy croutons',
                'price': 8.99,
            },
            {
                'name': 'Pad Thai',
                'cuisine': 'Thai',
                'difficulty': 'medium',
                'prep_time': 25,
                'servings': 2,
                'ingredients': [
                    {'name': 'rice noodles', 'amount': 200, 'unit': 'g'},
                    {'name': 'shrimp', 'amount': 250, 'unit': 'g'},
                    {'name': 'tamarind paste', 'amount': 3, 'unit': 'tbsp'},
                    {'name': 'fish sauce', 'amount': 2, 'unit': 'tbsp'},
                    {'name': 'peanuts', 'amount': 100, 'unit': 'g'},
                    {'name': 'lime', 'amount': 1, 'unit': 'pcs'},
                ],
                'nutrition': {'calories': 380, 'protein': 24, 'carbs': 45, 'fat': 12},
                'description': 'Stir-fried rice noodles with succulent shrimp and tangy tamarind sauce',
                'price': 13.99,
            },
            {
                'name': 'Beef Bourguignon',
                'cuisine': 'French',
                'difficulty': 'hard',
                'prep_time': 120,
                'servings': 6,
                'ingredients': [
                    {'name': 'beef chuck', 'amount': 1500, 'unit': 'g'},
                    {'name': 'red wine', 'amount': 750, 'unit': 'ml'},
                    {'name': 'pearl onions', 'amount': 12, 'unit': 'pcs'},
                    {'name': 'mushrooms', 'amount': 400, 'unit': 'g'},
                    {'name': 'beef broth', 'amount': 500, 'unit': 'ml'},
                    {'name': 'tomato paste', 'amount': 2, 'unit': 'tbsp'},
                ],
                'nutrition': {'calories': 520, 'protein': 45, 'carbs': 15, 'fat': 28},
                'description': 'Tender beef braised in red wine with vegetables',
                'price': 18.99,
            },
            {
                'name': 'Fish Tacos',
                'cuisine': 'Mexican',
                'difficulty': 'easy',
                'prep_time': 20,
                'servings': 4,
                'ingredients': [
                    {'name': 'white fish fillet', 'amount': 600, 'unit': 'g'},
                    {'name': 'tortillas', 'amount': 8, 'unit': 'pcs'},
                    {'name': 'cabbage slaw', 'amount': 2, 'unit': 'cup'},
                    {'name': 'lime crema', 'amount': 100, 'unit': 'ml'},
                    {'name': 'cilantro', 'amount': 50, 'unit': 'g'},
                ],
                'nutrition': {'calories': 280, 'protein': 22, 'carbs': 30, 'fat': 8},
                'description': 'Crispy fish in soft tortillas with fresh slaw and lime crema',
                'price': 10.99,
            },
            {
                'name': 'Risotto Milanese',
                'cuisine': 'Italian',
                'difficulty': 'hard',
                'prep_time': 35,
                'servings': 4,
                'ingredients': [
                    {'name': 'arborio rice', 'amount': 300, 'unit': 'g'},
                    {'name': 'chicken broth', 'amount': 1, 'unit': 'l'},
                    {'name': 'saffron threads', 'amount': 1, 'unit': 'g'},
                    {'name': 'white wine', 'amount': 100, 'unit': 'ml'},
                    {'name': 'parmesan cheese', 'amount': 100, 'unit': 'g'},
                    {'name': 'butter', 'amount': 50, 'unit': 'g'},
                ],
                'nutrition': {'calories': 420, 'protein': 14, 'carbs': 52, 'fat': 16},
                'description': 'Creamy saffron-infused rice with luxurious butter finish',
                'price': 15.99,
            },
            {
                'name': 'Miso Ramen',
                'cuisine': 'Japanese',
                'difficulty': 'medium',
                'prep_time': 40,
                'servings': 2,
                'ingredients': [
                    {'name': 'ramen noodles', 'amount': 400, 'unit': 'g'},
                    {'name': 'miso paste', 'amount': 100, 'unit': 'g'},
                    {'name': 'chicken broth', 'amount': 1, 'unit': 'l'},
                    {'name': 'chicken breast', 'amount': 300, 'unit': 'g'},
                    {'name': 'green onions', 'amount': 2, 'unit': 'pcs'},
                    {'name': 'soft-boiled eggs', 'amount': 2, 'unit': 'pcs'},
                ],
                'nutrition': {'calories': 480, 'protein': 35, 'carbs': 58, 'fat': 14},
                'description': 'Rich miso broth with tender chicken and silky eggs',
                'price': 12.99,
            },
        ]

        # Create recipes
        for recipe_data in recipes_data:
            recipe = Recipe(
                name=recipe_data['name'],
                cuisine=recipe_data['cuisine'],
                difficulty=recipe_data['difficulty'],
                prep_time=recipe_data['prep_time'],
                servings=recipe_data['servings'],
                ingredients_json=recipe_data['ingredients'],
                nutrition_json=recipe_data['nutrition'],
                chef_id=chef1.id if recipes_data.index(recipe_data) % 2 == 0 else chef2.id,
                description=recipe_data['description'],
                price=recipe_data.get('price'),
                rating=4.5,
                review_count=0,
                like_count=0,
            )
            db.session.add(recipe)
            db.session.flush()

        db.session.commit()
        print(f"[OK] Created {len(recipes_data)} test recipes")

        # Create test shopping lists (using existing JSON-based model)
        user = User.query.filter_by(email='admin@softfactory.com').first()
        if user:
            shopping_list = ShoppingList(
                user_id=user.id,
                name='Weekly Groceries'
            )
            db.session.add(shopping_list)
            db.session.flush()

            # Add items to shopping list
            items = [
                {'ingredient': 'Milk', 'quantity': 2, 'unit': 'l', 'estimated_price': 4.99},
                {'ingredient': 'Eggs', 'quantity': 12, 'unit': 'pcs', 'estimated_price': 3.49},
                {'ingredient': 'Bread', 'quantity': 1, 'unit': 'pcs', 'estimated_price': 2.99},
            ]
            for item in items:
                item_obj = ShoppingListItem(
                    list_id=shopping_list.id,
                    ingredient=item['ingredient'],
                    quantity=item['quantity'],
                    unit=item['unit'],
                    estimated_price=item['estimated_price'],
                    is_checked=False
                )
                db.session.add(item_obj)

            db.session.commit()
            print(f"[OK] Created test shopping list with {len(items)} items")

        print("\n[OK] Test data seeding completed successfully!")


if __name__ == '__main__':
    try:
        create_tables()
        seed_test_data()
        print("\n[OK][OK][OK] CooCook database setup completed successfully! [OK][OK][OK]")
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
