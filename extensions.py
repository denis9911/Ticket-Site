from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_caching import Cache

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    from extensions import db
    return db.session.get(User, int(user_id))
