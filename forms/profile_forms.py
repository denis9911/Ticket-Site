from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class ProfileForm(FlaskForm):
    display_name = StringField('Отображаемое имя')
    avatar = StringField('Ссылка на аватар')
    submit = SubmitField('Обновить профиль')
