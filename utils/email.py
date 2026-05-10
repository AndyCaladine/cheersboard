import os
from datetime import datetime
import resend
from flask import current_app
from utils.db import get_db_connection

resend.api_key = os.environ.get("RESEND_API_KEY", "")

SENDER = "CheersBoard <hello@cheersboard.co.uk>"
LOGO_URL = "https://andycaladine.co.uk/images/cb_logo_dark.jpg"

# ============================================================
# Temporary — replace with admin panel config when built
# ============================================================
ADMIN_EMAIL = "hello@cheersboard.co.uk"


def send_email(recipient_email, subject, html_body, email_type, user_id=None):
    """
    Send a transactional email via Resend and log the result to email_log.

    Args:
        recipient_email (str): The recipient's email address.
        subject (str):         The email subject line.
        html_body (str):       The full HTML content of the email.
        email_type (str):      A short identifier for the email type
                               e.g. 'welcome', 'password_reset', 'board_created'.
        user_id (int|None):    The user ID if the recipient has an account,
                               or None for guest emails.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    resend_id = None
    status = "failed"
    error_message = None

    try:
        response = resend.Emails.send({
            "from": SENDER,
            "to": recipient_email,
            "subject": subject,
            "html": html_body,
        })
        resend_id = response.get("id")
        status = "sent"

    except Exception as e:
        error_message = str(e)
        current_app.logger.error(
            f"[email] Failed to send '{email_type}' to {recipient_email}: {e}"
        )

    finally:
        try:
            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO email_log
                    (user_id, recipient_email, email_type, subject, resend_id, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, recipient_email, email_type, subject, resend_id, status, error_message),
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            current_app.logger.error(
                f"[email] Failed to write email_log for '{email_type}' to {recipient_email}: {db_err}"
            )

    return status == "sent"


def _base_template(content_html, preheader=""):
    """
    Wraps content in the CheersBoard branded email shell.
    All transactional emails share this outer wrapper.
    """
    current_year = datetime.now().year

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>CheersBoard</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #111111;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #ffffff;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                padding: 32px 16px;
            }}
            .email-header {{
                text-align: center;
                padding-bottom: 24px;
            }}
            .email-header img {{
                width: 280px;
                max-width: 100%;
                height: auto;
            }}
            .email-body {{
                background-color: #1a1a1a;
                border-radius: 16px;
                padding: 32px;
                border: 1px solid #2a2a2a;
            }}
            .email-body h2 {{
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
                margin-top: 0;
            }}
            .email-body p {{
                font-size: 16px;
                line-height: 1.6;
                color: #cccccc;
            }}
            .btn {{
                display: inline-block;
                padding: 14px 32px;
                border-radius: 50px;
                font-size: 16px;
                font-weight: 700;
                text-decoration: none;
                margin: 24px 0;
                background-color: #F5C518;
                color: #141B2D;
            }}
            .divider {{
                border: none;
                border-top: 1px solid #2a2a2a;
                margin: 24px 0;
            }}
            .detail-block {{
                background-color: #222222;
                border-radius: 8px;
                padding: 16px 20px;
                margin: 16px 0;
            }}
            .detail-block p {{
                margin: 6px 0;
                font-size: 14px;
                color: #cccccc;
            }}
            .detail-block strong {{
                color: #ffffff;
            }}
            .email-footer {{
                text-align: center;
                padding-top: 24px;
                font-size: 13px;
                color: #666666;
                line-height: 1.6;
            }}
            .email-footer a {{
                color: #888888;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        {'<span style="display:none;max-height:0;overflow:hidden;">' + preheader + '</span>' if preheader else ''}
        <div class="email-wrapper">
            <div class="email-header">
                <img src="{LOGO_URL}" alt="CheersBoard" />
            </div>
            <div class="email-body">
                {content_html}
            </div>
            <div class="email-footer">
                <hr class="divider" />
                <p>
                    This is an automated message from CheersBoard — please do not reply to this email
                    as this inbox is not monitored.<br />
                    If you need help, visit our <a href="https://cheersboard.co.uk/contact">Contact Us</a> page.
                </p>
                <p>
                    &copy; {current_year} CheersBoard &mdash; Making celebrations unforgettable.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# ============================================================
# Email builders
# Each function returns a bool (True = sent successfully).
# Add a new function here for each new email type.
# ============================================================

def send_welcome_email(user):
    """Send a welcome email to a newly registered user."""
    display_name = user["first_name"]
    subject = "Welcome to CheersBoard! 🎉"
    preheader = "You're in! Let's make some celebrations."

    content = f"""
        <h2>Welcome aboard, {display_name}!</h2>
        <p>
            We're so glad you're here. CheersBoard is all about bringing people together
            to celebrate the moments that matter — and now you're part of it. 🥳
        </p>
        <p>
            Head to your dashboard to create your first board and start sharing the love.
        </p>
        <p style="text-align:center;">
            <a href="https://cheersboard.co.uk/dashboard" class="btn">Go to my dashboard</a>
        </p>
        <hr class="divider" />
        <p style="font-size:14px; color:#888888;">
            If you didn't create this account, please
            <a href="https://cheersboard.co.uk/contact" style="color:#888888;">let us know</a>.
        </p>
    """

    return send_email(
        recipient_email=user["email"],
        subject=subject,
        html_body=_base_template(content, preheader),
        email_type="welcome",
        user_id=user["id"],
    )


def send_password_reset_email(user, reset_url):
    """Send a password reset link to the user."""
    display_name = user["first_name"]
    subject = "Reset your CheersBoard password"
    preheader = "Your password reset link is inside — it expires in 1 hour."

    content = f"""
        <h2>Password reset request</h2>
        <p>Hi {display_name},</p>
        <p>
            We received a request to reset your CheersBoard password.
            Click the button below to choose a new one. This link expires in <strong>1 hour</strong>.
        </p>
        <p style="text-align:center;">
            <a href="{reset_url}" class="btn">Reset my password</a>
        </p>
        <hr class="divider" />
        <p style="font-size:14px; color:#888888;">
            If you didn't request a password reset, you can safely ignore this email —
            your password won't change. If you're concerned, please
            <a href="https://cheersboard.co.uk/contact" style="color:#888888;">contact us</a>.
        </p>
    """

    return send_email(
        recipient_email=user["email"],
        subject=subject,
        html_body=_base_template(content, preheader),
        email_type="password_reset",
        user_id=user["id"],
    )


def send_contact_ack_email(name, email, subject):
    """Send an auto-acknowledgement to someone who submitted the contact form."""
    first_name = name.split()[0]
    email_subject = "We've received your message — CheersBoard"
    preheader = "We'll be in touch within 2 working days."

    content = f"""
        <h2>We've got your message!</h2>
        <p>Hi {first_name},</p>
        <p>
            Thanks for getting in touch. We've received your enquiry about
            <strong>{subject}</strong> and will get back to you within
            <strong>2 working days</strong>.
        </p>
        <p>
            In the meantime, if you have anything to add, please use the
            <a href="https://cheersboard.co.uk/contact" style="color:#F5C518;">contact form</a>
            to send us a follow-up — please do not reply to this email as this inbox is not monitored.
        </p>
        <hr class="divider" />
        <p style="font-size:14px; color:#888888;">
            Didn't submit this enquiry?
            <a href="https://cheersboard.co.uk/contact" style="color:#888888;">Let us know</a>.
        </p>
    """

    return send_email(
        recipient_email=email,
        subject=email_subject,
        html_body=_base_template(content, preheader),
        email_type="contact_ack",
        user_id=None,
    )


def send_contact_admin_email(name, email, subject, message):
    """
    Send a notification to the admin when a contact form is submitted.
    TODO: Replace ADMIN_EMAIL with a value from the admin panel config when built.
    """
    email_subject = f"New contact message: {subject}"
    preheader = f"New enquiry from {name}."

    content = f"""
        <h2>New contact form submission</h2>
        <p>A new message has been submitted via the CheersBoard contact form.</p>
        <div class="detail-block">
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
        </div>
        <p style="text-align:center;">
            <a href="https://cheersboard.co.uk/admin/contact" class="btn">View in admin panel</a>
        </p>
    """

    return send_email(
        recipient_email=ADMIN_EMAIL,
        subject=email_subject,
        html_body=_base_template(content, preheader),
        email_type="contact_admin",
        user_id=None,
    )