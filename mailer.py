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
        'smtp_host': os.environ.get('SMTP_HOST', 'smtp.gmail.com').strip(),
        'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
        'smtp_user': os.environ.get('SMTP_USER', '').strip(),
        'smtp_password': os.environ.get('SMTP_PASSWORD', '').replace(' ', '').strip(),
        'sender_name': os.environ.get('SMTP_SENDER_NAME', 'PageVault Security').strip(),
        'sender_email': os.environ.get('SMTP_SENDER_EMAIL', '').strip()
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_cfg = json.load(f)
                for k, v in file_cfg.items():
                    if v:
                        if k == 'smtp_password' and isinstance(v, str):
                            cfg[k] = v.replace(' ', '').strip()
                        elif isinstance(v, str):
                            cfg[k] = v.strip()
                        else:
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

    user = cfg.get('smtp_user', '').strip()
    pw = cfg.get('smtp_password', '').replace(' ', '').strip()
    has_credentials = bool(user and pw and pw.lower() != 'none')

    if has_credentials:
        try:
            print(f"[Mailer] Attempting SMTP delivery to {to_email} via {cfg['smtp_host']}:{cfg['smtp_port']} (Account: {user})...")
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
            server.login(user, pw)
            server.sendmail(cfg['sender_email'], [to_email], msg.as_string())
            server.quit()

            log_to_outbox(to_email, subject, code, True, "Dispatched via SMTP successfully")
            print(f"[Mailer] SUCCESS: Delivered verification email to {to_email}")
            return {'delivered': True, 'method': 'smtp', 'message': 'Email delivered via SMTP.'}
        except Exception as e:
            err_msg = f"SMTP dispatch error: {str(e)}"
            print(f"[Mailer] ERROR: {err_msg}")
            log_to_outbox(to_email, subject, code, False, err_msg)
            return {'delivered': False, 'method': 'error', 'message': err_msg}
    else:
        err_msg = "No SMTP credentials set. Please configure SMTP_USER and SMTP_PASSWORD in Render Environment settings."
        log_to_outbox(to_email, subject, code, False, err_msg)
        print(f"[Mailer] WARNING: {err_msg}")
        return {'delivered': False, 'method': 'outbox_logged', 'message': err_msg}



