"""
Email delivery module for PageVault.
Supports real SMTP delivery (e.g. Gmail, Outlook, Amazon SES, or custom SMTP),
as well as file logging to email_outbox.log for development and audit trails.
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_config.json')
OUTBOX_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_outbox.log')


def load_email_config():
    """Load email configuration from email_config.json or environment variables."""
    cfg = {
        'smtp_host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
        'smtp_user': os.environ.get('SMTP_USER', ''),
        'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
        'sender_name': os.environ.get('SMTP_SENDER_NAME', 'PageVault Security'),
        'sender_email': os.environ.get('SMTP_SENDER_EMAIL', '')
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_cfg = json.load(f)
                for k, v in file_cfg.items():
                    if v:
                        cfg[k] = v
        except Exception as e:
            print(f"[Mailer] Warning: Could not read {CONFIG_FILE}: {e}")

    # Fallback sender email to smtp_user if not specified
    if not cfg['sender_email'] and cfg['smtp_user']:
        cfg['sender_email'] = cfg['smtp_user']

    return cfg


def log_to_outbox(to_email: str, subject: str, code: str, delivered: bool, detail: str = ""):
    """Log outgoing email to email_outbox.log for audit and testing."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = (
        f"[{timestamp}] To: {to_email} | Subject: {subject} | "
        f"Code: {code} | Real SMTP Sent: {delivered}"
    )
    if detail:
        log_entry += f" | Status: {detail}"
    log_entry += "\n"

    try:
        with open(OUTBOX_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[Mailer] Failed to write outbox log: {e}")


def send_password_reset_email(to_email: str, full_name: str, code: str) -> dict:
    """
    Sends a 6-digit password verification code email.
    If SMTP credentials are provided, dispatches real email over TLS.
    Always logs to outbox so testing is smooth.
    """
    cfg = load_email_config()
    subject = f"Your PageVault Verification Code: {code}"
    sender = f"{cfg['sender_name']} <{cfg['sender_email'] or 'security@pagevault.com'}>"

    # Plain text version
    text_content = f"""Hello {full_name or 'Reader'},

We received a request to reset your password for your PageVault account.

Your 6-digit verification code is:

    {code}

This verification code is valid for 60 minutes.
If you did not request this, you can safely ignore this email — your account remains secure.

Warm regards,
The PageVault Team
https://pagevault.com
"""

    # HTML formatted version
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #F3EEE3; margin: 0; padding: 24px; color: #111111; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; border: 1px solid #E2DAD0; padding: 36px 32px; box-shadow: 0 4px 16px rgba(17,17,17,0.06); }}
    .logo-area {{ text-align: center; margin-bottom: 24px; }}
    .logo-title {{ font-size: 26px; font-weight: 800; color: #111111; letter-spacing: -0.5px; }}
    .logo-accent {{ color: #D9541E; }}
    .tagline {{ font-size: 11px; font-weight: 700; color: #736C62; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }}
    .heading {{ font-size: 20px; font-weight: 700; color: #111111; margin-top: 18px; margin-bottom: 12px; }}
    .message {{ font-size: 14px; line-height: 1.6; color: #4A453E; margin-bottom: 24px; }}
    .code-box {{ background: #FAF7F2; border: 1.5px dashed #D9541E; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
    .code-number {{ font-family: 'JetBrains Mono', Consolas, monospace; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #D9541E; }}
    .expiry-note {{ font-size: 12px; color: #8F877B; margin-top: 8px; }}
    .footer {{ margin-top: 32px; padding-top: 20px; border-top: 1px solid #E2DAD0; font-size: 12px; color: #8F877B; text-align: center; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="logo-area">
      <div class="logo-title">Page<span class="logo-accent">Vault</span></div>
      <div class="tagline">Curated Online Bookshop</div>
    </div>
    
    <div class="heading">Password Verification Code</div>
    <div class="message">
      Hello <strong>{full_name or 'Reader'}</strong>,<br><br>
      We received a request to verify your identity and reset the password for your PageVault account. Use the 6-digit code below to proceed:
    </div>

    <div class="code-box">
      <div class="code-number">{code}</div>
      <div class="expiry-note">Valid for 60 minutes</div>
    </div>

    <div class="message">
      If you did not request a password reset, please disregard this message. Your password will remain unchanged.
    </div>

    <div class="footer">
      &copy; 2026 PageVault &bull; Curated Books &bull; Inquiries: tamimtahmid270@gmail.com
    </div>
  </div>
</body>
</html>
"""

    has_credentials = bool(cfg['smtp_user'] and cfg['smtp_password'])

    if has_credentials:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = to_email

            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg['smtp_user'], cfg['smtp_password'])
            server.sendmail(cfg['sender_email'], [to_email], msg.as_string())
            server.quit()

            log_to_outbox(to_email, subject, code, True, "Dispatched via SMTP successfully")
            print(f"[Mailer] Successfully delivered verification email to {to_email}")
            return {'delivered': True, 'method': 'smtp', 'message': 'Email delivered via SMTP.'}
        except Exception as e:
            err_msg = f"SMTP dispatch error: {str(e)}"
            print(f"[Mailer] {err_msg}")
            log_to_outbox(to_email, subject, code, False, err_msg)
            return {'delivered': False, 'method': 'outbox_logged', 'message': err_msg}
    else:
        # No credentials configured yet; record to local outbox log
        log_to_outbox(to_email, subject, code, False, "No SMTP credentials set in email_config.json")
        print(f"[Mailer] Logged code for {to_email} to email_outbox.log (configure email_config.json for real SMTP delivery)")
        return {'delivered': False, 'method': 'outbox_logged', 'message': 'Logged to outbox.'}
