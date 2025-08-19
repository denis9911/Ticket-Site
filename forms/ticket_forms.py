from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, MultipleFileField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileAllowed


class TicketForm(FlaskForm):
    order_number = StringField('Номер заказа', validators=[DataRequired()])
    source = SelectField('Откуда тикет?', choices=[('talkme', 'TalkMe'), ('digiseller', 'Digiseller')],
                         validators=[DataRequired()])
    customer_email = StringField('Почта покупателя', validators=[Email(), DataRequired()])
    product = StringField('Купленный продукт', validators=[DataRequired()])
    reason = TextAreaField('Причина обращения', validators=[DataRequired()])
    images = MultipleFileField('Прикрепить изображения',
                               validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    status = SelectField('Статус', coerce=int, validators=[DataRequired()])  # <-- добавляем статус
    submit = SubmitField('Создать тикет')



class EditTicketForm(FlaskForm):
    order_number = StringField('Номер заказа', validators=[DataRequired()])
    source = SelectField('Источник', choices=[('talkme', 'TalkMe'), ('digiseller', 'Digiseller'), ('other', 'Другое')],
                         validators=[DataRequired()])
    customer_email = StringField('Email покупателя', validators=[Email(), DataRequired()])
    reason = TextAreaField('Причина обращения', validators=[DataRequired()])
    images = MultipleFileField('Прикрепить изображения',
                               validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    status = SelectField('Статус',
                         choices=[('open', 'Открыт'), ('waiting_for_dev', 'Ждём ответ разраба'), ('admin_needed', 'Требуется админ'), ('send_to_buyer', "Отправьте ключ"),
                                  ('closed', 'Закрыт')], validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')


class MessageForm(FlaskForm):
    content = TextAreaField('Сообщение')
    attachment = MultipleFileField(
        'Прикрепить файлы',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')]
    )
    submit = SubmitField('Отправить')


class TicketSearchForm(FlaskForm):
    query = StringField('Поиск', validators=[DataRequired()])
    submit = SubmitField('Найти')
