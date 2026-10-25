from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from models.contact import ContactRelation, ContactRequest
from models.user import User

NO_LONGER_PENDING = "Cette demande n'est plus en attente"
NOT_A_CONTACT = "Cette personne ne fait pas partie de vos contacts"

bp = Blueprint("contacts", __name__, url_prefix="/contacts")


@bp.app_context_processor
def inject_pending_contact_requests():
    if not current_user.is_authenticated:
        return {"pending_contact_requests": 0}
    count = db.session.scalar(
        select(func.count())
        .select_from(ContactRequest)
        .where(ContactRequest.recipient_id == current_user.id)
    )
    return {"pending_contact_requests": count}


@bp.route("")
@login_required
def mine():
    received = db.session.scalars(
        select(ContactRequest)
        .options(joinedload(ContactRequest.requester))
        .where(ContactRequest.recipient_id == current_user.id)
        .order_by(ContactRequest.created_at, ContactRequest.id)
    ).all()
    return render_template("contacts/mine.html", received=received, contacts=_my_contacts())


@bp.route("/requests", methods=["POST"])
@login_required
def send_request():
    recipient = db.session.get(User, request.form.get("recipient_id", type=int) or 0)
    if recipient is None or recipient.id == current_user.id:
        abort(404)
    back_to_search = redirect(url_for("search.results", type="user", q=request.form.get("q", "")))

    state = relation_states([recipient.id])[recipient.id]
    if state == "received":
        return redirect(url_for("contacts.mine"))
    if state in ("sent", "contact"):
        return back_to_search

    db.session.add(ContactRequest(requester_id=current_user.id, recipient_id=recipient.id))
    try:
        db.session.commit()
    except IntegrityError:
        # Another request for the pair was committed meanwhile; the next page shows it.
        db.session.rollback()
    return back_to_search


@bp.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept(request_id):
    contact_request = _received_request(request_id)
    if contact_request is None:
        return _back_from_answered_request()
    db.session.add(ContactRelation.between(contact_request.requester_id, current_user.id))
    db.session.delete(contact_request)
    db.session.commit()
    return redirect(url_for("contacts.mine"))


@bp.route("/requests/<int:request_id>/refuse", methods=["POST"])
@login_required
def refuse(request_id):
    contact_request = _received_request(request_id)
    if contact_request is None:
        return _back_from_answered_request()
    db.session.delete(contact_request)
    db.session.commit()
    return redirect(url_for("contacts.mine"))


@bp.route("/<int:user_id>/remove", methods=["GET"])
@login_required
def confirm_remove(user_id):
    contact, relation = _contact_relation(user_id)
    if relation is None:
        return _back_from_not_a_contact()
    return render_template("contacts/confirm_remove.html", contact=contact)


@bp.route("/<int:user_id>/remove", methods=["POST"])
@login_required
def remove(user_id):
    _, relation = _contact_relation(user_id)
    if relation is None:
        return _back_from_not_a_contact()
    db.session.delete(relation)
    db.session.commit()
    return redirect(url_for("contacts.mine"))


def relation_states(user_ids):
    """Each user's relation to the current user: none, sent, received or contact"""
    if not user_ids:
        return {}
    me = current_user.id
    sent = db.session.scalars(
        select(ContactRequest.recipient_id).where(
            ContactRequest.requester_id == me, ContactRequest.recipient_id.in_(user_ids)
        )
    ).all()
    received = db.session.scalars(
        select(ContactRequest.requester_id).where(
            ContactRequest.recipient_id == me, ContactRequest.requester_id.in_(user_ids)
        )
    ).all()
    relations = db.session.execute(
        select(ContactRelation.user_a_id, ContactRelation.user_b_id).where(
            or_(
                and_(ContactRelation.user_a_id == me, ContactRelation.user_b_id.in_(user_ids)),
                and_(ContactRelation.user_b_id == me, ContactRelation.user_a_id.in_(user_ids)),
            )
        )
    ).all()
    states = dict.fromkeys(user_ids, "none")
    states.update(dict.fromkeys(sent, "sent"))
    states.update(dict.fromkeys(received, "received"))
    states.update({a if b == me else b: "contact" for a, b in relations})
    return states


def _my_contacts():
    """The current user's contacts, by username regardless of case"""
    me = current_user.id
    return db.session.scalars(
        select(User)
        .join(
            ContactRelation,
            or_(
                and_(ContactRelation.user_a_id == me, ContactRelation.user_b_id == User.id),
                and_(ContactRelation.user_b_id == me, ContactRelation.user_a_id == User.id),
            ),
        )
        .order_by(func.lower(User.username), User.id)
    ).all()


def _received_request(request_id):
    """The request, locked until commit, if still pending; 404 if addressed to someone else"""
    contact_request = db.session.execute(
        select(ContactRequest).where(ContactRequest.id == request_id).with_for_update()
    ).scalar_one_or_none()
    if contact_request is not None and contact_request.recipient_id != current_user.id:
        abort(404)
    return contact_request


def _contact_relation(user_id):
    """A user and their relation to the current user, if any; 404 for an unknown user"""
    contact = db.session.get(User, user_id)
    if contact is None:
        abort(404)
    relation = db.session.get(ContactRelation, ContactRelation.pair(current_user.id, contact.id))
    return contact, relation


def _back_from_answered_request():
    """Where Back or a second submit lands once a request is answered and gone"""
    flash(NO_LONGER_PENDING)
    return redirect(url_for("contacts.mine"))


def _back_from_not_a_contact():
    flash(NOT_A_CONTACT)
    return redirect(url_for("contacts.mine"))
