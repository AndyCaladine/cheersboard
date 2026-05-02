from flask import Blueprint, render_template, redirect, url_for, session

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return render_template("login.html")

@auth_bp.route("/register")
def register():
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))