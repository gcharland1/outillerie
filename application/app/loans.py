from datetime import date, timedelta
from typing import NamedTuple

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import catalog, photos
from app.extensions import db
from models.loan import Loan, LoanStatus
from models.tool import Tool
from models.user import User

MAX_LEAD_DAYS = 14
MAX_LOAN_DAYS = 30
MESSAGE_MAX_LENGTH = Loan.message.type.length

INVALID_DATES = "Indiquez des dates valides"
START_IN_PAST = "La date de début ne peut pas être passée"
START_TOO_FAR = f"La date de début doit être dans les {MAX_LEAD_DAYS} prochains jours"
END_BEFORE_START = "La date de fin ne peut pas précéder la date de début"
TOO_LONG = f"Un prêt dure au plus {MAX_LOAN_DAYS} jours"
MESSAGE_TOO_LONG = f"Le message ne doit pas dépasser {MESSAGE_MAX_LENGTH} caractères"
NOT_AVAILABLE = "Cet outil n'est plus disponible"
NO_LONGER_PENDING = "Cette demande n'est plus en attente"
DATES_TAKEN = "Ces dates ne sont plus libres"
STATUS_CHANGED = "Ce prêt a déjà changé de statut"

STATUS_LABELS = {
    LoanStatus.REQUESTED: "En attente",
    LoanStatus.ACCEPTED: "Attente de récupération",
    LoanStatus.HANDOVER_CLAIMED: "Remise à confirmer",
    LoanStatus.LENT: "Prêté",
    LoanStatus.RETURN_CLAIMED: "Retour à confirmer",
    LoanStatus.RETURNED: "Complété",
    LoanStatus.REFUSED: "Refusée",
    LoanStatus.CANCELED: "Annulée",
}
EXPIRED = "Expirée"
OVERDUE = "En retard"
RECEIVED = "J'ai reçu l'outil"
CONFIRM_RECEIPT = "Confirmer la réception"

bp = Blueprint("loans", __name__, url_prefix="/loans")


class Button(NamedTuple):
    action: str
    label: str
    style: str


class LoanRow(NamedTuple):
    loan: Loan
    other: User
    dates: str
    status: str
    history: list[str]
    overdue: bool
    buttons: list[Button]


class Transition(NamedTuple):
    by_owner: bool
    sources: tuple[LoanStatus, ...]
    target: LoanStatus
    stamp: str | None = None


S = LoanStatus
# Who may move a loan from which statuses with each action: whoever gives the tool claims it,
# whoever receives it confirms, answers "Pas reçu", or records it without a claim.
ACTIONS = {
    "accept": [Transition(True, (S.REQUESTED,), S.ACCEPTED)],
    "refuse": [Transition(True, (S.REQUESTED,), S.REFUSED)],
    "withdraw": [Transition(False, (S.REQUESTED,), S.CANCELED)],
    "hand-over": [Transition(True, (S.ACCEPTED,), S.HANDOVER_CLAIMED)],
    "receive": [Transition(False, (S.ACCEPTED, S.HANDOVER_CLAIMED), S.LENT, "lent_at")],
    "give-back": [Transition(False, (S.LENT,), S.RETURN_CLAIMED)],
    "take-back": [Transition(True, (S.LENT, S.RETURN_CLAIMED), S.RETURNED, "returned_at")],
    "not-received": [
        Transition(False, (S.HANDOVER_CLAIMED,), S.ACCEPTED),
        Transition(True, (S.RETURN_CLAIMED,), S.LENT),
    ],
    "cancel": [
        Transition(True, (S.ACCEPTED,), S.CANCELED),
        Transition(False, (S.ACCEPTED,), S.CANCELED),
    ],
}
REQUEST_ACTIONS = {"accept", "refuse", "withdraw"}
# The buttons of "Mes prêts", in the order they are shown; cancelling opens its own page.
BUTTONS = (
    Button("refuse", "Refuser", "error"),
    Button("accept", "Accepter", "success"),
    Button("withdraw", "Retirer ma demande", "error"),
    Button("cancel", "Annuler le prêt", "error"),
    Button("not-received", "Pas reçu", "error"),
    Button("hand-over", "J'ai remis l'outil", "primary"),
    Button("receive", RECEIVED, "primary"),
    Button("give-back", "J'ai rendu l'outil", "primary"),
    Button("take-back", RECEIVED, "primary"),
)


@bp.app_context_processor
def inject_loan_actions():
    """How many loans wait for the user: answers and confirmations to give, overdue loans"""
    if not current_user.is_authenticated:
        return {"loan_actions": 0}
    my_tools = select(Tool.id).where(Tool.owner_id == current_user.id)
    as_owner = and_(
        Loan.tool_id.in_(my_tools),
        or_(
            catalog.pending_request(),
            Loan.status == LoanStatus.RETURN_CLAIMED,
            catalog.overdue_loan(),
        ),
    )
    as_borrower = and_(
        Loan.borrower_id == current_user.id,
        or_(Loan.status == LoanStatus.HANDOVER_CLAIMED, catalog.overdue_loan()),
    )
    count = db.session.scalar(
        select(func.count()).select_from(Loan).where(or_(as_owner, as_borrower))
    )
    return {"loan_actions": count}


