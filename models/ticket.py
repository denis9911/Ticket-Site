from extensions import db

from datetime import datetime, timezone


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50))
    source = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    product = db.Column(db.String(100), nullable=True)
    reason = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='open')
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


class TicketMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey('ticket.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
