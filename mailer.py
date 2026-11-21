"""
Email delivery module for PageVault.
Supports real SMTP delivery (e.g. Gmail, Outlook, Amazon SES, or custom SMTP),
as well as file logging to email_outbox.log for development and audit trails.
"""

import os
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_config.json')
OUTBOX_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_outbox.log')


def send_via_brevo_api(api_key: str, sender_email: str, sender_name: str, to_email: str, subject: str, html_content: str, text_content: str):
    """Dispatches transactional email via Brevo HTTPS API (Port 443 - works on Render Free Tier)."""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key.strip(),
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": sender_name or "PageVault", "email": sender_email or "tamimtahmid270@gmail.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=12) as resp:
            return True, "Delivered via Brevo HTTPS API"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        print(f"[Mailer] Brevo API HTTPError {e.code}: {err_body}")
        return False, f"Brevo HTTP {e.code}: {err_body}"
    except Exception as e:
        print(f"[Mailer] Brevo API delivery error: {e}")
        return False, str(e)


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

    # 1. Try HTTPS API first if configured (Bypasses Render Free Tier port 587 block)
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()
    if brevo_key:
        ok, detail = send_via_brevo_api(brevo_key, cfg['sender_email'], cfg['sender_name'], to_email, subject, html_content, text_content)
        if ok:
            log_to_outbox(to_email, subject, code, True, "Dispatched via Brevo HTTPS API successfully")
            print(f"[Mailer] SUCCESS: Delivered reset code to {to_email} via Brevo HTTPS API")
            return {'delivered': True, 'method': 'brevo_api', 'message': 'Email delivered via Brevo HTTPS API.'}
        else:
            log_to_outbox(to_email, subject, code, False, detail)
            print(f"[Mailer] ERROR: Brevo dispatch failed: {detail}")
            return {'delivered': False, 'method': 'brevo_api', 'message': detail}

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
            raw_err = str(e)
            if '101' in raw_err or 'Network is unreachable' in raw_err:
                err_msg = "Render Free blocks SMTP port 587. For online delivery, add a free BREVO_API_KEY, or view the verification code in your Admin Portal."
            else:
                err_msg = f"SMTP dispatch error: {raw_err}"
            print(f"[Mailer] ERROR: {err_msg}")
            log_to_outbox(to_email, subject, code, False, err_msg)
            return {'delivered': False, 'method': 'error', 'message': err_msg}
    else:
        err_msg = "No SMTP credentials set. Please configure SMTP_USER and SMTP_PASSWORD in Render Environment settings."
        log_to_outbox(to_email, subject, code, False, err_msg)
        print(f"[Mailer] WARNING: {err_msg}")
        return {'delivered': False, 'method': 'outbox_logged', 'message': err_msg}



