from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case, or_, select

from app import catalog, text_search
from app.contacts import (
    RELATION_FILTERS,
    by_name,
    read_expanded,
    read_relation_filter,
    relation_states,
)
from app.extensions import db
from models.user import User

SEARCH_MIN_LENGTH = 3
# Names are short: at 3 characters, two shared initials would be enough to match (ADR 0018).
USER_FUZZY_MIN_LENGTH = 4
USER_FUZZY_THRESHOLD = 0.5
USER_RESULTS_MAX = 25
USERS_SHOWN = 5
TOOLS_SHOWN = 6
DISTANCES = ("1km", "3km", "5km", "10km", "Aucune limite")

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("")
@login_required
def results():
    # A former "type" parameter is ignored: both sections are always shown.
    search_text = request.args.get("q", "").strip()
    normalized_text = text_search.normalize(search_text)
    if len(normalized_text) < SEARCH_MIN_LENGTH:
        return render_template(
            "search/results.html",
            search_text=search_text,
            message=f"Saisissez au moins {SEARCH_MIN_LENGTH} caractères",
        )
    relation = read_relation_filter(request.args)
    expanded = read_expanded(request.args)
    return render_template(
        "search/results.html",
        search_text=search_text,
        relation=relation,
        relation_filters=RELATION_FILTERS,
        distances=DISTANCES,
        expanded=expanded,
        users=_users_section(search_text, normalized_text, relation, expanded),
        tools=_tools_section(search_text),
    )


def _users_section(search_text, normalized_text, relation, expanded):
    """The users shown with their relation, their count, and what the section offers next"""
    fuzzy = len(normalized_text) >= USER_FUZZY_MIN_LENGTH
    users = _matching_users(search_text, fuzzy, relation)
    shown = users[: USER_RESULTS_MAX if expanded else USERS_SHOWN]
    states = relation_states([user.id for user in shown])
    over_cap = len(users) > USER_RESULTS_MAX
    total = f"plus de {USER_RESULTS_MAX}" if over_cap else str(len(users))
    message = None
    if expanded and over_cap:
        message = (
            f"Plus de {USER_RESULTS_MAX} utilisateurs correspondent à « {search_text} » ; "
            "précisez votre recherche"
        )
    return {
        "results": [(user, states[user.id]) for user in shown],
        "count": f"{len(shown)} de {total}",
        "more_url": (
            url_for(
                "search.results",
                q=search_text,
                relation=relation if relation != "all" else None,
                more="1",
            )
            if not expanded and len(users) > USERS_SHOWN
            else None
        ),
        "message": message,
    }


def _tools_section(search_text):
    """The first cards of the contacts' tools that match, their count, and the way to the rest"""
    tools = catalog.visible_tools(current_user.id, text=search_text)
    origin = {"origin": "find", "q": search_text}
    cards = catalog.tool_cards(tools[:TOOLS_SHOWN], viewer_id=current_user.id, origin=origin)
    return {
        "cards": cards,
        "count": f"{len(cards)} de {len(tools)}",
        "more_url": url_for("tools.find", q=search_text) if len(tools) > TOOLS_SHOWN else None,
    }


def _matching_users(search_text, fuzzy, relation):
    """Other users whose full name contains the text or, if fuzzy, resembles it; one past the cap"""
    full_name = User.first_name + " " + User.last_name
    contained = text_search.contains(full_name, search_text)
    condition, ordering = contained, []
    if fuzzy:
        score = text_search.similarity(full_name, search_text)
        condition = or_(contained, score >= USER_FUZZY_THRESHOLD)
        ordering = [case((contained, 0), else_=1), score.desc()]
    query = select(User).where(User.id != current_user.id, User.deleted_at.is_(None), condition)
    if relation == "contacts":
        query = query.where(User.id.in_(catalog.contact_ids_query(current_user.id)))
    elif relation == "others":
        query = query.where(User.id.not_in(catalog.contact_ids_query(current_user.id)))
    return db.session.scalars(
        query.order_by(*ordering, *by_name()).limit(USER_RESULTS_MAX + 1)
    ).all()
