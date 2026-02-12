from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Product, ProductRecipe, Recipe
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
        product = Product(
            shop_id=current_user.shop_id,
            name=request.form["name"].strip(),
            category=request.form.get("category", ""),
            selling_price=float(request.form.get("selling_price", 0)),
            vat_rate=float(request.form.get("vat_rate", 20)),
        )
        db.session.add(product)
        db.session.flush()

        recipe_ids = request.form.getlist("recipe_ids")
        recipe_qtys = request.form.getlist("recipe_qtys")
        for i, rid in enumerate(recipe_ids):
            if rid:
                qty = float(recipe_qtys[i]) if i < len(recipe_qtys) and recipe_qtys[i] else 1.0
                db.session.add(ProductRecipe(
                    product_id=product.id,
                    recipe_id=int(rid),
                    quantity_needed=qty,
                ))

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
        product.name = request.form["name"].strip()
        product.category = request.form.get("category", "")
        product.selling_price = float(request.form.get("selling_price", 0))
        product.vat_rate = float(request.form.get("vat_rate", 20))

        # Replace all linked recipes
        ProductRecipe.query.filter_by(product_id=product.id).delete()
        recipe_ids = request.form.getlist("recipe_ids")
        recipe_qtys = request.form.getlist("recipe_qtys")
        for i, rid in enumerate(recipe_ids):
            if rid:
                qty = float(recipe_qtys[i]) if i < len(recipe_qtys) and recipe_qtys[i] else 1.0
                db.session.add(ProductRecipe(
                    product_id=product.id,
                    recipe_id=int(rid),
                    quantity_needed=qty,
                ))

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
