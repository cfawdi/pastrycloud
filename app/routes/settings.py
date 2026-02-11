from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Shop

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/team")
@login_required
def team():
    members = User.query.filter_by(shop_id=current_user.shop_id).order_by(User.created_at).all()
    return render_template("settings/team.html", members=members, shop=current_user.shop)


@bp.route("/team/regenerate-invite", methods=["POST"])
@login_required
def regenerate_invite():
    if current_user.role != "owner":
        abort(403)
    shop = current_user.shop
    shop.invite_code = Shop.generate_invite_code()
    db.session.commit()
    flash("Invite code regenerated.", "success")
    return redirect(url_for("settings.team"))


@bp.route("/team/remove/<int:id>", methods=["POST"])
@login_required
def remove_member(id):
    if current_user.role != "owner":
        abort(403)
    if id == current_user.id:
        flash("You can't remove yourself.", "error")
        return redirect(url_for("settings.team"))

    user = User.query.filter_by(id=id, shop_id=current_user.shop_id).first_or_404()
    name = user.display_name
    db.session.delete(user)
    db.session.commit()
    flash(f"Removed {name} from the team.", "warning")
    return redirect(url_for("settings.team"))


@bp.route("/shop", methods=["GET", "POST"])
@login_required
def shop():
    if current_user.role != "owner":
        abort(403)

    s = current_user.shop
    if request.method == "POST":
        s.name = request.form.get("name", s.name).strip()
        s.currency = request.form.get("currency", s.currency).strip()
        s.default_vat_rate = float(request.form.get("default_vat_rate", s.default_vat_rate))
        db.session.commit()
        flash("Shop settings updated.", "success")
        return redirect(url_for("settings.shop"))

    return render_template("settings/shop.html", shop=s)
