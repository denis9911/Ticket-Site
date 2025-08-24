import time
import hashlib
import logging
import threading
import requests
import pytz
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from flask import current_app
from extensions import db
from app import cache
from models.sales import Sale, SalesLog


DIGISELLER_API_URL = "https://api.digiseller.com/api"

def save_sales_log(orders_count=0, note="", errors=None):
    """Сохраняет лог подгрузки заказов в БД"""
    error_text = "; ".join(errors) if errors else ""
    log_entry = SalesLog(
        orders_loaded=orders_count,
        note=note,
        errors=error_text
    )
    db.session.add(log_entry)
    db.session.commit()

def get_token():
    """Получаем и кэшируем токен Digiseller"""
    token = cache.get("digiseller_token")
    if token:
        return token

    seller_id = current_app.config['DIGISELLER_SELLER_ID']
    api_key = current_app.config['DIGISELLER_API_KEY']
    if not seller_id or not api_key:
        raise ValueError("DIGISELLER_SELLER_ID или DIGISELLER_API_KEY не настроены в конфиге")
    current_time = int(time.time())
    sign = hashlib.sha256((api_key + str(current_time)).encode()).hexdigest()

    payload = {"seller_id": seller_id, "timestamp": current_time, "sign": sign}
    headers = {"Accept": "application/json"}

    resp = requests.post(f"{DIGISELLER_API_URL}/apilogin", json=payload, headers=headers)
    data = resp.json()

    if data.get("retval") == 0:
        token = data["token"]
        cache.set("digiseller_token", token, timeout=6600)  # 1 час 50 минут
        return token
    else:
        raise Exception(f"Ошибка получения токена: {data}")


def get_last_sale_date():
    """Берём последнюю дату заказа в БД"""
    last_date = db.session.query(func.max(Sale.date_pay)).scalar()
    if not last_date:
        last_date = db.session.query(func.max(Sale.date_put)).scalar()

    if last_date:
        return last_date + timedelta(seconds=1)  # чуть дальше, чтобы не дублировать
    else:
        # если база пустая — старт с 2020 года
        tz_msk = pytz.timezone("Europe/Moscow")
        return datetime(2020, 1, 1, 0, 0, 0, tzinfo=tz_msk)


def get_moscow_time():
    """Текущее время в Москве (UTC+3)"""
    tz_msk = pytz.timezone("Europe/Moscow")
    return datetime.now(tz_msk)


def fetch_sales_v2():
    """Загрузка новых заказов через Digiseller API v2"""
    token = get_token()
    date_start = get_last_sale_date()
    date_finish = get_moscow_time()

    payload = {
        "date_start": date_start.strftime("%Y-%m-%d %H:%M:%S"),
        "date_finish": date_finish.strftime("%Y-%m-%d %H:%M:%S"),
        "returned": 0,
        "page": 1,
        "rows": 500
    }

    url = f"{DIGISELLER_API_URL}/seller-sells/v2?token={token}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    errors = []
    inserted_count = 0

    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            errors.append(f"HTTP {resp.status_code}: {resp.text}")
            logging.error(errors[-1])
            save_sales_log(0, note="Ошибка API", errors=errors)
            return 0

        data = resp.json()
        if "rows" not in data:
            errors.append(f"Пустой ответ: {data}")
            logging.warning(errors[-1])
            save_sales_log(0, note="Пустой ответ API", errors=errors)
            return 0

        for row in data["rows"]:
            # проверяем обязательные поля
            if not row.get("invoice_id") or not row.get("product_id") or not row.get("product_name") or not row.get("product_entry"):
                errors.append(f"Пропущен заказ из-за отсутствия обязательных полей: {row}")
                continue

            sale = Sale(
                invoice_id=row.get("invoice_id"),
                product_id=row.get("product_id"),
                product_name=row.get("product_name"),
                product_entry=row.get("product_entry"),
                date_put=datetime.strptime(row["date_put"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Europe/Moscow")),
                date_pay=datetime.strptime(row["date_pay"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Europe/Moscow")) if row.get("date_pay") else None,
                email=row.get("email") or "",
                amount_in=row.get("amount_in") or 0,
                amount_out=row.get("amount_out") or 0,
                amount_currency=row.get("amount_currency") or "",
                method_pay=row.get("method_pay") or "",
                aggregator_pay=row.get("aggregator") or "",
                ip=row.get("ip") or "",
                partner_id=row.get("partner_id") or 0,
                lang=row.get("lang") or "",
            )
            try:
                db.session.add(sale)
                db.session.commit()
                inserted_count += 1
            except IntegrityError:
                db.session.rollback()
            except Exception as e:
                db.session.rollback()
                errors.append(f"Ошибка вставки {row.get('id_invoice')}: {e}")

    except Exception as e:
        errors.append(f"Общая ошибка: {e}")

    # Сохраняем лог с количеством вставленных и ошибками
    save_sales_log(inserted_count, note="Автозагрузка", errors=errors)
    logging.info(f"Добавлено {inserted_count} новых заказов, ошибок: {len(errors)}")

    return inserted_count



def sales_loader_loop(app, interval=120):
    """Фоновая задача: каждые interval секунд загружает новые заказы"""
    with app.app_context():  # <- создаем контекст приложения
        while True:
            try:
                new_count = fetch_sales_v2()
                if new_count:
                    save_sales_log(new_count, note="Автозагрузка")
                logging.info(f"Загружено {new_count} заказов")
            except Exception as e:
                logging.error(f"Ошибка в загрузчике заказов: {e}")
            time.sleep(interval)


def start_sales_loader(app):
    """Запуск загрузчика заказов в отдельном потоке"""
    t = threading.Thread(target=sales_loader_loop, args=(app, 120), daemon=True)
    t.start()
    logging.info("Фоновый загрузчик заказов запущен")
