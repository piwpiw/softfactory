# 🔌 CooCook Shopping List API v2.0

> **Purpose**: **Status:** Production Ready | **Base Path:** `/api/coocook` | **Auth:** Required (JWT + Subscription)
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 CooCook Shopping List API v2.0 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> Complete Shopping List Service with Recipe-based Auto-Merging and Price Estimation

**Status:** Production Ready | **Base Path:** `/api/coocook` | **Auth:** Required (JWT + Subscription)

---

## Overview

The Shopping List v2.0 API provides comprehensive shopping management with automatic recipe-based ingredient merging, duplicate removal, quantity consolidation, and price estimation for all items.

### Key Features
- **Recipe-based Creation:** Automatically merge ingredients from multiple recipes
- **Duplicate Management:** Smart ingredient deduplication with quantity summation
- **Price Estimation:** Per-item and total cost calculation
- **Item Management:** Add, update, check-off, delete items
- **Category Grouping:** Automatic ingredient categorization (produce, protein, dairy, etc.)

---

## Data Models

### ShoppingList Model (Database)
```python
{
    "id": 123,
    "user_id": 45,
    "name": "Weekly Shopping - 2026-02-26",
    "items": [
        {
            "name": "chicken breast",
            "quantity": 2,
            "unit": "lb",
            "checked": false,
            "category": "protein",
            "estimated_price": 8.99
        },
        ...
    ],
    "created_at": "2026-02-26T10:30:00",
    "updated_at": "2026-02-26T10:30:00"
}
```

### ShoppingListService Methods
```python
# Core Service Class: backend/services/shopping_list.py
class ShoppingListService:
    # Recipe-based list creation with auto-merging
    create_list(user_id, name, recipe_ids, serving_sizes)

    # Retrieve operations
    get_user_lists(user_id)
    get_list_details(list_id, user_id)

    # Item operations
    add_item(list_id, ingredient, quantity, unit, user_id)
    update_item(list_id, item_index, quantity, is_checked, user_id)
    delete_item(list_id, item_index, user_id)

    # Cost calculation
    calculate_total_price(list_id, user_id)

    # Helper
    _ingredient_category(name)  # Categorize by type
```

---

## API Endpoints

### 1. Create Shopping List
**POST** `/shopping-lists`

Creates a shopping list from recipes with automatic ingredient merging and deduplication.

#### Request
```json
{
    "name": "Weekly Shopping",
    "recipe_ids": [1, 2, 3],
    "serving_sizes": {"1": 2, "2": 1, "3": 1}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Display name; defaults to "Shopping List - YYYY-MM-DD" |
| `recipe_ids` | array | No | Menu IDs to merge ingredients from |
| `serving_sizes` | object | No | Map of recipe_id -> serving multiplier |

#### Response (201 Created)
```json
{
    "id": 123,
    "message": "Shopping list created successfully",
    "shopping_list": {
        "id": 123,
        "user_id": 45,
        "name": "Weekly Shopping",
        "items": [
            {
                "name": "rice",
                "quantity": 2,
                "unit": "pack",
                "checked": false,
                "category": "grain",
                "estimated_price": 2.50
            },
            {
                "name": "chicken breast",
                "quantity": 3,
                "unit": "pack",
                "checked": false,
                "category": "protein",
                "estimated_price": 8.99
            }
        ],
        "created_at": "2026-02-26T10:30:00",
        "updated_at": "2026-02-26T10:30:00"
    }
}
```

#### Example
```bash
curl -X POST http://localhost:8000/api/coocook/shopping-lists \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Family Dinner Shopping",
    "recipe_ids": [1, 2],
    "serving_sizes": {"1": 2, "2": 1}
  }'