def send_order_confirmation_email(to_email: str, customer_name: str, order_code: str, total_amount: float, delivery_address: str, payment_method: str = "Cash on Delivery", items: list = None, transaction_id: str = "") -> dict:
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

    trx_text = f"- Transaction ID: {transaction_id}\n" if transaction_id else ""
    trx_html = f"<div><strong>Transaction ID:</strong> <span style='font-family: monospace; font-weight: 700; color: #111111;'>{transaction_id}</span></div>" if transaction_id else ""

    text_content = f"""Hello {customer_name},

Thank you for your order at PageVault!
Your order #{order_code} has been confirmed and is now being prepared for delivery.

Order Details:
- Order Reference: {order_code}
- Total Amount: ৳{total_amount:.2f}
- Payment Method: {payment_method}
{trx_text}- Delivery Address: {delivery_address}
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
      {trx_html}
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

    # 1. Try HTTPS API first if configured
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()
    if brevo_key:
        ok, detail = send_via_brevo_api(brevo_key, cfg['sender_email'], cfg['sender_name'], to_email, subject, html_content, text_content)
        if ok:
            log_to_outbox(to_email, subject, f"Order #{order_code}", True, "Order confirmation email sent via Brevo HTTPS API")
            print(f"[Mailer] Order confirmation email sent to {to_email} for #{order_code} via Brevo API")
            return {'delivered': True, 'method': 'brevo_api'}
        else:
            log_to_outbox(to_email, subject, f"Order #{order_code}", False, detail)
            print(f"[Mailer] ERROR: Brevo order email failed: {detail}")
            return {'delivered': False, 'method': 'brevo_api', 'message': detail}

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
            raw_err = str(e)
            if '101' in raw_err or 'Network is unreachable' in raw_err:
                err_msg = "Render Free blocks SMTP port 587. Add a free BREVO_API_KEY in Environment settings to deliver emails."
            else:
                err_msg = f"Order email SMTP error: {raw_err}"
            print(f"[Mailer] {err_msg}")
            log_to_outbox(to_email, subject, f"Order #{order_code}", False, err_msg)
            return {'delivered': False, 'method': 'outbox_logged', 'message': err_msg}
    else:
        log_to_outbox(to_email, subject, f"Order #{order_code}", False, "Logged order confirmation (SMTP credentials not yet set)")
        print(f"[Mailer] Logged order confirmation for {to_email} to email_outbox.log")
        return {'delivered': False, 'method': 'outbox_logged'}


def send_support_query_email(customer_name: str, customer_email: str, customer_phone: str, topic: str, message: str) -> dict:
    """
    Sends customer support inquiry to admin email (tamimtahmid270@gmail.com)
    and sends an auto-reply receipt to the customer's email.
    """
    admin_recipient = "tamimtahmid270@gmail.com"
    cfg = load_email_config()
    sender_email = cfg.get('sender_email') or admin_recipient
    sender_name = cfg.get('sender_name') or "PageVault Support"
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()

    admin_subject = f"[Support Inquiry] {topic} - from {customer_name}"
    admin_text = f"""New Customer Inquiry Received on PageVault:

Customer Name: {customer_name}
Customer Email: {customer_email}
Customer Phone: {customer_phone or 'Not provided'}
Topic: {topic}

Message:
{message}

