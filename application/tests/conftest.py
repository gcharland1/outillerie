import os

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from models.user import User

CI_DATABASE_URL = "postgresql+psycopg://outillerie:outillerie@localhost:5432/outillerie"
USER_PASSWORD = "secret123"


@pytest.fixture
def mock_app():
    """Create an app instance for testing"""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": os.getenv("TEST_DATABASE_URL", CI_DATABASE_URL),
            "SECRET_KEY": "test",
        }
    )
    # The app context wraps only setup and teardown: requests made while it is active would
    # share its `g`, where Flask-Login caches the current user across requests.
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(mock_app):
    """An app client to send requests"""
    return mock_app.test_client()


@pytest.fixture
def user(mock_app):
    """Username of a registered user whose password is USER_PASSWORD"""
    with mock_app.app_context():
        db.session.add(
            User(
                username="alice",
                password=generate_password_hash(USER_PASSWORD, method="pbkdf2:sha256"),
                first_name="Alice",
                last_name="Tremblay",
                email="alice@example.com",
            )
        )
        db.session.commit()
    return "alice"
