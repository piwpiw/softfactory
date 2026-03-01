"""Admin Service — User Management, Subscriptions, Metrics, Audit Logs"""
from flask import current_app
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from ..models import (
    db, User, Product, Subscription, Payment, SNSAccount,
    SNSAnalytics, ReviewAccount, Campaign, CampaignApplication, ErrorLog
)
import json


class AdminService:
    """Centralized admin operations with audit logging"""

    # ===== USER MANAGEMENT =====

    @staticmethod
    def get_users(page=1, per_page=50, search=None, role=None, status=None):
        """Retrieve paginated users with optional filtering"""
        query = User.query

        # Text search on email and name
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.name.ilike(f"%{search}%")
                )
            )

        # Filter by role
        if role:
            query = query.filter(User.role == role)

        # Filter by status
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        elif status == 'locked':
            query = query.filter(User.is_locked == True)

        # Paginate
        paginated = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'users': [u.to_dict() for u in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }

    @staticmethod
    def get_user_detail(user_id):
        """Retrieve full user details with related data"""
        user = User.query.get(user_id)
        if not user:
            return None

        detail = user.to_dict()
        detail.update({
            'subscriptions': [s.to_dict() for s in user.subscriptions],
            'payments_count': len(user.payments),
            'total_spent': sum(p.amount for p in user.payments),
            'sns_accounts': len(user.sns_accounts),
            'review_accounts': len(user.review_accounts),
            'campaigns_created': len(user.campaigns),
            'password_changed_at': user.password_changed_at.isoformat() if user.password_changed_at else None,
            'is_locked': user.is_locked,
            'locked_until': user.locked_until.isoformat() if user.locked_until else None,
            'email_verified': user.email_verified,
            'totp_enabled': user.totp_enabled
        })
        return detail

    @staticmethod
    def update_user_role(user_id, new_role, admin_id):
        """Change user role (user/admin)"""
        user = User.query.get(user_id)
        if not user:
            return None

        old_role = user.role
        user.role = new_role
        db.session.commit()

        AdminService.audit_log(
            admin_id=admin_id,
            action='UPDATE_ROLE',
            target_user_id=user_id,
            details={'old_role': old_role, 'new_role': new_role}
        )

        return user.to_dict()

    @staticmethod
    def toggle_user_active(user_id, is_active, admin_id):
        """Enable/disable user account"""
        user = User.query.get(user_id)
        if not user:
            return None

        old_status = user.is_active
        user.is_active = is_active
        db.session.commit()

        AdminService.audit_log(
            admin_id=admin_id,
            action='TOGGLE_ACTIVE',
            target_user_id=user_id,
            details={'old_status': old_status, 'new_status': is_active}
        )

        return user.to_dict()

    @staticmethod
    def unlock_user(user_id, admin_id):
        """Remove account lockout"""
        user = User.query.get(user_id)
        if not user:
            return None

        user.is_locked = False
        user.locked_until = None
        db.session.commit()

        AdminService.audit_log(
            admin_id=admin_id,
            action='UNLOCK_ACCOUNT',
            target_user_id=user_id
        )

        return user.to_dict()

    @staticmethod
    def delete_user(user_id, admin_id):
        """Delete user and all related data (cascading)"""
        user = User.query.get(user_id)
        if not user:
            return None

        user_email = user.email
        db.session.delete(user)
        db.session.commit()

        AdminService.audit_log(
            admin_id=admin_id,
            action='DELETE_USER',
            target_user_id=user_id,
            details={'email': user_email}
        )

        return {'success': True, 'deleted_user_id': user_id}

    @staticmethod
    def bulk_delete_users(user_ids, admin_id):
        """Delete multiple users"""
        users = User.query.filter(User.id.in_(user_ids)).all()
        count = len(users)

        for user in users:
            db.session.delete(user)

        db.session.commit()

        AdminService.audit_log(
            admin_id=admin_id,
            action='BULK_DELETE_USERS',
            details={'count': count, 'user_ids': user_ids}
        )

        return {'success': True, 'deleted_count': count}

    # ===== SUBSCRIPTION MANAGEMENT =====

    @staticmethod
    def get_subscriptions(page=1, per_page=50, user_id=None, product_id=None, status=None):
        """Retrieve subscriptions with filtering"""
        query = Subscription.query

        if user_id:
            query = query.filter(Subscription.user_id == user_id)
        if product_id:
            query = query.filter(Subscription.product_id == product_id)
        if status:
            query = query.filter(Subscription.status == status)

        paginated = query.order_by(desc(Subscription.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'subscriptions': [s.to_dict() for s in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages
        }

    @staticmethod
    def get_products(include_inactive=False):
        """Retrieve all products"""
        query = Product.query
        if not include_inactive:
            query = query.filter(Product.is_active == True)

        return [p.to_dict() for p in query.all()]

    @staticmethod
    def create_product(slug, name, monthly_price, annual_price=None, description=None, icon=None):
        """Create new product tier"""
        product = Product(
            slug=slug,
            name=name,
            monthly_price=monthly_price,
            annual_price=annual_price or monthly_price * 10,
            description=description,
            icon=icon,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        return product.to_dict()

    @staticmethod
    def update_product(product_id, **kwargs):
        """Update product details"""
        product = Product.query.get(product_id)
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        return product.to_dict()

    @staticmethod
    def delete_product(product_id):
        """Soft delete product (mark inactive)"""
        product = Product.query.get(product_id)
        if not product:
            return None

        product.is_active = False
        db.session.commit()
        return {'success': True}

    # ===== SYSTEM METRICS =====

    @staticmethod
    def get_system_stats():
        """Retrieve overall system metrics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        return {
            'users': {
                'total': User.query.count(),
                'active': User.query.filter(User.is_active == True).count(),
                'new_24h': User.query.filter(User.created_at >= last_24h).count(),
                'new_7d': User.query.filter(User.created_at >= last_7d).count(),
                'admins': User.query.filter(User.role == 'admin').count()
            },
            'subscriptions': {
                'total': Subscription.query.count(),
                'active': Subscription.query.filter(Subscription.status == 'active').count(),
                'canceled': Subscription.query.filter(Subscription.status == 'canceled').count(),
                'new_24h': Subscription.query.filter(Subscription.created_at >= last_24h).count()
            },
            'revenue': {
                'total_24h': sum(p.amount for p in Payment.query.filter(
                    Payment.created_at >= last_24h, Payment.status == 'completed'
                ).all() or []),
                'total_7d': sum(p.amount for p in Payment.query.filter(
                    Payment.created_at >= last_7d, Payment.status == 'completed'
                ).all() or []),
                'total_30d': sum(p.amount for p in Payment.query.filter(
                    Payment.created_at >= last_30d, Payment.status == 'completed'
                ).all() or []),
                'all_time': sum(p.amount for p in Payment.query.filter(
                    Payment.status == 'completed'
                ).all() or [])
            },
            'content': {
                'sns_accounts': SNSAccount.query.count(),
                'sns_posts': db.session.query(func.count()).select_from(SNSAccount).scalar() or 0,
                'review_accounts': ReviewAccount.query.count(),
                'campaigns': Campaign.query.count()
            },
            'errors': {
                'last_24h': ErrorLog.query.filter(ErrorLog.created_at >= last_24h).count(),
                'last_7d': ErrorLog.query.filter(ErrorLog.created_at >= last_7d).count()
            }
        }

    @staticmethod
    def get_revenue_stats(days=30):
        """Revenue breakdown by period"""
        now = datetime.utcnow()
        start = now - timedelta(days=days)

        payments = Payment.query.filter(
            and_(
                Payment.created_at >= start,
                Payment.status == 'completed'
            )
        ).all()

        # Group by date
        daily = {}
        for p in payments:
            date_key = p.created_at.strftime('%Y-%m-%d')
            daily[date_key] = daily.get(date_key, 0) + p.amount

        # Group by product
        by_product = {}
        for p in payments:
            product_name = p.product.name if p.product else 'Unknown'
            by_product[product_name] = by_product.get(product_name, 0) + p.amount

        return {
            'daily': daily,
            'by_product': by_product,
            'total': sum(payments, 0) if payments else 0,
            'period_days': days
        }

    @staticmethod
    def get_user_stats():
        """User growth and distribution stats"""
        now = datetime.utcnow()

        # Growth over time
        periods = {}
        for days in [7, 30, 90, 365]:
            start = now - timedelta(days=days)
            periods[f'last_{days}d'] = User.query.filter(User.created_at >= start).count()

        # Distribution
        return {
            'growth': periods,
            'by_role': {
                'admin': User.query.filter(User.role == 'admin').count(),
                'user': User.query.filter(User.role == 'user').count()
            },
            'by_status': {
                'active': User.query.filter(User.is_active == True).count(),
                'inactive': User.query.filter(User.is_active == False).count(),
                'locked': User.query.filter(User.is_locked == True).count()
            }
        }

    # ===== AUDIT LOGGING =====

    @staticmethod
    def audit_log(admin_id, action, target_user_id=None, details=None):
        """Record admin action for audit trail"""
        try:
            log = ErrorLog(
                error_type='ADMIN_ACTION',
                message=f'Admin {admin_id}: {action}',
                context={
                    'admin_id': admin_id,
                    'action': action,
                    'target_user_id': target_user_id,
                    'details': details
                },
                severity='info'
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Audit log failed: {str(e)}")

    @staticmethod
    def get_audit_logs(page=1, per_page=100, action=None, admin_id=None):
        """Retrieve audit logs"""
        query = ErrorLog.query.filter(ErrorLog.error_type == 'ADMIN_ACTION')

        if action:
            query = query.filter(ErrorLog.message.ilike(f"%{action}%"))

        if admin_id:
            # Search in context JSON for admin_id
            pass  # SQLite/JSON filtering would be complex; skip for now

        paginated = query.order_by(desc(ErrorLog.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'logs': [
                {
                    'id': log.id,
                    'action': log.message,
                    'details': log.context or {},
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'severity': log.severity
                }
                for log in paginated.items
            ],
            'total': paginated.total,
            'pages': paginated.pages
        }

    # ===== SNS MONITORING =====

    @staticmethod
    def get_sns_accounts_summary(limit=50):
        """Summary of all SNS accounts"""
        accounts = SNSAccount.query.limit(limit).all()

        return [
            {
                'id': a.id,
                'user_id': a.user_id,
                'platform': a.platform,
                'account_name': a.account_name,
                'followers': a.followers or 0,
                'posts_count': a.posts_count or 0,
                'created_at': a.created_at.isoformat() if a.created_at else None
            }
            for a in accounts
        ]

    # ===== CAMPAIGN MONITORING =====

    @staticmethod
    def get_campaigns_summary(limit=50):
        """Summary of active campaigns"""
        campaigns = Campaign.query.order_by(desc(Campaign.created_at)).limit(limit).all()

        return [
            {
                'id': c.id,
                'title': c.title,
                'creator_id': c.creator_id,
                'status': c.status,
                'start_date': c.start_date.isoformat() if c.start_date else None,
                'end_date': c.end_date.isoformat() if c.end_date else None,
                'applications': len(c.applications) if hasattr(c, 'applications') else 0
            }
            for c in campaigns
        ]

    @staticmethod
    def export_users_csv():
        """Generate CSV data of all users"""
        users = User.query.all()

        csv_lines = ['ID,Email,Name,Role,Status,Created At']
        for u in users:
            status = 'Active' if u.is_active else 'Inactive'
            csv_lines.append(
                f'{u.id},{u.email},{u.name},{u.role},{status},{u.created_at.isoformat()}'
            )

        return '\n'.join(csv_lines)

    @staticmethod
    def export_payments_csv():
        """Generate CSV data of all payments"""
        payments = Payment.query.all()

        csv_lines = ['ID,User,Product,Amount,Status,Date']
        for p in payments:
            csv_lines.append(
                f'{p.id},{p.user.email},{p.product.name if p.product else "N/A"},{p.amount},{p.status},{p.created_at.isoformat()}'
            )

        return '\n'.join(csv_lines)
