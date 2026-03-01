"""
i18n (Internationalization) Module for JARVIS Backend
Handles multi-language support for API responses, emails, and messages.

Usage:
    from .i18n import I18nManager, get_translated_message, require_language

    # Translate a key
    message = get_translated_message('error_not_found', lang='en')

    # Use middleware
    from flask import g
    @app.before_request
    def before_request():
        g.language = request.args.get('lang', 'en')
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache
from flask import request, g, jsonify


class I18nManager:
    """
    Manages translations for the JARVIS application.
    Loads JSON translation files and provides translation methods.
    """

    def __init__(self, locales_dir: str = None):
        """
        Initialize the I18n manager.

        Args:
            locales_dir: Path to directory containing locale JSON files.
                        Defaults to PROJECT_ROOT/locales
        """
        if locales_dir is None:
            locales_dir = os.path.join(
                os.path.dirname(__file__),
                '..',
                'locales'
            )

        self.locales_dir = locales_dir
        self.supported_languages = ['ko', 'en', 'ja', 'zh']
        self.default_language = 'en'
        self.translations: Dict[str, Dict[str, str]] = {}

        # Load all translations on init
        self._load_all_translations()

    def _load_all_translations(self) -> None:
        """Load all translation files into memory."""
        for lang in self.supported_languages:
            self.load_language(lang)

    @lru_cache(maxsize=4)
    def load_language(self, lang: str) -> Dict[str, str]:
        """
        Load translations for a specific language.

        Args:
            lang: Language code (e.g., 'en', 'ko')

        Returns:
            Dictionary of translations
        """
        if lang in self.translations:
            return self.translations[lang]

        file_path = os.path.join(self.locales_dir, f'{lang}.json')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations[lang] = json.load(f)
                return self.translations[lang]
        except FileNotFoundError:
            print(f"Warning: Translation file not found: {file_path}")
            if lang != self.default_language:
                return self.load_language(self.default_language)
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding translation file {file_path}: {e}")
            return {}

    def get(
        self,
        key: str,
        lang: str = None,
        params: Dict[str, Any] = None,
        default: str = None
    ) -> str:
        """
        Get a translated string.

        Args:
            key: Translation key (e.g., 'error_not_found')
            lang: Language code. Defaults to current request language.
            params: Parameters for string interpolation
            default: Default value if key not found

        Returns:
            Translated string
        """
        if lang is None:
            lang = self.get_current_language()

        # Ensure language is supported
        if lang not in self.supported_languages:
            lang = self.default_language

        # Get translation
        translation = self.translations.get(lang, {}).get(key)

        if translation is None:
            if default is not None:
                translation = default
            else:
                print(f"Warning: Translation key not found: {key} ({lang})")
                translation = key

        # Handle interpolation
        if params:
            for param_key, param_value in params.items():
                translation = translation.replace(
                    f"{{{{{param_key}}}}}",
                    str(param_value)
                )

        return translation

    def translate_dict(
        self,
        data: Dict,
        lang: str = None,
        keys_to_translate: list = None
    ) -> Dict:
        """
        Translate specific keys in a dictionary.

        Args:
            data: Dictionary to translate
            lang: Language code
            keys_to_translate: List of keys to translate

        Returns:
            Dictionary with translated values
        """
        if lang is None:
            lang = self.get_current_language()

        result = data.copy()

        if keys_to_translate is None:
            return result

        for key in keys_to_translate:
            if key in result and isinstance(result[key], str):
                # If value looks like a translation key
                if result[key].startswith('error_') or \
                   result[key].startswith('success_') or \
                   result[key].startswith('warning_'):
                    result[key] = self.get(result[key], lang)

        return result

    def get_current_language(self) -> str:
        """
        Get the current request language.

        Priority:
        1. URL parameter ?lang=xx
        2. HTTP header Accept-Language
        3. Flask g.language (set by middleware)
        4. Default language

        Returns:
            Language code
        """
        # Check Flask g object
        if hasattr(g, 'language') and g.language:
            return g.language

        # Check URL parameter
        lang = request.args.get('lang', '').lower()
        if lang in self.supported_languages:
            return lang

        # Check Accept-Language header
        best_lang = request.accept_languages.best_match(self.supported_languages)
        if best_lang:
            return best_lang

        return self.default_language

    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return self.supported_languages

    def is_supported(self, lang: str) -> bool:
        """Check if language is supported."""
        return lang in self.supported_languages


# Global instance
_i18n_manager = None


def get_i18n_manager() -> I18nManager:
    """Get or create the global I18n manager instance."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def init_i18n(app, locales_dir: str = None):
    """
    Initialize i18n for Flask application.

    Args:
        app: Flask application instance
        locales_dir: Path to locales directory
    """
    global _i18n_manager
    _i18n_manager = I18nManager(locales_dir)

    # Add before_request handler
    @app.before_request
    def before_request():
        g.language = _i18n_manager.get_current_language()

    # Add utility functions to template context
    @app.context_processor
    def inject_i18n():
        return {
            't': lambda key, **kwargs: _i18n_manager.get(key, g.language, kwargs)
        }


