import os
import re
from io import BytesIO

import pytest
from itsdangerous import TimestampSigner
from PIL import ExifTags, Image
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from models import Tool
from models.user import User
from tests.factories import make_tool

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


@pytest.fixture(autouse=True)
def development_environment(monkeypatch):
    """Keeps a FLASK_ENVIRONMENT set in the shell from changing the apps the tests build"""
    monkeypatch.delenv("FLASK_ENVIRONMENT", raising=False)


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


@pytest.fixture
def csrf_client(mock_app, client):
    """A client of an app that checks CSRF tokens, as in production"""
    mock_app.config["WTF_CSRF_ENABLED"] = True
    return client


def token_in(response):
    return re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))[1]


def log_in_with_page_token(client, username, password):
    token = token_in(client.get("/login"))
    return client.post(
        "/login", data={"username": username, "password": password, "csrf_token": token}
    )


def user_id_in(mock_app, username):
    """A registered user's id, from outside any app context (unlike factories.user_id)"""
    with mock_app.app_context():
        return User.query.filter_by(username=username).one().id


@pytest.fixture
def alice_id(mock_app, user):
    return user_id_in(mock_app, user)


@pytest.fixture
def bob_id(mock_app, bob):
    return user_id_in(mock_app, bob)


def add_tool(mock_app, owner_id, name="Perceuse", **fields):
    with mock_app.app_context():
        return make_tool(owner_id, name=name, **fields).id


def stored(mock_app, tool_id):
    """The tool's fields as the database holds them, or None if it is gone"""
    with mock_app.app_context():
        tool = db.session.get(Tool, tool_id)
        if tool is None:
            return None
        return {
            "owner_id": tool.owner_id,
            "name": tool.name,
            "description": tool.description,
            "condition": tool.condition,
            "private_notes": tool.private_notes,
            "is_active": tool.is_active,
        }


def tool_count(mock_app):
    with mock_app.app_context():
        return Tool.query.count()


def tool_form(**fields):
    return {
        "name": "Perceuse",
        "description": "Perceuse sans fil 18 V",
        "condition": "functional",
        "private_notes": "",
        **fields,
    }


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


def encoded(image, image_format, **options):
    """The bytes of an image saved in the given format"""
    buffer = BytesIO()
    image.save(buffer, image_format, **options)
    return buffer.getvalue()


def a_photo(size=(400, 300)):
    return Image.new("RGB", size, (200, 120, 40))


@pytest.fixture
def jpeg_photo():
    return encoded(a_photo(), "JPEG")


@pytest.fixture
def transparent_png():
    image = Image.new("RGBA", (300, 200), (0, 0, 0, 0))
    image.paste((0, 0, 255, 255), (100, 50, 200, 150))
    return encoded(image, "PNG")


@pytest.fixture
def webp_photo():
    return encoded(a_photo(), "WEBP")


@pytest.fixture
def gif_image():
    return encoded(a_photo(), "GIF")


@pytest.fixture
def huge_png():
    """50 million pixels: a bilevel image keeps it light to build and to send"""
    return encoded(Image.new("1", (10_000, 5_000)), "PNG")


@pytest.fixture
def truncated_jpeg(jpeg_photo):
    return jpeg_photo[: len(jpeg_photo) // 2]


@pytest.fixture
def large_geotagged_photo():
    """A 4000 × 3000 phone photo whose metadata hold a GPS position"""
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = "Phone"
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = (46.0, 48.0, 0.0)
    gps[ExifTags.GPS.GPSLongitudeRef] = "W"
    gps[ExifTags.GPS.GPSLongitude] = (71.0, 13.0, 0.0)
    return encoded(a_photo((4000, 3000)), "JPEG", exif=exif)


@pytest.fixture
def sideways_photo():
    """A 3000 × 4000 portrait stored lying down, with the orientation tag that turns it upright"""
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6
    return encoded(a_photo((4000, 3000)), "JPEG", exif=exif)
