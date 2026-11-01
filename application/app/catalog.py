"""The tools a user sees among their contacts' tools, and how each one stands for a loan."""

from datetime import datetime
from typing import NamedTuple
from zoneinfo import ZoneInfo

from sqlalchemy import String, and_, case, exists, func, or_, select
from sqlalchemy.orm import joinedload

from app import photos
from app.extensions import db
from models.contact import ContactRelation
from models.loan import Loan, LoanStatus
from models.tool import Tool, ToolCondition

CONDITION_LABELS = {
    ToolCondition.FUNCTIONAL: "Fonctionnel",
    ToolCondition.NEEDS_REPAIR: "À réparer",
    ToolCondition.OUT_OF_ORDER: "Hors d'usage",
}
DESCRIPTION_MAX_LENGTH = 125
# A word_similarity score from 0 to 1; tuned by the search scenarios of the spec (ADR 0016).
FUZZY_THRESHOLD = 0.5
# Below this length, trigrams match too loosely: only substrings count.
FUZZY_MIN_LENGTH = 3
# The server runs in UTC; a loan's last day ends at midnight where its users live.
SITE_TIMEZONE = ZoneInfo("America/Toronto")
MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

AVAILABLE = "Disponible"
PENDING = "En attente de prêt"
NO_CONTACT = "Vous n'avez encore aucun contact"
NO_TOOL = "Vos contacts n'ont encore aucun outil à prêter"
NO_MATCH = "Aucun outil ne correspond à ces filtres"


class ToolCard(NamedTuple):
    tool: Tool
    has_photo: bool
    description: str
    condition: str
    status: str
    available: bool


def tool_list(user_id, args, owner=None):
    """What a page listing tools needs: the filters read from its URL, the cards, or why none"""
    filters = {
        "text": args.get("q", "").strip(),
        "available_only": args.get("available") == "1",
    }
    owner_id = owner.id if owner is not None else None
    cards = tool_cards(visible_tools(user_id, owner_id=owner_id, **filters))
    empty_message = None
    if not cards:
        empty_message = _empty_message(user_id, owner, filtered=any(filters.values()))
    return {
        "filters": filters,
        "cards": cards,
        "empty_message": empty_message,
        "suggest_search": empty_message == NO_CONTACT,
    }


def is_contact(user_id, other_id):
    """Whether two different users are in contact"""
    if user_id == other_id:
        return False
    return db.session.get(ContactRelation, ContactRelation.pair(user_id, other_id)) is not None


def has_contacts(user_id):
    return db.session.scalar(select(exists().where(_relations_of(user_id))))


def visible_tools(user_id, owner_id=None, text="", available_only=False):
    """The contacts' tools the user may see, filtered and ordered as the spec says"""
    query = (
        select(Tool)
        .options(joinedload(Tool.owner))
        .where(
            Tool.is_active,
            Tool.condition != ToolCondition.OUT_OF_ORDER,
            Tool.owner_id.in_(_contact_ids(user_id)),
        )
    )
    if owner_id is not None:
        query = query.where(Tool.owner_id == owner_id)
    if available_only:
        query = query.where(~exists().where(Loan.tool_id == Tool.id, _blocking_loan()))
    if text:
        condition, ordering = _text_search(text)
        query = query.where(condition).order_by(*ordering)
    return db.session.scalars(query.order_by(func.lower(Tool.name), Tool.id)).all()


def tool_cards(tools):
    """What each tool's card shows, with statuses and photos read in one query each"""
    tool_ids = [tool.id for tool in tools]
    statuses = loan_statuses(tool_ids)
    photo_ids = photos.tool_ids_with_photo(tool_ids)
    return [
        ToolCard(
            tool=tool,
            has_photo=tool.id in photo_ids,
            description=short_description(tool.description),
            condition=CONDITION_LABELS[tool.condition],
            status=statuses[tool.id],
            available=statuses[tool.id] == AVAILABLE,
        )
        for tool in tools
    ]


def loan_statuses(tool_ids):
    """Each tool's loan status label: lent wins over a pending loan, which wins over available"""
    statuses = dict.fromkeys(tool_ids, AVAILABLE)
    if not tool_ids:
        return statuses
    lent_until = {}
    rows = db.session.execute(
        select(Loan.tool_id, Loan.status, Loan.end_date).where(
            Loan.tool_id.in_(tool_ids), _blocking_loan()
        )
    )
    for tool_id, status, end_date in rows:
        if status == LoanStatus.LENT:
            lent_until[tool_id] = max(end_date, lent_until.get(tool_id, end_date))
        else:
            statuses[tool_id] = PENDING
    for tool_id, end_date in lent_until.items():
        statuses[tool_id] = f"Prêté jusqu'au {french_date(end_date)}"
    return statuses


def site_today():
    return datetime.now(SITE_TIMEZONE).date()


def short_description(description):
    if len(description) <= DESCRIPTION_MAX_LENGTH:
        return description
    return description[:DESCRIPTION_MAX_LENGTH] + "…"


def french_date(day):
    """3 novembre 2026"""
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _empty_message(user_id, owner, filtered):
    owner_id = owner.id if owner is not None else None
    if filtered and visible_tools(user_id, owner_id=owner_id):
        return NO_MATCH
    if owner is not None:
        return f"{owner.first_name} {owner.last_name} n'a encore aucun outil à prêter"
    if not has_contacts(user_id):
        return NO_CONTACT
    return NO_TOOL


def _relations_of(user_id):
    return or_(ContactRelation.user_a_id == user_id, ContactRelation.user_b_id == user_id)


def _contact_ids(user_id):
    other = case(
        (ContactRelation.user_a_id == user_id, ContactRelation.user_b_id),
        else_=ContactRelation.user_a_id,
    )
    return select(other).where(_relations_of(user_id))


def _blocking_loan():
    """A loan that keeps the tool from being borrowed now: lent, or pending and not over"""
    return or_(
        Loan.status == LoanStatus.LENT,
        and_(
            Loan.status.in_((LoanStatus.REQUESTED, LoanStatus.ACCEPTED)),
            Loan.end_date >= site_today(),
        ),
    )


def _text_search(text):
    """The condition a tool's name or description must meet, and the order of the matches"""
    name = func.unaccent(Tool.name, type_=String)
    description = func.unaccent(Tool.description, type_=String)
    pattern = func.unaccent("%" + _escape_like(text) + "%", type_=String)
    name_contains = name.ilike(pattern, escape="\\")
    description_contains = description.ilike(pattern, escape="\\")
    if len(text) < FUZZY_MIN_LENGTH:
        return or_(name_contains, description_contains), [name_contains.desc()]

    searched = func.unaccent(text, type_=String)
    name_score = func.word_similarity(searched, name)
    description_score = func.word_similarity(searched, description)
    condition = or_(
        name_contains,
        description_contains,
        name_score >= FUZZY_THRESHOLD,
        description_score >= FUZZY_THRESHOLD,
    )
    return condition, [name_contains.desc(), name_score.desc(), description_score.desc()]


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