```

---

### 2. Get All Shopping Lists
**GET** `/shopping-lists`

Retrieve all shopping lists for the authenticated user.

#### Response (200 OK)
```json
{
    "shopping_lists": [
        {
            "id": 123,
            "user_id": 45,
            "name": "Weekly Shopping",
            "items": [...],
            "created_at": "2026-02-26T10:30:00",
            "updated_at": "2026-02-26T10:30:00"
        },
        {
            "id": 124,
            "user_id": 45,
            "name": "Party Prep",
            "items": [...],
            "created_at": "2026-02-25T15:20:00",
            "updated_at": "2026-02-25T15:20:00"
        }
    ],
    "total": 2
}
```

---

### 3. Get Shopping List Details
**GET** `/shopping-lists/{list_id}`

Retrieve a specific shopping list with full details and price estimate.

#### Response (200 OK)
```json
{
    "shopping_list": {
        "id": 123,
        "user_id": 45,
        "name": "Weekly Shopping",
        "items": [...],
        "created_at": "2026-02-26T10:30:00",
        "updated_at": "2026-02-26T10:30:00"
    },
    "price_estimate": {
        "list_id": 123,
        "list_name": "Weekly Shopping",
        "item_breakdown": [
            {
                "name": "chicken breast",
                "quantity": 2,
                "unit": "lb",
                "unit_price": 8.99,
                "total_price": 17.98
            },
            {
                "name": "rice",
                "quantity": 1,
                "unit": "pack",
                "unit_price": 2.50,
                "total_price": 2.50
            }
        ],
        "total_items": 2,
        "estimated_total": 20.48,
        "currency": "USD"
    }
}
```

---

### 4. Update Shopping List
**PUT** `/shopping-lists/{list_id}`

Update a shopping list's name or items.

#### Request
```json
{
    "name": "Updated Shopping List Name",
    "items": [
        {
            "name": "chicken breast",
            "quantity": 3,
            "unit": "lb",
            "checked": true,
            "category": "protein",
            "estimated_price": 8.99
        }
    ]
}
```

#### Response (200 OK)
```json
{
    "message": "Shopping list updated",
    "shopping_list": { ... }
}
```

---

### 5. Delete Shopping List
**DELETE** `/shopping-lists/{list_id}`

Delete a shopping list permanently.

#### Response (200 OK)
```json
{
    "message": "Shopping list deleted"
}
```

---

### 6. Add Item to Shopping List
**POST** `/shopping-lists/{list_id}/items`

Add a single item to a shopping list. If item exists, quantity is summed.

#### Request
```json
{
    "ingredient": "chicken breast",
    "quantity": 2,
    "unit": "lb"
}
```

#### Response (201 Created)
```json
{
    "message": "Item added to shopping list",
    "shopping_list": { ... }
}
```

---

### 7. Update Shopping List Item
**PATCH** `/shopping-lists/{list_id}/items/{item_id}`

Update an item's quantity or checked status.

#### Request
```json
{
    "quantity": 3,
    "is_checked": true
}
```

#### Response (200 OK)
```json
{
    "message": "Item updated",
    "shopping_list": { ... }
}
```

---

### 8. Delete Shopping List Item
**DELETE** `/shopping-lists/{list_id}/items/{item_id}`

Remove a single item from the shopping list.

#### Response (200 OK)
```json
{
    "message": "Item deleted",
    "shopping_list": { ... }
}
```

---

### 9. Get Price Estimate
**GET** `/shopping-lists/{list_id}/price-estimate`

Calculate total estimated cost for all items.

#### Response (200 OK)
```json
{
    "list_id": 123,
    "list_name": "Weekly Shopping",
    "item_breakdown": [
        {
            "name": "chicken breast",
            "quantity": 2,
            "unit": "lb",
            "unit_price": 8.99,
            "total_price": 17.98
        },
        {
            "name": "salmon",
            "quantity": 1,
            "unit": "lb",
            "unit_price": 12.99,
            "total_price": 12.99
        }
    ],
    "total_items": 2,
    "estimated_total": 30.97,
    "currency": "USD"
}
```

---

## Ingredient Categories

Ingredients are automatically categorized into 5 groups:

| Category | Examples |
|----------|----------|
| **produce** | broccoli, spinach, onion, garlic, carrot, mushroom, potato |
| **protein** | chicken breast, beef, salmon, shrimp, tofu, egg |
| **grain** | rice, pasta |
| **dairy** | cheese, butter |
| **condiment** | soy sauce, olive oil, kimchi |
| **other** | Any unlisted ingredient |

---

## Ingredient Prices

Estimated prices (per unit) for cost calculation:

```
rice: $2.50/kg
chicken breast: $8.99/lb
salmon: $12.99/lb
tofu: $3.49/block
egg: $0.30/unit
pasta: $1.99/box
beef: $7.99/lb
shrimp: $14.99/lb
broccoli: $2.49/bunch
kimchi: $5.99/jar
mushroom: $4.99/lb
spinach: $3.49/bunch
onion: $0.99/unit
garlic: $0.50/bulb
olive oil: $8.99/bottle
soy sauce: $3.99/bottle
butter: $4.49/lb
potato: $1.99/lb
carrot: $0.79/lb
cheese: $6.99/lb
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
    "error": "Missing ingredient"
}
```

### 403 Forbidden (No Subscription)
```json
{
    "error": "Subscription required for coocook"
}
```

### 404 Not Found
```json
{
    "error": "Shopping list not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error"
}
```

---

## Implementation Details

### Service File: `backend/services/shopping_list.py` (309 lines)

**Key Methods:**

1. **create_list()** - Create list from recipes
   - Merges ingredients from multiple recipes
   - Handles serving size multipliers
   - Deduplicates by ingredient name (case-insensitive)
   - Sums quantities for duplicate items

2. **get_user_lists()** - Retrieve all user lists
   - Ordered by creation date (newest first)

3. **get_list_details()** - Get single list with auth check
   - Verifies user ownership

4. **add_item()** - Add/update item in list
   - Checks if item exists (case-insensitive)
   - Sums quantity if duplicate
   - Adds new item if unique

5. **update_item()** - Modify quantity/status
   - Updates by index
   - Supports partial updates

6. **delete_item()** - Remove item
   - Removes by index

7. **calculate_total_price()** - Cost breakdown
   - Per-item and total calculations
   - Rounds to 2 decimal places

8. **_ingredient_category()** - Auto-categorize
   - Uses lookup table
   - Defaults to 'other'

### Updated File: `backend/services/coocook.py`

**New Endpoints Added:** 8

- POST `/shopping-lists` — Create with recipe merging
- GET `/shopping-lists` — List all
- GET `/shopping-lists/{id}` — Get details + price
- PUT `/shopping-lists/{id}` — Update
- DELETE `/shopping-lists/{id}` — Delete
- POST `/shopping-lists/{id}/items` — Add item
- PATCH `/shopping-lists/{id}/items/{item_id}` — Update item
- DELETE `/shopping-lists/{id}/items/{item_id}` — Delete item
- GET `/shopping-lists/{id}/price-estimate` — Get cost

**Total CooCook Endpoints:** 33

---

## Database Integration

**Existing Model Used:** `ShoppingList` (backend/models.py, line 239)

```python
class ShoppingList(db.Model):
    __tablename__ = 'shopping_lists'
    __table_args__ = (
        Index('idx_shopping_list_user', 'user_id'),
        Index('idx_shopping_list_created', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    items = db.Column(db.JSON, default=list)  # [{name, quantity, unit, checked, category}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'items': self.items or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
```

---

## Usage Examples

### Create List from Multiple Recipes
```bash
curl -X POST http://localhost:8000/api/coocook/shopping-lists \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Family Dinner",
    "recipe_ids": [1, 3, 5],
    "serving_sizes": {"1": 2, "3": 1, "5": 2}
  }'
```

**Result:** Ingredients from recipes 1, 3, 5 merged with quantities multiplied by serving sizes.

### Add Item to Existing List
```bash
curl -X POST http://localhost:8000/api/coocook/shopping-lists/123/items \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredient": "olive oil",
    "quantity": 1,
    "unit": "bottle"
  }'
```

### Check Off Item
```bash
curl -X PATCH http://localhost:8000/api/coocook/shopping-lists/123/items/0 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_checked": true}'
```

### Get Total Cost
```bash
curl -X GET http://localhost:8000/api/coocook/shopping-lists/123/price-estimate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Testing Checklist

- [x] Service file created (309 lines)
- [x] All 9 endpoints implemented
- [x] Price estimation for 20 ingredients
- [x] Ingredient categorization (5 categories)
- [x] Recipe-based auto-merging
- [x] Duplicate deduplication
- [x] Quantity summation
- [x] User authorization checks
- [x] Database model integration
- [x] Error handling

---

## Performance Notes

- **List Creation:** O(n*m) where n=recipes, m=avg ingredients per recipe
- **Item Operations:** O(n) where n=total items in list
- **Price Calculation:** O(n) single pass through items
- **Database Queries:** Indexed by user_id and created_at for fast retrieval

---

**Version:** 2.0 | **Completed:** 2026-02-26 | **Time:** 30 minutes