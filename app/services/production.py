from datetime import datetime
from app.extensions import db
from app.models import ProductionRun, convert_to_base
from app.services.inventory import deduct_ingredient, check_recipe_stock


def complete_production_run(run_id):
    """Complete a production run: deduct all ingredients from stock.
    Returns True on success, error string on failure."""
    run = db.session.get(ProductionRun, run_id)
    if not run:
        return "Production run not found"
    if run.status == "completed":
        return "Production run already completed"

    recipe = run.recipe
    multiplier = run.quantity_produced / recipe.yield_quantity if recipe.yield_quantity else run.quantity_produced

    # Check stock first
    shortages = check_recipe_stock(recipe, multiplier)
    if shortages:
        msgs = [f"{s['ingredient']}: need {s['needed']:.1f} {s['unit']}, have {s['available']:.1f}" for s in shortages]
        return "Insufficient stock:\n" + "\n".join(msgs)

    # Deduct all ingredients
    for ri in recipe.ingredients:
        result = deduct_ingredient(
            ri.ingredient_id,
            ri.quantity * multiplier,
            ri.unit,
        )
        if result is not True:
            db.session.rollback()
            return result

    # Calculate cost
    cost = 0.0
    for ri in recipe.ingredients:
        base_qty = convert_to_base(ri.quantity * multiplier, ri.unit, ri.ingredient.base_unit)
        cost += base_qty * ri.ingredient.cost_per_base_unit

    run.status = "completed"
    run.cost_total = cost
    run.produced_at = datetime.utcnow()
    db.session.commit()
    return True
