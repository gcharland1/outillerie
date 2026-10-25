import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from models import ContactRelation, ContactRequest
from tests.factories import make_contact_relation, make_contact_request, user_id


@pytest.fixture
def ids(mock_app, user, bob):
    with mock_app.app_context():
        return user_id(user), user_id(bob)


def test_request_is_stored(mock_app, ids):
    alice_id, bob_id = ids
    with mock_app.app_context():
        request = make_contact_request(alice_id, bob_id)
        db.session.expire_all()
        stored = db.session.get(ContactRequest, request.id)
        assert (stored.requester.id, stored.recipient.id) == (alice_id, bob_id)
        assert stored.created_at is not None


def test_request_to_oneself_is_refused(mock_app, ids):
    alice_id, _ = ids
    with (
        mock_app.app_context(),
        pytest.raises(IntegrityError, match="ck_contact_request_not_self"),
    ):
        make_contact_request(alice_id, alice_id)


def test_second_request_is_refused(mock_app, ids):
    alice_id, bob_id = ids
    with mock_app.app_context():
        make_contact_request(alice_id, bob_id)
        with pytest.raises(IntegrityError, match="uq_contact_request_pair"):
            make_contact_request(alice_id, bob_id)


def test_crossed_request_is_refused(mock_app, ids):
    alice_id, bob_id = ids
    with mock_app.app_context():
        make_contact_request(bob_id, alice_id)
        with pytest.raises(IntegrityError, match="uq_contact_request_pair"):
            make_contact_request(alice_id, bob_id)


def test_new_request_is_accepted_once_the_previous_one_is_deleted(mock_app, ids):
    alice_id, bob_id = ids
    with mock_app.app_context():
        db.session.delete(make_contact_request(alice_id, bob_id))
        db.session.commit()
        make_contact_request(alice_id, bob_id)
        assert ContactRequest.query.count() == 1


@pytest.mark.parametrize("order", [(0, 1), (1, 0)])
def test_between_orders_the_pair_either_way(mock_app, ids, order):
    first_id, second_id = (ids[i] for i in order)
    relation = ContactRelation.between(first_id, second_id)
    assert (relation.user_a_id, relation.user_b_id) == (min(ids), max(ids))


def test_unordered_pair_is_refused(mock_app, ids):
    with mock_app.app_context():
        db.session.add(ContactRelation(user_a_id=max(ids), user_b_id=min(ids)))
        with pytest.raises(IntegrityError, match="ck_contact_relation_ordered_pair"):
            db.session.commit()


def test_duplicate_relation_is_refused(mock_app, ids):
    alice_id, bob_id = ids
    with mock_app.app_context():
        make_contact_relation(alice_id, bob_id)
        with pytest.raises(IntegrityError, match="pk_contact_relation"):
            make_contact_relation(bob_id, alice_id)
