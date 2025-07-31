from flask import Flask
from config import Config
from extensions import db, login_manager, migrate
from routes.auth import auth_bp
from routes.ticket import ticket_bp
from routes.profile import profile_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'

    # Регистрация блюпринтов
    app.register_blueprint(auth_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(profile_bp)

    # Создаём таблицы при старте (только для отладки/первого запуска)
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
