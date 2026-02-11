from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
from .ingredients import bp as ingredients_bp
from .recipes import bp as recipes_bp
from .products import bp as products_bp
from .production import bp as production_bp
from .sales import bp as sales_bp
from .waste import bp as waste_bp
from .exports import bp as exports_bp
from .settings import bp as settings_bp

ALL_BLUEPRINTS = [
    auth_bp,
    dashboard_bp,
    ingredients_bp,
    recipes_bp,
    products_bp,
    production_bp,
    sales_bp,
    waste_bp,
    exports_bp,
    settings_bp,
]
