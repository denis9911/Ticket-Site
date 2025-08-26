from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_caching import Cache
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
socketio = SocketIO(cors_allowed_origins="*")

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    from extensions import db
    return db.session.get(User, int(user_id))
