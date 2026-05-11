from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
from utils.db import get_db_connection
import re
import secrets


boards_bp = Blueprint("boards", __name__)


# ============================================================
# Helpers
# ============================================================

def login_required(f):
    """Simple session-based auth guard."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def get_theme_preference():
    """Return the logged-in user's theme preference, defaulting to dark."""
    if "user_id" not in session:
        return "dark"
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT theme_preference FROM users WHERE id = ? AND is_active = 1",
            (session["user_id"],)
        ).fetchone()
        return user["theme_preference"] if user else "dark"
    finally:
        conn.close()


def generate_slug(title):
    """
    Turn a board title into a URL-safe slug.
    Appends a short random suffix to avoid collisions.
    e.g. "Sarah's 30th!" -> "sarahs-30th-a3f9"
    """
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    slug = slug[:40]
    suffix = secrets.token_hex(2)
    return f"{slug}-{suffix}"


# ============================================================
# Dashboard
# ============================================================

@boards_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    try:
        user = conn.execute(
            """
            SELECT id, first_name, last_name, email, is_admin, theme_preference
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (session["user_id"],)
        ).fetchone()

        if not user:
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for("auth.login"))

        boards = conn.execute(
            """
            SELECT
                b.id,
                b.title,
                b.recipient_name,
                b.slug,
                b.tier,
                b.status,
                b.is_paid,
                b.created_at,
                o.name AS occasion_name,
                t.name AS theme_name,
                t.css_class AS theme_css_class,
                COUNT(m.id) AS message_count
            FROM boards b
            LEFT JOIN occasions o ON b.occasion_id = o.id
            LEFT JOIN themes t ON b.theme_id = t.id
            LEFT JOIN messages m ON m.board_id = b.id AND m.is_hidden = 0
            WHERE b.owner_user_id = ? AND b.status != 'deleted'
            GROUP BY b.id
            ORDER BY b.created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        boards=boards,
        theme=user["theme_preference"],
    )


# ============================================================
# Toggle theme preference
# ============================================================

@boards_bp.route("/dashboard/theme", methods=["POST"])
def toggle_theme():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorised"}), 401

    data = request.get_json()
    preference = data.get("preference", "dark")

    if preference not in ("dark", "light"):
        return jsonify({"error": "Invalid preference"}), 400

    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE users
            SET theme_preference = ?,
                updated_at = CURRENT_TIMESTAMP,
                updated_by_user_id = ?,
                updated_by_role = 'customer'
            WHERE id = ?
            """,
            (preference, session["user_id"], session["user_id"])
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"preference": preference})


# ============================================================
# Create board
# ============================================================

@boards_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_board():
    conn = get_db_connection()
    try:
        occasions = conn.execute(
            "SELECT id, name, slug FROM occasions WHERE is_active = 1 ORDER BY display_order"
        ).fetchall()

        themes = conn.execute(
            """
            SELECT id, name, slug, layout_type, tier_required, css_class
            FROM themes
            WHERE is_active = 1
            ORDER BY display_order
            """,
        ).fetchall()
    finally:
        conn.close()

    theme = get_theme_preference()
    errors = {}

    if request.method == "POST":
        board_name      = request.form.get("board_name",      "").strip()
        recipient_name  = request.form.get("recipient_name",  "").strip()
        occasion_id     = request.form.get("occasion_id",     "").strip()
        theme_id        = request.form.get("theme_id",        "").strip()
        event_date      = request.form.get("event_date",      "").strip()
        creator_message = request.form.get("creator_message", "").strip()

        if not board_name:
            errors["board_name"] = "Board name is required."
        elif len(board_name) > 80:
            errors["board_name"] = "Board name must be 80 characters or fewer."

        if not recipient_name:
            errors["recipient_name"] = "Recipient name is required."
        elif len(recipient_name) > 80:
            errors["recipient_name"] = "Recipient name must be 80 characters or fewer."

        if not occasion_id:
            errors["occasion_id"] = "Please choose an occasion."

        if not theme_id:
            errors["theme_id"] = "Please choose a theme."

        if len(creator_message) > 500:
            errors["creator_message"] = "Your message must be 500 characters or fewer."

        selected_theme = None
        if theme_id and not errors.get("theme_id"):
            conn = get_db_connection()
            try:
                selected_theme = conn.execute(
                    "SELECT id, tier_required FROM themes WHERE id = ? AND is_active = 1",
                    (theme_id,)
                ).fetchone()
            finally:
                conn.close()

            if not selected_theme:
                errors["theme_id"] = "Invalid theme selected."

        if not errors and selected_theme:
            tier    = selected_theme["tier_required"]
            is_paid = 1 if tier == "free" else 0
            slug    = generate_slug(board_name)

            conn = get_db_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO boards (
                        owner_user_id, title, recipient_name, slug,
                        occasion_id, theme_id, tier, is_paid,
                        updated_by_user_id, updated_by_role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session["user_id"],
                        board_name,
                        recipient_name,
                        slug,
                        occasion_id,
                        theme_id,
                        tier,
                        is_paid,
                        session["user_id"],
                        "customer",
                    )
                )
                conn.commit()
            finally:
                conn.close()

            flash(
                f"Board created! {'Share it below.' if tier == 'free' else 'Complete your payment to unlock it.'}",
                "success"
            )
            return redirect(url_for("boards.board_settings", slug=slug))

    return render_template(
        "create_board.html",
        occasions=occasions,
        themes=themes,
        errors=errors,
        form=request.form,
        theme=theme,
        tier_prices={
            'free':    '£0',
            'lite':    '£4.99',
            'premium': '£9.99',
            'event':   '£19.99',
        }
    )


# ============================================================
# Board settings
# ============================================================

@boards_bp.route("/board/<slug>/settings")
@login_required
def board_settings(slug):
    conn = get_db_connection()
    try:
        board = conn.execute(
            """
            SELECT b.*, o.name AS occasion_name, t.name AS theme_name
            FROM boards b
            LEFT JOIN occasions o ON b.occasion_id = o.id
            LEFT JOIN themes    t ON b.theme_id    = t.id
            WHERE b.slug = ? AND b.owner_user_id = ?
            """,
            (slug, session["user_id"])
        ).fetchone()
    finally:
        conn.close()

    if not board:
        flash("Board not found.", "error")
        return redirect(url_for("boards.dashboard"))

    ui_theme = get_theme_preference()
    board_url = request.host_url.rstrip('/') + '/board/' + board['slug']

    return render_template(
        "board_settings.html",
        board=board,
        ui_theme=ui_theme,
        board_url=board_url,
    )


# ============================================================
# Regenerate board slug
# ============================================================

@boards_bp.route("/board/<slug>/regenerate", methods=["POST"])
@login_required
def regenerate_slug(slug):
    conn = get_db_connection()
    try:
        board = conn.execute(
            "SELECT id, title FROM boards WHERE slug = ? AND owner_user_id = ?",
            (slug, session["user_id"])
        ).fetchone()

        if not board:
            flash("Board not found.", "error")
            return redirect(url_for("boards.dashboard"))

        new_slug = generate_slug(board["title"])

        conn.execute(
            """
            UPDATE boards
            SET slug = ?, updated_at = CURRENT_TIMESTAMP,
                updated_by_user_id = ?, updated_by_role = 'customer'
            WHERE id = ?
            """,
            (new_slug, session["user_id"], board["id"])
        )
        conn.commit()

    finally:
        conn.close()

    flash("Your share code has been regenerated. Make sure to share the new link.", "success")
    return redirect(url_for("boards.board_settings", slug=new_slug))