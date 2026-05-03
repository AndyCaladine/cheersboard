from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
from utils.db import get_db_connection
 
 
boards_bp = Blueprint("boards", __name__)


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