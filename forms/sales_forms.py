from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SalesSearchForm(FlaskForm):
    query = StringField("Поиск по платежам", validators=[DataRequired()])
    submit = SubmitField("Искать")