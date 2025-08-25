from flask import Blueprint, render_template, request
from sqlalchemy import or_
from extensions import db
from models.sales import Sale, SalesLog   # ваша модель платежей
from forms.sales_forms import SalesSearchForm  # создадим форму поиска

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales/search', methods=['GET', 'POST'])
def search_sales():
    form = SalesSearchForm()
    results = []

    if form.validate_on_submit():
        search_term = form.query.data.strip()

        results = db.session.query(Sale).filter(
            or_(
                Sale.invoice_id.ilike(f"%{search_term}%"),
                Sale.product_name.ilike(f"%{search_term}%"),
                Sale.product_entry.ilike(f"%{search_term}%"),
                Sale.email.ilike(f"%{search_term}%"),
                Sale.ip.ilike(f"%{search_term}%")
            )
        ).order_by(Sale.date_pay.desc()).all()

    return render_template('search_sales_result.html', form=form, results=results)


@sales_bp.route("/sales-log")
def sales_log():
    logs = SalesLog.query.order_by(SalesLog.timestamp.desc()).all()
    return render_template("sales_log.html", logs=logs)