"""The user's own account: address and phone, and its deletion by anonymization (ADR 0023)."""

import math
import re
import secrets
from typing import NamedTuple

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

from app import catalog, email_confirmation, loans, photos, text_search
from app.extensions import db
from models.contact import ContactRelation, ContactRequest
from models.loan import Loan
from models.tool import Tool
from models.user import User

ADDRESS_MAX_LENGTH = User.address.type.length
PHONE_MAX_LENGTH = User.phone.type.length
PHONE_CHARACTERS = re.compile(r"[0-9 +\-().]*")

SAVED = "Votre profil a été enregistré"
ADDRESS_TOO_LONG = f"L'adresse ne doit pas dépasser {ADDRESS_MAX_LENGTH} caractères"
PHONE_TOO_LONG = f"Le téléphone ne doit pas dépasser {PHONE_MAX_LENGTH} caractères"
PHONE_INVALID = (
    "Le téléphone ne peut contenir que des chiffres, des espaces et les caractères + - ( ) ."
)
LOANS_IN_PROGRESS = "Tous vos prêts en cours doivent être complétés avant de supprimer votre compte"
MISMATCH = "Le nom ou le mot de passe ne correspond pas"

bp = Blueprint("profile", __name__, url_prefix="/profile")


class LoanInProgress(NamedTuple):
    tool: Tool
    other: User
    status: str


@bp.app_context_processor
def inject_email_to_confirm():
    """1 while the logged-in user has not confirmed their email, for the menu's badge"""
    unconfirmed = current_user.is_authenticated and not current_user.email_confirmed
    return {"email_to_confirm": 1 if unconfirmed else 0}


@bp.route("")
@login_required
def show():
    values = {"address": current_user.address or "", "phone": current_user.phone or ""}
    return _render_show(values)


@bp.route("", methods=["POST"])
@login_required
def save():
    # Only these two fields: a submitted name or email is ignored.
    values = {field: request.form.get(field, "").strip() for field in ("address", "phone")}
    errors = _profile_errors(values)
    if errors:
        for error in errors:
            flash(error)
        return _render_show(values)
    # Not the object load_user read: a deletion holding the account's lock must win.
    result = db.session.execute(
        update(User)
        .where(User.id == current_user.id, User.deleted_at.is_(None))
        .values(address=values["address"] or None, phone=values["phone"] or None)
        .execution_options(synchronize_session=False)
    )
    db.session.commit()
    if result.rowcount == 0:
        logout_user()
        return redirect(url_for("auth.login"))
    flash(SAVED, "success")
    return redirect(url_for("profile.show"))


