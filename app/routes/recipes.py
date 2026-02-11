from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Recipe, RecipeIngredient, Ingredient, get_compatible_units
from app.utils import get_or_404

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


@bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()
    query = Recipe.query.filter_by(shop_id=current_user.shop_id)
    if search:
        query = query.filter(Recipe.name.ilike(f"%{search}%"))
    recipes = query.order_by(Recipe.name).all()

    if request.headers.get("HX-Request") and request.args.get("partial"):
        return render_template("recipes/table_body.html", recipes=recipes)

    return render_template("recipes/list.html", recipes=recipes, search=search)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        recipe = Recipe(
            shop_id=current_user.shop_id,
            name=request.form["name"].strip(),
            description=request.form.get("description", ""),
            yield_quantity=float(request.form.get("yield_quantity", 1)),
            yield_unit=request.form.get("yield_unit", "pcs"),
            estimated_time_minutes=int(request.form.get("estimated_time_minutes", 0)),
        )
        db.session.add(recipe)
        db.session.flush()

        idx = 0
        while f"ingredient_id_{idx}" in request.form:
            ing_id = request.form.get(f"ingredient_id_{idx}")
            qty = request.form.get(f"ingredient_qty_{idx}")
            unit = request.form.get(f"ingredient_unit_{idx}")
            if ing_id and qty:
                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=int(ing_id),
                    quantity=float(qty),
                    unit=unit or "g",
                )
                db.session.add(ri)
            idx += 1

        db.session.commit()
        flash(f"Recipe '{recipe.name}' created!", "success")
        return redirect(url_for("recipes.detail", id=recipe.id))

    ingredients = Ingredient.query.filter_by(shop_id=current_user.shop_id).order_by(Ingredient.name).all()
    return render_template("recipes/form.html", recipe=None, ingredients=ingredients)


@bp.route("/<int:id>")
@login_required
def detail(id):
    recipe = get_or_404(Recipe, id)
    scale = float(request.args.get("scale", 1.0))
    return render_template("recipes/detail.html", recipe=recipe, scale=scale)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    recipe = get_or_404(Recipe, id)

    if request.method == "POST":
        recipe.name = request.form["name"].strip()
        recipe.description = request.form.get("description", "")
        recipe.yield_quantity = float(request.form.get("yield_quantity", 1))
        recipe.yield_unit = request.form.get("yield_unit", "pcs")
        recipe.estimated_time_minutes = int(request.form.get("estimated_time_minutes", 0))

        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

        idx = 0
        while f"ingredient_id_{idx}" in request.form:
            ing_id = request.form.get(f"ingredient_id_{idx}")
            qty = request.form.get(f"ingredient_qty_{idx}")
            unit = request.form.get(f"ingredient_unit_{idx}")
            if ing_id and qty:
                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=int(ing_id),
                    quantity=float(qty),
                    unit=unit or "g",
                )
                db.session.add(ri)
            idx += 1

        db.session.commit()
        flash(f"Recipe '{recipe.name}' updated!", "success")
        return redirect(url_for("recipes.detail", id=recipe.id))

    ingredients = Ingredient.query.filter_by(shop_id=current_user.shop_id).order_by(Ingredient.name).all()
    return render_template("recipes/form.html", recipe=recipe, ingredients=ingredients)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    recipe = get_or_404(Recipe, id)
    name = recipe.name
    db.session.delete(recipe)
    db.session.commit()
    flash(f"Recipe '{name}' deleted.", "warning")
    return redirect(url_for("recipes.index"))


@bp.route("/search_ingredients")
@login_required
def search_ingredients():
    """HTMX endpoint for ingredient search in recipe form."""
    q = request.args.get("q", "").strip()
    ingredients = Ingredient.query.filter(
        Ingredient.shop_id == current_user.shop_id,
        Ingredient.name.ilike(f"%{q}%"),
    ).order_by(Ingredient.name).limit(10).all()
    return render_template("recipes/ingredient_search_results.html",
                           ingredients=ingredients)


@bp.route("/ingredient_units/<int:ingredient_id>")
@login_required
def ingredient_units(ingredient_id):
    """Return compatible units for an ingredient."""
    ingredient = get_or_404(Ingredient, ingredient_id)
    units = get_compatible_units(ingredient.base_unit)
    return jsonify(units)