Sent via PageVault Help Desk.
"""
    admin_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 580px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 8px;">Page<span style="color: #D9541E;">Vault</span> Support Desk</div>
    <div style="display: inline-block; background: #EBF5FF; color: #1E40AF; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 12px; margin-bottom: 20px;">New Customer Inquiry</div>
    
    <div style="background: #FAF7F2; border: 1px solid #E2DAD0; border-radius: 10px; padding: 18px; margin-bottom: 20px; font-size: 14px; line-height: 1.8;">
      <div><strong>Customer Name:</strong> {customer_name}</div>
      <div><strong>Email:</strong> <a href="mailto:{customer_email}" style="color: #D9541E; font-weight: 600;">{customer_email}</a></div>
      <div><strong>Phone:</strong> {customer_phone or 'Not provided'}</div>
      <div><strong>Topic:</strong> <span style="font-weight: 700; color: #D9541E;">{topic}</span></div>
    </div>

    <div style="margin-bottom: 24px;">
      <strong style="font-size: 14px; color: #111;">Message Details:</strong>
      <div style="background: #FFF; border: 1px solid #E2DAD0; border-radius: 8px; padding: 16px; margin-top: 8px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; color: #222;">{message}</div>
    </div>

    <div style="font-size: 12px; color: #736C62; border-top: 1px solid #E2DAD0; padding-top: 16px;">
      Reply directly to the customer at <a href="mailto:{customer_email}" style="color: #D9541E; font-weight: 600;">{customer_email}</a>.
    </div>
  </div>
</body>
</html>
"""

    admin_delivered = False
    delivery_method = 'outbox_logged'
    status_detail = ''

    # 1. Dispatch to Admin via Brevo HTTPS API if available
    if brevo_key:
        ok, detail = send_via_brevo_api(brevo_key, sender_email, sender_name, admin_recipient, admin_subject, admin_html, admin_text)
        if ok:
            admin_delivered = True
            delivery_method = 'brevo_api'
            log_to_outbox(admin_recipient, admin_subject, "Support Query", True, "Delivered via Brevo API")
            print(f"[Mailer] Support inquiry sent to {admin_recipient} via Brevo API")
        else:
            status_detail = detail
            log_to_outbox(admin_recipient, admin_subject, "Support Query", False, detail)
            print(f"[Mailer] Brevo API support inquiry failed: {detail}")

    # Fallback to SMTP for Admin
    user = cfg.get('smtp_user', '').strip()
    pw = cfg.get('smtp_password', '').replace(' ', '').strip()
    if not admin_delivered and user and pw and pw.lower() != 'none':
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = admin_subject
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = admin_recipient
            msg.attach(MIMEText(admin_text, 'plain', 'utf-8'))
            msg.attach(MIMEText(admin_html, 'html', 'utf-8'))

            server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pw)
            server.sendmail(sender_email, [admin_recipient], msg.as_string())
            server.quit()
            admin_delivered = True
            delivery_method = 'smtp'
            log_to_outbox(admin_recipient, admin_subject, "Support Query", True, "Dispatched via SMTP")
            print(f"[Mailer] Support inquiry sent to {admin_recipient} via SMTP")
        except Exception as e:
            status_detail = str(e)
            log_to_outbox(admin_recipient, admin_subject, "Support Query", False, f"SMTP error: {e}")
            print(f"[Mailer] SMTP support query error: {e}")

    if not admin_delivered and not status_detail:
        log_to_outbox(admin_recipient, admin_subject, "Support Query", False, "Inquiry recorded (Logged to outbox)")

    # 2. Auto-reply confirmation to customer
    if customer_email and '@' in customer_email:
        cust_subject = f"Inquiry Received: {topic} - PageVault Support"
        cust_text = f"""Hello {customer_name},

Thank you for reaching out to PageVault Support!
We have received your query regarding "{topic}". Our customer team is reviewing your request and will respond shortly.

Your Message:
"{message}"

Warm regards,
PageVault Support Team
tamimtahmid270@gmail.com
"""
        cust_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 540px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 12px; text-align: center;">Page<span style="color: #D9541E;">Vault</span> Support</div>
    <p style="font-size: 15px; line-height: 1.6;">Hello <strong>{customer_name}</strong>,</p>
    <p style="font-size: 14px; line-height: 1.6; color: #444;">
      Thank you for reaching out to us! We have received your query regarding <strong>&ldquo;{topic}&rdquo;</strong>. Our customer support team is reviewing your message and will respond as soon as possible.
    </p>
    <div style="background: #FAF7F2; border-left: 4px solid #D9541E; padding: 14px; margin: 20px 0; font-size: 13px; font-style: italic; color: #555;">
      &ldquo;{message}&rdquo;
    </div>
    <p style="font-size: 13px; color: #736C62;">If you need urgent assistance, you can also reach us directly at <a href="mailto:tamimtahmid270@gmail.com" style="color: #D9541E; font-weight: 600;">tamimtahmid270@gmail.com</a>.</p>
    <div style="font-size: 12px; color: #999; border-top: 1px solid #E2DAD0; padding-top: 14px; text-align: center; margin-top: 24px;">&copy; 2026 PageVault &bull; Dhaka, Bangladesh</div>
  </div>
