from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import WasteLog, Ingredient, Product, convert_to_base
from app.utils import get_or_404

bp = Blueprint("waste", __name__, url_prefix="/waste")

WASTE_CATEGORIES = ["expired", "spoiled", "failed_batch", "unsold", "other"]


@bp.route("/")
@login_required
def index():
    category = request.args.get("category", "").strip()
    query = WasteLog.query.filter_by(shop_id=current_user.shop_id)
    if category:
        query = query.filter(WasteLog.category == category)
    logs = query.order_by(WasteLog.logged_at.desc()).all()
    return render_template("waste/list.html", logs=logs,
                           categories=WASTE_CATEGORIES, sel_category=category)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        waste_type = request.form.get("waste_type", "ingredient")
        ingredient_id = None
        product_id = None
        cost = float(request.form.get("cost_estimate", 0))

        if waste_type == "ingredient":
            ingredient_id = int(request.form["ingredient_id"]) if request.form.get("ingredient_id") else None
            if ingredient_id and cost == 0:
                ing = get_or_404(Ingredient, ingredient_id)
                unit = request.form.get("unit", ing.base_unit)
                qty = float(request.form.get("quantity", 0))
                base_qty = convert_to_base(qty, unit, ing.base_unit)
                cost = base_qty * ing.cost_per_base_unit
        else:
            product_id = int(request.form["product_id"]) if request.form.get("product_id") else None

        log = WasteLog(
            shop_id=current_user.shop_id,
            ingredient_id=ingredient_id,
            product_id=product_id,
            quantity=float(request.form.get("quantity", 0)),
            unit=request.form.get("unit", ""),
            cost_estimate=cost,
            category=request.form.get("category", "other"),
            notes=request.form.get("notes", ""),
        )
        db.session.add(log)
        db.session.commit()
        flash("Waste entry logged.", "success")
        return redirect(url_for("waste.index"))

    ingredients = Ingredient.query.filter_by(shop_id=current_user.shop_id).order_by(Ingredient.name).all()
    products = Product.query.filter_by(shop_id=current_user.shop_id).order_by(Product.name).all()
    return render_template("waste/form.html", waste=None,
                           ingredients=ingredients, products=products,
                           categories=WASTE_CATEGORIES)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    log = get_or_404(WasteLog, id)
    db.session.delete(log)
    db.session.commit()
    flash("Waste entry deleted.", "warning")
    return redirect(url_for("waste.index"))
