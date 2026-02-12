#!/usr/bin/env python3
"""Import choux pastry recipes into the database.

Usage:
    python seed_choux_data.py              # Run import
    python seed_choux_data.py --dry-run    # Preview without writing
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    Ingredient, Product, ProductRecipe, Recipe, RecipeIngredient, User,
)

USER_EMAIL = "yasminealami98@gmail.com"
SELLING_PRICE = 31.67
VAT_RATE = 20.0

# ── 43 Standard Ingredients (name, base_unit, cost_per_base_unit, category) ──
INGREDIENTS_DATA = [
    ("Eau", "mL", 0.00002, "Basics"),
    ("Lait", "mL", 0.00933, "Dairy"),
    ("Sel", "g", 0.0046, "Basics"),
    ("Sucre", "g", 0.00715, "Sweeteners"),
    ("Beurre", "g", 0.13, "Dairy"),
    ("Farine", "g", 0.00556, "Flour & Grains"),
    ("Oeufs", "pcs", 1.38, "Eggs"),
    ("Cassonade", "g", 0.04899, "Sweeteners"),
    ("Creme", "mL", 0.055, "Dairy"),
    ("Chocolat noir Valrhona", "g", 0.154, "Chocolate"),
    ("Chocolat blanc Callebaut", "g", 0.1688, "Chocolate"),
    ("Chocolat au lait", "g", 0.1632, "Chocolate"),
    ("Fecule", "g", 0.0104, "Flour & Grains"),
    ("Gelatine poudre", "g", 0.785, "Gelling Agents"),
    ("Gelatine feuille", "pcs", 1.644, "Gelling Agents"),
    ("Trimoline", "g", 0.03543, "Sweeteners"),
    ("Glucose", "g", 0.012, "Sweeteners"),
    ("Pectine NH", "g", 0.677, "Gelling Agents"),
    ("Sesame", "g", 0.084, "Nuts & Seeds"),
    ("Pate miso", "g", 0.1375, "Flavorings"),
    ("Pistache", "g", 0.28588, "Nuts & Seeds"),
    ("Amande", "g", 0.1, "Nuts & Seeds"),
    ("Noisette", "g", 0.235, "Nuts & Seeds"),
    ("Feuilletine", "g", 0.1316, "Flour & Grains"),
    ("Vanille gousses", "pcs", 7.57895, "Flavorings"),
    ("Cafe java timor", "g", 0.25, "Flavorings"),
    ("Earl grey sachets", "pcs", 2.08, "Flavorings"),
    ("Fleur de sel", "g", 0.2345, "Flavorings"),
    ("Eau de rose", "mL", 0.1968, "Flavorings"),
    ("Eau de fleur d'oranger", "mL", 0.1, "Flavorings"),
    ("Puree framboises", "g", 0.16632, "Fruits"),
    ("Framboises", "g", 0.25028, "Fruits"),
    ("Puree de mangue", "g", 0.138, "Fruits"),
    ("Puree passion", "g", 0.138, "Fruits"),
    ("Puree de citron vert", "g", 0.171, "Fruits"),
    ("Jus de citron", "mL", 0.048, "Fruits"),
    ("Puree coco", "g", 0.2, "Fruits"),
    ("Matcha", "g", 0.8, "Flavorings"),
    ("Pate vanille", "g", 0.36, "Flavorings"),
    ("Huile", "mL", 0.019, "Basics"),
    ("Litchi", "g", 0.128, "Fruits"),
    ("Mangue fraiche", "g", 0.045, "Fruits"),
    ("Chocolat framboise", "g", 0.556, "Chocolate"),
]

# ── Base Recipes (ingredient_name, qty, unit) ───────────────────────
PATE_A_CHOUX = {
    "name": "Pate a choux",
    "yield": 48, "yield_unit": "pcs",
    "ingredients": [
        ("Eau", 125, "mL"), ("Lait", 125, "mL"), ("Sel", 5, "g"),
        ("Sucre", 5, "g"), ("Beurre", 100, "g"), ("Farine", 150, "g"),
        ("Oeufs", 5, "pcs"),
    ],
}

CRAQUELIN = {
    "name": "Craquelin",
    "yield": 75, "yield_unit": "pcs",
    "ingredients": [
        ("Beurre", 100, "g"), ("Cassonade", 100, "g"), ("Farine", 100, "g"),
    ],
}

# ── 14 Flavor Recipes ───────────────────────────────────────────────
# Each: (ingredient_name, qty_per_chou, unit)
# Quantities are PER SINGLE CHOU, will be scaled to yield in code.
# Computed from Excel sub-recipes: qty / (final_mass / portion_g)
# Cross-refs resolved to raw ingredients proportionally.

FLAVOR_RECIPES = {
    "Chocolat Noir Sesame Miso": {
        "yield": 53,
        "ingredients": [
            # Creme pat choc noir (53.57 portions)
            ("Lait", 9.33, "mL"), ("Sucre", 1.87, "g"), ("Oeufs", 0.075, "pcs"),
            ("Fecule", 0.75, "g"), ("Chocolat noir Valrhona", 1.68, "g"),
            # Pate sesame (261.5 portions)
            ("Sesame", 1.91, "g"), ("Huile", 0.19, "mL"),
            # Miso caramel (416 portions)
            ("Creme", 0.96, "mL"), ("Sucre", 0.96, "g"), ("Pate miso", 0.18, "g"),
            # Ganache sesame (220.4 portions) - raw ingredients only
            ("Creme", 3.95, "mL"), ("Gelatine poudre", 0.023, "g"),
            ("Trimoline", 0.159, "g"), ("Chocolat blanc Callebaut", 0.726, "g"),
            ("Glucose", 0.159, "g"),
            # Cross-ref: Pate sesame 56g in ganache → 56/550 of pate batch, /220.4 portions
            ("Sesame", 0.231, "g"), ("Huile", 0.023, "mL"),
        ],
    },
    "Caramel": {
        "yield": 49,
        "ingredients": [
            # Cremeux caramel (49.68 portions)
            ("Sucre", 2.62, "g"), ("Creme", 7.25, "mL"), ("Oeufs", 0.060, "pcs"),
            ("Fecule", 0.262, "g"), ("Beurre", 3.32, "g"),
            ("Fleur de sel", 0.050, "g"), ("Gelatine poudre", 0.040, "g"),
            ("Eau", 0.242, "mL"),
            # Caramel tendre (86.15 portions)
            ("Beurre", 0.929, "g"), ("Creme", 1.567, "mL"), ("Sucre", 1.625, "g"),
            ("Sel", 0.023, "g"), ("Gelatine poudre", 0.009, "g"), ("Eau", 0.056, "mL"),
            # Caramel decor (34 portions)
            ("Sucre", 2.941, "g"), ("Eau", 0.971, "mL"), ("Glucose", 0.294, "g"),
        ],
    },
    "Vanille": {
        "yield": 36,
        "ingredients": [
            # Creme pat vanille (36.94 portions)
            ("Lait", 13.53, "mL"), ("Sucre", 2.71, "g"), ("Oeufs", 0.108, "pcs"),
            ("Fecule", 1.08, "g"), ("Vanille gousses", 0.0135, "pcs"),
            # Ganache pate vanille (269 portions)
            ("Creme", 3.23, "mL"), ("Gelatine poudre", 0.0186, "g"),
            ("Trimoline", 0.130, "g"), ("Chocolat blanc Callebaut", 0.595, "g"),
            ("Glucose", 0.130, "g"), ("Pate vanille", 0.104, "g"),
            # Decor: chocolat blanc 2g/chou
            ("Chocolat blanc Callebaut", 2.0, "g"),
        ],
    },
    "Framboise": {
        "yield": 50,
        "ingredients": [
            # Creme pat framboise (50.79 portions)
            ("Lait", 9.84, "mL"), ("Sucre", 1.97, "g"), ("Oeufs", 0.079, "pcs"),
            ("Puree framboises", 0.965, "g"), ("Fecule", 0.787, "g"),
            # Framboise pepin sub (43 portions)
            ("Puree framboises", 2.791, "g"), ("Framboises", 0.698, "g"),
            ("Pectine NH", 0.035, "g"), ("Sucre", 0.698, "g"),
            # Ganache framboise (275.5 portions) - raw only
            ("Creme", 3.157, "mL"), ("Gelatine poudre", 0.018, "g"),
            ("Trimoline", 0.127, "g"), ("Chocolat blanc Callebaut", 0.581, "g"),
            ("Glucose", 0.127, "g"),
            # Cross-ref: Framboise pepin 56g in ganache → 56/181.5 of batch, /275.5
            ("Puree framboises", 0.134, "g"), ("Framboises", 0.034, "g"),
            ("Pectine NH", 0.002, "g"), ("Sucre", 0.034, "g"),
            # Decor: chocolat framboise 2g/chou
            ("Chocolat framboise", 2.0, "g"),
        ],
    },
    "Pistache": {
        "yield": 51,
        "ingredients": [
            # Creme pat + praline pistache (51.71 portions)
            ("Lait", 9.67, "mL"), ("Sucre", 1.93, "g"), ("Oeufs", 0.077, "pcs"),
            ("Fecule", 0.774, "g"),
            # Cross-ref: Praline pistache 70g in creme → 70/930 of batch, /51.71
            ("Pistache", 0.702, "g"), ("Sucre", 0.468, "g"),
            ("Eau", 0.117, "mL"), ("Huile", 0.073, "mL"),
            # Praline pistache sub (216.25 portions)
            ("Pistache", 2.22, "g"), ("Sucre", 1.48, "g"),
            ("Eau", 0.370, "mL"), ("Huile", 0.231, "mL"),
            # Ganache praline pistache (220.4 portions) - raw only
            ("Creme", 3.95, "mL"), ("Gelatine poudre", 0.023, "g"),
            ("Trimoline", 0.159, "g"), ("Chocolat blanc Callebaut", 0.726, "g"),
            ("Glucose", 0.159, "g"),
            # Cross-ref: Praline pistache 56g in ganache → 56/930, /220.4
            ("Pistache", 0.131, "g"), ("Sucre", 0.087, "g"),
            ("Eau", 0.022, "mL"), ("Huile", 0.014, "mL"),
            # Decor: ~1.6g pistache/chou
            ("Pistache", 1.6, "g"),
        ],
    },
    "Cafe": {
        "yield": 36,
        "ingredients": [
            # Creme pat cafe (36.94 portions)
            ("Lait", 13.53, "mL"), ("Sucre", 2.71, "g"), ("Oeufs", 0.108, "pcs"),
            ("Fecule", 1.08, "g"), ("Cafe java timor", 1.353, "g"),
            # Ganache neutre (209.8 portions)
            ("Creme", 4.15, "mL"), ("Gelatine poudre", 0.024, "g"),
            ("Trimoline", 0.167, "g"), ("Chocolat blanc Callebaut", 0.763, "g"),
            ("Glucose", 0.167, "g"),
        ],
    },
    "Earl Grey": {
        "yield": 36,
        "ingredients": [
            # Creme pat earl grey (36.94 portions)
            ("Lait", 13.53, "mL"), ("Sucre", 2.71, "g"), ("Oeufs", 0.108, "pcs"),
            ("Fecule", 1.08, "g"), ("Earl grey sachets", 0.054, "pcs"),
            # Ganache neutre (209.8 portions)
            ("Creme", 4.15, "mL"), ("Gelatine poudre", 0.024, "g"),
            ("Trimoline", 0.167, "g"), ("Chocolat blanc Callebaut", 0.763, "g"),
            ("Glucose", 0.167, "g"),
        ],
    },
    "Praline": {
        "yield": 47,
        "ingredients": [
            # Creme pat nature (47.5 portions)
            ("Lait", 10.53, "mL"), ("Sucre", 2.11, "g"), ("Oeufs", 0.084, "pcs"),
            ("Fecule", 0.842, "g"),
            # Praline noisette sub (158 portions)
            ("Amande", 1.519, "g"), ("Noisette", 1.519, "g"),
            ("Eau", 0.506, "mL"), ("Sucre", 2.025, "g"),
            # Ganache praline (220.4 portions) - raw only
            ("Creme", 3.95, "mL"), ("Gelatine poudre", 0.023, "g"),
            ("Trimoline", 0.159, "g"), ("Chocolat blanc Callebaut", 0.726, "g"),
            ("Glucose", 0.159, "g"),
            # Cross-ref: Praline noisette 56g in ganache → 56/880, /220.4
            ("Amande", 0.016, "g"), ("Noisette", 0.016, "g"),
            ("Eau", 0.005, "mL"), ("Sucre", 0.021, "g"),
        ],
    },
    "Litchi Rose Framboise": {
        "yield": 52,
        "ingredients": [
            # Creme pat rose (52.29 portions)
            ("Lait", 9.56, "mL"), ("Sucre", 1.91, "g"), ("Oeufs", 0.077, "pcs"),
            ("Fecule", 0.765, "g"), ("Eau de rose", 1.339, "mL"),
            # Litchi 2g/chou
            ("Litchi", 2.0, "g"),
            # Framboise pepin sub (86 portions)
            ("Puree framboises", 1.395, "g"), ("Framboises", 0.349, "g"),
            ("Pectine NH", 0.017, "g"), ("Sucre", 0.349, "g"),
            # Ganache rose (275.5 portions)
            ("Creme", 3.157, "mL"), ("Gelatine poudre", 0.018, "g"),
            ("Trimoline", 0.127, "g"), ("Chocolat blanc Callebaut", 0.581, "g"),
            ("Glucose", 0.127, "g"), ("Eau de rose", 0.200, "mL"),
        ],
    },
    "Citron": {
        "yield": 15,
        "ingredients": [
            # Cremeux citron (15.39 portions)
            ("Jus de citron", 6.01, "mL"), ("Sucre", 5.98, "g"),
            ("Oeufs", 0.325, "pcs"), ("Beurre", 1.43, "g"),
            # Gel citron (63.25 portions)
            ("Jus de citron", 0.791, "mL"), ("Puree de citron vert", 0.633, "g"),
            ("Sucre", 0.633, "g"), ("Pectine NH", 0.055, "g"),
            # Meringue (86.75 portions)
            ("Eau", 0.749, "mL"), ("Sucre", 2.306, "g"), ("Oeufs", 0.046, "pcs"),
        ],
    },
    "Chocolat Lait Croustillant": {
        "yield": 53,
        "ingredients": [
            # Creme pat choc lait (53.57 portions)
            ("Lait", 9.33, "mL"), ("Sucre", 1.87, "g"), ("Oeufs", 0.075, "pcs"),
            ("Fecule", 0.75, "g"), ("Chocolat au lait", 1.68, "g"),
            # Croustillant (166.25 portions) - raw only
            ("Chocolat au lait", 0.602, "g"), ("Feuilletine", 1.203, "g"),
            # Cross-ref: Praline noisette 400g in croustillant → 400/880, /166.25
            ("Amande", 0.657, "g"), ("Noisette", 0.657, "g"),
            ("Eau", 0.219, "mL"), ("Sucre", 0.875, "g"),
            # Ganache praline (275.5 portions) - raw only
            ("Creme", 3.157, "mL"), ("Gelatine poudre", 0.018, "g"),
            ("Trimoline", 0.127, "g"), ("Chocolat blanc Callebaut", 0.581, "g"),
            ("Glucose", 0.127, "g"),
            # Cross-ref: Praline noisette 56g in ganache → 56/880, /275.5
            ("Amande", 0.092, "g"), ("Noisette", 0.092, "g"),
            ("Eau", 0.031, "mL"), ("Sucre", 0.123, "g"),
            # Decor: chocolat au lait 1g/chou
            ("Chocolat au lait", 1.0, "g"),
        ],
    },
    "Matcha Coco": {
        "yield": 60,
        "ingredients": [
            # Mousse coco (60.83 portions)
            ("Puree coco", 7.596, "g"), ("Gelatine feuille", 0.074, "pcs"),
            ("Creme", 6.445, "mL"), ("Sucre", 2.302, "g"),
            ("Oeufs", 0.066, "pcs"), ("Eau", 0.690, "mL"),
            # Ganache matcha (210.9 portions)
            ("Creme", 4.125, "mL"), ("Gelatine poudre", 0.024, "g"),
            ("Trimoline", 0.166, "g"), ("Chocolat blanc Callebaut", 0.759, "g"),
            ("Glucose", 0.166, "g"), ("Matcha", 0.026, "g"),
        ],
    },
    "Amande Fleur d'Oranger": {
        "yield": 52,
        "ingredients": [
            # Creme pat fleur d'oranger (52.29 portions)
            ("Lait", 9.56, "mL"), ("Sucre", 1.91, "g"), ("Oeufs", 0.077, "pcs"),
            ("Fecule", 0.765, "g"), ("Eau de fleur d'oranger", 1.339, "mL"),
            # Praline amande sub (209 portions)
            ("Amande", 2.297, "g"), ("Eau", 0.383, "mL"), ("Sucre", 1.531, "g"),
            # Ganache fleur d'oranger (275.5 portions)
            ("Creme", 3.157, "mL"), ("Gelatine poudre", 0.018, "g"),
            ("Trimoline", 0.127, "g"), ("Chocolat blanc Callebaut", 0.581, "g"),
            ("Glucose", 0.127, "g"), ("Eau de fleur d'oranger", 0.200, "mL"),
        ],
    },
    "Mangue Passion": {
        "yield": 29,
        "ingredients": [
            # Cremeux mangue/passion (29.67 portions)
            ("Puree de mangue", 6.507, "g"), ("Puree passion", 6.507, "g"),
            ("Sucre", 3.034, "g"), ("Pectine NH", 0.270, "g"),
            ("Fecule", 0.506, "g"), ("Beurre", 2.124, "g"),
            # Ganache zeste citron (262.5 portions)
            ("Creme", 3.314, "mL"), ("Gelatine poudre", 0.019, "g"),
            ("Trimoline", 0.133, "g"), ("Chocolat blanc Callebaut", 0.610, "g"),
            ("Glucose", 0.133, "g"),
            # Decor: mangue fraiche 2g/chou
            ("Mangue fraiche", 2.0, "g"),
        ],
    },
}


def merge_ingredients(per_chou_list, yield_qty):
    """Merge duplicate ingredients and scale to yield."""
    merged = {}
    for name, qty_per_chou, unit in per_chou_list:
        if name in merged:
            merged[name] = (merged[name][0] + qty_per_chou * yield_qty, unit)
        else:
            merged[name] = (qty_per_chou * yield_qty, unit)
    return [(name, round(qty, 2), unit) for name, (qty, unit) in merged.items()]


def run_import(dry_run=False, email=USER_EMAIL):
    app = create_app()
    with app.app_context():
        # 1. Look up user
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"ERROR: User {USER_EMAIL} not found!")
            sys.exit(1)
        shop_id = user.shop_id
        print(f"Found user: {user.display_name} (shop_id={shop_id})")

        # Idempotency check
        existing = Recipe.query.filter_by(shop_id=shop_id, name="Pate a choux").first()
        if existing:
            print("WARNING: 'Pate a choux' recipe already exists. Aborting to prevent duplicates.")
            sys.exit(1)

        # 2. Create ingredients
        print(f"\nCreating {len(INGREDIENTS_DATA)} ingredients...")
        ing_map = {}  # name → Ingredient object
        for name, base_unit, cost, category in INGREDIENTS_DATA:
            ing = Ingredient(
                shop_id=shop_id, name=name, base_unit=base_unit,
                cost_per_base_unit=cost, category=category,
            )
            db.session.add(ing)
            ing_map[name] = ing
        db.session.flush()
        print(f"  Created {len(ing_map)} ingredients")

        # 3. Create base recipes
        def create_recipe(data):
            recipe = Recipe(
                shop_id=shop_id, name=data["name"],
                yield_quantity=data["yield"], yield_unit=data.get("yield_unit", "pcs"),
            )
            db.session.add(recipe)
            db.session.flush()
            for ing_name, qty, unit in data["ingredients"]:
                ri = RecipeIngredient(
                    recipe_id=recipe.id, ingredient_id=ing_map[ing_name].id,
                    quantity=qty, unit=unit,
                )
                db.session.add(ri)
            return recipe

        print("\nCreating base recipes...")
        pate_recipe = create_recipe(PATE_A_CHOUX)
        print(f"  Pate a choux: cost/unit = {pate_recipe.cost_per_unit:.4f}")
        craq_recipe = create_recipe(CRAQUELIN)
        print(f"  Craquelin: cost/unit = {craq_recipe.cost_per_unit:.4f}")

        # 4. Create flavor recipes
        print(f"\nCreating {len(FLAVOR_RECIPES)} flavor recipes...")
        flavor_recipe_map = {}  # flavor_name → Recipe
        for flavor_name, data in FLAVOR_RECIPES.items():
            yield_qty = data["yield"]
            merged = merge_ingredients(data["ingredients"], yield_qty)
            recipe_data = {
                "name": f"Garniture {flavor_name}",
                "yield": yield_qty,
                "yield_unit": "pcs",
                "ingredients": merged,
            }
            recipe = create_recipe(recipe_data)
            flavor_recipe_map[flavor_name] = recipe
            print(f"  {recipe.name}: cost/unit = {recipe.cost_per_unit:.4f}")

        # 5. Create products
        print(f"\nCreating {len(FLAVOR_RECIPES)} products...")
        for flavor_name, flavor_recipe in flavor_recipe_map.items():
            product = Product(
                shop_id=shop_id, name=f"Choux {flavor_name}",
                category="Pastries", selling_price=SELLING_PRICE, vat_rate=VAT_RATE,
            )
            db.session.add(product)
            db.session.flush()

            for recipe, qty in [(pate_recipe, 1.0), (craq_recipe, 1.0), (flavor_recipe, 1.0)]:
                db.session.add(ProductRecipe(
                    product_id=product.id, recipe_id=recipe.id, quantity_needed=qty,
                ))

            total_cost = product.total_recipe_cost
            margin = product.profit_margin
            print(f"  {product.name}: cost={total_cost:.2f}, margin={margin:.1f}%")

        # Commit or rollback
        if dry_run:
            db.session.rollback()
            print("\n[DRY RUN] All changes rolled back.")
        else:
            db.session.commit()
            print(f"\nDone! Created {len(INGREDIENTS_DATA)} ingredients, "
                  f"{2 + len(FLAVOR_RECIPES)} recipes, {len(FLAVOR_RECIPES)} products.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import choux pastry data")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--email", default=USER_EMAIL, help="User email to import for")
    args = parser.parse_args()
    run_import(dry_run=args.dry_run, email=args.email)
