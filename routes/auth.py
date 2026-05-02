from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
from utils.security import hash_answer
from config import Config

auth_bp = Blueprint("auth", __name__)

SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What was the name of the street you grew up on?",
    "What was the name of your primary school?",
    "What is your mother's maiden name?",
    "What was the make of your first car?",
    "What is the name of the town where you were born?",
    "What was the name of your childhood best friend?",
]

# ============================================================
# Helpers
# ============================================================

def assemble_dob (day, month, year):
    """
    Take three sting parts from the date of birth dropdowns and returns a single string
    in YYYY-MM-DD format, or None if any part os missing or invalid.
    """
    if not day or not month or not year:
        return None
    try:
        dob = datetime(int(year), int(month), int(day))
        return dob.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    
def validate_step1(form):
    """
    Validates step 1 fields. Returns an error dict keyed by field name.
    Am e,pty dict means the validation has passed
    """

    errors = {}

    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    email = form.get("email", "").strip().lower()
    dob_day = form.get("dob_day", "").strip()
    dob_month = form.get("dob_month", "").strip()
    dob_year = form.get("dob_year", "").strip()
    mobile_number = form.get("mobile_number", "").strip()

    if not first_name:
        errors["first_name"] = "Please enter your first name"

    if not last_name:
        errors["last_name"] = "Please enter your surname. If you do not have a surname enter your first name again."

    if not email:
        errors["email"] = "Please enter your email address."

    if not dob_day or not dob_month or not dob_year:
        errors["date_of_birth"] = "Please enter your date of birth in all fields."
    else:
        dob_str = assemble_dob(dob_day, dob_month, dob_year)
        if not dob_str:
            errors["date_of_birth"] = "The date of birth you have entered is not valid."
        else:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            age = (datetime.today() - dob).days // 365
            if age < 13:
                errors["date_of_birth"] = "You must be at least 13 years old to register."
    
    return errors

def validate_step2(form):
    errors = {}
 
    if not form.get("address_line_1", "").strip():
        errors["address_line_1"] = "Please enter the first line of your address."
 
    if not form.get("city", "").strip():
        errors["city"] = "Please enter your city or town."
 
    if not form.get("postcode", "").strip():
        errors["postcode"] = "Please enter your postcode."
 
    if not form.get("country", "").strip():
        errors["country"] = "Please select your country."
 
    return errors

def validate_step3(form):
    errors = {}

    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")
    security_question = form.get("security_question", "").strip()
    security_answer = form.get("security_answer", "").strip()

    #Password rules
    if not password:
        errors["password"] = "Please enter a password"
    else:
        password_errors = []
        if len(password) < 8:
            password_errors.append("at least 8 charactrers")
        if not any(c.islower() for c in password):
            password_errors.append("one lowercase letter")
        if not any(c.isupper() for c in password):
            password_errors.append("one uppercase letter")
        if not any(c.isdigit() for c in password):
            password_errors.append("one number")
        if not any(c.isalnum() for c in password):
            password_errors.append("one special character")

        if password_errors:
            errors["password"] = "Your password must contain " + ", ".join(password_errors) + "."

    if not errors.get("password"):
        if not confirm_password:
            errors["confirm_password"] = "Please confirm your password."
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match. Please try again."

    if not security_question:
        errors["security_question"] = "Please select a secuirty question."
    elif security_question not in SECURITY_QUESTIONS:
        errors["security_question"] = "Please select a valid question from the list."

    if not security_answer:
        errors["security_answer"] = "Please enter an answer to your security question."
    elif security_answer == password:
        errors["security_answer"] = "Your security answer cannot be the same as your password."
 
    return errors

def validate_step4(form):
    errors = {}
 
    communication_preference = form.get("communication_preference", "").strip()
    if communication_preference not in ("email", "sms", "both", "none"):
        errors["communication_preference"] = "Please select a communication preference."
 
    if not form.get("terms_agreed"):
        errors["terms_agreed"] = "You must agree to the Terms & Conditions to continue."
 
    if not form.get("gdpr_agreed"):
        errors["gdpr_agreed"] = "You must confirm you have read the Privacy Policy to continue."
 
    return errors


# ============================================================
# Registration — Step 1: About You
# ============================================================
 
