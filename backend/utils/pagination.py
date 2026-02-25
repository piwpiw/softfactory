"""Pagination Utilities for SNS Endpoints

Implements:
- Cursor-based pagination (performant)
- Offset-based pagination (compatible)
- Partial response/field filtering
- Pagination metadata
"""

from typing import List, Dict, Any, Optional, Tuple
from flask import request, jsonify
from functools import wraps


class CursorPagination:
    """Cursor-based pagination for better performance"""

    @staticmethod
    def paginate_query(query, per_page: int = 50, cursor: Optional[int] = None):
        """
        Paginate query using cursor.

        Args:
            query: SQLAlchemy query
            per_page: Items per page
            cursor: Last item ID from previous page

        Returns:
            items, has_more, next_cursor
        """
        # Add one extra to check if more items exist
        items = query.limit(per_page + 1).all()

        has_more = len(items) > per_page
        items = items[:per_page]

        next_cursor = items[-1].id if (has_more and items) else None

        return items, has_more, next_cursor

    @staticmethod
    def build_response(items: List[Any], has_more: bool, next_cursor: Optional[int],
                      item_to_dict=None) -> dict:
        """Build pagination response"""
        if item_to_dict is None:
            item_to_dict = lambda x: x.to_dict() if hasattr(x, 'to_dict') else x

        return {
            'data': [item_to_dict(item) for item in items],
            'pagination': {
                'has_more': has_more,
                'next_cursor': next_cursor,
                'count': len(items)
            }
        }


class OffsetPagination:
    """Traditional offset-based pagination"""

    @staticmethod
    def paginate_query(query, page: int = 1, per_page: int = 50):
        """
        Paginate query using offset.

        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            items, page, total, pages
        """
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            paginated.items,
            paginated.page,
            paginated.total,
            paginated.pages
        )

    @staticmethod
    def build_response(items: List[Any], page: int, total: int, pages: int,
                      item_to_dict=None) -> dict:
        """Build pagination response"""
        if item_to_dict is None:
            item_to_dict = lambda x: x.to_dict() if hasattr(x, 'to_dict') else x

        return {
            'data': [item_to_dict(item) for item in items],
            'pagination': {
                'page': page,
                'per_page': len(items),
                'total': total,
                'pages': pages,
                'has_next': page < pages,
                'has_prev': page > 1
            }
        }


class FieldFilter:
    """Partial response - allow clients to request only certain fields"""

    @staticmethod
    def get_requested_fields(default_fields: List[str] = None) -> Optional[List[str]]:
        """
        Get fields parameter from query string.

        Usage:
            ?fields=id,title,description

        Returns:
            List of field names or None if not specified
        """
        fields_param = request.args.get('fields')
        if not fields_param:
            return default_fields

        return [f.strip() for f in fields_param.split(',')]

    @staticmethod
    def filter_dict(data: dict, fields: Optional[List[str]]) -> dict:
        """Filter dictionary to only include requested fields"""
        if not fields:
            return data

        return {k: v for k, v in data.items() if k in fields}

    @staticmethod
    def filter_list(items: List[dict], fields: Optional[List[str]]) -> List[dict]:
        """Filter list of dictionaries"""
        if not fields:
            return items

        return [FieldFilter.filter_dict(item, fields) for item in items]


class PaginationMixin:
    """Mixin for easy pagination in endpoints"""

    @staticmethod
    def parse_pagination_params() -> Tuple[Optional[int], int, str]:
        """
        Parse pagination parameters from request.

        Returns:
            (cursor/page, per_page, pagination_type)
        """
        pagination_type = request.args.get('pagination', 'cursor')  # cursor or offset

        if pagination_type == 'cursor':
            cursor = request.args.get('cursor', type=int)
            per_page = request.args.get('per_page', 50, type=int)
            per_page = min(per_page, 100)  # Cap at 100
            return cursor, per_page, 'cursor'
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            per_page = min(per_page, 100)  # Cap at 100
            return page, per_page, 'offset'

    @staticmethod
    def paginate_endpoint(pagination_type: str = 'cursor'):
        """Decorator for endpoints that support pagination"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Parse params
                if pagination_type == 'cursor':
                    cursor = request.args.get('cursor', type=int)
                    per_page = request.args.get('per_page', 50, type=int)
                    per_page = min(per_page, 100)

                    # Add to kwargs
                    kwargs['cursor'] = cursor
                    kwargs['per_page'] = per_page
                else:
                    page = request.args.get('page', 1, type=int)
                    per_page = request.args.get('per_page', 50, type=int)
                    per_page = min(per_page, 100)

                    kwargs['page'] = page
                    kwargs['per_page'] = per_page

                # Parse fields
                fields = FieldFilter.get_requested_fields()
                kwargs['fields'] = fields

                return f(*args, **kwargs)

            return decorated_function
        return decorator
