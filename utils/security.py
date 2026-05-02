import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# Password reset tokens
# ============================================================

def generate_reset_token():
    return secrets.token_urlsafe(32)


def get_reset_expiry(hours=1):
    return (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# Security answer hashing
# ============================================================
# Security answers are hashed the same way as passwords so they
# are never stored or compared in plain text.
# Answers are normalised to lowercase and stripped before
# hashing so comparison is case-insensitive.
# ============================================================

def hash_answer(answer):
    return generate_password_hash(answer.strip().lower())


def check_answer(answer, answer_hash):
    return check_password_hash(answer_hash, answer.strip().lower())