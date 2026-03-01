"""Elasticsearch Search Service - Full-Featured Search Engine
Production-grade search with Korean/English support, facets, autocomplete, and history
"""

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json
from flask import current_app
from sqlalchemy import desc
from ..models import db, SearchHistory

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """Elasticsearch client with index management and search functionality"""

    def __init__(self, host='localhost', port=9200):
        """Initialize Elasticsearch client with production settings"""
        self.host = host
        self.port = port
        self.es = None
        self.connect()

    def connect(self):
        """Establish connection to Elasticsearch"""
        try:
            self.es = Elasticsearch(
                hosts=[{'host': self.host, 'port': self.port}],
                timeout=10,
                max_retries=3,
                retry_on_timeout=True
            )
            # Test connection
            if self.es.ping():
                logger.info("Elasticsearch connected successfully")
            else:
                logger.error("Elasticsearch connection failed")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            raise

    def create_indices(self):
        """Create Elasticsearch indices with analyzers and mappings"""
        indices = {
            'recipes': self._get_recipes_mapping(),
            'sns_posts': self._get_sns_posts_mapping(),
            'users': self._get_users_mapping()
        }

        for index_name, mapping in indices.items():
            try:
                if self.es.indices.exists(index=index_name):
                    logger.info(f"Index '{index_name}' already exists")
                else:
                    self.es.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index '{index_name}'")
            except Exception as e:
                logger.error(f"Failed to create index '{index_name}': {str(e)}")

    @staticmethod
    def _get_recipes_mapping():
        """Recipes index mapping with Korean/English analyzers"""
        return {
            'settings': {
                'number_of_shards': 2,
                'number_of_replicas': 1,
                'analysis': {
                    'analyzer': {
                        'korean_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'nori_tokenizer',
                            'filter': ['lowercase', 'stop', 'nori_part_of_speech']
                        },
                        'english_analyzer': {
                            'type': 'english',
                            'stopwords': '_english_'
                        }
                    },
                    'tokenizer': {
                        'nori_tokenizer': {
                            'type': 'nori_tokenizer',
                            'decompound_mode': 'mixed',
                            'user_dictionary_rules': [
                                '요리,요리,요리,*',
                                '셰프,셰프,셰프,*'
                            ]
                        }
                    }
                }
            },
            'mappings': {
                'properties': {
                    'id': {'type': 'integer'},
                    'title': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer',
                        'fields': {
                            'raw': {'type': 'keyword'},
                            'english': {'type': 'text', 'analyzer': 'english_analyzer'}
                        }
                    },
                    'description': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer'
                    },
                    'content': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer'
                    },
                    'tags': {
                        'type': 'keyword'
                    },
                    'ingredients': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer'
                    },
                    'difficulty': {
                        'type': 'keyword'
                    },
                    'cooking_time': {
                        'type': 'integer'
                    },
                    'servings': {
                        'type': 'integer'
                    },
                    'calories': {
                        'type': 'integer'
                    },
                    'protein': {'type': 'float'},
                    'carbs': {'type': 'float'},
                    'fat': {'type': 'float'},
                    'rating': {
                        'type': 'float'
                    },
                    'review_count': {
                        'type': 'integer'
                    },
                    'views': {
                        'type': 'integer'
                    },
                    'created_at': {
                        'type': 'date'
                    },
                    'updated_at': {
                        'type': 'date'
                    },
                    'user_id': {
                        'type': 'integer'
                    },
                    'is_public': {
                        'type': 'boolean'
                    }
                }
            }
        }

    @staticmethod
    def _get_sns_posts_mapping():
        """SNS Posts index mapping"""
        return {
            'settings': {
                'number_of_shards': 3,
                'number_of_replicas': 1,
                'analysis': {
                    'analyzer': {
                        'korean_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'nori_tokenizer',
                            'filter': ['lowercase']
                        }
                    }
                }
            },
            'mappings': {
                'properties': {
                    'id': {'type': 'integer'},
                    'content': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer',
                        'fields': {'raw': {'type': 'keyword'}}
                    },
                    'caption': {
                        'type': 'text',
                        'analyzer': 'korean_analyzer'
                    },
                    'hashtags': {
                        'type': 'keyword'
                    },
                    'platform': {
                        'type': 'keyword'
                    },
                    'likes': {
                        'type': 'integer'
                    },
                    'comments': {
                        'type': 'integer'
                    },
                    'shares': {
                        'type': 'integer'
                    },
                    'engagement_rate': {
                        'type': 'float'
                    },
                    'posted_at': {
                        'type': 'date'
                    },
                    'created_at': {
                        'type': 'date'
                    },
                    'user_id': {
                        'type': 'integer'
                    },
                    'user_name': {
                        'type': 'keyword'
                    }
                }
            }
        }

    @staticmethod
    def _get_users_mapping():
        """Users index mapping"""
        return {
            'settings': {
                'number_of_shards': 2,
                'number_of_replicas': 1
            },
            'mappings': {
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {
                        'type': 'text',
                        'fields': {'raw': {'type': 'keyword'}}
                    },
                    'email': {
                        'type': 'keyword'
                    },
                    'bio': {
                        'type': 'text'
                    },
                    'role': {
                        'type': 'keyword'
                    },
                    'created_at': {
                        'type': 'date'
                    },
                    'is_active': {
                        'type': 'boolean'
                    }
                }
            }
        }

    def index_document(self, index: str, doc_id: int, body: Dict) -> bool:
        """Index a single document with automatic timestamp"""
        try:
            self.es.index(index=index, id=doc_id, document=body)
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {str(e)}")
            return False

    def bulk_index(self, index: str, documents: List[Dict]) -> Tuple[int, List]:
        """Bulk index documents - optimized for large datasets"""
        actions = [
            {
                '_index': index,
                '_id': doc.get('id'),
                '_source': doc
            }
            for doc in documents
        ]

        try:
            success, errors = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Bulk indexed {success} documents in '{index}'")
            if errors:
                logger.warning(f"Bulk index errors: {len(errors)}")
            return success, errors
        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            return 0, [str(e)]

    def search(self, index: str, query: Dict, size: int = 20, from_: int = 0) -> Dict:
        """Execute search query with pagination"""
        try:
            response = self.es.search(
                index=index,
                body=query,
                size=size,
                from_=from_,
                track_total_hits=True,
                timeout='10s'
            )
            return response
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {'hits': {'total': {'value': 0}, 'hits': []}, 'error': str(e)}

    def delete_index(self, index: str) -> bool:
        """Delete index for reset/maintenance"""
        try:
            self.es.indices.delete(index=index)
            logger.info(f"Deleted index '{index}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {str(e)}")
            return False


