from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Ingredient, CONVERSION_TO_BASE
from app.utils import get_or_404

bp = Blueprint("ingredients", __name__, url_prefix="/ingredients")

CATEGORIES = ["Flour & Grains", "Dairy", "Sweeteners", "Nuts & Dried Fruits",
              "Fats & Oils", "Eggs", "Flavorings", "Chocolate", "Fruits", "Other"]


@bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()

    query = Ingredient.query.filter_by(shop_id=current_user.shop_id)

    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Ingredient.category == category)
    if status == "low":
        query = query.filter(
            Ingredient.quantity_on_hand <= Ingredient.min_stock_level,
            Ingredient.quantity_on_hand > 0,
        )
    elif status == "out":
        query = query.filter(Ingredient.quantity_on_hand <= 0)
    elif status == "ok":
        query = query.filter(Ingredient.quantity_on_hand > Ingredient.min_stock_level)

    ingredients = query.order_by(Ingredient.name).all()

    if request.headers.get("HX-Request"):
        return render_template("ingredients/table_body.html",
                               ingredients=ingredients, today=date.today())

    return render_template("ingredients/list.html",
                           ingredients=ingredients, categories=CATEGORIES,
                           search=search, sel_category=category,
                           sel_status=status, today=date.today())


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        display_unit = request.form.get("display_unit", "g")
        qty = float(request.form.get("quantity_on_hand", 0))
        min_stock = float(request.form.get("min_stock_level", 0))
        cost_input = float(request.form.get("cost_per_unit", 0))

        base_unit_map = {"g": "g", "kg": "g", "mL": "mL", "ml": "mL",
                         "L": "mL", "l": "mL", "pcs": "pcs", "dozen": "pcs"}
        base_unit = base_unit_map.get(display_unit, display_unit)
        factor = CONVERSION_TO_BASE.get(display_unit, 1.0)

        qty_base = qty * factor
        min_stock_base = min_stock * factor
        cost_per_base = cost_input / factor if factor else cost_input

        expiry = request.form.get("expiry_date", "").strip()

        ingredient = Ingredient(
            shop_id=current_user.shop_id,
            name=request.form["name"].strip(),
            category=request.form.get("category", ""),
            base_unit=base_unit,
            quantity_on_hand=qty_base,
            cost_per_base_unit=cost_per_base,
            min_stock_level=min_stock_base,
            expiry_date=date.fromisoformat(expiry) if expiry else None,
            notes=request.form.get("notes", ""),
        )
        db.session.add(ingredient)
        db.session.commit()
        flash(f"Ingredient '{ingredient.name}' added successfully!", "success")
        return redirect(url_for("ingredients.index"))

    return render_template("ingredients/form.html",
                           ingredient=None, categories=CATEGORIES)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    ingredient = get_or_404(Ingredient, id)

    if request.method == "POST":
        display_unit = request.form.get("display_unit", ingredient.base_unit)
        qty = float(request.form.get("quantity_on_hand", 0))
        min_stock = float(request.form.get("min_stock_level", 0))
        cost_input = float(request.form.get("cost_per_unit", 0))

        base_unit_map = {"g": "g", "kg": "g", "mL": "mL", "ml": "mL",
                         "L": "mL", "l": "mL", "pcs": "pcs", "dozen": "pcs"}
        base_unit = base_unit_map.get(display_unit, display_unit)
        factor = CONVERSION_TO_BASE.get(display_unit, 1.0)

        ingredient.name = request.form["name"].strip()
        ingredient.category = request.form.get("category", "")
        ingredient.base_unit = base_unit
        ingredient.quantity_on_hand = qty * factor
        ingredient.cost_per_base_unit = cost_input / factor if factor else cost_input
        ingredient.min_stock_level = min_stock * factor
        expiry = request.form.get("expiry_date", "").strip()
        ingredient.expiry_date = date.fromisoformat(expiry) if expiry else None
        ingredient.notes = request.form.get("notes", "")

        db.session.commit()
        flash(f"Ingredient '{ingredient.name}' updated!", "success")
        return redirect(url_for("ingredients.index"))

    return render_template("ingredients/form.html",
                           ingredient=ingredient, categories=CATEGORIES)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    ingredient = get_or_404(Ingredient, id)
    name = ingredient.name
    db.session.delete(ingredient)
    db.session.commit()
    flash(f"Ingredient '{name}' deleted.", "warning")
    return redirect(url_for("ingredients.index"))
