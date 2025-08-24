from extensions import db
from datetime import datetime, timezone

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(50), unique=True, index=True)      # Номер заказа, уникальный
    product_id = db.Column(db.BigInteger)                                # Идентификатор товара, может повторяться
    product_name = db.Column(db.String(255))                             # Название товара, может повторяться
    product_entry = db.Column(db.Text)                                   # Содержимое товара (ключ/текст)
    date_put = db.Column(db.DateTime(timezone=True))                     # Дата добавления
    date_pay = db.Column(db.DateTime(timezone=True))                     # Дата оплаты
    email = db.Column(db.String(255))                                    # Email покупателя
    amount_in = db.Column(db.Float)                                      # Оплачено
    amount_out = db.Column(db.Float)                                     # Зачислено
    amount_currency = db.Column(db.String(5))                             # Валюта
    method_pay = db.Column(db.String(50))                                 # Метод оплаты
    aggregator_pay = db.Column(db.String(50))                             # Площадка / агрегатор
    ip = db.Column(db.String(50))                                         # IP покупателя
    partner_id = db.Column(db.BigInteger)                                 # ID агента / партнёра
    lang = db.Column(db.String(10))                                       # Язык покупателя

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

class SalesLog(db.Model):
    __tablename__ = "sales_log"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    orders_loaded = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)  # например: "Автообновление" или "Ручная загрузка"
    errors = db.Column(db.Text)
