from datetime import date, timedelta
from typing import NamedTuple

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import catalog, photos
from app.extensions import db
from models.loan import Loan, LoanStatus
from models.tool import Tool

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

STATUS_LABELS = {
    LoanStatus.REQUESTED: "En attente",
    LoanStatus.ACCEPTED: "Acceptée",
    LoanStatus.REFUSED: "Refusée",
    LoanStatus.CANCELED: "Annulée",
    LoanStatus.LENT: "Prêté",
    LoanStatus.RETURNED: "Rendu",
}
EXPIRED = "Expirée"

bp = Blueprint("loans", __name__, url_prefix="/loans")


class LoanRow(NamedTuple):
    loan: Loan
    dates: str
    status: str
    pending: bool


@bp.app_context_processor
def inject_pending_loan_requests():
    if not current_user.is_authenticated:
        return {"pending_loan_requests": 0}
    my_tools = select(Tool.id).where(Tool.owner_id == current_user.id)
    return {"pending_loan_requests": catalog.count_pending_requests(Loan.tool_id.in_(my_tools))}


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
    dates, error = _read_dates(values)
    if error is None and len(values["message"]) > MESSAGE_MAX_LENGTH:
        error = MESSAGE_TOO_LONG
    if error is not None:
        flash(error)
        return _render_confirm(tool, values, origin)
    if not catalog.is_available(tool.id):
        return _back_from_unavailable(tool, origin)

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
    received = db.session.scalars(
        select(Loan)
        .join(Tool, Loan.tool_id == Tool.id)
        .options(joinedload(Loan.tool), joinedload(Loan.borrower))
        .where(Tool.owner_id == current_user.id)
        .order_by(Loan.start_date.desc(), Loan.id.desc())
    ).all()
    sent = db.session.scalars(
        select(Loan)
        .options(joinedload(Loan.tool).joinedload(Tool.owner))
        .where(Loan.borrower_id == current_user.id)
        .order_by(Loan.start_date.desc(), Loan.id.desc())
    ).all()
    return render_template(
        "loans/mine.html",
        received=[_row(loan) for loan in received],
        sent=[_row(loan) for loan in sent],
    )


@bp.route("/<int:loan_id>/accept", methods=["POST"])
@login_required
def accept(loan_id):
    loan = _pending_loan(loan_id, owner=True)
    if loan is None:
        return _back_from_answered_request()
    loan.status = LoanStatus.ACCEPTED
    try:
        db.session.commit()
    except IntegrityError:
        # Another committed loan of the tool shares a day with this one.
        db.session.rollback()
        flash(DATES_TAKEN)
    return redirect(url_for("loans.mine"))


@bp.route("/<int:loan_id>/refuse", methods=["POST"])
@login_required
def refuse(loan_id):
    loan = _pending_loan(loan_id, owner=True)
    if loan is None:
        return _back_from_answered_request()
    loan.status = LoanStatus.REFUSED
    db.session.commit()
    return redirect(url_for("loans.mine"))


@bp.route("/<int:loan_id>/withdraw", methods=["POST"])
@login_required
def withdraw(loan_id):
    loan = _pending_loan(loan_id, owner=False)
    if loan is None:
        return _back_from_answered_request()
    loan.status = LoanStatus.CANCELED
    db.session.commit()
    return redirect(url_for("loans.mine"))


def _render_confirm(tool, values, origin):
    return render_template(
        "loans/confirm.html",
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


def _back_from_unavailable(tool, origin):
    flash(NOT_AVAILABLE)
    return redirect(_origin_url(origin, tool))


def _pending_loan(loan_id, owner):
    """The loan, locked until commit, if still pending; 404 unless it is the user's to answer"""
    loan = db.session.execute(
        select(Loan).where(Loan.id == loan_id).with_for_update()
    ).scalar_one_or_none()
    if loan is None:
        abort(404)
    actor_id = loan.tool.owner_id if owner else loan.borrower_id
    if actor_id != current_user.id:
        abort(404)
    if not _is_pending(loan):
        return None
    return loan


def _is_pending(loan):
    return loan.status == LoanStatus.REQUESTED and loan.start_date >= catalog.site_today()


def _row(loan):
    pending = _is_pending(loan)
    expired = loan.status == LoanStatus.REQUESTED and not pending
    dates = f"du {catalog.french_date(loan.start_date)} au {catalog.french_date(loan.end_date)}"
    status = EXPIRED if expired else STATUS_LABELS[loan.status]
    return LoanRow(loan=loan, dates=dates, status=status, pending=pending)


def _back_from_answered_request():
    """Where Back or a second submit lands once a request is answered, withdrawn or expired"""
    flash(NO_LONGER_PENDING)
    return redirect(url_for("loans.mine"))
