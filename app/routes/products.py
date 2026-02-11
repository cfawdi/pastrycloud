from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Product, Recipe
from app.utils import get_or_404

bp = Blueprint("products", __name__, url_prefix="/products")

PRODUCT_CATEGORIES = ["Pastries", "Cakes", "Cookies", "Bread", "Viennoiserie",
                      "Drinks", "Other"]


@bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()
    query = Product.query.filter_by(shop_id=current_user.shop_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    products = query.order_by(Product.name).all()

    if request.headers.get("HX-Request") and request.args.get("partial"):
        return render_template("products/table_body.html", products=products)

    return render_template("products/list.html", products=products,
                           categories=PRODUCT_CATEGORIES, search=search)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        recipe_id = request.form.get("recipe_id", "").strip()
        product = Product(
            shop_id=current_user.shop_id,
            name=request.form["name"].strip(),
            category=request.form.get("category", ""),
            recipe_id=int(recipe_id) if recipe_id else None,
            selling_price=float(request.form.get("selling_price", 0)),
            vat_rate=float(request.form.get("vat_rate", 20)),
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Product '{product.name}' created!", "success")
        return redirect(url_for("products.index"))

    recipes = Recipe.query.filter_by(shop_id=current_user.shop_id, is_active=True).order_by(Recipe.name).all()
    return render_template("products/form.html", product=None,
                           categories=PRODUCT_CATEGORIES, recipes=recipes)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    product = get_or_404(Product, id)

    if request.method == "POST":
        recipe_id = request.form.get("recipe_id", "").strip()
        product.name = request.form["name"].strip()
        product.category = request.form.get("category", "")
        product.recipe_id = int(recipe_id) if recipe_id else None
        product.selling_price = float(request.form.get("selling_price", 0))
        product.vat_rate = float(request.form.get("vat_rate", 20))

        db.session.commit()
        flash(f"Product '{product.name}' updated!", "success")
        return redirect(url_for("products.index"))

    recipes = Recipe.query.filter_by(shop_id=current_user.shop_id, is_active=True).order_by(Recipe.name).all()
    return render_template("products/form.html", product=product,
                           categories=PRODUCT_CATEGORIES, recipes=recipes)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    product = get_or_404(Product, id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{name}' deleted.", "warning")
    return redirect(url_for("products.index"))


@bp.route("/search")
@login_required
def search():
    """HTMX/JSON endpoint for product search (used in quick sale)."""
    q = request.args.get("q", "").strip()
    products = Product.query.filter(
        Product.shop_id == current_user.shop_id,
        Product.is_active == True,
        Product.name.ilike(f"%{q}%"),
    ).order_by(Product.name).limit(10).all()

    if request.headers.get("HX-Request"):
        return render_template("products/search_results.html", products=products)

    return jsonify([{
        "id": p.id, "name": p.name, "selling_price": p.selling_price,
        "vat_rate": p.vat_rate, "category": p.category,
    } for p in products])
