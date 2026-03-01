"""
i18n Database Models for JARVIS
Stores user language preferences and custom translations.
"""

from datetime import datetime
from .models import db


class UserLanguagePreference(db.Model):
    """
    Stores user's language preference.
    """
    __tablename__ = 'user_language_preferences'
    __table_args__ = (
        db.Index('idx_user_language', 'user_id'),
        db.Index('idx_language', 'language'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    language = db.Column(db.String(10), default='en')  # e.g., 'en', 'ko', 'ja', 'zh'
    timezone = db.Column(db.String(50), default='UTC')  # e.g., 'America/New_York'
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    time_format = db.Column(db.String(20), default='HH:mm:ss')
    currency_code = db.Column(db.String(10), default='USD')
    theme = db.Column(db.String(20), default='dark')  # 'dark', 'light', 'auto'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'language': self.language,
            'timezone': self.timezone,
            'date_format': self.date_format,
            'time_format': self.time_format,
            'currency_code': self.currency_code,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TranslationKey(db.Model):
    """
    Stores translation keys and their base values.
    Used for managing and querying available translations.
    """
    __tablename__ = 'translation_keys'
    __table_args__ = (
        db.Index('idx_key', 'key'),
        db.Index('idx_category', 'category'),
    )

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'error', 'success', 'validation', 'ui'
    description = db.Column(db.Text)
    default_value = db.Column(db.Text, nullable=False)  # English value
    requires_interpolation = db.Column(db.Boolean, default=False)
    interpolation_params = db.Column(db.JSON)  # e.g., ['min', 'max']
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to translations
    translations = db.relationship('Translation', backref='translation_key', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'category': self.category,
            'description': self.description,
            'default_value': self.default_value,
            'requires_interpolation': self.requires_interpolation,
            'interpolation_params': self.interpolation_params,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Translation(db.Model):
    """
    Stores translations for specific languages and keys.
    """
    __tablename__ = 'translations'
    __table_args__ = (
        db.Index('idx_key_language', 'translation_key_id', 'language'),
        db.Index('idx_language', 'language'),
        db.Index('idx_status', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    translation_key_id = db.Column(db.Integer, db.ForeignKey('translation_keys.id'), nullable=False)
    language = db.Column(db.String(10), nullable=False)  # 'en', 'ko', 'ja', 'zh'
    value = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='approved')  # 'draft', 'pending_review', 'approved', 'outdated'
    translator = db.Column(db.String(120))
    reviewer = db.Column(db.String(120))
    reviewed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    is_automated = db.Column(db.Boolean, default=False)  # True if translated by automated service
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.translation_key.key if self.translation_key else None,
            'language': self.language,
            'value': self.value,
            'status': self.status,
            'translator': self.translator,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class EmailTemplate(db.Model):
    """
    Stores multi-language email templates.
    """
    __tablename__ = 'email_templates'
    __table_args__ = (
        db.Index('idx_template_name', 'template_name'),
        db.Index('idx_language', 'language'),
    )

    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(100), nullable=False)  # e.g., 'welcome', 'password_reset'
    language = db.Column(db.String(10), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    html_body = db.Column(db.Text, nullable=False)
    text_body = db.Column(db.Text)
    variables = db.Column(db.JSON)  # e.g., ['name', 'email', 'reset_url']
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'language': self.language,
            'subject': self.subject,
            'variables': self.variables,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LocalizationLog(db.Model):
    """
    Logs all localization changes and accesses.
    Used for auditing translation management.
    """
    __tablename__ = 'localization_logs'
    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_action', 'action'),
        db.Index('idx_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)  # 'update_language', 'add_translation', 'modify_template'
    resource_type = db.Column(db.String(50))  # 'translation', 'email_template', 'language_preference'
    resource_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    changes = db.Column(db.JSON)  # Track what changed
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
