from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, MultipleFileField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileAllowed


class TicketForm(FlaskForm):
    order_number = StringField('Номер заказа')
    source = SelectField('Откуда тикет?', choices=[('talkme', 'TalkMe'), ('digiseller', 'Digiseller')],
                         validators=[DataRequired()])
    customer_email = StringField('Почта покупателя', validators=[Email()])
    product = StringField('Купленный продукт (необязательно)')
    images = MultipleFileField('Прикрепить изображения',
                               validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    reason = TextAreaField('Причина обращения', validators=[DataRequired()])
    submit = SubmitField('Создать тикет')


class EditTicketForm(FlaskForm):
    order_number = StringField('Номер заказа')
    source = SelectField('Источник', choices=[('talkme', 'TalkMe'), ('digiseller', 'Digiseller'), ('other', 'Другое')],
                         validators=[DataRequired()])
    customer_email = StringField('Email покупателя', validators=[Email()])
    reason = TextAreaField('Причина обращения', validators=[DataRequired()])
    images = MultipleFileField('Прикрепить изображения',
                               validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    status = SelectField('Статус',
                         choices=[('open', 'Открыт'), ('in_progress', 'В работе'), ('admin_needed', 'Требуется админ'),
                                  ('closed', 'Закрыт')], validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')


class MessageForm(FlaskForm):
    content = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')


class TicketSearchForm(FlaskForm):
    query = StringField('Поиск', validators=[DataRequired()])
    submit = SubmitField('Найти')
