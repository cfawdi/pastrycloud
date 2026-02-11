from app.extensions import db
from app.models import Ingredient, convert_to_base


def deduct_ingredient(ingredient_id, quantity, unit):
    """Deduct quantity from ingredient stock. Returns True on success, error string on failure."""
    ingredient = db.session.get(Ingredient, ingredient_id)
    if not ingredient:
        return f"Ingredient #{ingredient_id} not found"

    base_qty = convert_to_base(quantity, unit, ingredient.base_unit)
    if ingredient.quantity_on_hand < base_qty:
        return (
            f"Insufficient stock for {ingredient.name}: "
            f"need {base_qty} {ingredient.base_unit}, "
            f"have {ingredient.quantity_on_hand} {ingredient.base_unit}"
        )

    ingredient.quantity_on_hand -= base_qty
    return True


def check_recipe_stock(recipe, multiplier=1.0):
    """Check if all ingredients are available for a recipe * multiplier.
    Returns list of shortage dicts or empty list if OK."""
    shortages = []
    for ri in recipe.ingredients:
        needed = convert_to_base(ri.quantity * multiplier, ri.unit, ri.ingredient.base_unit)
        available = ri.ingredient.quantity_on_hand
        if available < needed:
            shortages.append({
                "ingredient": ri.ingredient.name,
                "needed": needed,
                "available": available,
                "unit": ri.ingredient.base_unit,
                "deficit": needed - available,
            })
    return shortages


def get_low_stock_ingredients(shop_id):
    """Return ingredients that are at or below minimum stock level."""
    return Ingredient.query.filter(
        Ingredient.shop_id == shop_id,
        Ingredient.quantity_on_hand <= Ingredient.min_stock_level,
    ).order_by(Ingredient.quantity_on_hand.asc()).all()
