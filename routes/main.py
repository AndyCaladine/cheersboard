from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from utils.db import get_db_connection
from utils.email import send_contact_ack_email, send_contact_admin_email

main_bp = Blueprint("main", __name__)

CONTACT_SUBJECTS = [
    "General enquiry",
    "Problem with my board",
    "Billing question",
    "Report inappropriate content",
    "Press & partnerships",
    "Other",
]


# ============================================================
# Contact
# ============================================================

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    errors = {}

    # Pre-fill name and email for logged-in users
    prefill = {}
    if "user_id" in session:
        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT first_name, last_name, email FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()
            if user:
                prefill["name"] = f"{user['first_name']} {user['last_name']}"
                prefill["email"] = user["email"]
        finally:
            conn.close()

    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Validation
        if not name:
            errors["name"] = "Please enter your name."
        if not email:
            errors["email"] = "Please enter your email address."
        if not subject or subject not in CONTACT_SUBJECTS:
            errors["subject"] = "Please select a subject."
        if not message:
            errors["message"] = "Please enter your message."
        elif len(message) < 10:
            errors["message"] = "Your message is a little short — please give us a bit more detail."

        if not errors:
            user_id = session.get("user_id")

            conn = get_db_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO contact_messages
                        (user_id, name, email, subject, message, gdpr_consent)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (user_id, name, email, subject, message)
                )
                conn.commit()
            finally:
                conn.close()

            # Send auto-ack to sender and notification to admin
            send_contact_ack_email(name, email, subject)
            send_contact_admin_email(name, email, subject, message)

            flash(
                "Thanks for getting in touch! We've received your message and will get back to you within 2 working days.",
                "success"
            )
            return redirect(url_for("main.contact"))

    return render_template(
        "contact.html",
        errors=errors,
        prefill=prefill,
        subjects=CONTACT_SUBJECTS,
        form_data=request.form if request.method == "POST" else {},
    )


# ============================================================
# Privacy Policy
# ============================================================

@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ============================================================
# Terms and Conditions
# ============================================================

@main_bp.route("/terms")
def terms():
    return render_template("terms.html")