</body>
</html>
"""
        if brevo_key:
            send_via_brevo_api(brevo_key, sender_email, sender_name, customer_email, cust_subject, cust_html, cust_text)
        elif admin_delivered and delivery_method == 'smtp' and user and pw:
            try:
                cmsg = MIMEMultipart('alternative')
                cmsg['Subject'] = cust_subject
                cmsg['From'] = f"{sender_name} <{sender_email}>"
                cmsg['To'] = customer_email
                cmsg.attach(MIMEText(cust_text, 'plain', 'utf-8'))
                cmsg.attach(MIMEText(cust_html, 'html', 'utf-8'))
                server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, pw)
                server.sendmail(sender_email, [customer_email], cmsg.as_string())
                server.quit()
            except Exception:
                pass

    return {
        'delivered': admin_delivered,
        'method': delivery_method,
        'message': 'Your inquiry has been submitted and sent to PageVault Support.'
    }


def send_book_request_email(customer_name: str, customer_email: str, customer_phone: str, book_title: str, author_name: str = "", isbn: str = "", notes: str = "", genre_or_topic: str = "") -> dict:
    """
    Sends customer book request notification to admin email (tamimtahmid270@gmail.com)
    and sends an auto-reply receipt to the customer's email.
    """
    admin_recipient = "tamimtahmid270@gmail.com"
    cfg = load_email_config()
    sender_email = cfg.get('sender_email') or admin_recipient
    sender_name = cfg.get('sender_name') or "PageVault Catalog Desk"
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()

    admin_subject = f"[Book Request] \"{book_title}\" - from {customer_name}"
    admin_text = f"""New Book Request Received on PageVault:

Requested Title: {book_title}
Author / Creator: {author_name or 'Not specified'}
ISBN / Edition: {isbn or 'Not specified'}
Genre / Topic: {genre_or_topic or 'General'}

Customer Information:
Name: {customer_name}
Email: {customer_email}
Phone: {customer_phone or 'Not provided'}

Additional Notes:
{notes or 'None'}

