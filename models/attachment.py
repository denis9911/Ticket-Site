from extensions import db
from flask import url_for

class TicketAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey('ticket.id', ondelete='CASCADE'),
        nullable=False
    )

    def url(self):
        return url_for('static', filename='uploads/' + self.filename)