@bp.route("/new/<int:tool_id>", methods=["GET"])
@login_required
def new(tool_id):
    tool = _requestable_tool(tool_id)
    origin = _origin(request.args)
    if not catalog.is_available(tool.id):
        return _back_from_unavailable(tool, origin)
    values = {"start": catalog.site_today().isoformat(), "end": "", "message": ""}
    return _render_confirm(tool, values, origin)


@bp.route("/new/<int:tool_id>", methods=["POST"])
@login_required
def create(tool_id):
    # Serializes concurrent requests for the tool until commit.
    db.session.execute(select(Tool.id).where(Tool.id == tool_id).with_for_update())
    tool = _requestable_tool(tool_id)
    origin = _origin(request.form)
    values = {
        "start": request.form.get("start", "").strip(),
        "end": request.form.get("end", "").strip(),
        "message": request.form.get("message", "").replace("\r\n", "\n").strip(),
    }
    if not catalog.is_available(tool.id):
        return _back_from_unavailable(tool, origin)
    dates, error = _read_dates(values)
    if error is None and len(values["message"]) > MESSAGE_MAX_LENGTH:
        error = MESSAGE_TOO_LONG
    if error is not None:
        flash(error)
        return _render_confirm(tool, values, origin)

    start, end = dates
    db.session.add(
        Loan(
            tool_id=tool.id,
            borrower_id=current_user.id,
            start_date=start,
            end_date=end,
            message=values["message"] or None,
        )
    )
    db.session.commit()
    flash(f"Demande envoyée à {tool.owner.first_name} {tool.owner.last_name}", "success")
    return redirect(_origin_url(origin, tool))


@bp.route("")
@login_required
def mine():
    today = catalog.site_today()
    received = db.session.scalars(
        select(Loan)
        .join(Tool, Loan.tool_id == Tool.id)
        .options(joinedload(Loan.tool), joinedload(Loan.borrower))
        .where(Tool.owner_id == current_user.id)
        .order_by(Loan.created_at.desc(), Loan.id.desc())
    ).all()
    sent = db.session.scalars(
        select(Loan)
        .options(joinedload(Loan.tool).joinedload(Tool.owner))
        .where(Loan.borrower_id == current_user.id)
        .order_by(Loan.created_at.desc(), Loan.id.desc())
    ).all()
    return render_template(
        "loans/mine.html",
        lent=_rows(received, by_owner=True, today=today),
        borrowed=_rows(sent, by_owner=False, today=today),
    )


@bp.route("/<int:loan_id>/cancel", methods=["GET"])
@login_required
def confirm_cancel(loan_id):
    loan, transition = _loan_for(loan_id, "cancel", lock=False)
    if transition is None:
        flash(STATUS_CHANGED)
        return redirect(url_for("loans.mine"))
    other = loan.borrower if loan.tool.owner_id == current_user.id else loan.lender
    return render_template("loans/confirm_cancel.html", loan=loan, other=other, dates=_dates(loan))


@bp.route("/<int:loan_id>/<action>", methods=["POST"])
@login_required
def act(loan_id, action):
    if action not in ACTIONS:
        abort(404)
    loan, transition = _loan_for(loan_id, action)
    if transition is None:
        flash(NO_LONGER_PENDING if action in REQUEST_ACTIONS else STATUS_CHANGED)
        return redirect(url_for("loans.mine"))
    target = transition.target
    if action == "not-received" and target == LoanStatus.ACCEPTED and not _still_lendable(loan):
        # The cascade spared the claimed handover; once disputed, it would have cancelled it.
        target = LoanStatus.CANCELED
    loan.status = target
    if transition.stamp is not None:
        setattr(loan, transition.stamp, func.now())
    try:
        db.session.commit()
    except IntegrityError:
        # Only an acceptance changes which days are taken: another committed loan has one of them.
        db.session.rollback()
        flash(DATES_TAKEN)
    return redirect(url_for("loans.mine"))


def _still_lendable(loan):
    """Whether the tool is still in circulation and both people still contacts"""
    return catalog.visible_tool(loan.borrower_id, loan.tool_id) is not None


def _render_confirm(tool, values, origin):
    today = catalog.site_today()
    return render_template(
        "loans/confirm.html",
        bounds={
            "first": today.isoformat(),
            "last_start": (today + timedelta(days=MAX_LEAD_DAYS)).isoformat(),
            "last_end": (today + timedelta(days=MAX_LEAD_DAYS + MAX_LOAN_DAYS - 1)).isoformat(),
        },
        tool=tool,
        has_photo=bool(photos.tool_ids_with_photo([tool.id])),
        condition=catalog.CONDITION_LABELS[tool.condition],
        values=values,
        origin=origin,
        back_url=_origin_url(origin, tool),
        message_max_length=MESSAGE_MAX_LENGTH,
    )


