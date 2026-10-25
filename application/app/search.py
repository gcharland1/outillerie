from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from app.contacts import relation_states
from app.extensions import db
from models.user import User

SEARCH_MIN_LENGTH = 3

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("")
@login_required
def results():
    search_type = request.args.get("type", "user")
    search_text = request.args.get("q", "").strip()
    page = {"search_text": search_text, "results": [], "message": None}

    if search_type != "user":
        page["message"] = "Ce type de recherche n'est pas encore disponible"
    elif len(search_text) < SEARCH_MIN_LENGTH:
        page["message"] = f"Saisissez au moins {SEARCH_MIN_LENGTH} caractères"
    else:
        users = _matching_users(search_text)
        states = relation_states([user.id for user in users])
        page["results"] = [(user, states[user.id]) for user in users]
        if not users:
            page["message"] = f"Aucun utilisateur ne correspond à « {search_text} »"

    return render_template("search/results.html", **page)


def _matching_users(search_text):
    """Other users whose username, first name, last name or full name contains the text"""
    return db.session.scalars(
        select(User)
        .where(
            User.id != current_user.id,
            or_(
                User.username.icontains(search_text, autoescape=True),
                User.first_name.icontains(search_text, autoescape=True),
                User.last_name.icontains(search_text, autoescape=True),
                (User.first_name + " " + User.last_name).icontains(search_text, autoescape=True),
            ),
        )
        .order_by(func.lower(User.username), User.id)
    ).all()
