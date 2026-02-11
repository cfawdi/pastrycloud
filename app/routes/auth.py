from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.extensions import db
from app.models import User, Shop

bp = Blueprint("auth", __name__)


@bp.route("/landing")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("auth/landing.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip()
        invite_code = request.form.get("invite_code", "").strip()

        if not email or not password or not display_name:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("auth/register.html")

        if invite_code:
            # Join existing shop
            shop = Shop.query.filter_by(invite_code=invite_code).first()
            if not shop:
                flash("Invalid invite code.", "error")
                return render_template("auth/register.html")
            role = "member"
        else:
            # Create new shop
            shop_name = request.form.get("shop_name", "").strip() or f"{display_name}'s Shop"
            shop = Shop(
                name=shop_name,
                invite_code=Shop.generate_invite_code(),
            )
            db.session.add(shop)
            db.session.flush()
            role = "owner"

        user = User(
            email=email,
            display_name=display_name,
            role=role,
            shop_id=shop.id,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        flash(f"Welcome to PastryCloud, {display_name}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.landing"))
