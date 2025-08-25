from app import create_app
from digiseller import configure_digiseller, fetch_sales_v2

app = create_app()
with app.app_context():
    configure_digiseller(
        app.config['DIGISELLER_SELLER_ID'],
        app.config['DIGISELLER_API_KEY']
    )
    count = fetch_sales_v2()