@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/register/step/1", methods=["GET", "POST"])
def register_step1():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    if request.method == "POST":
        form = request.form
 
        first_name = form.get("first_name", "").strip()
        last_name = form.get("last_name", "").strip()
        email = form.get("email", "").strip().lower()
        dob_day = form.get("dob_day", "").strip()
        dob_month = form.get("dob_month", "").strip()
        dob_year = form.get("dob_year", "").strip()
        mobile_number = form.get("mobile_number", "").strip()
 
        errors = validate_step1(form)
 
        # Email uniqueness check — only if no other errors so far
        if not errors.get("email") and email:
            conn = get_db_connection()
            try:
                existing = conn.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (email,)
                ).fetchone()
                if existing:
                    errors["email"] = "An account already exists for that email address."
            finally:
                conn.close()
 
        if errors:
            return render_template(
                "register_step1.html",
                form_data=form.to_dict(),
                errors=errors,
                step=1
            )
 
        dob_str = assemble_dob(dob_day, dob_month, dob_year)
 
        session["reg_step1"] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "date_of_birth": dob_str,
            "dob_day": dob_day,
            "dob_month": dob_month,
            "dob_year": dob_year,
            "mobile_number": mobile_number,
        }
 
        return redirect(url_for("auth.register_step2"))
 
    form_data = session.get("reg_step1", {})
    return render_template(
        "register_step1.html",
        form_data=form_data,
        errors={},
        step=1
    )
 
 
# ============================================================
# Registration — Step 2: Your Address
# ============================================================
 
@auth_bp.route("/register/step/2", methods=["GET", "POST"])
def register_step2():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    if "reg_step1" not in session:
        flash("Your session has expired. Please start again.", "error")
        return redirect(url_for("auth.register_step1"))
 
    if request.method == "POST":
        form = request.form
 
        address_line_1 = form.get("address_line_1", "").strip()
        address_line_2 = form.get("address_line_2", "").strip()
        city = form.get("city", "").strip()
        county = form.get("county", "").strip()
        postcode = form.get("postcode", "").strip()
        country = form.get("country", "United Kingdom").strip()
 
        errors = validate_step2(form)
 
        if errors:
            return render_template(
                "register_step2.html",
                form_data=form.to_dict(),
                errors=errors,
                step=2
            )
 
        session["reg_step2"] = {
            "address_line_1": address_line_1,
            "address_line_2": address_line_2,
            "city": city,
            "county": county,
            "postcode": postcode,
            "country": country,
        }
 
        return redirect(url_for("auth.register_step3"))
 
    form_data = session.get("reg_step2", {})
    return render_template(
        "register_step2.html",
        form_data=form_data,
        errors={},
        step=2
    )
 
 
# ============================================================
# Registration — Step 3: Password & Security
# ============================================================
 
@auth_bp.route("/register/step/3", methods=["GET", "POST"])
def register_step3():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    if "reg_step2" not in session:
        flash("Your session has expired. Please start again.", "error")
        return redirect(url_for("auth.register_step1"))
 
    if request.method == "POST":
        form = request.form
        errors = validate_step3(form)
 
        if errors:
            return render_template(
                "register_step3.html",
                form_data=form.to_dict(),
                errors=errors,
                security_questions=SECURITY_QUESTIONS,
                step=3
            )
 
        session["reg_step3"] = {
            "password": form.get("password", ""),
            "security_question": form.get("security_question", "").strip(),
            "security_answer": form.get("security_answer", "").strip(),
        }
 
        return redirect(url_for("auth.register_step4"))
 
    form_data = session.get("reg_step3", {})
    return render_template(
        "register_step3.html",
        form_data=form_data,
        errors={},
        security_questions=SECURITY_QUESTIONS,
        step=3
    )
 
 
# ============================================================
# Registration — Step 4: Preferences & Agreements
# ============================================================
 
