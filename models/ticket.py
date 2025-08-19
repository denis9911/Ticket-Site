from extensions import db
from flask import url_for

from datetime import datetime, timezone


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50))
    source = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    product = db.Column(db.String(100), nullable=True)
    reason = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    status = db.relationship("Status")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime(timezone=True))
    messages = db.relationship(
        'TicketMessage',
        backref='ticket',
        lazy=True,
        order_by="TicketMessage.created_at",
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    images = db.relationship(
        'TicketAttachment',
        backref='ticket',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class Status(db.Model):
    __tablename__ = "status" 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # техническое имя ("open", "admin_needed", "closed", )
    label = db.Column(db.String(100), nullable=False)              # человекочитаемое ("Открыт", "Нужен Админ", "Закрыт")
    category = db.Column(db.String(50), nullable=True)             # категория ("reason", "process", "final")
    color = db.Column(db.String(20), nullable=True)                # например: "warning", "primary", "success"
    description = db.Column(db.String(100), nullable=True)         # например: "Вопрос по платежу - Завис платеж или другие проблемы с ним"


class TicketMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey('ticket.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    attachments = db.relationship(
        'TicketMessageAttachment',
        backref='message',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class TicketMessageAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    message_id = db.Column(
        db.Integer,
        db.ForeignKey('ticket_message.id', ondelete='CASCADE'),
        nullable=False
    )

    def url(self):
        return url_for('static', filename='uploads/' + self.filename)

