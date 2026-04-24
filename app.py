from flask import Flask
from config import Config
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.boards import boards_bp
    from routes.payments import payments_bp
    from routes.admin import admin_bp

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.register_blueprint(auth_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

