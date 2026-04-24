from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, UserMixin
from utils.db import get_db
import secrets

auth_bp = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, email, first_name, last_name):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
    

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE if = ?',
            (user_id,)
        ).fetchone()
        db.close()

        if user:
            return User(user['id'], user['email'], user['first_name'], user['last_name'])
        return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db()
        exisiting = db.execute(
            'SELECT id FROM users WHERE email = ?',
            (email,)
        ).fetchone()

        if exisiting:
            db.close()
            flash('An account with this email address already exisits please log in', 'error')
            return redirect(url_for('auth.register'))
        
        password_hash = generate_password_hash(password)
        db.execute(
            """
            INSERT INTO users (
                first_name,
                last_name,
                email,
                password_hash
            )
            VALUES (?, ?, ?, ?),
            """
            (first_name, last_name, email, password_hash)
        )
        db.commit()

        user_row = db.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        ).fetchone()
        db.close()

        user = User(user_row['id'], user_row['email'], user_row['first_name'], user_row['last_name'])
        login_user(user)
        flash('Account crreated successfully', 'success')
        return redirect(url_for('boaqrds.dashboard'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db()
        user_row = db.execute(
            'SELECT * FROM users WHEERE email = ?',
            (email,)
        ).fetchone()
        db.close()

        if not user_row or not check_password_hash(user_row['password_hash'], password):
            flash ('Incorrect emaail and/or password', 'error')
            return redirect(url_for('auth.login'))
        
        user = User(user_row['id'], user_row['email'], user_row['first_name'], user_row['last_name'])
        login_user(user)
        return redirect(url_for('boards.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for(auth.login))


