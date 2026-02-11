from flask import abort
from flask_login import current_user
from .extensions import db


def get_or_404(model, id):
    """Get by ID, 404 if not found or wrong shop."""
    obj = db.session.get(model, id)
    if not obj or (hasattr(obj, 'shop_id') and obj.shop_id != current_user.shop_id):
        abort(404)
    return obj
