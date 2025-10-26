"""
Email Service using ServerSMTP.com
SMTP configuration is system-wide and managed by sysadmin only.
Users cannot modify SMTP settings.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    System-wide email service using ServerSMTP.com

    Configuration is done via environment variables (sysadmin only):
    - SMTP_HOST: ServerSMTP.com host (default: mail.serversmtp.com)
    - SMTP_PORT: SMTP port (default: 587 for TLS)
    - SMTP_USER: ServerSMTP.com username
    - SMTP_PASSWORD: ServerSMTP.com password
    - SMTP_FROM_EMAIL: From email address (default: noreply@saft.aquinos.io)
    - SMTP_FROM_NAME: From name (default: SAFT Doctor)
    """

    def __init__(self, config: dict = None):
        # System-wide SMTP configuration (sysadmin only)
        # Can be provided via config dict (from DB) or environment variables
        if config:
            self.smtp_host = config.get('smtp_host', 'mail.serversmtp.com')
            self.smtp_port = int(config.get('smtp_port', 587))
            self.smtp_user = config.get('smtp_user')
            self.smtp_password = config.get('smtp_password')
            self.from_email = config.get('from_email', 'noreply@saft.aquinos.io')
            self.from_name = config.get('from_name', 'SAFT Doctor')
            self.app_url = config.get('app_url', 'https://saft.aquinos.io')
        else:
            # Fallback to environment variables
            self.smtp_host = os.getenv('SMTP_HOST', 'mail.serversmtp.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))  # TLS port
            self.smtp_user = os.getenv('SMTP_USER')
            self.smtp_password = os.getenv('SMTP_PASSWORD')
            self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@saft.aquinos.io')
            self.from_name = os.getenv('SMTP_FROM_NAME', 'SAFT Doctor')
            self.app_url = os.getenv('APP_URL', 'https://saft.aquinos.io')

        # Validate configuration
        if not self.smtp_user or not self.smtp_password:
            logger.warning('⚠️ SMTP credentials not configured. Email service disabled.')
            logger.warning('Sysadmin: Set SMTP_USER and SMTP_PASSWORD environment variables.')

    def is_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(self.smtp_user and self.smtp_password)

    def _create_connection(self):
        """Create and return SMTP connection"""
        if not self.is_configured():
            raise Exception('SMTP not configured. Contact sysadmin.')

        try:
            # Connect to ServerSMTP.com
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            smtp.ehlo()
            smtp.starttls()  # Upgrade to secure connection
            smtp.ehlo()
            smtp.login(self.smtp_user, self.smtp_password)
            logger.info(f'✅ SMTP connection established to {self.smtp_host}')
            return smtp
        except Exception as e:
            logger.error(f'❌ Failed to connect to SMTP server: {e}')
            raise

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """
        Send email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML version of email body
            text_body: Plain text version (optional)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error('❌ SMTP not configured. Cannot send email.')
            logger.error('Sysadmin: Configure SMTP_USER and SMTP_PASSWORD.')
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{self.from_name} <{self.from_email}>'
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

            # Add plain text version (fallback)
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)

            # Send email
            with self._create_connection() as smtp:
                smtp.send_message(msg)

            logger.info(f'✅ Email sent successfully to {to_email}: {subject}')
            return True

        except Exception as e:
            logger.error(f'❌ Failed to send email to {to_email}: {e}')
            return False

    def send_password_reset_email(self, to_email: str, username: str, reset_token: str):
        """
        Send password reset email

        Args:
            to_email: User's email address
            username: User's username
            reset_token: Password reset token (JWT)

        Returns:
            bool: True if sent successfully
        """
        # Build reset link
        reset_link = f'{self.app_url}/?reset_token={reset_token}'

        # Email subject
        subject = '🔐 SAFT Doctor - Recuperação de Password'

        # HTML body (beautiful, professional template)
        html_body = self._get_reset_email_template(username, reset_link)

        # Plain text version (fallback for old email clients)
        text_body = f"""
SAFT Doctor - Recuperação de Password

Olá {username},

Recebeu este email porque foi solicitada a recuperação de password da sua conta no SAFT Doctor.

Para criar uma nova password, aceda ao seguinte link:
{reset_link}

⚠️ IMPORTANTE:
- Este link é válido por 1 hora
- Por motivos de segurança, após esse período terá de solicitar um novo link

Não solicitou esta recuperação?
Se não foi você, ignore este email. A sua conta permanece segura.

---
SAFT Doctor | Validador Profissional de Ficheiros SAFT-T (PT)
{self.app_url}

© {datetime.now().year} SAFT Doctor. Todos os direitos reservados.
"""

        return self.send_email(to_email, subject, html_body, text_body)

    def send_password_changed_notification(self, to_email: str, username: str):
        """
        Send notification that password was changed

        Args:
            to_email: User's email address
            username: User's username

        Returns:
            bool: True if sent successfully
        """
        subject = '✅ SAFT Doctor - Password Alterada com Sucesso'

        html_body = self._get_password_changed_template(username)

        text_body = f"""
SAFT Doctor - Password Alterada com Sucesso

Olá {username},

A password da sua conta foi alterada com sucesso.

Data e Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')} (UTC)

Já pode fazer login com a sua nova password em:
{self.app_url}

⚠️ Não reconhece esta alteração?
Se não foi você, contacte imediatamente: support@aquinos.io

---
SAFT Doctor
© {datetime.now().year} Todos os direitos reservados.
"""

        return self.send_email(to_email, subject, html_body, text_body)

    def _get_reset_email_template(self, username: str, reset_link: str) -> str:
        """Get HTML template for password reset email"""
        return f"""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperação de Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">🏥 SAFT Doctor</h1>
                            <p style="margin: 10px 0 0 0; color: #dbeafe; font-size: 16px;">Validador Profissional de Ficheiros SAFT-T</p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #2563eb; font-size: 24px;">Recuperação de Password</h2>

                            <p style="margin: 0 0 15px 0; color: #334155; font-size: 16px; line-height: 1.6;">
                                Olá <strong>{username}</strong>,
                            </p>

                            <p style="margin: 0 0 15px 0; color: #334155; font-size: 16px; line-height: 1.6;">
                                Recebemos um pedido para recuperar a password da sua conta no SAFT Doctor.
                            </p>

                            <p style="margin: 0 0 30px 0; color: #334155; font-size: 16px; line-height: 1.6;">
                                Se foi você que solicitou esta recuperação, clique no botão abaixo para criar uma nova password:
                            </p>

                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 0 0 30px 0;">
                                        <a href="{reset_link}"
                                           style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                            🔓 Recuperar Password
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Warning Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 30px 0;">
                                <tr>
                                    <td style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 6px;">
                                        <p style="margin: 0 0 10px 0; color: #92400e; font-size: 15px; font-weight: 600;">
                                            ⚠️ Importante
                                        </p>
                                        <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.5;">
                                            Este link é válido por <strong>1 hora</strong>.<br>
                                            Por motivos de segurança, após esse período terá de solicitar um novo link de recuperação.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alternative Link -->
                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 14px;">
                                Se não conseguir clicar no botão, copie e cole o seguinte link no seu navegador:
                            </p>
                            <p style="margin: 0 0 30px 0; background-color: #f8fafc; padding: 15px; border-radius: 6px; word-break: break-all; font-size: 12px; color: #475569;">
                                {reset_link}
                            </p>

                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

                            <!-- Security Notice -->
                            <p style="margin: 0 0 15px 0; color: #64748b; font-size: 14px; line-height: 1.6;">
                                <strong>Não solicitou esta recuperação?</strong><br>
                                Se não foi você que pediu para recuperar a password, pode ignorar este email em segurança. A sua conta permanece protegida e nenhuma alteração será feita.
                            </p>

                            <p style="margin: 0; color: #64748b; font-size: 14px;">
                                Para sua segurança, nunca partilhe a sua password com terceiros.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px; text-align: center;">
                            <p style="margin: 0 0 10px 0; color: #475569; font-size: 14px; font-weight: 600;">
                                SAFT Doctor
                            </p>
                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 13px;">
                                Validador Profissional de Ficheiros SAFT-T (PT)
                            </p>
                            <p style="margin: 0 0 15px 0;">
                                <a href="{self.app_url}" style="color: #2563eb; text-decoration: none; font-size: 13px;">
                                    {self.app_url}
                                </a>
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                © {datetime.now().year} SAFT Doctor. Todos os direitos reservados.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _get_password_changed_template(self, username: str) -> str:
        """Get HTML template for password changed notification"""
        return f"""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Alterada</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">🏥 SAFT Doctor</h1>
                            <p style="margin: 10px 0 0 0; color: #d1fae5; font-size: 16px;">Password Alterada com Sucesso</p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <div style="display: inline-block; background-color: #d1fae5; border-radius: 50%; padding: 25px; margin-bottom: 20px;">
                                <span style="font-size: 48px;">✅</span>
                            </div>

                            <h2 style="margin: 0 0 20px 0; color: #10b981; font-size: 24px;">Password Alterada!</h2>

                            <p style="margin: 0 0 15px 0; color: #334155; font-size: 16px; line-height: 1.6; text-align: left;">
                                Olá <strong>{username}</strong>,
                            </p>

                            <p style="margin: 0 0 30px 0; color: #334155; font-size: 16px; line-height: 1.6; text-align: left;">
                                A password da sua conta no SAFT Doctor foi alterada com sucesso.
                            </p>

                            <!-- Info Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 30px 0;">
                                <tr>
                                    <td style="background-color: #dbeafe; border-left: 4px solid #2563eb; padding: 20px; border-radius: 6px; text-align: left;">
                                        <p style="margin: 0; color: #1e40af; font-size: 15px;">
                                            <strong>📅 Data e Hora:</strong><br>
                                            <span style="color: #1e3a8a;">{datetime.now().strftime('%d de %B de %Y, %H:%M')} (UTC)</span>
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 0 0 30px 0; color: #334155; font-size: 16px; line-height: 1.6; text-align: left;">
                                Já pode fazer login na aplicação com a sua nova password.
                            </p>

                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 0 0 30px 0;">
                                        <a href="{self.app_url}"
                                           style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                            🔓 Aceder ao SAFT Doctor
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

                            <!-- Warning Box -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 6px; text-align: left;">
                                        <p style="margin: 0 0 10px 0; color: #92400e; font-size: 15px; font-weight: 600;">
                                            ⚠️ Não reconhece esta alteração?
                                        </p>
                                        <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.5;">
                                            Se não foi você que alterou a password, a sua conta pode estar comprometida.<br>
                                            <strong>Contacte imediatamente:</strong> support@aquinos.io
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px; text-align: center;">
                            <p style="margin: 0 0 10px 0; color: #475569; font-size: 14px; font-weight: 600;">
                                SAFT Doctor
                            </p>
                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 13px;">
                                Validador Profissional de Ficheiros SAFT-T (PT)
                            </p>
                            <p style="margin: 0 0 15px 0;">
                                <a href="{self.app_url}" style="color: #2563eb; text-decoration: none; font-size: 13px;">
                                    {self.app_url}
                                </a>
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                © {datetime.now().year} SAFT Doctor. Todos os direitos reservados.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