def _requestable_tool(tool_id):
    """A contact's tool the user may request; the same 404 for anything else"""
    tool = catalog.visible_tool(current_user.id, tool_id)
    if tool is None:
        abort(404)
    return tool


def _read_dates(values):
    """The requested first and last days, and the message refusing them, if any"""
    try:
        start = date.fromisoformat(values["start"])
        end = date.fromisoformat(values["end"])
    except ValueError:
        return None, INVALID_DATES
    today = catalog.site_today()
    if start < today:
        return None, START_IN_PAST
    if start > today + timedelta(days=MAX_LEAD_DAYS):
        return None, START_TOO_FAR
    if end < start:
        return None, END_BEFORE_START
    if (end - start).days + 1 > MAX_LOAN_DAYS:
        return None, TOO_LONG
    return (start, end), None


def _origin(params):
    """The list a request was started from, as a fixed set of values, never a URL"""
    return {
        "origin": "contact" if params.get("origin") == "contact" else "find",
        "q": params.get("q", "").strip(),
        "available": "1" if params.get("available") == "1" else "",
    }


def _origin_url(origin, tool):
    filters = {"q": origin["q"] or None, "available": origin["available"] or None}
    if origin["origin"] == "contact" and catalog.is_contact(current_user.id, tool.owner_id):
        return url_for("contacts.show", user_id=tool.owner_id, **filters)
    return url_for("tools.find", **filters)


def _dates(loan):
    return f"{catalog.french_date(loan.start_date)} au {catalog.french_date(loan.end_date)}"


def _back_from_unavailable(tool, origin):
    flash(NOT_AVAILABLE)
    return redirect(_origin_url(origin, tool))


def _loan_for(loan_id, action, lock=True):
    """The loan, locked until commit unless told not to, and the transition the user may make now

    404 unless the user is the actor of one of the action's transitions; no transition if the
    loan's status no longer allows it.
    """
    query = select(Loan).where(Loan.id == loan_id)
    if lock:
        query = query.with_for_update()
    loan = db.session.execute(query).scalar_one_or_none()
    if loan is None:
        abort(404)
    is_owner = loan.tool.owner_id == current_user.id
    if not is_owner and loan.borrower_id != current_user.id:
        abort(404)
    transitions = [t for t in ACTIONS[action] if t.by_owner == is_owner]
    if not transitions:
        abort(404)
    today = catalog.site_today()
    allowed = [t for t in transitions if _allows(t, loan, today)]
    return loan, allowed[0] if allowed else None


def _allows(transition, loan, today):
    if loan.status not in transition.sources:
        return False
    if loan.status == LoanStatus.REQUESTED:
        return loan.start_date >= today
    if loan.status == LoanStatus.ACCEPTED:
        return loan.end_date >= today
    return True


def _rows(loans, by_owner, today):
    """Overdue loans first, oldest last day first, then loans the user can act on"""
    rows = [_row(loan, by_owner, today) for loan in loans]
    return sorted(
        rows,
        key=lambda row: (
            not row.overdue,
            row.loan.end_date if row.overdue else date.min,
            not row.buttons,
        ),
    )


def _row(loan, by_owner, today):
    overdue = loan.status in catalog.HANDED_OVER and loan.end_date < today
    expired = (loan.status == LoanStatus.REQUESTED and loan.start_date < today) or (
        loan.status == LoanStatus.ACCEPTED and loan.end_date < today
    )
    if overdue:
        status = OVERDUE
    elif expired:
        status = EXPIRED
    else:
        status = STATUS_LABELS[loan.status]
    return LoanRow(
        loan=loan,
        other=loan.borrower if by_owner else loan.lender,
        dates=f"du {_dates(loan)}",
        status=status,
        history=_history(loan),
        overdue=overdue,
        buttons=[
            _button(button, loan)
            for button in BUTTONS
            if _may(button.action, loan, by_owner, today)
        ],
    )


def _may(action, loan, by_owner, today):
    return any(t.by_owner == by_owner and _allows(t, loan, today) for t in ACTIONS[action])


def _button(button, loan):
    if button.action in ("receive", "take-back") and loan.status in (
        LoanStatus.HANDOVER_CLAIMED,
        LoanStatus.RETURN_CLAIMED,
    ):
        return button._replace(label=CONFIRM_RECEIPT)
    return button


def _history(loan):
    def on(moment):
        return catalog.french_date(moment.astimezone(catalog.SITE_TIMEZONE).date())

    history = []
    if loan.lent_at is not None:
        history.append(f"Prêté le {on(loan.lent_at)}")
    if loan.returned_at is not None:
        history.append(f"Complété le {on(loan.returned_at)}")
    return history
