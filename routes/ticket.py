import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from extensions import db
from forms.profile_forms import StatusForm
from models.ticket import Ticket, TicketMessage, TicketMessageAttachment, Status
from models.attachment import TicketAttachment
from models.ticket_view import TicketView
from forms.ticket_forms import TicketForm, MessageForm, EditTicketForm, TicketSearchForm
from sqlalchemy import or_

ticket_bp = Blueprint('ticket', __name__)


def save_file(file):
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename


@ticket_bp.route('/')
@ticket_bp.route('/dashboard')
@login_required
def dashboard():
    # Получаем "открытые" статусы, кроме категории final
    open_statuses = Status.query.filter(
        Status.category != 'final'
    ).all()
    open_status_ids = [s.id for s in open_statuses]

    # Открытые тикеты
    open_tickets = Ticket.query.filter(Ticket.status_id.in_(open_status_ids)).order_by(Ticket.created_at.desc()).all()

    # Закрытые тикеты (не в категории final)
    closed_statuses = Status.query.filter(Status.category == 'final').all()
    closed_status_ids = [s.id for s in closed_statuses]
    closed_tickets = Ticket.query.filter(Ticket.status_id.in_(closed_status_ids)).order_by(Ticket.closed_at.desc()).all()

    # Подсветка новых/обновлённых тикетов
    ticket_highlights = {}
    for ticket in open_tickets:
        view = TicketView.query.filter_by(ticket_id=ticket.id, user_id=current_user.id).first()
        ticket_highlights[ticket.id] = not view or (ticket.updated_at and ticket.updated_at > view.last_viewed_at)

    return render_template(
        'dashboard.html',
        open_tickets=open_tickets,
        closed_tickets=closed_tickets,
        ticket_highlights=ticket_highlights
    )


@ticket_bp.route('/new_ticket', methods=['GET', 'POST'])
@login_required
def new_ticket():
    form = TicketForm()

    # Берём только статусы из категории "reason"
    reason_statuses = Status.query.filter_by(category='reason').all()
    form.status.choices = [(s.id, s.label) for s in reason_statuses]

    if form.validate_on_submit():
        status_obj = Status.query.get(form.status.data)

        ticket = Ticket(
            order_number=form.order_number.data,
            source=form.source.data,
            customer_email=form.customer_email.data,
            product=form.product.data,
            reason=form.reason.data,
            user_id=current_user.id,
            status=status_obj
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

    return render_template('new_ticket.html', form=form, all_statuses=reason_statuses)


@ticket_bp.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = MessageForm()

    # --- Обновление информации о просмотре тикета ---
    view = TicketView.query.filter_by(ticket_id=ticket.id, user_id=current_user.id).first()
    if not view:
        view = TicketView(ticket_id=ticket.id, user_id=current_user.id)
        db.session.add(view)
    view.last_viewed_at = datetime.now(timezone.utc)
    db.session.commit()

    if form.validate_on_submit():
        # Создаем сообщение
        message = TicketMessage(
            content=form.content.data,
            ticket_id=ticket.id,
            user_id=current_user.id
        )
        db.session.add(message)
        db.session.commit()  # чтобы был message.id

        # Сохраняем вложения
        if form.attachment.data:
            for file in form.attachment.data:
                if file.filename != '':
                    filename = save_file(file)
                    attachment = TicketMessageAttachment(
                        filename=filename,
                        message_id=message.id
                    )
                    db.session.add(attachment)
            db.session.commit()

        ticket.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('Сообщение отправлено', 'success')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    # Получаем все статусы для кнопок
    all_statuses = Status.query.all()

    return render_template(
        'ticket_view.html',
        ticket=ticket,
        form=form,
        all_statuses=all_statuses  # <-- передаём сюда
    )



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
    ticket = Ticket.query.get_or_404(ticket_id)
    
    new_status_id = request.form.get('new_status_id')
    if not new_status_id:
        abort(400)

    status_obj = Status.query.get(new_status_id)
    if not status_obj:
        abort(400)

    status_obj = Status.query.get(request.form.get('new_status_id'))
    old_status = ticket.status  # ticket.status – объект Status
    ticket.status = status_obj

    if old_status and old_status.name != 'closed' and status_obj.name == 'closed':
        ticket.closed_at = datetime.now(timezone.utc)
    elif old_status and old_status.name == 'closed' and status_obj.name != 'closed':
        ticket.closed_at = None

    db.session.commit()
    flash(f'Статус изменен на "{status_obj.label}"', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/statuses', methods=['GET', 'POST'])
@login_required
def manage_statuses():
    if not current_user.is_admin:
        abort(403)

    status_form = StatusForm()

    if status_form.validate_on_submit():
        status = Status(
            name=status_form.name.data,
            label=status_form.label.data,
            category=status_form.category.data,
            color=status_form.color.data,
            description=status_form.description.data
        )
        db.session.add(status)
        db.session.commit()
        flash("Статус добавлен", "success")
        return redirect(url_for('profile.profile'))

    statuses = Status.query.all()
    return redirect(url_for('profile.profile'))


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

    if not current_user.is_admin:
        abort(403)

    # Удаляем все связанные TicketView
    TicketView.query.filter_by(ticket_id=ticket.id).delete()

    # Удаляем вложения сообщений
    for msg in ticket.messages:
        for att in msg.attachments:
            try:
                os.remove(os.path.join(current_app.static_folder, 'uploads', att.filename))
            except Exception:
                pass
            db.session.delete(att)

    # Удаляем файлы самого тикета
    for att in ticket.images:
        try:
            os.remove(os.path.join(current_app.static_folder, 'uploads', att.filename))
        except Exception:
            pass
        db.session.delete(att)

    # Наконец, удаляем тикет
    db.session.delete(ticket)
    db.session.commit()

    flash(f'Тикет #{ticket.id} удалён', 'success')
    return redirect(url_for('ticket.dashboard'))

@ticket_bp.route('/add_status', methods=['POST'])
@login_required
def add_status():
    if not current_user.is_admin:
        abort(403)

    label = request.form.get('label')
    category = request.form.get('category')

    if not label or not category:
        flash("Все поля обязательны", "danger")
        return redirect(url_for('ticket.new_ticket'))

    status = Status(label=label, name=label.lower().replace(' ', '_'), category=category)
    db.session.add(status)
    db.session.commit()
    flash(f'Статус "{label}" добавлен', 'success')
    return redirect(url_for('ticket.new_ticket'))