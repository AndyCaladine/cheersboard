from datetime import datetime
from flask import Flask, redirect, url_for, session, render_template
from config import Config
from routes.auth import auth_bp
from routes.boards import boards_bp
from routes.payments import payments_bp
from routes.admin import admin_bp


app = Flask(__name__)
app.config.from_object(Config)


# ============================================================
# Template filters
# ============================================================

@app.template_filter("format_date")
def format_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y")
    except:
        return value


@app.template_filter("format_datetime")
def format_datetime(value):
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y %H:%M")
    except:
        return value


@app.template_filter("pence_to_pounds")
def pence_to_pounds(value):
    if not value:
        return "£0.00"
    try:
        return f"£{int(value) / 100:.2f}"
    except:
        return value


# ============================================================
# Blueprints
# ============================================================

app.register_blueprint(auth_bp)
app.register_blueprint(boards_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(admin_bp)


# ============================================================
# Root route
# ============================================================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("boards.dashboard"))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)