import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from models.user import User
from tests.factories import make_user


def test_email_is_unique_regardless_of_case(mock_app):
    with mock_app.app_context():
        db.session.add(make_user("alice", "alice@example.com"))
        db.session.commit()
        db.session.add(make_user("alice2", "Alice@Example.com"))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_phone_keeps_20_characters(mock_app):
    phone = "+1 418 555-1234 x123"
    assert len(phone) == 20
    with mock_app.app_context():
        db.session.add(make_user("alice", "alice@example.com", phone=phone))
        db.session.commit()
        assert User.query.filter_by(username="alice").one().phone == phone
