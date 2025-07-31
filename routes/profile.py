import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from forms.profile_forms import ProfileForm
from forms.auth_forms import RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint('profile', __name__)


def save_avatar(file):
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)
    return f'uploads/{unique_name}'


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    register_form = RegisterForm()  # ← добавляем форму регистрации

    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename != '':
                current_user.avatar = save_avatar(avatar_file)
        db.session.commit()
        flash('Профиль обновлен', 'success')
        return redirect(url_for('profile.profile'))

    elif request.method == 'GET':
        form.display_name.data = current_user.display_name

    return render_template('profile.html', form=form, register_form=register_form)


@profile_bp.route('/change_avatar', methods=['POST'])
@login_required
def change_avatar():
    if 'avatar' in request.files:
        avatar_file = request.files['avatar']
        if avatar_file.filename != '':
            current_user.avatar = save_avatar(avatar_file)
            db.session.commit()
            flash('Аватар обновлен', 'success')
        else:
            flash('Файл не выбран', 'warning')
    else:
        flash('Файл не получен', 'danger')

    return redirect(url_for('profile.profile'))


@profile_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Текущий пароль неверен', 'danger')
        return redirect(url_for('profile.profile'))

    if new_password != confirm_password:
        flash('Новые пароли не совпадают', 'danger')
        return redirect(url_for('profile.profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()

    flash('Пароль успешно изменен', 'success')
    return redirect(url_for('profile.profile'))
