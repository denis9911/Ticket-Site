from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
from forms.auth_forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('ticket.dashboard'))
        flash('Неверные учетные данные', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin:
        abort(403)
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Пользователь с таким логином уже существует', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            user = User(
                username=form.username.data,
                password=hashed_password,
                display_name=form.display_name.data or form.username.data
            )
            db.session.add(user)
            db.session.commit()
            flash(f'Пользователь {form.username.data} успешно зарегистрирован!', 'success')
            return redirect(url_for('auth.register'))
    return render_template('register.html', form=form)
