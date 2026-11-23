import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from models.user import User
from tests.factories import make_user


def test_email_is_unique_regardless_of_case(mock_app):
    with mock_app.app_context():
        db.session.add(make_user("alice@example.com"))
        db.session.commit()
        db.session.add(make_user("Alice@Example.com"))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_phone_keeps_20_characters(mock_app):
    phone = "+1 418 555-1234 x123"
    assert len(phone) == 20
    with mock_app.app_context():
        db.session.add(make_user("alice@example.com", phone=phone))
        db.session.commit()
        assert User.query.filter_by(email="alice@example.com").one().phone == phone


def test_session_id_of_version_0_is_the_account_alone(mock_app):
    with mock_app.app_context():
        db.session.add(make_user("alice@example.com"))
        db.session.commit()
        alice = User.query.filter_by(email="alice@example.com").one()
        assert alice.session_version == 0
        assert alice.get_id() == str(alice.id)


def test_session_id_holds_a_later_session_version(mock_app):
    with mock_app.app_context():
        db.session.add(make_user("alice@example.com", session_version=2))
        db.session.commit()
        alice = User.query.filter_by(email="alice@example.com").one()
        assert alice.get_id() == f"{alice.id}:2"