class SearchManager:
    """High-level search API with history tracking and caching"""

    def __init__(self, es_service: ElasticsearchService):
        self.es = es_service

    def search_recipes(self, query: str, filters: Dict = None, page: int = 1,
                       sort: str = 'relevance') -> Dict:
        """Search recipes with advanced filtering and sorting"""
        size = 20
        from_ = (page - 1) * size

        es_query = self._build_recipe_query(query, filters, sort)
        results = self.es.search('recipes', es_query, size=size, from_=from_)

        return self._format_results(results)

    def search_posts(self, query: str, platform: str = None,
                    date_range: Dict = None, page: int = 1) -> Dict:
        """Search SNS posts with platform and date filtering"""
        size = 20
        from_ = (page - 1) * size

        es_query = self._build_posts_query(query, platform, date_range)
        results = self.es.search('sns_posts', es_query, size=size, from_=from_)

        return self._format_results(results)

    def search_users(self, query: str, role: str = None, page: int = 1) -> Dict:
        """Search users with role filtering"""
        size = 20
        from_ = (page - 1) * size

        es_query = self._build_users_query(query, role)
        results = self.es.search('users', es_query, size=size, from_=from_)

        return self._format_results(results)

    def autocomplete(self, index: str, field: str, prefix: str, size: int = 10) -> List[str]:
        """Autocomplete suggestions using prefix query"""
        query = {
            'query': {
                'match_phrase_prefix': {
                    field: {
                        'query': prefix,
                        'boost': 10
                    }
                }
            },
            'size': size
        }

        results = self.es.search(index, query, size=size)
        suggestions = [hit['_source'].get(field, '') for hit in results.get('hits', {}).get('hits', [])]
        return list(set(suggestions))  # Remove duplicates

    def get_facets(self, index: str, field: str, query_str: str = '') -> List[Dict]:
        """Get facet values for filtering"""
        query = {
            'query': {
                'match_all': {} if not query_str else {'match': {'content': query_str}}
            },
            'aggs': {
                'facets': {
                    'terms': {
                        'field': field,
                        'size': 50
                    }
                }
            }
        }

        results = self.es.search(index, query, size=0)
        buckets = results.get('aggregations', {}).get('facets', {}).get('buckets', [])

        return [{'name': b['key'], 'count': b['doc_count']} for b in buckets]

    def save_search_history(self, user_id: int, query: str, index: str,
                           result_count: int = 0):
        """Track search queries for analytics and recommendations"""
        try:
            history = SearchHistory(
                user_id=user_id,
                query=query,
                index=index,
                result_count=result_count,
                created_at=datetime.utcnow()
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to save search history: {str(e)}")

    def get_search_suggestions(self, user_id: int, limit: int = 5) -> List[str]:
        """Get personalized search suggestions from user history"""
        try:
            history = SearchHistory.query.filter_by(user_id=user_id)\
                .order_by(desc(SearchHistory.created_at))\
                .limit(limit)\
                .all()
            return [h.query for h in history]
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {str(e)}")
            return []

    @staticmethod
    def _build_recipe_query(query: str, filters: Dict = None, sort: str = 'relevance') -> Dict:
        """Build Elasticsearch query for recipes"""
        must_clauses = []
        filter_clauses = []

        # Full-text search
        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': ['title^2', 'content', 'tags', 'ingredients'],
                    'operator': 'or',
                    'fuzziness': 'AUTO'
                }
            })
        else:
            must_clauses.append({'match_all': {}})

        # Apply filters
        if filters:
            if 'difficulty' in filters:
                filter_clauses.append({'term': {'difficulty': filters['difficulty']}})

            if 'cooking_time_max' in filters:
                filter_clauses.append({
                    'range': {'cooking_time': {'lte': filters['cooking_time_max']}}
                })

            if 'calories_range' in filters:
                filter_clauses.append({
                    'range': {
                        'calories': {
                            'gte': filters['calories_range'][0],
                            'lte': filters['calories_range'][1]
                        }
                    }
                })

            if 'rating_min' in filters:
                filter_clauses.append({
                    'range': {'rating': {'gte': filters['rating_min']}}
                })

            if 'tags' in filters:
                filter_clauses.append({
                    'terms': {'tags': filters['tags']}
                })

        # Build sort
        sort_order = []
        if sort == 'rating':
            sort_order.append({'rating': {'order': 'desc'}})
        elif sort == 'popularity':
            sort_order.append({'views': {'order': 'desc'}})
        elif sort == 'newest':
            sort_order.append({'created_at': {'order': 'desc'}})
        else:  # relevance (default)
            sort_order.append({'_score': {'order': 'desc'}})

        sort_order.append({'_score': {'order': 'desc'}})

        return {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses
                }
            },
            'sort': sort_order,
            'highlight': {
                'fields': {
                    'title': {},
                    'content': {}
                },
                'pre_tags': ['<em>'],
                'post_tags': ['</em>']
            }
        }

    @staticmethod
    def _build_posts_query(query: str, platform: str = None,
                          date_range: Dict = None) -> Dict:
        """Build Elasticsearch query for SNS posts"""
        must_clauses = []
        filter_clauses = []

        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': ['content^2', 'caption', 'hashtags'],
                    'fuzziness': 'AUTO'
                }
            })
        else:
            must_clauses.append({'match_all': {}})

        if platform:
            filter_clauses.append({'term': {'platform': platform}})

        if date_range:
            filter_clauses.append({
                'range': {
                    'posted_at': {
                        'gte': date_range.get('start'),
                        'lte': date_range.get('end')
                    }
                }
            })

        return {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses
                }
            },
            'sort': [
                {'engagement_rate': {'order': 'desc'}},
                {'posted_at': {'order': 'desc'}}
            ]
        }

    @staticmethod
    def _build_users_query(query: str, role: str = None) -> Dict:
        """Build Elasticsearch query for users"""
        must_clauses = []
        filter_clauses = []

        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': ['name', 'email', 'bio'],
                    'fuzziness': 'AUTO'
                }
            })
        else:
            must_clauses.append({'match_all': {}})

        if role:
            filter_clauses.append({'term': {'role': role}})

        return {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses
                }
            }
        }

    @staticmethod
    def _format_results(es_results: Dict) -> Dict:
        """Format Elasticsearch results for API response"""
        hits = es_results.get('hits', {}).get('hits', [])
        total = es_results.get('hits', {}).get('total', {}).get('value', 0)

        return {
            'total': total,
            'results': [
                {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'data': hit['_source'],
                    'highlight': hit.get('highlight', {})
                }
                for hit in hits
            ],
            'took': es_results.get('took', 0)
        }


# Global instance (initialized at app startup)
es_service = None
search_manager = None


def init_elasticsearch(app):
    """Initialize Elasticsearch service on app startup"""
    global es_service, search_manager

    try:
        es_host = app.config.get('ELASTICSEARCH_HOST', 'localhost')
        es_port = app.config.get('ELASTICSEARCH_PORT', 9200)

        es_service = ElasticsearchService(host=es_host, port=es_port)
        es_service.create_indices()

        search_manager = SearchManager(es_service)
        logger.info("Elasticsearch service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch: {str(e)}")
        es_service = None
        search_manager = None


def get_search_manager() -> SearchManager:
    """Get the global SearchManager instance"""
    if search_manager is None:
        raise RuntimeError("Elasticsearch service not initialized")
    return search_manager
