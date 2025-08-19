from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class ProfileForm(FlaskForm):
    display_name = StringField('Отображаемое имя')
    avatar = StringField('Ссылка на аватар')
    submit = SubmitField('Обновить профиль')


class StatusForm(FlaskForm):
    name = StringField('Техническое имя', validators=[DataRequired()])
    label = StringField('Название', validators=[DataRequired()])
    category = SelectField(
        'Категория',
        choices=[('reason', 'Reason'), ('process', 'Process'), ('final', 'Final')],
        validators=[DataRequired()]
    )
    color = SelectField(
        'Цвет',
        choices=[('primary', 'Primary'), ('warning', 'Warning'), ('success', 'Success')]
    )
    description = StringField('Описание')
    submit = SubmitField('Добавить')