import csv
import io
import json
from openpyxl import Workbook
from app.models import Ingredient, Recipe, Product, ProductionRun, Sale, SaleItem, WasteLog


EXPORTABLE = {
    "ingredients": {
        "model": Ingredient,
        "columns": ["id", "name", "category", "base_unit", "quantity_on_hand",
                     "cost_per_base_unit", "min_stock_level", "expiry_date", "notes"],
    },
    "recipes": {
        "model": Recipe,
        "columns": ["id", "name", "description", "yield_quantity", "yield_unit",
                     "estimated_time_minutes", "is_active"],
    },
    "products": {
        "model": Product,
        "columns": ["id", "name", "category", "recipe_id", "selling_price", "vat_rate", "is_active"],
    },
    "production_runs": {
        "model": ProductionRun,
        "columns": ["id", "recipe_id", "quantity_produced", "status", "produced_at",
                     "cost_total", "notes"],
    },
    "sales": {
        "model": Sale,
        "columns": ["id", "sale_date", "total_amount", "vat_amount", "payment_method",
                     "customer_name", "notes"],
    },
    "waste_logs": {
        "model": WasteLog,
        "columns": ["id", "ingredient_id", "product_id", "quantity", "unit",
                     "cost_estimate", "category", "notes", "logged_at"],
    },
}


def _get_rows(entity, shop_id):
    info = EXPORTABLE[entity]
    model = info["model"]
    if hasattr(model, "shop_id"):
        items = model.query.filter_by(shop_id=shop_id).all()
    else:
        items = model.query.all()
    rows = []
    for item in items:
        row = {}
        for col in info["columns"]:
            val = getattr(item, col, "")
            if val is None:
                val = ""
            elif hasattr(val, "isoformat"):
                val = val.isoformat()
            row[col] = val
        rows.append(row)
    return info["columns"], rows


def export_csv(entity, shop_id):
    columns, rows = _get_rows(entity, shop_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_json(entity, shop_id):
    _, rows = _get_rows(entity, shop_id)
    return json.dumps(rows, indent=2, ensure_ascii=False)


def export_excel(entity, shop_id):
    columns, rows = _get_rows(entity, shop_id)
    wb = Workbook()
    ws = wb.active
    ws.title = entity.replace("_", " ").title()
    ws.append(columns)
    for row in rows:
        ws.append([row[c] for c in columns])
    # Auto-width
    for col_cells in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