Sent via PageVault Catalog Request System.
"""
    admin_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 580px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 8px;">Page<span style="color: #D9541E;">Vault</span> Catalog Desk</div>
    <div style="display: inline-block; background: #FEF3C7; color: #92400E; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 12px; margin-bottom: 20px;">📖 New Customer Book Request</div>
    
    <div style="background: #FAF7F2; border-left: 4px solid #D9541E; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
      <div style="font-size: 18px; font-weight: 800; color: #111;">{book_title}</div>
      <div style="font-size: 14px; color: #666; margin-top: 4px;">by <strong>{author_name or 'Unknown / Not specified'}</strong></div>
      {f'<div style="font-size: 13px; color: #736C62; margin-top: 4px;">ISBN: {isbn}</div>' if isbn else ''}
      {f'<div style="font-size: 13px; color: #736C62; margin-top: 2px;">Genre/Discipline: {genre_or_topic}</div>' if genre_or_topic else ''}
    </div>

    <div style="background: #FFF; border: 1px solid #E2DAD0; border-radius: 10px; padding: 18px; margin-bottom: 20px; font-size: 14px; line-height: 1.8;">
      <div><strong>Customer Name:</strong> {customer_name}</div>
      <div><strong>Email:</strong> <a href="mailto:{customer_email}" style="color: #D9541E; font-weight: 600;">{customer_email}</a></div>
      <div><strong>Phone:</strong> {customer_phone or 'Not provided'}</div>
      {f'<div><strong>Notes:</strong> {notes}</div>' if notes else ''}
    </div>

    <div style="font-size: 12px; color: #736C62; border-top: 1px solid #E2DAD0; padding-top: 16px;">
      Reply directly to customer at <a href="mailto:{customer_email}" style="color: #D9541E; font-weight: 600;">{customer_email}</a> to update them on stock availability.
    </div>
  </div>
</body>
</html>
"""

    admin_delivered = False
    delivery_method = 'outbox_logged'
    status_detail = ''

    # 1. Dispatch to Admin via Brevo HTTPS API if available
    if brevo_key:
        ok, detail = send_via_brevo_api(brevo_key, sender_email, sender_name, admin_recipient, admin_subject, admin_html, admin_text)
        if ok:
            admin_delivered = True
            delivery_method = 'brevo_api'
            log_to_outbox(admin_recipient, admin_subject, "Book Request", True, "Delivered via Brevo API")
            print(f"[Mailer] Book request notification sent to {admin_recipient} via Brevo API")
        else:
            status_detail = detail
            log_to_outbox(admin_recipient, admin_subject, "Book Request", False, detail)
            print(f"[Mailer] Brevo API book request failed: {detail}")

    # Fallback to SMTP for Admin
    user = cfg.get('smtp_user', '').strip()
    pw = cfg.get('smtp_password', '').replace(' ', '').strip()
    if not admin_delivered and user and pw and pw.lower() != 'none':
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = admin_subject
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = admin_recipient
            msg.attach(MIMEText(admin_text, 'plain', 'utf-8'))
            msg.attach(MIMEText(admin_html, 'html', 'utf-8'))

            server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pw)
            server.sendmail(sender_email, [admin_recipient], msg.as_string())
            server.quit()
            admin_delivered = True
            delivery_method = 'smtp'
            log_to_outbox(admin_recipient, admin_subject, "Book Request", True, "Dispatched via SMTP")
            print(f"[Mailer] Book request notification sent to {admin_recipient} via SMTP")
        except Exception as e:
            status_detail = str(e)
            log_to_outbox(admin_recipient, admin_subject, "Book Request", False, f"SMTP error: {e}")
            print(f"[Mailer] SMTP book request error: {e}")

    if not admin_delivered and not status_detail:
        log_to_outbox(admin_recipient, admin_subject, "Book Request", False, "Book request recorded (Logged to outbox)")

    # 2. Auto-reply confirmation to customer
    if customer_email and '@' in customer_email:
        cust_subject = f"Book Request Received: \"{book_title}\" - PageVault"
        cust_text = f"""Hello {customer_name},

Thank you for your book request on PageVault!
We have received your request to add "{book_title}" (by {author_name or 'the author'}) to our catalog.

Our sourcing and curation team has added this to our distributor inquiry queue. We will check availability with our publishers and distributors, and we will email you directly at {customer_email} as soon as copies are sourced and available for ordering!

Details Received:
- Title: {book_title}
- Author: {author_name or 'N/A'}
- ISBN: {isbn or 'N/A'}

Warm regards,
PageVault Editorial & Curation Desk
tamimtahmid270@gmail.com
"""
        cust_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 540px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 12px; text-align: center;">Page<span style="color: #D9541E;">Vault</span> Curation Desk</div>
    <p style="font-size: 15px; line-height: 1.6;">Hello <strong>{customer_name}</strong>,</p>
    <p style="font-size: 14px; line-height: 1.6; color: #444;">
      Thank you for letting us know! We have received your request for:
    </p>
    <div style="background: #FAF7F2; border-left: 4px solid #D9541E; padding: 16px 20px; border-radius: 8px; margin: 18px 0;">
      <div style="font-size: 17px; font-weight: 700; color: #111;">{book_title}</div>
      <div style="font-size: 13px; color: #666; margin-top: 4px;">{f'Author: {author_name}' if author_name else ''} {f'&bull; ISBN: {isbn}' if isbn else ''}</div>
    </div>
    <p style="font-size: 14px; line-height: 1.6; color: #444;">
      Our curation team is currently checking distribution channels and publisher stock for this title. As soon as it is cataloged and available for purchase, you will receive an update at <strong>{customer_email}</strong>.
    </p>
    <p style="font-size: 13px; color: #736C62; margin-top: 18px;">
      If you have questions or want to update your request, feel free to reply directly to <a href="mailto:tamimtahmid270@gmail.com" style="color: #D9541E; font-weight: 600;">tamimtahmid270@gmail.com</a>.
    </p>
    <div style="font-size: 12px; color: #999; border-top: 1px solid #E2DAD0; padding-top: 14px; text-align: center; margin-top: 24px;">&copy; 2026 PageVault &bull; Dhaka, Bangladesh</div>
  </div>