@bp.route("/courriel/renvoyer", methods=["POST"])
@login_required
def resend_confirmation():
    # Locked until commit: of two resends at once, only one sends.
    account = db.session.scalar(
        select(User)
        .where(User.id == current_user.id, User.deleted_at.is_(None))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None:
        logout_user()
        return redirect(url_for("auth.login"))
    if account.email_confirmed:
        db.session.rollback()
        flash(email_confirmation.ALREADY_CONFIRMED)
        return redirect(url_for("profile.show"))
    # Not now(), the transaction start: a concurrent resend may have committed since.
    now = db.session.scalar(select(func.clock_timestamp()))
    sent_at = account.email_confirmation_sent_at
    if sent_at is not None and now - sent_at < email_confirmation.RESEND_DELAY:
        db.session.rollback()
        remaining = email_confirmation.RESEND_DELAY - (now - sent_at)
        flash(email_confirmation.TOO_SOON.format(minutes=math.ceil(remaining.total_seconds() / 60)))
        return redirect(url_for("profile.show"))
    account.email_confirmation_sent_at = now
    db.session.commit()
    email_confirmation.send_link(account)
    flash(email_confirmation.SENT.format(email=account.email), "success")
    return redirect(url_for("profile.show"))


@bp.route("/delete", methods=["GET"])
@login_required
def confirm_delete():
    if loans_in_progress(current_user.id):
        flash(LOANS_IN_PROGRESS)
        return redirect(url_for("profile.show"))
    return _render_confirm_delete(name="")


@bp.route("/delete", methods=["POST"])
@login_required
def delete_account():
    name = request.form.get("name", "")
    if not (
        _is_full_name(name)
        and check_password_hash(current_user.password, request.form.get("password", ""))
    ):
        flash(MISMATCH)
        return _render_confirm_delete(name)

    me = current_user.id
    # The account first, as every write linking two accounts does, then its tools and loans.
    deleted_at = db.session.scalar(select(User.deleted_at).where(User.id == me).with_for_update())
    if deleted_at is not None:
        # Sent twice: the first deletion is done, the account is not anonymized again.
        db.session.rollback()
        return _logged_out_after_deletion()
    db.session.execute(
        select(Tool.id).where(Tool.owner_id == me).order_by(Tool.id).with_for_update()
    )
    db.session.execute(select(Loan.id).where(_involving(me)).order_by(Loan.id).with_for_update())
    if db.session.scalar(select(exists().where(_involving(me), Loan.status.in_(catalog.OUT)))):
        db.session.rollback()
        flash(LOANS_IN_PROGRESS)
        return redirect(url_for("profile.show"))

    catalog.cancel_unstarted_loans(_involving(me))
    db.session.execute(
        update(Loan)
        .where(Loan.borrower_id == me)
        .values(message=None)
        .execution_options(synchronize_session=False)
    )
    for tool in db.session.scalars(select(Tool).where(Tool.owner_id == me)).all():
        tool.is_active = False
        tool.description = ""
        tool.private_notes = None
        photos.remove_photo(tool)
    db.session.execute(
        delete(ContactRequest).where(
            or_(ContactRequest.requester_id == me, ContactRequest.recipient_id == me)
        )
    )
    db.session.execute(
        delete(ContactRelation).where(
            or_(ContactRelation.user_a_id == me, ContactRelation.user_b_id == me)
        )
    )
    account = db.session.get(User, me)
    account.email = None
    account.address = None
    account.phone = None
    # A hash in the expected format of a secret thrown away: no password ever matches it.
    account.password = generate_password_hash(secrets.token_urlsafe(32))
    account.deleted_at = func.now()
    db.session.commit()
    return _logged_out_after_deletion()


def _logged_out_after_deletion():
    logout_user()
    session.clear()
    return redirect(url_for("auth.logged_out", reason="account-deleted"))


def loans_in_progress(user_id):
    """The user's loans whose tool may be away, as borrower or lender: they block a deletion"""
    rows = db.session.execute(
        select(Loan, catalog.overdue_loan())
        .options(joinedload(Loan.tool).joinedload(Tool.owner), joinedload(Loan.borrower))
        .where(_involving(user_id), Loan.status.in_(catalog.OUT))
        .order_by(Loan.end_date, Loan.id)
    ).all()
    return [
        LoanInProgress(
            tool=loan.tool,
            other=loan.tool.owner if loan.borrower_id == user_id else loan.borrower,
            status=loans.OVERDUE if overdue else loans.STATUS_LABELS[loan.status],
        )
        for loan, overdue in rows
    ]


def _involving(user_id):
    """Loans where the user is the borrower or the lender"""
    return or_(
        Loan.borrower_id == user_id,
        Loan.tool_id.in_(select(Tool.id).where(Tool.owner_id == user_id)),
    )


def _profile_errors(values):
    errors = []
    if len(values["address"]) > ADDRESS_MAX_LENGTH:
        errors.append(ADDRESS_TOO_LONG)
    if len(values["phone"]) > PHONE_MAX_LENGTH:
        errors.append(PHONE_TOO_LONG)
    if not PHONE_CHARACTERS.fullmatch(values["phone"]):
        errors.append(PHONE_INVALID)
    return errors


def _is_full_name(name):
    """Whether the name is the user's first then last name, as names are compared (ADR 0018)"""
    typed = text_search.sort_key(name)
    full_name = text_search.sort_key(User.first_name + " " + User.last_name)
    return db.session.scalar(
        select(exists().where(User.id == current_user.id, typed != "", typed == full_name))
    )


def _render_show(values):
    return render_template(
        "profile/show.html", values=values, loans_in_progress=loans_in_progress(current_user.id)
    )


def _render_confirm_delete(name):
    involving = _involving(current_user.id)
    return render_template(
        "profile/confirm_delete.html",
        name=name,
        cancel_notice=catalog.cancel_notice(
            catalog.count_pending_requests(involving),
            catalog.count_upcoming_acceptances(involving),
        ),
    )
