from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ProductionRun, Recipe
from app.services.production import complete_production_run
from app.services.inventory import check_recipe_stock
from app.utils import get_or_404

bp = Blueprint("production", __name__, url_prefix="/production")


@bp.route("/")
@login_required
def index():
    runs = ProductionRun.query.filter_by(shop_id=current_user.shop_id).order_by(ProductionRun.created_at.desc()).all()
    return render_template("production/list.html", runs=runs)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        recipe_id = int(request.form["recipe_id"])
        qty = float(request.form.get("quantity_produced", 1))
        recipe = get_or_404(Recipe, recipe_id)

        multiplier = qty / recipe.yield_quantity if recipe.yield_quantity else qty
        cost = recipe.total_cost * multiplier

        run = ProductionRun(
            shop_id=current_user.shop_id,
            recipe_id=recipe_id,
            quantity_produced=qty,
            notes=request.form.get("notes", ""),
            cost_total=cost,
        )
        db.session.add(run)
        db.session.commit()
        flash(f"Production run #{run.id} created (planned).", "success")
        return redirect(url_for("production.index"))

    recipes = Recipe.query.filter_by(shop_id=current_user.shop_id, is_active=True).order_by(Recipe.name).all()
    return render_template("production/form.html", recipes=recipes)


@bp.route("/<int:id>/complete", methods=["POST"])
@login_required
def complete(id):
    get_or_404(ProductionRun, id)
    result = complete_production_run(id)
    if result is True:
        flash(f"Production run #{id} completed! Stock deducted.", "success")
    else:
        flash(f"Error: {result}", "error")
    return redirect(url_for("production.index"))


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    run = get_or_404(ProductionRun, id)
    if run.status == "completed":
        flash("Cannot delete a completed production run.", "error")
        return redirect(url_for("production.index"))
    db.session.delete(run)
    db.session.commit()
    flash("Production run deleted.", "warning")
    return redirect(url_for("production.index"))


@bp.route("/check_stock/<int:recipe_id>")
@login_required
def check_stock(recipe_id):
    """HTMX endpoint: check stock availability for a recipe."""
    recipe = get_or_404(Recipe, recipe_id)

    qty = float(request.args.get("qty", recipe.yield_quantity or 1))
    multiplier = qty / recipe.yield_quantity if recipe.yield_quantity else qty
    shortages = check_recipe_stock(recipe, multiplier)
    cost = recipe.total_cost * multiplier

    return render_template("production/stock_check.html",
                           recipe=recipe, shortages=shortages,
                           cost=cost, qty=qty)
