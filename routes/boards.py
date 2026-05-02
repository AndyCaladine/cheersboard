from flask import Blueprint, render_template, redirect, url_for, session

boards_bp = Blueprint("boards", __name__)

@boards_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashbaord.html")