def send_order_confirmation_email(to_email: str, customer_name: str, order_code: str, total_amount: float, delivery_address: str, payment_method: str = "Cash on Delivery", items: list = None) -> dict:
    """
    Sends an order confirmation receipt email to the customer.
    Delivered to whoever placed the order and entered their email address.
    """
    if not to_email:
        return {'delivered': False, 'message': 'No customer email provided.'}

    cfg = load_email_config()
    subject = f"Order Confirmed: #{order_code} - PageVault"
    sender = f"{cfg['sender_name']} <{cfg['sender_email'] or 'orders@pagevault.com'}>"

    items_list_text = ""
    items_list_html = ""
    if items:
        for it in items:
            title = it.get('title', 'Book')
            qty = it.get('quantity', 1)
            price = it.get('unit_price', 0)
            items_list_text += f"- {title} (x{qty}) - ৳{price:.2f}\n"
            items_list_html += f"<tr><td style='padding: 8px 0; border-bottom: 1px solid #E2DAD0;'>{title} <span style='color: #736C62;'>&times; {qty}</span></td><td style='padding: 8px 0; text-align: right; border-bottom: 1px solid #E2DAD0; font-family: monospace; font-weight: 700;'>৳{price:.2f}</td></tr>"

    text_content = f"""Hello {customer_name},

Thank you for your order at PageVault!
Your order #{order_code} has been confirmed and is now being prepared for delivery.

Order Details:
- Order Reference: {order_code}
- Total Amount: ৳{total_amount:.2f}
- Payment Method: {payment_method}
- Delivery Address: {delivery_address}
- Estimated Delivery: 24 to 48 Hours nationwide

{items_list_text}
If you have any questions or inquiries regarding your package, feel free to reply to this email or reach us at tamimtahmid270@gmail.com.

Warm regards,
The PageVault Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #F3EEE3; margin: 0; padding: 24px; color: #111111; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; border: 1px solid #E2DAD0; padding: 36px 32px; box-shadow: 0 4px 16px rgba(17,17,17,0.06); }}
    .logo-title {{ font-size: 26px; font-weight: 800; color: #111111; text-align: center; }}
    .logo-accent {{ color: #D9541E; }}
    .badge {{ display: inline-block; background: #E8F5E9; color: #2E7D32; font-weight: 700; font-size: 13px; padding: 6px 14px; border-radius: 20px; margin-top: 12px; }}
    .order-box {{ background: #FAF7F2; border: 1px solid #E2DAD0; border-radius: 12px; padding: 20px; margin: 24px 0; font-size: 14px; line-height: 1.8; }}
    .total-row {{ font-size: 18px; font-weight: 800; color: #D9541E; font-family: monospace; }}
    .footer {{ margin-top: 28px; padding-top: 20px; border-top: 1px solid #E2DAD0; font-size: 12px; color: #736C62; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div style="text-align: center;">
      <div class="logo-title">Page<span class="logo-accent">Vault</span></div>
      <div class="badge">&#10003; Order Confirmed &amp; Processing</div>
    </div>

    <p style="font-size: 15px; line-height: 1.6; margin-top: 24px;">
      Hello <strong>{customer_name}</strong>,<br>
      Thank you for shopping with PageVault! We have received your order and our logistics team is preparing it for prompt delivery.
    </p>

    <div class="order-box">
      <div><strong>Order Code:</strong> <span style="font-family: monospace; color: #D9541E; font-weight: 700;">#{order_code}</span></div>
      <div><strong>Payment Method:</strong> {payment_method}</div>
      <div><strong>Delivery Address:</strong> {delivery_address}</div>
      <div><strong>Estimated Delivery:</strong> 24–48 Hours (Nationwide)</div>
      <div style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed #E2DAD0;">
        <span style="font-size: 15px;">Total Payable: </span>
        <span class="total-row">৳{total_amount:.2f}</span>
      </div>
    </div>

    <p style="font-size: 13px; color: #736C62; line-height: 1.6;">
      Need assistance or changes to your delivery details? Reach our support directly at <a href="mailto:tamimtahmid270@gmail.com" style="color: #D9541E; font-weight: 600;">tamimtahmid270@gmail.com</a>.
    </p>

    <div class="footer">
      &copy; 2026 PageVault &bull; Curated Online Bookshop &bull; Bangladesh
    </div>
  </div>
</body>
</html>
"""

    user = cfg.get('smtp_user', '').strip()
    pw = cfg.get('smtp_password', '').replace(' ', '').strip()
    has_credentials = bool(user and pw and pw.lower() != 'none')

    if has_credentials:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = to_email

            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pw)
            server.sendmail(cfg['sender_email'], [to_email], msg.as_string())
            server.quit()

            log_to_outbox(to_email, subject, f"Order #{order_code}", True, "Order confirmation email sent via SMTP")
            print(f"[Mailer] Order confirmation email sent to {to_email} for #{order_code}")
            return {'delivered': True, 'method': 'smtp'}
        except Exception as e:
            err_msg = f"Order email SMTP error: {str(e)}"
            print(f"[Mailer] {err_msg}")
            log_to_outbox(to_email, subject, f"Order #{order_code}", False, err_msg)
            return {'delivered': False, 'method': 'outbox_logged', 'message': err_msg}
    else:
        log_to_outbox(to_email, subject, f"Order #{order_code}", False, "Logged order confirmation (SMTP credentials not yet set)")
        print(f"[Mailer] Logged order confirmation for {to_email} to email_outbox.log")
        return {'delivered': False, 'method': 'outbox_logged'}
