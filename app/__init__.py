import os
from datetime import datetime
from flask import Flask
from flask_login import current_user
from .extensions import db, login_manager
from .models import User, Ingredient
from .routes import ALL_BLUEPRINTS


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Ensure instance folder exists (for SQLite local dev)
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        if current_user.is_authenticated:
            shop = current_user.shop
            low_stock = Ingredient.query.filter(
                Ingredient.shop_id == current_user.shop_id,
                Ingredient.quantity_on_hand <= Ingredient.min_stock_level,
                Ingredient.quantity_on_hand > 0,
            ).count()
            return {
                "shop_name": shop.name,
                "currency": shop.currency,
                "default_vat_rate": shop.default_vat_rate,
                "low_stock_count": low_stock,
                "now": datetime.utcnow,
                "current_user": current_user,
            }
        return {
            "shop_name": "PastryCloud",
            "currency": "DH",
            "default_vat_rate": 20.0,
            "low_stock_count": 0,
            "now": datetime.utcnow,
        }

    with app.app_context():
        db.create_all()

    return app
