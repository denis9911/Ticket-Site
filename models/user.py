from datetime import datetime, timezone
from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    tickets = db.relationship('Ticket', backref='author', lazy=True)
    messages = db.relationship('TicketMessage', backref='author', lazy=True)