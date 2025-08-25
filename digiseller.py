import time
import hashlib
import logging
import requests
import pytz
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from extensions import db
from models.sales import Sale, SalesLog

DIGISELLER_API_URL = "https://api.digiseller.com/api"

# Глобальные переменные для конфигурации (будут установлены извне)
DIGISELLER_SELLER_ID = None
DIGISELLER_API_KEY = None
CACHE = {}  # Простой кэш вместо flask-cache

def configure_digiseller(seller_id, api_key):
    """Установка конфигурации извне"""
    global DIGISELLER_SELLER_ID, DIGISELLER_API_KEY
    DIGISELLER_SELLER_ID = seller_id
    DIGISELLER_API_KEY = api_key

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
    # Проверяем кэш
    if "digiseller_token" in CACHE:
        token, expiry = CACHE["digiseller_token"]
        if time.time() < expiry:
            return token
    
    if not DIGISELLER_SELLER_ID or not DIGISELLER_API_KEY:
        raise ValueError("DIGISELLER_SELLER_ID или DIGISELLER_API_KEY не настроены")
    
    current_time = int(time.time())
    sign = hashlib.sha256((DIGISELLER_API_KEY + str(current_time)).encode()).hexdigest()

    payload = {"seller_id": DIGISELLER_SELLER_ID, "timestamp": current_time, "sign": sign}
    headers = {"Accept": "application/json"}

    resp = requests.post(f"{DIGISELLER_API_URL}/apilogin", json=payload, headers=headers, timeout=30)
    data = resp.json()

    if data.get("retval") == 0:
        token = data["token"]
        # Кэшируем на 1 час 50 минут
        CACHE["digiseller_token"] = (token, time.time() + 6600)
        return token
    else:
        raise Exception(f"Ошибка получения токена: {data}")

def get_last_sale_date():
    """Берём последнюю дату заказа в БД"""
    last_date = db.session.query(func.max(Sale.date_pay)).scalar()
    if not last_date:
        last_date = db.session.query(func.max(Sale.date_put)).scalar()

    if last_date:
        return last_date + timedelta(seconds=1)
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
    if not DIGISELLER_SELLER_ID or not DIGISELLER_API_KEY:
        logging.error("Digiseller не настроен. Вызовите configure_digiseller() first.")
        return 0

    try:
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

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            error_msg = f"HTTP {resp.status_code}: {resp.text}"
            logging.error(error_msg)
            save_sales_log(0, note="Ошибка API", errors=[error_msg])
            return 0

        data = resp.json()
        if "rows" not in data or not data["rows"]:
            logging.info("Новых заказов нет")
            return 0

        for row in data["rows"]:
            if not all([row.get("invoice_id"), row.get("product_id"), row.get("product_name"), row.get("product_entry")]):
                errors.append(f"Пропущен заказ из-за отсутствия обязательных полей: {row.get('invoice_id')}")
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
                errors.append(f"Ошибка вставки {row.get('invoice_id')}: {e}")

        # Сохраняем лог
        save_sales_log(inserted_count, note="Автозагрузка", errors=errors)
        logging.info(f"Добавлено {inserted_count} новых заказов, ошибок: {len(errors)}")
        
        return inserted_count

    except Exception as e:
        logging.error(f"Общая ошибка в fetch_sales_v2: {e}")
        save_sales_log(0, note="Общая ошибка", errors=[str(e)])
        return 0