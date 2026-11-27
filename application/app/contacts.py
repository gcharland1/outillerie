from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import catalog, text_search
from app.extensions import db
from models.contact import ContactRelation, ContactRequest
from models.user import User

NO_LONGER_PENDING = "Cette demande n'est plus en attente"
NOT_A_CONTACT = "Cette personne ne fait pas partie de vos contacts"
REFUSED = "Demande refusée"
# A pending request, sent or received, is not a contact yet: it falls under "others".
RELATION_FILTERS = {
    "all": "Tous les utilisateurs",
    "contacts": "Mes contacts uniquement",
    "others": "Pas en contact uniquement",
}

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


@bp.app_context_processor
def inject_contact_ids():
    """Who the user's contacts are, so that a name links to the contact's page"""
    if not current_user.is_authenticated:
        return {"contact_ids": set()}
    return {"contact_ids": catalog.contact_ids(current_user.id)}


@bp.route("")
@login_required
def mine():
    return render_template(
        "contacts/mine.html",
        received=received_requests(current_user.id),
        contacts=_my_contacts(),
    )


def received_requests(user_id):
    """The requests waiting for the user's answer, oldest first"""
    return db.session.scalars(
        select(ContactRequest)
        .options(joinedload(ContactRequest.requester))
        .where(ContactRequest.recipient_id == user_id)
        .order_by(ContactRequest.created_at, ContactRequest.id)
    ).all()


def recent_contacts(user_id, since):
    """The users who became the user's contacts since then, newest first"""
    other = case(
        (ContactRelation.user_a_id == user_id, ContactRelation.user_b_id),
        else_=ContactRelation.user_a_id,
    )
    return db.session.scalars(
        select(User)
        .join(ContactRelation, User.id == other)
        .where(
            or_(ContactRelation.user_a_id == user_id, ContactRelation.user_b_id == user_id),
            ContactRelation.created_at >= since,
        )
        .order_by(ContactRelation.created_at.desc(), User.id)
    ).all()


@bp.route("/<int:user_id>")
@login_required
def show(user_id):
    """A contact's page; the same 404 for anyone who is not a contact"""
    contact = db.session.get(User, user_id)
    if (
        contact is None
        or contact.deleted_at is not None
        or not catalog.is_contact(current_user.id, contact.id)
    ):
        abort(404)
    page = catalog.tool_list(current_user.id, request.args, owner=contact)
    return render_template("contacts/show.html", contact=contact, **page)


@bp.route("/requests", methods=["POST"])
@login_required
def send_request():
    recipient_id = request.form.get("recipient_id", type=int) or 0
    if recipient_id == current_user.id or not lock_live_accounts(current_user.id, recipient_id):
        abort(404)
    back_to_search = redirect(search_results_url(request.form))

    state = relation_states([recipient_id])[recipient_id]
    if state == "received":
        return redirect(url_for("contacts.mine"))
    if state in ("sent", "contact"):
        return back_to_search

    db.session.add(ContactRequest(requester_id=current_user.id, recipient_id=recipient_id))
    try:
        db.session.commit()
    except IntegrityError:
        # Another request for the pair was committed meanwhile; the next page shows it.
        db.session.rollback()
    return back_to_search


@bp.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept(request_id):
    requester_id = db.session.scalar(
        select(ContactRequest.requester_id).where(ContactRequest.id == request_id)
    )
    if requester_id is not None:
        # Accounts before the request, as a deletion takes them; a deleted requester's is gone.
        lock_live_accounts(requester_id, current_user.id)
    contact_request = _received_request(request_id)
    if contact_request is None:
        return _back_from_answered_request()
    requester = contact_request.requester
    db.session.add(ContactRelation.between(contact_request.requester_id, current_user.id))
    db.session.delete(contact_request)
    db.session.commit()
    flash(
        f"Vous êtes maintenant en contact avec {requester.first_name} {requester.last_name}",
        "success",
    )
    return redirect(_back_url())


@bp.route("/requests/<int:request_id>/refuse", methods=["POST"])
@login_required
def refuse(request_id):
    contact_request = _received_request(request_id)
    if contact_request is None:
        return _back_from_answered_request()
    db.session.delete(contact_request)
    db.session.commit()
    flash(REFUSED, "success")
    return redirect(_back_url())


@bp.route("/<int:user_id>/remove", methods=["GET"])
@login_required
def confirm_remove(user_id):
    contact, relation = _contact_relation(user_id)
    if relation is None:
        return _back_from_not_a_contact()
    between = catalog.requests_between(current_user.id, contact.id)
    return render_template(
        "contacts/confirm_remove.html",
        contact=contact,
        cancel_notice=catalog.cancel_notice(
            catalog.count_pending_requests(between),
            catalog.count_upcoming_acceptances(between),
            between=True,
        ),
    )


@bp.route("/<int:user_id>/remove", methods=["POST"])
@login_required
def remove(user_id):
    _, relation = _contact_relation(user_id)
    if relation is None:
        return _back_from_not_a_contact()
    catalog.cancel_unstarted_loans(catalog.requests_between(current_user.id, user_id))
    db.session.delete(relation)
    db.session.commit()
    return redirect(url_for("contacts.mine"))


def read_relation_filter(params):
    """The relation filter asked for, among RELATION_FILTERS; all users for anything else"""
    relation = params.get("relation")
    return relation if relation in RELATION_FILTERS else "all"


def read_expanded(params):
    """Whether the users of the search results are shown up to the cap"""
    return params.get("more") == "1"


def search_results_url(params):
    """The search results with the text, filter and expanded state these parameters hold"""
    relation = read_relation_filter(params)
    return url_for(
        "search.results",
        q=params.get("q", ""),
        relation=relation if relation != "all" else None,
        more="1" if read_expanded(params) else None,
    )


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


def lock_live_accounts(*user_ids):
    """Locks these accounts against a deletion until commit; whether all exist, none deleted"""
    deleted_at = db.session.scalars(
        select(User.deleted_at)
        .where(User.id.in_(user_ids))
        .order_by(User.id)
        .with_for_update(read=True)
    ).all()
    return len(deleted_at) == len(set(user_ids)) and all(when is None for when in deleted_at)


def by_name():
    """The order of lists of accounts: first name, last name, then the oldest account first"""
    return (text_search.sort_key(User.first_name), text_search.sort_key(User.last_name), User.id)


def _my_contacts():
    """The current user's contacts, by first then last name regardless of case and accents"""
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
        .order_by(*by_name())
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
    return redirect(_back_url())


def _back_url():
    """Home when the answer was sent from there, "Mes contacts" otherwise"""
    return url_for("index") if request.form.get("origin") == "home" else url_for("contacts.mine")


def _back_from_not_a_contact():
    flash(NOT_A_CONTACT)
    return redirect(url_for("contacts.mine"))
