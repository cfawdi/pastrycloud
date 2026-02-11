from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Ingredient, Product, Sale, SaleItem, ProductionRun, WasteLog
from app.services.inventory import get_low_stock_ingredients

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.landing"))

    today = date.today()
    sid = current_user.shop_id

    # Stock value
    stock_value = db.session.query(
        func.sum(Ingredient.quantity_on_hand * Ingredient.cost_per_base_unit)
    ).filter(Ingredient.shop_id == sid).scalar() or 0

    # Low stock count
    low_stock = get_low_stock_ingredients(sid)

    # Today's sales
    today_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == sid, Sale.sale_date == today
    ).scalar() or 0

    today_sales_count = Sale.query.filter_by(shop_id=sid, sale_date=today).count()

    # Today's production
    today_production = ProductionRun.query.filter(
        ProductionRun.shop_id == sid,
        func.date(ProductionRun.created_at) == today,
    ).count()

    # Recent sales (last 5)
    recent_sales = Sale.query.filter_by(shop_id=sid).order_by(Sale.created_at.desc()).limit(5).all()

    # Recent production (last 5)
    recent_production = ProductionRun.query.filter_by(shop_id=sid).order_by(
        ProductionRun.created_at.desc()
    ).limit(5).all()

    # Sales data for chart (last 7 days)
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime("%b %d"))
        day_total = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.shop_id == sid, Sale.sale_date == d
        ).scalar() or 0
        chart_data.append(round(day_total, 2))

    # Top products (by quantity sold, last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    top_products_q = (
        db.session.query(
            Product.name,
            func.sum(SaleItem.quantity).label("total_qty"),
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.shop_id == sid, Sale.sale_date >= thirty_days_ago)
        .group_by(Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_product_labels = [r[0] for r in top_products_q]
    top_product_data = [float(r[1]) for r in top_products_q]

    # Total waste cost (this month)
    first_of_month = today.replace(day=1)
    waste_cost = db.session.query(func.sum(WasteLog.cost_estimate)).filter(
        WasteLog.shop_id == sid,
        WasteLog.logged_at >= datetime.combine(first_of_month, datetime.min.time()),
    ).scalar() or 0

    return render_template(
        "dashboard.html",
        stock_value=stock_value,
        low_stock=low_stock,
        today_sales=today_sales,
        today_sales_count=today_sales_count,
        today_production=today_production,
        recent_sales=recent_sales,
        recent_production=recent_production,
        chart_labels=chart_labels,
        chart_data=chart_data,
        top_product_labels=top_product_labels,
        top_product_data=top_product_data,
        waste_cost=waste_cost,
    )
