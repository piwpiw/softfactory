"""SoftFactory Database Models"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ============ PLATFORM ============

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    sns_accounts = db.relationship('SNSAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    sns_posts = db.relationship('SNSPost', backref='user', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='creator', lazy=True, cascade='all, delete-orphan', foreign_keys='Campaign.creator_id')
    campaign_applications = db.relationship('CampaignApplication', backref='user', lazy=True, cascade='all, delete-orphan')
    ai_employees = db.relationship('AIEmployee', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # emoji or icon name
    monthly_price = db.Column(db.Float, nullable=False)
    annual_price = db.Column(db.Float)
    stripe_price_id_monthly = db.Column(db.String(255))
    stripe_price_id_annual = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    subscriptions = db.relationship('Subscription', backref='product', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'monthly_price': self.monthly_price,
            'annual_price': self.annual_price,
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255))
    plan_type = db.Column(db.String(20), default='monthly')  # 'monthly' or 'annual'
    status = db.Column(db.String(20), default='active')  # 'active', 'canceled', 'expired'
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'plan_type': self.plan_type,
            'status': self.status,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ COOCOOK ============

class Chef(db.Model):
    __tablename__ = 'chefs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text)
    cuisine_type = db.Column(db.String(50))  # Korean, Italian, Japanese, French, Mexican
    location = db.Column(db.String(200))
    price_per_session = db.Column(db.Float, nullable=False)  # USD
    rating = db.Column(db.Float, default=5.0)
    rating_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='chef', lazy=True, cascade='all, delete-orphan')


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chef_id = db.Column(db.Integer, db.ForeignKey('chefs.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Integer, default=2)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'completed', 'canceled'
    total_price = db.Column(db.Float, nullable=False)
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class BookingPayment(db.Model):
    __tablename__ = "booking_payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="KRW")
    status = db.Column(db.String(20), default="completed")
    transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BookingReview(db.Model):
    __tablename__ = "booking_reviews"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    chef_id = db.Column(db.Integer, db.ForeignKey("chefs.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "chef_id": self.chef_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
# ============ SNS AUTO ============

class SNSAccount(db.Model):
    __tablename__ = 'sns_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50))  # 'instagram', 'blog', 'tiktok', 'youtube_shorts'
    account_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('SNSPost', backref='account', lazy=True, cascade='all, delete-orphan')


class SNSPost(db.Model):
    __tablename__ = 'sns_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('sns_accounts.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(50))
    status = db.Column(db.String(20), default='draft')  # 'draft', 'scheduled', 'published', 'failed'
    scheduled_at = db.Column(db.DateTime)
    template_type = db.Column(db.String(50))  # 'card_news', 'blog_post', 'reel', 'shorts'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ REVIEW CAMPAIGNS ============

class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'beauty', 'food', 'tech', 'fashion'
    reward_type = db.Column(db.String(50))  # 'product', 'cash', 'both'
    reward_value = db.Column(db.String(200))  # e.g., "$50" or "Free product"
    max_reviewers = db.Column(db.Integer, default=10)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('CampaignApplication', backref='campaign', lazy=True, cascade='all, delete-orphan')


class CampaignApplication(db.Model):
    __tablename__ = 'campaign_applications'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)  # Why they want to review
    sns_link = db.Column(db.String(500))
    follower_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ AI AUTOMATION ============

class AIEmployee(db.Model):
    """AI Employee (Automation Instance)"""
    __tablename__ = 'ai_employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    scenario_type = db.Column(db.String(50), nullable=False)  # email, social, customer_service, data_entry, scheduling
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, training, active, paused
    monthly_savings_hours = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'description': self.description,
            'status': self.status,
            'monthly_savings_hours': self.monthly_savings_hours,
            'created_at': self.created_at.isoformat(),
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None
        }


class Scenario(db.Model):
    """Pre-built Automation Scenario Template"""
    __tablename__ = 'scenarios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # email, social, customer_service, data_entry, scheduling
    description = db.Column(db.Text)
    estimated_savings = db.Column(db.Integer)  # hours/month
    complexity = db.Column(db.String(20))  # easy, medium, advanced
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'estimated_savings': self.estimated_savings,
            'complexity': self.complexity,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat()
        }


# ============ WEBAPP BUILDER ============

class BootcampEnrollment(db.Model):
    """User enrolled in bootcamp course"""
    __tablename__ = 'bootcamp_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # 'weekday' or 'weekend'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='enrolled')  # enrolled, in_progress, completed, dropped
    progress = db.Column(db.Integer, default=0)  # 0-100%
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bootcamp_enrollments')

    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan_type,
            'status': self.status,
            'progress': self.progress,
            'start': self.start_date.isoformat(),
            'end': self.end_date.isoformat(),
            'days_remaining': (self.end_date - datetime.utcnow()).days
        }


class WebApp(db.Model):
    """User's built webapp"""
    __tablename__ = 'webapps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500))  # Live URL
    status = db.Column(db.String(20), default='draft')  # draft, building, deployed, live
    code_repo = db.Column(db.String(500))  # GitHub URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='webapps')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'url': self.url,
            'repo': self.code_repo,
            'created': self.created_at.isoformat(),
            'deployed': self.deployed_at.isoformat() if self.deployed_at else None
        }


