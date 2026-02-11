from flask import Blueprint, render_template, request, Response
from flask_login import login_required, current_user
from app.services.export import export_csv, export_json, export_excel, EXPORTABLE

bp = Blueprint("exports", __name__, url_prefix="/export")


@bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("exports/export.html", entities=list(EXPORTABLE.keys()))


@bp.route("/download", methods=["GET"])
@login_required
def download():
    entity = request.args.get("entity", "")
    fmt = request.args.get("format", "csv")

    if entity not in EXPORTABLE:
        return "Invalid entity", 400

    shop_id = current_user.shop_id
    filename = f"{entity}.{fmt}" if fmt != "excel" else f"{entity}.xlsx"

    if fmt == "csv":
        data = export_csv(entity, shop_id)
        return Response(data, mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={filename}"})
    elif fmt == "json":
        data = export_json(entity, shop_id)
        return Response(data, mimetype="application/json",
                        headers={"Content-Disposition": f"attachment; filename={filename}"})
    elif fmt == "excel":
        data = export_excel(entity, shop_id)
        return Response(data,
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename={filename}"})

    return "Invalid format", 400