</body>
</html>
"""
        if brevo_key:
            send_via_brevo_api(brevo_key, sender_email, sender_name, customer_email, cust_subject, cust_html, cust_text)
        elif admin_delivered and delivery_method == 'smtp' and user and pw:
            try:
                cmsg = MIMEMultipart('alternative')
                cmsg['Subject'] = cust_subject
                cmsg['From'] = f"{sender_name} <{sender_email}>"
                cmsg['To'] = customer_email
                cmsg.attach(MIMEText(cust_text, 'plain', 'utf-8'))
                cmsg.attach(MIMEText(cust_html, 'html', 'utf-8'))
                server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=12)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, pw)
                server.sendmail(sender_email, [customer_email], cmsg.as_string())
                server.quit()
            except Exception:
                pass

    return {
        'delivered': admin_delivered,
        'method': delivery_method,
        'message': 'Your book request has been submitted and queued for catalog sourcing.'
    }


def send_order_cancellation_email(customer_name: str, customer_email: str, order_code: str,
                                 total_amount: float, delivery_fee: float, refund_amount: float,
                                 payment_method: str, is_online_paid: bool, cancel_reason: str = "",
                                 placed_at: str = "", cancelled_at: str = "") -> dict:
    """
    Sends order cancellation and refund confirmation email to customer,
    and alerts PageVault administrative desk (tamimtahmid270@gmail.com).
    """
    admin_recipient = "tamimtahmid270@gmail.com"
    cfg = load_email_config()
    sender_email = cfg.get('sender_email') or admin_recipient
    sender_name = cfg.get('sender_name') or "PageVault Support"
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()

    admin_subject = f"[Order Cancelled] #{order_code} - by {customer_name}"
    admin_text = f"""Order #{order_code} has been cancelled by customer within the 12-hour window.