def init_db(app):
    """Initialize database with tables and seed data"""
    with app.app_context():
        db.create_all()

        # Check if data already exists
        if User.query.count() > 0:
            return

        # Create admin user
        admin = User(email='admin@softfactory.com', name='Admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # Create 5 products
        products = [
            Product(slug='coocook', name='CooCook', description='Local food experiences & chef booking',
                   icon='🍳', monthly_price=29.0, annual_price=290.0),
            Product(slug='sns-auto', name='SNS Auto', description='Auto-post to Instagram, Blog, TikTok, Shorts',
                   icon='📱', monthly_price=49.0, annual_price=490.0),
            Product(slug='review', name='Review Campaign', description='Brand review & influencer campaigns',
                   icon='⭐', monthly_price=39.0, annual_price=390.0),
            Product(slug='ai-automation', name='AI Automation', description='24/7 AI employees for business automation',
                   icon='🤖', monthly_price=89.0, annual_price=890.0),
            Product(slug='webapp-builder', name='WebApp Builder', description='8-week bootcamp: Learn automation + build your own web app',
                   icon='💻', monthly_price=590000.0, annual_price=None),
        ]
        for product in products:
            db.session.add(product)

        # Create sample user
        user = User(email='demo@softfactory.com', name='Demo User', role='user')
        user.set_password('demo123')
        db.session.add(user)

        db.session.commit()

        # Create sample chefs (after commit to get user_id)
        chefs = [
            Chef(user_id=user.id, name='Chef Park', bio='Korean traditional cuisine',
                cuisine_type='Korean', location='Seoul', price_per_session=120.0),
            Chef(user_id=user.id, name='Chef Marco', bio='Italian pasta & risotto expert',
                cuisine_type='Italian', location='Seoul', price_per_session=130.0),
            Chef(user_id=user.id, name='Chef Tanaka', bio='Authentic Japanese sushi master',
                cuisine_type='Japanese', location='Seoul', price_per_session=150.0),
            Chef(user_id=user.id, name='Chef Dubois', bio='French culinary techniques',
                cuisine_type='French', location='Seoul', price_per_session=140.0),
            Chef(user_id=user.id, name='Chef Garcia', bio='Authentic Mexican street food',
                cuisine_type='Mexican', location='Seoul', price_per_session=110.0),
        ]
        for chef in chefs:
            db.session.add(chef)

        # Create sample campaigns
        campaigns = [
            Campaign(creator_id=admin.id, title='New Skincare Product Launch',
                    product_name='GlowSkin Pro', category='beauty',
                    reward_type='product', reward_value='Free $150 skincare kit',
                    max_reviewers=20, deadline=datetime.utcnow() + timedelta(days=30)),
            Campaign(creator_id=admin.id, title='Organic Coffee Brand Review',
                    product_name='BeanBliss Coffee', category='food',
                    reward_type='cash', reward_value='$50 gift card',
                    max_reviewers=15, deadline=datetime.utcnow() + timedelta(days=25)),
            Campaign(creator_id=admin.id, title='Latest Tech Gadget Review',
                    product_name='SmartHub X3', category='tech',
                    reward_type='both', reward_value='Product + $75 bonus',
                    max_reviewers=10, deadline=datetime.utcnow() + timedelta(days=20)),
        ]
        for campaign in campaigns:
            db.session.add(campaign)

        # Create sample automation scenarios
        scenarios = [
            Scenario(name='Email Response Automation', category='email', complexity='easy',
                    description='AI automatically responds to customer emails', estimated_savings=15, is_premium=False),
            Scenario(name='Social Media Posting', category='social', complexity='medium',
                    description='AI writes and posts content to social media', estimated_savings=20, is_premium=False),
            Scenario(name='Customer Support Bot', category='customer_service', complexity='advanced',
                    description='24/7 AI customer support with escalation to humans', estimated_savings=30, is_premium=True),
            Scenario(name='Data Entry Automation', category='data_entry', complexity='medium',
                    description='AI extracts and enters data from documents', estimated_savings=25, is_premium=False),
            Scenario(name='Meeting Scheduling', category='scheduling', complexity='easy',
                    description='AI manages calendar and schedules meetings', estimated_savings=10, is_premium=False),
        ]
        for scenario in scenarios:
            db.session.add(scenario)

        db.session.commit()
