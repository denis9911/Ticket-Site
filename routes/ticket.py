import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from extensions import db
from models.ticket import Ticket, TicketMessage
from models.attachment import TicketAttachment
from forms.ticket_forms import TicketForm, MessageForm, EditTicketForm, TicketSearchForm
from sqlalchemy import or_

ticket_bp = Blueprint('ticket', __name__)


def save_file(file):
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(path)
    return unique_name


@ticket_bp.route('/')
@ticket_bp.route('/dashboard')
@login_required
def dashboard():
    open_tickets = Ticket.query.filter(
        Ticket.status.in_(['open', 'in_progress', 'admin_needed'])
    ).order_by(Ticket.created_at.desc()).all()

    closed_tickets = Ticket.query.filter(Ticket.status == 'closed').order_by(Ticket.closed_at.desc()).all()

    return render_template('dashboard.html', open_tickets=open_tickets, closed_tickets=closed_tickets)


@ticket_bp.route('/new_ticket', methods=['GET', 'POST'])
@login_required
def new_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(
            order_number=form.order_number.data,
            source=form.source.data,
            customer_email=form.customer_email.data,
            product=form.product.data,
            reason=form.reason.data,
            user_id=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()

        files = request.files.getlist('images')
        for file in files:
            if file.filename != '':
                filename = save_file(file)
                attachment = TicketAttachment(filename=filename, ticket_id=ticket.id)
                db.session.add(attachment)
        db.session.commit()

        flash('Тикет успешно создан!', 'success')
        return redirect(url_for('ticket.dashboard'))
    return render_template('new_ticket.html', form=form)


@ticket_bp.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = MessageForm()

    if form.validate_on_submit():
        message = TicketMessage(
            content=form.content.data,
            ticket_id=ticket.id,
            user_id=current_user.id
        )
        db.session.add(message)

        if ticket.status == 'open':
            ticket.status = 'in_progress'

        ticket.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        flash('Сообщение отправлено', 'success')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    return render_template('ticket_view.html', ticket=ticket, form=form)


@ticket_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = EditTicketForm()

    if form.validate_on_submit():
        ticket.order_number = form.order_number.data
        ticket.source = form.source.data
        ticket.customer_email = form.customer_email.data
        ticket.reason = form.reason.data
        ticket.status = form.status.data

        if form.status.data == 'closed' and ticket.status != 'closed':
            ticket.closed_at = datetime.now(timezone.utc)
        elif form.status.data != 'closed' and ticket.status == 'closed':
            ticket.closed_at = None

        if form.images.data:
            for img in form.images.data:
                if img.filename != '':
                    filename = save_file(img)
                    attachment = TicketAttachment(filename=filename, ticket_id=ticket.id)
                    db.session.add(attachment)

        ticket.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        flash('Тикет успешно обновлен', 'success')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    if request.method == 'GET':
        form.order_number.data = ticket.order_number
        form.source.data = ticket.source
        form.customer_email.data = ticket.customer_email
        form.reason.data = ticket.reason
        form.status.data = ticket.status

    return render_template('edit_ticket.html', form=form, ticket=ticket)


@ticket_bp.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    message = TicketMessage.query.get_or_404(message_id)
    if message.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    ticket_id = message.ticket_id
    db.session.delete(message)
    db.session.commit()
    flash('Сообщение удалено', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


@ticket_bp.route('/ticket/<int:ticket_id>/change_status', methods=['POST'])
@login_required
def change_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        abort(404)

    new_status = request.form.get('new_status')
    if new_status not in ['open', 'in_progress', 'admin_needed', 'closed']:
        abort(400)

    # Логика изменения статуса
    # Сохраняем старый статус для сравнения
    old_status = ticket.status

    ticket.status = new_status

    if new_status == 'closed' and old_status != 'closed':
        ticket.closed_at = datetime.now(timezone.utc)
    elif old_status == 'closed' and new_status != 'closed':
        ticket.closed_at = None

    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'Статус изменен на "{new_status}"', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/tickets/search', methods=['GET', 'POST'])
def search_tickets():
    form = TicketSearchForm()
    results = []

    if form.validate_on_submit():
        search_term = form.query.data.strip()

        # Поиск по полям Ticket и связанным TicketMessage
        results = db.session.query(Ticket).outerjoin(TicketMessage).filter(
            or_(
                Ticket.order_number.ilike(f"%{search_term}%"),
                Ticket.customer_email.ilike(f"%{search_term}%"),
                Ticket.product.ilike(f"%{search_term}%"),
                Ticket.reason.ilike(f"%{search_term}%"),
                TicketMessage.content.ilike(f"%{search_term}%")
            )
        ).distinct().all()

    return render_template('search_result.html', form=form, results=results)


@ticket_bp.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Разрешим удаление только администратору
    if not current_user.is_admin:
        abort(403)

    db.session.delete(ticket)
    db.session.commit()
    flash(f'Тикет #{ticket.id} удалён', 'success')
    return redirect(url_for('ticket.dashboard'))
