"""Email Service — AWS SES / SMTP production email sending"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

logger = logging.getLogger('email_service')

# Attempt to load Jinja2; graceful fallback to plain-text if unavailable
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning('Jinja2 not installed — email templates will use plain-text fallback')

# Attempt to load boto3; graceful fallback to SMTP if unavailable
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.info('boto3 not installed — AWS SES unavailable, using SMTP')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATE_DIR = Path(__file__).parent.parent.parent / 'web' / 'email-templates'

DEV_MODE = os.getenv('EMAIL_DEV_MODE', 'false').lower() in ('true', '1', 'yes')


class EmailService:
    """Production-ready email service supporting AWS SES and SMTP.

    In development (no config / EMAIL_DEV_MODE=true) emails are logged to
    the console instead of being sent — no exceptions are raised.
    """

    def __init__(self):
        self.provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()  # 'ses' or 'smtp'
        self.from_email = os.getenv('EMAIL_FROM', 'noreply@softfactory.kr')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'SoftFactory')
        self._ses_client = None
        self._init_provider()
        self._init_templates()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_provider(self):
        """Validate provider choice; fall back to SMTP when SES is unavailable."""
        if self.provider == 'ses':
            if not BOTO3_AVAILABLE:
                logger.warning('AWS SES selected but boto3 is not installed. Falling back to SMTP.')
                self.provider = 'smtp'
            else:
                try:
                    self._ses_client = boto3.client(
                        'ses',
                        region_name=os.getenv('AWS_REGION', 'us-east-1'),
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    )
                    logger.info('AWS SES client initialised (region=%s)', os.getenv('AWS_REGION', 'us-east-1'))
                except Exception as exc:
                    logger.warning('Failed to initialise AWS SES client: %s. Falling back to SMTP.', exc)
                    self.provider = 'smtp'
                    self._ses_client = None
        else:
            self.provider = 'smtp'
            logger.info('Email provider: SMTP (%s:%s)', os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                        os.getenv('SMTP_PORT', '587'))

    def _init_templates(self):
        """Set up Jinja2 template environment."""
        if JINJA2_AVAILABLE and TEMPLATE_DIR.exists():
            self._jinja_env = Environment(
                loader=FileSystemLoader(str(TEMPLATE_DIR)),
                autoescape=select_autoescape(['html', 'xml']),
            )
            logger.info('Email templates loaded from %s', TEMPLATE_DIR)
        else:
            self._jinja_env = None
            if not TEMPLATE_DIR.exists():
                logger.warning('Template directory not found: %s', TEMPLATE_DIR)

    # ── Internal send helpers ─────────────────────────────────────────────────

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render a Jinja2 HTML template.  Returns plain-text fallback on error."""
        if self._jinja_env:
            try:
                tmpl = self._jinja_env.get_template(template_name)
                return tmpl.render(**context)
            except Exception as exc:
                logger.error('Template render error (%s): %s', template_name, exc)
        # Plain-text fallback
        lines = [f'<html><body><pre>']
        for k, v in context.items():
            lines.append(f'{k}: {v}')
        lines.append('</pre></body></html>')
        return '\n'.join(lines)

    def _send_via_smtp(self, to_email: str, subject: str, html_body: str,
                       text_body: str = '') -> bool:
        """Send email via SMTP with TLS.  Returns True on success."""
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')

        if not smtp_user or not smtp_password:
            self._log_dev_email(to_email, subject, html_body)
            return True  # Dev mode — treat as success

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{self.from_name} <{self.from_email}>'
        msg['To'] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            logger.info('Email sent via SMTP to %s (subject=%s)', to_email, subject)
            return True
        except smtplib.SMTPAuthenticationError as exc:
            logger.error('SMTP authentication failed: %s', exc)
            return False
        except smtplib.SMTPException as exc:
            logger.error('SMTP error sending to %s: %s', to_email, exc)
            return False
        except OSError as exc:
            logger.error('Network error sending email to %s: %s', to_email, exc)
            return False

    def _send_via_ses(self, to_email: str, subject: str, html_body: str,
                      text_body: str = '') -> bool:
        """Send email via AWS SES.  Returns True on success."""
        if not self._ses_client:
            logger.warning('SES client not available; falling back to SMTP')
            return self._send_via_smtp(to_email, subject, html_body, text_body)

        body_parts = {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
        if text_body:
            body_parts['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}

        try:
            self._ses_client.send_email(
                Source=f'{self.from_name} <{self.from_email}>',
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': body_parts,
                },
            )
            logger.info('Email sent via SES to %s (subject=%s)', to_email, subject)
            return True
        except ClientError as exc:
            error_code = exc.response['Error']['Code']
            logger.error('SES ClientError sending to %s: [%s] %s', to_email, error_code, exc)
            return False
        except BotoCoreError as exc:
            logger.error('SES BotoCoreError sending to %s: %s', to_email, exc)
            return False
        except Exception as exc:
            logger.error('Unexpected SES error sending to %s: %s', to_email, exc)
            return False

    def _send(self, to_email: str, subject: str, html_body: str,
              text_body: str = '') -> bool:
        """Route to the correct provider."""
        if DEV_MODE or (not os.getenv('SMTP_USER') and not os.getenv('AWS_ACCESS_KEY_ID')):
            self._log_dev_email(to_email, subject, html_body)
            return True

        if self.provider == 'ses':
            return self._send_via_ses(to_email, subject, html_body, text_body)
        return self._send_via_smtp(to_email, subject, html_body, text_body)

    @staticmethod
    def _log_dev_email(to_email: str, subject: str, html_body: str):
        """Log email content to console in development mode."""
        separator = '=' * 70
        logger.info('\n%s\n[DEV EMAIL] To: %s\nSubject: %s\n%s\n%s\n%s',
                    separator, to_email, subject, '-' * 70,
                    html_body[:500] + ('...' if len(html_body) > 500 else ''),
                    separator)

    # ── Public API ────────────────────────────────────────────────────────────

    def send_verification_email(self, to_email: str, user_name: str,
                                verification_token: str) -> bool:
        """Send 6-digit email verification code.

        Args:
            to_email: Recipient email address.
            user_name: Display name of the recipient.
            verification_token: 6-digit numeric code.

        Returns:
            True if the email was sent (or logged in dev mode), False on error.
        """
        try:
            subject = '[SoftFactory] 이메일 주소를 인증해주세요'
            html_body = self._render_template('verification.html', {
                'user_name': user_name,
                'verification_token': verification_token,
                'year': datetime.utcnow().year,
                'expires_hours': 24,
            })
            text_body = (
                f'안녕하세요 {user_name}님,\n\n'
                f'이메일 인증 코드: {verification_token}\n\n'
                f'이 코드는 24시간 후 만료됩니다.\n'
                f'본인이 요청하지 않았다면 이 이메일을 무시하세요.\n\n'
                f'- SoftFactory 팀'
            )
            return self._send(to_email, subject, html_body, text_body)
        except Exception as exc:
            logger.error('send_verification_email failed for %s: %s', to_email, exc)
            return False

    def send_password_reset_email(self, to_email: str, user_name: str,
                                  reset_token: str) -> bool:
        """Send password-reset link.

        Args:
            to_email: Recipient email address.
            user_name: Display name of the recipient.
            reset_token: URL-safe reset token.

        Returns:
            True if sent (or logged in dev mode), False on error.
        """
        try:
            base_url = os.getenv('PLATFORM_BASE_URL', 'http://localhost:9000')
            reset_url = f'{base_url}/platform/reset-password.html?token={reset_token}'
            subject = '[SoftFactory] 비밀번호 재설정 요청'
            html_body = self._render_template('password_reset.html', {
                'user_name': user_name,
                'reset_url': reset_url,
                'year': datetime.utcnow().year,
                'expires_hours': 1,
            })
            text_body = (
                f'안녕하세요 {user_name}님,\n\n'
                f'비밀번호 재설정 링크: {reset_url}\n\n'
                f'이 링크는 1시간 후 만료됩니다.\n'
                f'본인이 요청하지 않았다면 이 이메일을 무시하세요.\n\n'
                f'- SoftFactory 팀'
            )
            return self._send(to_email, subject, html_body, text_body)
        except Exception as exc:
            logger.error('send_password_reset_email failed for %s: %s', to_email, exc)
            return False

    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email after successful registration.

        Args:
            to_email: Recipient email address.
            user_name: Display name of the new user.

        Returns:
            True if sent (or logged in dev mode), False on error.
        """
        try:
            base_url = os.getenv('PLATFORM_BASE_URL', 'http://localhost:9000')
            dashboard_url = f'{base_url}/platform/dashboard.html'
            subject = f'[SoftFactory] 환영합니다, {user_name}님!'
            html_body = self._render_template('welcome.html', {
                'user_name': user_name,
                'dashboard_url': dashboard_url,
                'year': datetime.utcnow().year,
            })
            text_body = (
                f'환영합니다, {user_name}님!\n\n'
                f'SoftFactory 가입을 진심으로 환영합니다.\n'
                f'지금 바로 시작하세요: {dashboard_url}\n\n'
                f'- SoftFactory 팀'
            )
            return self._send(to_email, subject, html_body, text_body)
        except Exception as exc:
            logger.error('send_welcome_email failed for %s: %s', to_email, exc)
            return False

    def send_payment_confirmation(self, to_email: str, user_name: str,
                                  plan_name: str, amount: float,
                                  next_billing_date: str = '') -> bool:
        """Send payment-confirmation receipt.

        Args:
            to_email: Recipient email address.
            user_name: Display name of the recipient.
            plan_name: Name of the purchased plan.
            amount: Amount charged (KRW or USD).
            next_billing_date: ISO-formatted next billing date string.

        Returns:
            True if sent (or logged in dev mode), False on error.
        """
        try:
            subject = '[SoftFactory] 결제가 완료되었습니다'
            html_body = self._render_template('payment_confirmation.html', {
                'user_name': user_name,
                'plan_name': plan_name,
                'amount': f'{amount:,.0f}',
                'next_billing_date': next_billing_date or '자동 갱신',
                'year': datetime.utcnow().year,
                'paid_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            })
            text_body = (
                f'안녕하세요 {user_name}님,\n\n'
                f'결제가 완료되었습니다.\n'
                f'플랜: {plan_name}\n'
                f'금액: {amount:,.0f}원\n'
                f'다음 결제일: {next_billing_date or "자동 갱신"}\n\n'
                f'이용해 주셔서 감사합니다.\n\n'
                f'- SoftFactory 팀'
            )
            return self._send(to_email, subject, html_body, text_body)
        except Exception as exc:
            logger.error('send_payment_confirmation failed for %s: %s', to_email, exc)
            return False

    def send_notification(self, to_email: str, subject: str, message: str) -> bool:
        """Send a generic notification email.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            message: Plain-text or HTML notification body.

        Returns:
            True if sent (or logged in dev mode), False on error.
        """
        try:
            html_body = self._render_template('notification.html', {
                'subject': subject,
                'message': message,
                'year': datetime.utcnow().year,
            })
            return self._send(to_email, subject, html_body, message)
        except Exception as exc:
            logger.error('send_notification failed for %s: %s', to_email, exc)
            return False

    def send_account_deleted_notification(self, to_email: str, user_name: str) -> bool:
        """Send account deletion confirmation email."""
        try:
            subject = '[SoftFactory] 계정 삭제가 완료되었습니다'
            html_body = self._render_template('notification.html', {
                'subject': subject,
                'message': (
                    f'{user_name}님의 계정 삭제 요청이 처리되었습니다.\\n'
                    '데이터 정리 작업이 진행되었으며, 관련 법적/청구 처리 기록은 보존됩니다.'
                ),
                'year': datetime.utcnow().year,
            })
            text_body = (
                f'{user_name}님,\\n\\n'
                'SoftFactory 계정 삭제 요청이 정상적으로 처리되었습니다.\\n'
                '개인정보 삭제 요청은 즉시 반영되었으며, 결제/정산 관련 기록은 법적 의무에 따라 보존됩니다.\\n'
                '서비스 이용에 감사드립니다.'
            )
            return self._send(to_email, subject, html_body, text_body)
        except Exception as exc:
            logger.error('send_account_deleted_notification failed for %s: %s', to_email, exc)
            return False


# ── Module-level singleton ────────────────────────────────────────────────────
# Instantiated lazily so that import-time errors are suppressed in dev environments.
_email_service_instance = None


def get_email_service() -> EmailService:
    """Return the module-level EmailService singleton."""
    global _email_service_instance
    if _email_service_instance is None:
        try:
            _email_service_instance = EmailService()
        except Exception as exc:
            logger.error('Failed to create EmailService: %s', exc)
            _email_service_instance = EmailService.__new__(EmailService)
            _email_service_instance.provider = 'smtp'
            _email_service_instance.from_email = 'noreply@softfactory.kr'
            _email_service_instance.from_name = 'SoftFactory'
            _email_service_instance._ses_client = None
            _email_service_instance._jinja_env = None
    return _email_service_instance
