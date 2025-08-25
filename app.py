from flask import Flask
from config import Config
from extensions import db, login_manager, migrate, cache
from routes.auth import auth_bp
from routes.ticket import ticket_bp
from routes.profile import profile_bp
from routes.sales import sales_bp
from digiseller import start_sales_loader


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config.get("DIGISELLER_SELLER_ID") or not app.config.get("DIGISELLER_API_KEY"):
        raise RuntimeError("DIGISELLER_SELLER_ID или DIGISELLER_API_KEY не заданы в окружении")

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    
    # Кэш для Digiseller токена
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 6600})
    
    # Регистрация блюпринтов
    app.register_blueprint(auth_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(sales_bp)

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
