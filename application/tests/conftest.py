import os

import pytest
from itsdangerous import TimestampSigner
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from models.user import User

CI_DATABASE_URL = "postgresql+psycopg://outillerie:outillerie@localhost:5432/outillerie"
USER_PASSWORD = "secret123"
MINUTE = 60


def app_config():
    """Configuration of every app the tests create"""
    return {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.getenv("TEST_DATABASE_URL", CI_DATABASE_URL),
        "SECRET_KEY": "test",
        "WTF_CSRF_ENABLED": False,
    }


@pytest.fixture
def mock_app():
    """Create an app instance for testing"""
    app = create_app(app_config())
    # The app context wraps only setup and teardown: requests made while it is active would
    # share its `g`, where Flask-Login caches the current user across requests.
    with app.app_context():
        # Needed by the GiST exclusion constraint on loan; the Alembic revision creates it too.
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        db.session.commit()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        # Each test builds its own app and pool; release its connections before the next one.
        db.engine.dispose()


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


@pytest.fixture
def bob(mock_app):
    """Username of a second registered user, for checks across accounts"""
    with mock_app.app_context():
        db.session.add(
            User(
                username="bob",
                password=generate_password_hash(USER_PASSWORD, method="pbkdf2:sha256"),
                first_name="Bob",
                last_name="Gagnon",
                email="bob@example.com",
            )
        )
        db.session.commit()
    return "bob"


@pytest.fixture
def carole(mock_app):
    """Username of a third registered user"""
    with mock_app.app_context():
        db.session.add(
            User(
                username="carole",
                password=generate_password_hash(USER_PASSWORD, method="pbkdf2:sha256"),
                first_name="Carole",
                last_name="Roy",
                email="carole@example.com",
            )
        )
        db.session.commit()
    return "carole"


@pytest.fixture
def logged_in_client(client, user):
    """A client logged in as `user`"""
    client.post("/login", data={"username": user, "password": USER_PASSWORD})
    return client


class FakeClock:
    def __init__(self):
        self.now = 1_000_000_000

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    """Controls the clock used to sign session cookies and to check their age"""
    fake = FakeClock()
    monkeypatch.setattr(TimestampSigner, "get_timestamp", lambda self: fake.now)
    return fake
