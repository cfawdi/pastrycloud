"""Seed data with sample Moroccan pastry ingredients, recipes, and products."""

from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import Shop, User, Ingredient, Recipe, RecipeIngredient, Product

app = create_app()


def seed():
    with app.app_context():
        # Skip if data already exists
        if Shop.query.first():
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database...")

        # --- Demo shop & user ---
        shop = Shop(
            name="Atelier Alami",
            currency="DH",
            default_vat_rate=20.0,
            invite_code=Shop.generate_invite_code(),
        )
        db.session.add(shop)
        db.session.flush()

        owner = User(
            email="demo@pastrycloud.com",
            display_name="Demo Owner",
            role="owner",
            shop_id=shop.id,
        )
        owner.set_password("demo123")
        db.session.add(owner)
        db.session.flush()

        print(f"  Created shop '{shop.name}' (invite: {shop.invite_code})")
        print(f"  Created user '{owner.email}' / demo123")

        # --- Ingredients ---
        ingredients_data = [
            # Flour & Grains
            ("All-Purpose Flour", "Flour & Grains", "g", 50000, 0.008, 5000, 90),
            ("Semolina (Fine)", "Flour & Grains", "g", 20000, 0.012, 3000, 120),
            ("Almond Flour", "Nuts & Dried Fruits", "g", 10000, 0.080, 2000, 60),
            ("Cornstarch", "Flour & Grains", "g", 5000, 0.015, 1000, 180),

            # Dairy
            ("Butter (Unsalted)", "Dairy", "g", 10000, 0.060, 2000, 30),
            ("Fresh Cream", "Dairy", "mL", 5000, 0.040, 1000, 7),
            ("Milk", "Dairy", "mL", 10000, 0.008, 2000, 5),
            ("Cream Cheese", "Dairy", "g", 3000, 0.050, 500, 14),

            # Sweeteners
            ("Granulated Sugar", "Sweeteners", "g", 30000, 0.006, 5000, 365),
            ("Powdered Sugar", "Sweeteners", "g", 10000, 0.008, 2000, 365),
            ("Honey", "Sweeteners", "mL", 5000, 0.040, 1000, 365),
            ("Orange Blossom Water", "Flavorings", "mL", 2000, 0.030, 500, 365),

            # Nuts & Dried Fruits
            ("Whole Almonds", "Nuts & Dried Fruits", "g", 8000, 0.070, 2000, 90),
            ("Walnuts", "Nuts & Dried Fruits", "g", 5000, 0.080, 1000, 90),
            ("Dates (Medjool)", "Nuts & Dried Fruits", "g", 5000, 0.060, 1000, 60),
            ("Sesame Seeds", "Nuts & Dried Fruits", "g", 3000, 0.025, 500, 180),
            ("Dried Coconut", "Nuts & Dried Fruits", "g", 3000, 0.030, 500, 180),

            # Fats & Oils
            ("Vegetable Oil", "Fats & Oils", "mL", 5000, 0.010, 1000, 365),
            ("Olive Oil", "Fats & Oils", "mL", 3000, 0.030, 500, 365),

            # Eggs
            ("Eggs", "Eggs", "pcs", 60, 1.500, 12, 21),

            # Flavorings
            ("Vanilla Extract", "Flavorings", "mL", 500, 0.100, 100, 365),
            ("Cinnamon (Ground)", "Flavorings", "g", 500, 0.040, 100, 365),
            ("Mastic Gum", "Flavorings", "g", 100, 0.500, 20, 365),
            ("Rose Water", "Flavorings", "mL", 1000, 0.025, 200, 365),

            # Chocolate
            ("Dark Chocolate (70%)", "Chocolate", "g", 5000, 0.050, 1000, 180),
            ("White Chocolate", "Chocolate", "g", 3000, 0.055, 500, 180),

            # Fruits
            ("Fresh Oranges", "Fruits", "pcs", 30, 3.000, 10, 14),
            ("Lemons", "Fruits", "pcs", 20, 2.500, 5, 14),
        ]

        ingredients = {}
        for name, cat, unit, qty, cost, min_stock, exp_days in ingredients_data:
            ing = Ingredient(
                shop_id=shop.id,
                name=name,
                category=cat,
                base_unit=unit,
                quantity_on_hand=qty,
                cost_per_base_unit=cost,
                min_stock_level=min_stock,
                expiry_date=date.today() + timedelta(days=exp_days),
            )
            db.session.add(ing)
            ingredients[name] = ing

        db.session.flush()

        # --- Recipes ---

        # 1. Cornes de Gazelle (Kaab el Ghazal)
        r1 = Recipe(
            shop_id=shop.id,
            name="Cornes de Gazelle",
            description="Crescent-shaped Moroccan almond pastry with orange blossom water. A classic celebration treat.",
            yield_quantity=30,
            yield_unit="pcs",
            estimated_time_minutes=90,
        )
        db.session.add(r1)
        db.session.flush()
        for ing_name, qty, unit in [
            ("Almond Flour", 500, "g"),
            ("Powdered Sugar", 250, "g"),
            ("Orange Blossom Water", 30, "mL"),
            ("Butter (Unsalted)", 50, "g"),
            ("All-Purpose Flour", 300, "g"),
            ("Cinnamon (Ground)", 5, "g"),
            ("Mastic Gum", 2, "g"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r1.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 2. Msemen (Moroccan Flatbread)
        r2 = Recipe(
            shop_id=shop.id,
            name="Msemen",
            description="Flaky, layered Moroccan flatbread. Perfect with honey and butter for breakfast.",
            yield_quantity=12,
            yield_unit="pcs",
            estimated_time_minutes=45,
        )
        db.session.add(r2)
        db.session.flush()
        for ing_name, qty, unit in [
            ("All-Purpose Flour", 500, "g"),
            ("Semolina (Fine)", 200, "g"),
            ("Butter (Unsalted)", 100, "g"),
            ("Vegetable Oil", 50, "mL"),
            ("Granulated Sugar", 20, "g"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r2.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 3. Croissants
        r3 = Recipe(
            shop_id=shop.id,
            name="Croissants",
            description="Classic French-style butter croissants with flaky layers.",
            yield_quantity=12,
            yield_unit="pcs",
            estimated_time_minutes=180,
        )
        db.session.add(r3)
        db.session.flush()
        for ing_name, qty, unit in [
            ("All-Purpose Flour", 500, "g"),
            ("Butter (Unsalted)", 280, "g"),
            ("Granulated Sugar", 60, "g"),
            ("Milk", 150, "mL"),
            ("Eggs", 1, "pcs"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r3.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 4. Chebakia (Honey cookies)
        r4 = Recipe(
            shop_id=shop.id,
            name="Chebakia",
            description="Sesame-coated flower-shaped cookies soaked in honey. Traditional Ramadan treat.",
            yield_quantity=40,
            yield_unit="pcs",
            estimated_time_minutes=120,
        )
        db.session.add(r4)
        db.session.flush()
        for ing_name, qty, unit in [
            ("All-Purpose Flour", 500, "g"),
            ("Sesame Seeds", 100, "g"),
            ("Whole Almonds", 100, "g"),
            ("Honey", 300, "mL"),
            ("Orange Blossom Water", 40, "mL"),
            ("Butter (Unsalted)", 50, "g"),
            ("Vegetable Oil", 500, "mL"),
            ("Cinnamon (Ground)", 10, "g"),
            ("Eggs", 2, "pcs"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r4.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 5. Briouats aux Amandes (Almond Triangles)
        r5 = Recipe(
            shop_id=shop.id,
            name="Briouats aux Amandes",
            description="Crispy filo triangles stuffed with almond paste and soaked in honey.",
            yield_quantity=24,
            yield_unit="pcs",
            estimated_time_minutes=60,
        )
        db.session.add(r5)
        db.session.flush()
        for ing_name, qty, unit in [
            ("Almond Flour", 400, "g"),
            ("Granulated Sugar", 150, "g"),
            ("Orange Blossom Water", 20, "mL"),
            ("Butter (Unsalted)", 100, "g"),
            ("Honey", 200, "mL"),
            ("Cinnamon (Ground)", 5, "g"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r5.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 6. Ghriba (Coconut Cookies)
        r6 = Recipe(
            shop_id=shop.id,
            name="Ghriba Coco",
            description="Soft, crinkled Moroccan coconut cookies with a melt-in-your-mouth texture.",
            yield_quantity=30,
            yield_unit="pcs",
            estimated_time_minutes=40,
        )
        db.session.add(r6)
        db.session.flush()
        for ing_name, qty, unit in [
            ("Dried Coconut", 300, "g"),
            ("Granulated Sugar", 200, "g"),
            ("Eggs", 3, "pcs"),
            ("Powdered Sugar", 50, "g"),
            ("Vanilla Extract", 5, "mL"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r6.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        # 7. Chocolate Fondant
        r7 = Recipe(
            shop_id=shop.id,
            name="Fondant au Chocolat",
            description="Rich molten chocolate cake with a gooey center.",
            yield_quantity=6,
            yield_unit="pcs",
            estimated_time_minutes=30,
        )
        db.session.add(r7)
        db.session.flush()
        for ing_name, qty, unit in [
            ("Dark Chocolate (70%)", 200, "g"),
            ("Butter (Unsalted)", 100, "g"),
            ("Eggs", 4, "pcs"),
            ("Granulated Sugar", 100, "g"),
            ("All-Purpose Flour", 50, "g"),
        ]:
            db.session.add(RecipeIngredient(
                recipe_id=r7.id, ingredient_id=ingredients[ing_name].id,
                quantity=qty, unit=unit,
            ))

        db.session.flush()

        # --- Products ---
        products_data = [
            ("Cornes de Gazelle", "Pastries", r1.id, 15.00, 20),
            ("Msemen (x3)", "Bread", r2.id, 10.00, 20),
            ("Croissant", "Viennoiserie", r3.id, 8.00, 20),
            ("Chebakia (250g box)", "Pastries", r4.id, 35.00, 20),
            ("Briouats aux Amandes (x6)", "Pastries", r5.id, 25.00, 20),
            ("Ghriba Coco (x6)", "Cookies", r6.id, 18.00, 20),
            ("Fondant au Chocolat", "Cakes", r7.id, 22.00, 20),
            ("Assorted Pastry Box (500g)", "Pastries", None, 65.00, 20),
            ("Fresh Orange Juice", "Drinks", None, 12.00, 20),
            ("Mint Tea", "Drinks", None, 8.00, 20),
        ]

        for name, cat, recipe_id, price, vat in products_data:
            db.session.add(Product(
                shop_id=shop.id,
                name=name,
                category=cat,
                recipe_id=recipe_id,
                selling_price=price,
                vat_rate=vat,
            ))

        db.session.commit()
        print("Seed data loaded successfully!")
        print(f"  - {len(ingredients_data)} ingredients")
        print(f"  - 7 recipes")
        print(f"  - {len(products_data)} products")


if __name__ == "__main__":
    seed()