def get_translated_message(
    key: str,
    lang: str = None,
    params: Dict[str, Any] = None
) -> str:
    """
    Get a translated message string.

    Args:
        key: Translation key
        lang: Language code
        params: Interpolation parameters

    Returns:
        Translated string
    """
    manager = get_i18n_manager()
    return manager.get(key, lang, params)


def translate_error_response(
    error_key: str,
    status_code: int = 400,
    lang: str = None,
    details: Dict = None
) -> tuple:
    """
    Create a translated error response.

    Args:
        error_key: Error translation key
        status_code: HTTP status code
        lang: Language code
        details: Additional error details

    Returns:
        Tuple of (response_dict, status_code)
    """
    manager = get_i18n_manager()
    if lang is None:
        lang = manager.get_current_language()

    response = {
        'error': True,
        'message': manager.get(error_key, lang),
        'code': error_key,
        'language': lang
    }

    if details:
        response['details'] = details

    return response, status_code


def translate_success_response(
    message_key: str,
    data: Dict = None,
    lang: str = None
) -> Dict:
    """
    Create a translated success response.

    Args:
        message_key: Success message translation key
        data: Additional response data
        lang: Language code

    Returns:
        Response dictionary
    """
    manager = get_i18n_manager()
    if lang is None:
        lang = manager.get_current_language()

    response = {
        'success': True,
        'message': manager.get(message_key, lang),
        'language': lang
    }

    if data:
        response['data'] = data

    return response


# API error messages mapping
API_ERROR_MESSAGES = {
    400: 'api_error_400',
    401: 'api_error_401',
    403: 'api_error_403',
    404: 'api_error_404',
    409: 'api_error_409',
    429: 'api_error_429',
    500: 'api_error_500',
    502: 'api_error_502',
    503: 'api_error_503',
}


def api_error_response(
    status_code: int,
    message: str = None,
    lang: str = None,
    details: Dict = None
) -> tuple:
    """
    Create an API error response with translation.

    Args:
        status_code: HTTP status code
        message: Custom message or translation key
        lang: Language code
        details: Additional details

    Returns:
        Tuple of (response_dict, status_code)
    """
    manager = get_i18n_manager()
    if lang is None:
        lang = manager.get_current_language()

    # Get translated message
    if message and message in API_ERROR_MESSAGES.values():
        translated_message = manager.get(message, lang)
    elif message and message.startswith('api_error_'):
        translated_message = manager.get(message, lang)
    else:
        error_key = API_ERROR_MESSAGES.get(status_code, 'api_error_500')
        translated_message = manager.get(error_key, lang)
        if message:
            translated_message = f"{translated_message}: {message}"

    response = {
        'error': True,
        'message': translated_message,
        'status_code': status_code,
        'language': lang
    }

    if details:
        response['details'] = details

    return response, status_code


# Validation error messages
def get_validation_error_message(
    field: str,
    rule: str,
    params: Dict = None,
    lang: str = None
) -> str:
    """
    Get a validation error message.

    Args:
        field: Field name
        rule: Validation rule (required, email, min_length, max_length, pattern)
        params: Rule parameters
        lang: Language code

    Returns:
        Translated validation message
    """
    manager = get_i18n_manager()
    if lang is None:
        lang = manager.get_current_language()

    # Map validation rules to translation keys
    rule_map = {
        'required': 'validation_required',
        'email': 'validation_email',
        'min_length': 'validation_min_length',
        'max_length': 'validation_max_length',
        'pattern': 'validation_pattern',
    }

    key = rule_map.get(rule, 'validation_required')
    return manager.get(key, lang, params)


def get_validation_errors(
    errors: Dict[str, str],
    lang: str = None
) -> Dict[str, str]:
    """
    Translate validation errors.

    Args:
        errors: Dictionary of field -> error message
        lang: Language code

    Returns:
        Dictionary with translated error messages
    """
    manager = get_i18n_manager()
    if lang is None:
        lang = manager.get_current_language()

    translated = {}
    for field, message in errors.items():
        # If message is a translation key, translate it
        if isinstance(message, str) and (
            message.startswith('validation_') or
            message.startswith('error_')
        ):
            translated[field] = manager.get(message, lang)
        else:
            translated[field] = message

    return translated


# Email subject and template translation
def get_email_subject(subject_key: str, lang: str = None) -> str:
    """Get translated email subject."""
    return get_translated_message(f'email_subject_{subject_key}', lang)


def get_email_greeting(lang: str = None) -> str:
    """Get translated email greeting."""
    return get_translated_message('email_greeting', lang)


def get_email_farewell(lang: str = None) -> str:
    """Get translated email farewell."""
    return get_translated_message('email_farewell', lang)


def get_email_company_name(lang: str = None) -> str:
    """Get translated company name for email."""
    return get_translated_message('email_company', lang)