@auth_bp.route("/register/step/4", methods=["GET", "POST"])
def register_step4():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    if "reg_step3" not in session:
        flash("Your session has expired. Please start again.", "error")
        return redirect(url_for("auth.register_step1"))
 
    if request.method == "POST":
        form = request.form
        errors = validate_step4(form)
 
        if errors:
            return render_template(
                "register_step4.html",
                form_data=form.to_dict(),
                errors=errors,
                step=4
            )
 
        session["reg_step4"] = {
            "communication_preference": form.get("communication_preference", "email").strip(),
            "marketing_opt_in": 1 if form.get("marketing_opt_in") else 0,
            "notifications_opt_in": 1 if form.get("notifications_opt_in") else 0,
            "terms_agreed": 1,
            "gdpr_agreed": 1,
        }
 
        return redirect(url_for("auth.register_review"))
 
    form_data = session.get("reg_step4", {})
    return render_template(
        "register_step4.html",
        form_data=form_data,
        errors={},
        step=4
    )
 
 
# ============================================================
# Registration — Step 5: Review & Submit
# ============================================================
 
@auth_bp.route("/register/review", methods=["GET", "POST"])
def register_review():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    for key in ("reg_step1", "reg_step2", "reg_step3", "reg_step4"):
        if key not in session:
            flash("Your session has expired. Please start again.", "error")
            return redirect(url_for("auth.register_step1"))
 
    if request.method == "POST":
        voucher_code = request.form.get("voucher_code", "").strip().upper()
 
        s1 = session["reg_step1"]
        s2 = session["reg_step2"]
        s3 = session["reg_step3"]
        s4 = session["reg_step4"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (s1["email"],)
            ).fetchone()
 
            if existing:
                flash("An account already exists for that email address. Please log in.", "error")
                for key in ("reg_step1", "reg_step2", "reg_step3", "reg_step4"):
                    session.pop(key, None)
                return redirect(url_for("auth.login"))
 
            conn.execute(
                """
                INSERT INTO users (
                    first_name, last_name, email, date_of_birth, mobile_number,
                    password_hash, security_question, security_answer_hash,
                    address_line_1, address_line_2, city, county, postcode, country,
                    terms_accepted, terms_accepted_at, terms_version,
                    gdpr_accepted, gdpr_accepted_at, gdpr_version,
                    marketing_opt_in, notifications_opt_in, communication_preference,
                    is_active, updated_by_role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s1["first_name"], s1["last_name"], s1["email"],
                    s1["date_of_birth"], s1["mobile_number"] or None,
                    generate_password_hash(s3["password"]),
                    s3["security_question"], hash_answer(s3["security_answer"]),
                    s2["address_line_1"], s2["address_line_2"] or None,
                    s2["city"], s2["county"] or None, s2["postcode"], s2["country"],
                    1, now, Config.TERMS_VERSION,
                    1, now, Config.GDPR_VERSION,
                    s4["marketing_opt_in"], s4["notifications_opt_in"],
                    s4["communication_preference"], 1, "customer",
                )
            )
            conn.commit()
 
            user = conn.execute(
                "SELECT id, first_name, is_admin FROM users WHERE email = ?",
                (s1["email"],)
            ).fetchone()
 
            for key in ("reg_step1", "reg_step2", "reg_step3", "reg_step4"):
                session.pop(key, None)
 
            session["user_id"] = user["id"]
            session["email"] = s1["email"]
            session["user_name"] = user["first_name"]
            session["is_admin"] = user["is_admin"]
 
            if voucher_code:
                session["pending_voucher"] = voucher_code
 
            flash(f"Welcome to CheersBoard, {user['first_name']}! Your account has been created.", "success")
            return redirect(url_for("boards.dashboard"))
 
        finally:
            conn.close()
 
    return render_template(
        "register_review.html",
        s1=session["reg_step1"],
        s2=session["reg_step2"],
        s3=session["reg_step3"],
        s4=session["reg_step4"],
        step=5
    )
 
 
# ============================================================
# Login
# ============================================================
 
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
 
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
 
        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT id, first_name, email, password_hash, is_admin
            FROM users
            WHERE email = ? AND is_active = 1
            """,
            (email,)
        ).fetchone()
        conn.close()
 
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["user_name"] = user["first_name"]
            session["is_admin"] = user["is_admin"]
            flash(f"Welcome back, {user['first_name']}!", "success")
            return redirect(url_for("boards.dashboard"))
 
        flash("Incorrect email or password. Please check your details and try again.", "error")
 
    return render_template("login.html")
 
 
# ============================================================
# Logout
# ============================================================
 
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
 