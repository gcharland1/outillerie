"""The tools a user sees among their contacts' tools, and how each one stands for a loan."""

from datetime import datetime
from typing import NamedTuple
from zoneinfo import ZoneInfo

from flask import url_for
from sqlalchemy import String, and_, case, exists, func, or_, select, update
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

# A claimed handover counts as done until the borrower answers "Pas reçu".
HANDED_OVER = (LoanStatus.HANDOVER_CLAIMED, LoanStatus.LENT)
# The tool may be with the borrower: it stays out until its return is confirmed.
OUT = (*HANDED_OVER, LoanStatus.RETURN_CLAIMED)

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
    requested_by_viewer: bool
    borrow_url: str | None


def tool_list(user_id, args, owner=None):
    """What a page listing tools needs: the filters read from its URL, the cards, or why none"""
    filters = {
        "text": args.get("q", "").strip(),
        "available_only": args.get("available") == "1",
    }
    owner_id = owner.id if owner is not None else None
    origin = {
        "origin": "contact" if owner is not None else "find",
        "q": filters["text"] or None,
        "available": "1" if filters["available_only"] else None,
    }
    tools = visible_tools(user_id, owner_id=owner_id, **filters)
    cards = tool_cards(tools, viewer_id=user_id, origin=origin)
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


def visible_tool(user_id, tool_id):
    """One of the contacts' tools the user may see, or None"""
    query = select(Tool).options(joinedload(Tool.owner)).where(Tool.id == tool_id)
    return db.session.scalars(query.where(_visible(user_id))).one_or_none()


def is_available(tool_id):
    """Whether no loan keeps the tool from being requested now"""
    return not db.session.scalar(select(exists().where(Loan.tool_id == tool_id, blocking_loan())))


def count_pending_requests(*conditions):
    """How many unexpired requests meet these conditions on Loan"""
    return _count(pending_request(), *conditions)


def count_upcoming_acceptances(*conditions):
    """How many accepted loans, not handed over nor expired, meet these conditions on Loan"""
    return _count(upcoming_acceptance(), *conditions)


def cancel_unstarted_loans(*conditions):
    """Cancels unexpired requests and acceptances meeting these conditions; the caller commits"""
    db.session.execute(
        update(Loan)
        .where(or_(pending_request(), upcoming_acceptance()), *conditions)
        .values(status=LoanStatus.CANCELED)
        .execution_options(synchronize_session=False)
    )


def _count(*conditions):
    return db.session.scalar(select(func.count()).select_from(Loan).where(*conditions))


def requests_for_tool(tool_id):
    return Loan.tool_id == tool_id


def requests_between(user_id, other_id):
    """Requests of either user for a tool of the other"""

    def tools_of(owner_id):
        return select(Tool.id).where(Tool.owner_id == owner_id)

    return or_(
        and_(Loan.borrower_id == user_id, Loan.tool_id.in_(tools_of(other_id))),
        and_(Loan.borrower_id == other_id, Loan.tool_id.in_(tools_of(user_id))),
    )


def cancel_notice(requests, acceptances=0, between=False):
    """What a confirmation page says about the requests and loans its action will cancel"""

    def plural(count):
        return "s" if count > 1 else ""

    parts = []
    if requests:
        parts.append(f"{requests} demande{plural(requests)} d'emprunt en attente")
    if acceptances:
        parts.append(f"{acceptances} prêt{plural(acceptances)} accepté{plural(acceptances)}")
    if not parts:
        return None
    where = " entre vous" if between else ""
    if len(parts) == 2:
        return f"{parts[0]} et {parts[1]}{where} seront annulés"
    count = requests or acceptances
    verb = "seront" if count > 1 else "sera"
    return f"{parts[0]}{where} {verb} annulé{'e' if requests else ''}{plural(count)}"


def has_contacts(user_id):
    return db.session.scalar(select(exists().where(_relations_of(user_id))))


def visible_tools(user_id, owner_id=None, text="", available_only=False):
    """The contacts' tools the user may see, filtered and ordered as the spec says"""
    query = select(Tool).options(joinedload(Tool.owner)).where(_visible(user_id))
    if owner_id is not None:
        query = query.where(Tool.owner_id == owner_id)
    if available_only:
        query = query.where(~exists().where(Loan.tool_id == Tool.id, blocking_loan()))
    if text:
        condition, ordering = _text_search(text)
        query = query.where(condition).order_by(*ordering)
    return db.session.scalars(query.order_by(func.lower(Tool.name), Tool.id)).all()


def tool_cards(tools, viewer_id=None, origin=None):
    """What each tool's card shows, with statuses and photos read in one query each"""
    tool_ids = [tool.id for tool in tools]
    statuses, requested_by_viewer = _loan_states(tool_ids, viewer_id)
    photo_ids = photos.tool_ids_with_photo(tool_ids)
    return [
        ToolCard(
            tool=tool,
            has_photo=tool.id in photo_ids,
            description=short_description(tool.description),
            condition=CONDITION_LABELS[tool.condition],
            status=statuses[tool.id],
            available=statuses[tool.id] == AVAILABLE,
            requested_by_viewer=tool.id in requested_by_viewer,
            borrow_url=url_for("loans.new", tool_id=tool.id, **origin) if origin else None,
        )
        for tool in tools
    ]


def loan_statuses(tool_ids):
    """Each tool's loan status label: lent wins over a pending loan, which wins over available"""
    return _loan_states(tool_ids, viewer_id=None)[0]


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


def pending_request():
    """A request still awaiting an answer: it expires once its first day is over"""
    return and_(Loan.status == LoanStatus.REQUESTED, Loan.start_date >= site_today())


def upcoming_acceptance():
    """An accepted loan not handed over whose last day has not passed"""
    return and_(Loan.status == LoanStatus.ACCEPTED, Loan.end_date >= site_today())


def expired_acceptance():
    """An accepted loan whose last day passed without the tool being handed over"""
    return and_(Loan.status == LoanStatus.ACCEPTED, Loan.end_date < site_today())


def overdue_loan():
    """A loan whose tool is with the borrower past its last day, until a return is claimed"""
    return and_(Loan.status.in_(HANDED_OVER), Loan.end_date < site_today())


def blocking_loan():
    """A loan that keeps the tool from being requested now: out, accepted and not over, pending"""
    return or_(
        Loan.status.in_(OUT),
        upcoming_acceptance(),
        pending_request(),
    )


def _visible(user_id):
    return and_(
        Tool.is_active,
        Tool.condition != ToolCondition.OUT_OF_ORDER,
        Tool.owner_id.in_(_contact_ids(user_id)),
    )


def _loan_states(tool_ids, viewer_id):
    """Each tool's status label, and which tools the viewer has a pending request for"""
    statuses = dict.fromkeys(tool_ids, AVAILABLE)
    requested_by_viewer = set()
    if not tool_ids:
        return statuses, requested_by_viewer
    lent_until = {}
    rows = db.session.execute(
        select(Loan.tool_id, Loan.status, Loan.end_date, Loan.borrower_id).where(
            Loan.tool_id.in_(tool_ids), blocking_loan()
        )
    )
    for tool_id, status, end_date, borrower_id in rows:
        if status in OUT:
            lent_until[tool_id] = max(end_date, lent_until.get(tool_id, end_date))
            continue
        statuses[tool_id] = PENDING
        if status == LoanStatus.REQUESTED and borrower_id == viewer_id:
            requested_by_viewer.add(tool_id)
    for tool_id, end_date in lent_until.items():
        statuses[tool_id] = f"Prêté jusqu'au {french_date(end_date)}"
    return statuses, requested_by_viewer


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
