import uuid
from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class Shop(db.Model):
    __tablename__ = "shops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), default="DH")
    default_vat_rate = db.Column(db.Float, default=20.0)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", back_populates="shop", cascade="all, delete-orphan")

    @staticmethod
    def generate_invite_code():
        return uuid.uuid4().hex[:8]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="member")  # owner / member
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shop = db.relationship("Shop", back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default="")
    base_unit = db.Column(db.String(10), nullable=False)  # g, mL, pcs
    quantity_on_hand = db.Column(db.Float, default=0.0)  # stored in base units
    cost_per_base_unit = db.Column(db.Float, default=0.0)
    min_stock_level = db.Column(db.Float, default=0.0)  # in base units
    expiry_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recipe_ingredients = db.relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    waste_logs = db.relationship("WasteLog", back_populates="ingredient")

    @property
    def stock_status(self):
        if self.quantity_on_hand <= 0:
            return "out"
        if self.quantity_on_hand <= self.min_stock_level:
            return "low"
        return "ok"

    @property
    def stock_value(self):
        return self.quantity_on_hand * self.cost_per_base_unit

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False

    @property
    def display_quantity(self):
        """Show quantity in readable units (e.g. 2.5 kg instead of 2500 g)."""
        return format_quantity(self.quantity_on_hand, self.base_unit)

    @property
    def display_min_stock(self):
        return format_quantity(self.min_stock_level, self.base_unit)


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    yield_quantity = db.Column(db.Float, default=1.0)
    yield_unit = db.Column(db.String(20), default="pcs")
    estimated_time_minutes = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ingredients = db.relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    products = db.relationship("Product", back_populates="recipe")
    production_runs = db.relationship("ProductionRun", back_populates="recipe")

    @property
    def total_cost(self):
        total = 0.0
        for ri in self.ingredients:
            base_qty = convert_to_base(ri.quantity, ri.unit, ri.ingredient.base_unit)
            total += base_qty * ri.ingredient.cost_per_base_unit
        return total

    @property
    def cost_per_unit(self):
        if self.yield_quantity and self.yield_quantity > 0:
            return self.total_cost / self.yield_quantity
        return self.total_cost


class RecipeIngredient(db.Model):
    __tablename__ = "recipe_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)  # display unit

    recipe = db.relationship("Recipe", back_populates="ingredients")
    ingredient = db.relationship("Ingredient", back_populates="recipe_ingredients")

    @property
    def base_quantity(self):
        return convert_to_base(self.quantity, self.unit, self.ingredient.base_unit)

    @property
    def line_cost(self):
        return self.base_quantity * self.ingredient.cost_per_base_unit


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default="")
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=True)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    vat_rate = db.Column(db.Float, default=20.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship("Recipe", back_populates="products")
    sale_items = db.relationship("SaleItem", back_populates="product")
    waste_logs = db.relationship("WasteLog", back_populates="product")

    @property
    def price_with_vat(self):
        return self.selling_price * (1 + self.vat_rate / 100)


class ProductionRun(db.Model):
    __tablename__ = "production_runs"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    quantity_produced = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(20), default="planned")  # planned, completed
    produced_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, default="")
    cost_total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship("Recipe", back_populates="production_runs")


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    sale_date = db.Column(db.Date, default=date.today)
    total_amount = db.Column(db.Float, default=0.0)
    vat_amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20), default="cash")  # cash, card, mobile
    customer_name = db.Column(db.String(100), default="")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items)


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    vat_rate = db.Column(db.Float, default=20.0)
    line_total = db.Column(db.Float, default=0.0)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")


class WasteLog(db.Model):
    __tablename__ = "waste_logs"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(10), default="")
    cost_estimate = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(30), default="other")  # expired, spoiled, failed_batch, unsold, other
    notes = db.Column(db.Text, default="")
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient = db.relationship("Ingredient", back_populates="waste_logs")
    product = db.relationship("Product", back_populates="waste_logs")


# --- Unit conversion helpers ---

CONVERSION_TO_BASE = {
    "g": 1.0,
    "kg": 1000.0,
    "mL": 1.0,
    "ml": 1.0,
    "L": 1000.0,
    "l": 1000.0,
    "pcs": 1.0,
    "dozen": 12.0,
}

UNIT_FAMILIES = {
    "g": "mass",
    "kg": "mass",
    "mL": "volume",
    "ml": "volume",
    "L": "volume",
    "l": "volume",
    "pcs": "count",
    "dozen": "count",
}

BASE_UNITS = {"mass": "g", "volume": "mL", "count": "pcs"}


def convert_to_base(quantity, from_unit, base_unit):
    """Convert a quantity from display unit to base unit."""
    factor = CONVERSION_TO_BASE.get(from_unit, 1.0)
    return quantity * factor


def convert_from_base(quantity, base_unit):
    """Convert from base unit to a readable display unit."""
    if base_unit == "g" and quantity >= 1000:
        return quantity / 1000, "kg"
    if base_unit == "mL" and quantity >= 1000:
        return quantity / 1000, "L"
    return quantity, base_unit


def format_quantity(quantity, base_unit):
    """Format a base-unit quantity for display."""
    val, unit = convert_from_base(quantity, base_unit)
    if val == int(val):
        return f"{int(val)} {unit}"
    return f"{val:.2f} {unit}"


def get_compatible_units(base_unit):
    """Return list of units compatible with a base unit."""
    family = UNIT_FAMILIES.get(base_unit, None)
    if not family:
        return [base_unit]
    return [u for u, f in UNIT_FAMILIES.items() if f == family]
