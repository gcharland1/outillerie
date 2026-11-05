import pytest
from flask import request, url_for

from app import EXAMPLE_SECRET_KEY, create_app
from app.extensions import db
from tests.conftest import USER_PASSWORD, app_config


@pytest.fixture
def app_in(mock_app, monkeypatch):
    """Builds an app for a FLASK_ENVIRONMENT value (None: unset), sharing mock_app's database"""
    apps = []

    def build(environment):
        if environment is None:
            monkeypatch.delenv("FLASK_ENVIRONMENT", raising=False)
        else:
            monkeypatch.setenv("FLASK_ENVIRONMENT", environment)
        app = create_app(app_config())
        apps.append(app)
        return app

    yield build
    for app in apps:
        with app.app_context():
            db.engine.dispose()


def session_cookie_after_login(app, username):
    response = app.test_client().post(
        "/login", data={"username": username, "password": USER_PASSWORD}
    )
    return next(c for c in response.headers.getlist("Set-Cookie") if "session=" in c)


def test_session_cookie_is_secure_in_production(app_in, user):
    assert "Secure" in session_cookie_after_login(app_in("production"), user)


@pytest.mark.parametrize("environment", ["development", None])
def test_session_cookie_is_not_secure_in_development(app_in, user, environment):
    assert "Secure" not in session_cookie_after_login(app_in(environment), user)


@pytest.fixture
def scheme_client(mock_app):
    """A client of an app with a route reporting how it sees the request"""

    @mock_app.route("/scheme")
    def scheme():
        return {"secure": request.is_secure, "url": url_for("index", _external=True)}

    return mock_app.test_client()


def test_request_relayed_over_https_is_secure(scheme_client):
    seen = scheme_client.get("/scheme", headers={"X-Forwarded-Proto": "https"}).json

    assert seen["secure"]
    assert seen["url"].startswith("https://")


def test_direct_request_is_not_secure(scheme_client):
    seen = scheme_client.get("/scheme").json

    assert not seen["secure"]
    assert seen["url"].startswith("http://")


@pytest.fixture
def environment_without_test_config(monkeypatch):
    """Sets what create_app reads from the environment when no test_config is given"""

    def set_environment(environment, secret_key):
        monkeypatch.setenv("FLASK_ENVIRONMENT", environment)
        monkeypatch.setenv("DATABASE_URL", app_config()["SQLALCHEMY_DATABASE_URI"])
        if secret_key is None:
            monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
        else:
            monkeypatch.setenv("FLASK_SECRET_KEY", secret_key)

    return set_environment


@pytest.mark.parametrize("secret_key", [EXAMPLE_SECRET_KEY, "", None])
def test_production_refuses_missing_or_example_secret_key(
    environment_without_test_config, secret_key
):
    environment_without_test_config("production", secret_key)

    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY") as refusal:
        create_app()

    assert EXAMPLE_SECRET_KEY not in str(refusal.value)


def test_production_accepts_a_real_secret_key(environment_without_test_config):
    environment_without_test_config("production", "a-real-secret")

    assert create_app().config["SECRET_KEY"] == "a-real-secret"


def test_development_accepts_the_example_secret_key(environment_without_test_config):
    environment_without_test_config("development", EXAMPLE_SECRET_KEY)

    assert create_app().config["SECRET_KEY"] == EXAMPLE_SECRET_KEY
