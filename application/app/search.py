from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case, or_, select

from app import text_search
from app.contacts import by_name, relation_states
from app.extensions import db
from models.user import User

SEARCH_MIN_LENGTH = 3
# Names are short: at 3 characters, two shared initials would be enough to match (ADR 0018).
USER_FUZZY_MIN_LENGTH = 4
USER_FUZZY_THRESHOLD = 0.5
USER_RESULTS_MAX = 25

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("")
@login_required
def results():
    search_type = request.args.get("type", "user")
    search_text = request.args.get("q", "").strip()
    page = {"search_text": search_text, "search_type": search_type, "results": [], "message": None}

    if search_type not in ("user", "tool"):
        page["search_type"] = "tool"
        page["message"] = "Ce type de recherche n'est pas disponible"
    elif len(normalized_text := text_search.normalize(search_text)) < SEARCH_MIN_LENGTH:
        page["message"] = f"Saisissez au moins {SEARCH_MIN_LENGTH} caractères"
    elif search_type == "tool":
        return redirect(url_for("tools.find", q=search_text))
    else:
        users = _matching_users(search_text, fuzzy=len(normalized_text) >= USER_FUZZY_MIN_LENGTH)
        shown = users[:USER_RESULTS_MAX]
        states = relation_states([user.id for user in shown])
        page["results"] = [(user, states[user.id]) for user in shown]
        if not users:
            page["message"] = f"Aucun utilisateur ne correspond à « {search_text} »"
        elif len(users) > USER_RESULTS_MAX:
            page["message"] = (
                f"Plus de {USER_RESULTS_MAX} utilisateurs correspondent à « {search_text} » ; "
                "précisez votre recherche"
            )

    return render_template("search/results.html", **page)


def _matching_users(search_text, fuzzy):
    """Other users whose full name contains the text or, if fuzzy, resembles it; one past the cap"""
    full_name = User.first_name + " " + User.last_name
    contained = text_search.contains(full_name, search_text)
    condition, ordering = contained, []
    if fuzzy:
        score = text_search.similarity(full_name, search_text)
        condition = or_(contained, score >= USER_FUZZY_THRESHOLD)
        ordering = [case((contained, 0), else_=1), score.desc()]
    return db.session.scalars(
        select(User)
        .where(User.id != current_user.id, User.deleted_at.is_(None), condition)
        .order_by(*ordering, *by_name())
        .limit(USER_RESULTS_MAX + 1)
    ).all()
