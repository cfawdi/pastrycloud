from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Sale, SaleItem, Product
from app.utils import get_or_404

bp = Blueprint("sales", __name__, url_prefix="/sales")


@bp.route("/")
@login_required
def index():
    sale_date = request.args.get("date", "").strip()
    query = Sale.query.filter_by(shop_id=current_user.shop_id)
    if sale_date:
        query = query.filter(Sale.sale_date == date.fromisoformat(sale_date))
    sales = query.order_by(Sale.created_at.desc()).all()

    today = date.today()
    today_sales = Sale.query.filter_by(shop_id=current_user.shop_id, sale_date=today).all()
    daily_total = sum(s.total_amount for s in today_sales)
    daily_vat = sum(s.vat_amount for s in today_sales)
    daily_count = len(today_sales)

    return render_template("sales/list.html", sales=sales,
                           daily_total=daily_total, daily_vat=daily_vat,
                           daily_count=daily_count, today=today,
                           filter_date=sale_date)


@bp.route("/quick", methods=["GET"])
@login_required
def quick_sale():
    """Quick sale page with Alpine.js cart."""
    products = Product.query.filter_by(shop_id=current_user.shop_id, is_active=True).order_by(Product.name).all()
    return render_template("sales/quick_sale.html", products=products)


@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """Process sale from quick sale form (JSON)."""
    data = request.get_json()
    if not data or not data.get("items"):
        return jsonify({"error": "No items in cart"}), 400

    sale = Sale(
        shop_id=current_user.shop_id,
        sale_date=date.today(),
        payment_method=data.get("payment_method", "cash"),
        customer_name=data.get("customer_name", ""),
        notes=data.get("notes", ""),
    )

    subtotal = 0
    vat_total = 0

    for item_data in data["items"]:
        product = db.session.get(Product, item_data["product_id"])
        if not product or product.shop_id != current_user.shop_id:
            continue

        qty = float(item_data.get("quantity", 1))
        unit_price = product.selling_price
        vat_rate = product.vat_rate
        line_subtotal = unit_price * qty
        line_vat = line_subtotal * (vat_rate / 100)
        line_total = line_subtotal + line_vat

        sale_item = SaleItem(
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            vat_rate=vat_rate,
            line_total=line_total,
        )
        sale.items.append(sale_item)
        subtotal += line_subtotal
        vat_total += line_vat

    sale.total_amount = subtotal + vat_total
    sale.vat_amount = vat_total

    db.session.add(sale)
    db.session.commit()

    return jsonify({
        "success": True,
        "sale_id": sale.id,
        "total": sale.total_amount,
        "vat": sale.vat_amount,
    })


@bp.route("/<int:id>")
@login_required
def detail(id):
    sale = get_or_404(Sale, id)
    return render_template("sales/detail.html", sale=sale)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    sale = get_or_404(Sale, id)
    db.session.delete(sale)
    db.session.commit()
    flash("Sale deleted.", "warning")
    return redirect(url_for("sales.index"))