Customer: {customer_name} ({customer_email})
Order Reference: #{order_code}
Payment Method: {payment_method}
Total Amount: ৳{total_amount:.2f}
Delivery Fee (Deducted): ৳{delivery_fee:.2f}
Net Refund Initiated: ৳{refund_amount:.2f}
Online Paid: {'Yes' if is_online_paid else 'No (Cash on Delivery)'}
Cancellation Reason: {cancel_reason or 'Customer self-cancellation'}
Placed At: {placed_at}
Cancelled At: {cancelled_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: Inventory items have been automatically restored to catalog stock.
"""
    admin_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 580px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 8px;">Page<span style="color: #D9541E;">Vault</span> Operations Desk</div>
    <div style="display: inline-block; background: #FEE2E2; color: #B91C1C; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 12px; margin-bottom: 20px;">🚫 Order Cancelled (Within 12h)</div>
    
    <div style="background: #FAF7F2; border: 1px solid #E2DAD0; border-radius: 10px; padding: 18px; margin-bottom: 20px; font-size: 14px; line-height: 1.8;">
      <div><strong>Order Code:</strong> <span style="font-family: monospace; color: #D9541E; font-weight: 700;">#{order_code}</span></div>
      <div><strong>Customer:</strong> {customer_name} (<a href="mailto:{customer_email}" style="color: #D9541E;">{customer_email}</a>)</div>
      <div><strong>Payment Method:</strong> {payment_method}</div>
      <div><strong>Total Amount:</strong> ৳{total_amount:.2f}</div>
      {f'<div><strong>Deducted Delivery Fee:</strong> ৳{delivery_fee:.2f}</div><div><strong>Net Refund:</strong> ৳{refund_amount:.2f}</div>' if is_online_paid else '<div><strong>Type:</strong> Cash on Delivery (Zero fees)</div>'}
      <div><strong>Reason:</strong> {cancel_reason or 'Customer requested'}</div>
      <div><strong>Cancelled At:</strong> {cancelled_at or 'Just now'}</div>
    </div>
    <p style="font-size: 13px; color: #666;">Catalog inventory for this order has been automatically replenished.</p>
  </div>
</body>
</html>
"""

    admin_delivered = False
    delivery_method = 'outbox_logged'

    if brevo_key:
        ok, detail = send_via_brevo_api(brevo_key, sender_email, sender_name, admin_recipient, admin_subject, admin_html, admin_text)
        if ok:
            admin_delivered = True
            delivery_method = 'brevo_api'
            log_to_outbox(admin_recipient, admin_subject, "Order Cancellation", True, "Delivered via Brevo API")
        else:
            log_to_outbox(admin_recipient, admin_subject, "Order Cancellation", False, detail)

    # Customer notification email
    if customer_email and '@' in customer_email:
        cust_subject = f"Order Cancelled: #{order_code} - PageVault"
        
        refund_clause_text = f"""
Refund Information:
Since your order was paid online via {payment_method}, a refund of ৳{refund_amount:.2f} has been initiated to your account.
As per our 12-hour cancellation policy, the delivery processing fee (৳{delivery_fee:.2f}) has been deducted.
The refund will reflect in your payment account within 3 to 5 business days.
""" if is_online_paid else """
Refund Information:
Since this order was scheduled for Cash on Delivery, no payment was charged and your order has been cancelled with zero fees.
"""

        cust_text = f"""Hello {customer_name},

Your order #{order_code} has been successfully cancelled per your request within the 12-hour policy window.

Order Code: #{order_code}
{refund_clause_text}

Cancellation Reason: {cancel_reason or 'Customer request'}

If you need any further assistance, please contact our support desk at tamimtahmid270@gmail.com.

Warm regards,
PageVault Customer Care
"""

        cust_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #F3EEE3; padding: 24px; color: #111;">
  <div style="max-width: 540px; margin: 0 auto; background: #FFF; border-radius: 14px; border: 1px solid #E2DAD0; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <div style="font-size: 22px; font-weight: 800; color: #111; margin-bottom: 12px; text-align: center;">Page<span style="color: #D9541E;">Vault</span> Customer Care</div>
    <div style="text-align: center; margin-bottom: 20px;">
      <span style="background: #FEE2E2; color: #B91C1C; font-size: 13px; font-weight: 700; padding: 4px 14px; border-radius: 12px;">Order Cancelled</span>
    </div>
    <p style="font-size: 15px; line-height: 1.6;">Hello <strong>{customer_name}</strong>,</p>
    <p style="font-size: 14px; line-height: 1.6; color: #444;">
      Your order <strong style="color: #D9541E;">#{order_code}</strong> has been cancelled successfully as requested within our 12-hour window.
    </p>

    <div style="background: #FAF7F2; border-radius: 10px; border: 1px solid #E2DAD0; padding: 18px; margin: 20px 0; font-size: 14px; line-height: 1.8;">
      {'<div style="color: #111; font-weight: 700; margin-bottom: 8px;">💳 Refund Breakdown:</div>' if is_online_paid else ''}
      <div><strong>Payment Method:</strong> {payment_method}</div>
      <div><strong>Total Amount:</strong> ৳{total_amount:.2f}</div>
      {f'''<div><strong>Deducted Delivery Fee:</strong> -৳{delivery_fee:.2f}</div>
      <div style="font-size: 16px; font-weight: 800; color: #065F46; margin-top: 6px; border-top: 1px dashed #E2DAD0; padding-top: 6px;">
        Net Refund Amount: ৳{refund_amount:.2f}
      </div>
      <div style="font-size: 12px; color: #666; margin-top: 6px;">Your refund will be credited back to your {payment_method} account within 3 to 5 business days.</div>
      ''' if is_online_paid else '<div style="color: #065F46; font-weight: 600; margin-top: 6px;">Zero charges incurred (Cash on Delivery).</div>'}
    </div>

    <p style="font-size: 13px; color: #736C62;">If you cancelled by mistake or have any questions, our support desk is always here to help at <a href="mailto:tamimtahmid270@gmail.com" style="color: #D9541E; font-weight: 600;">tamimtahmid270@gmail.com</a>.</p>
    <div style="font-size: 12px; color: #999; border-top: 1px solid #E2DAD0; padding-top: 14px; text-align: center; margin-top: 24px;">&copy; 2026 PageVault &bull; Dhaka, Bangladesh</div>
  </div>
</body>
</html>
"""
        if brevo_key:
            send_via_brevo_api(brevo_key, sender_email, sender_name, customer_email, cust_subject, cust_html, cust_text)

    return {'delivered': admin_delivered, 'message': 'Cancellation notifications dispatched.'}

