from datetime import timedelta
from html import unescape

import pytest
from itsdangerous import TimestampSigner

from tests.conftest import USER_PASSWORD

MINUTE = 60


def page_text(response):
    return unescape(response.get_data(as_text=True))


def is_logged_in(client):
    return "Rebonjour" in page_text(client.get("/"))


@pytest.fixture
def logged_in_client(client, user):
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


def test_session_cookie_is_httponly_and_samesite_lax(client, user):
    response = client.post("/login", data={"username": user, "password": USER_PASSWORD})

    session_cookie = next(c for c in response.headers.getlist("Set-Cookie") if "session=" in c)
    assert "HttpOnly" in session_cookie
    assert "SameSite=Lax" in session_cookie


def test_logged_out_page_after_logout(client):
    text = page_text(client.get("/logged-out"))

    assert "Vous êtes déconnecté" in text
    assert 'href="/login"' in text


def test_logged_out_page_after_inactivity(client):
    text = page_text(client.get("/logged-out?reason=inactivity"))

    assert "Votre session a expiré après 30 minutes d'inactivité" in text
    assert 'href="/login"' in text


def test_logged_out_page_shows_configured_lifetime(mock_app, client):
    mock_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

    text = page_text(client.get("/logged-out?reason=inactivity"))

    assert "Votre session a expiré après 15 minutes d'inactivité" in text


def test_logged_out_page_ignores_unknown_reason(client):
    assert "Vous êtes déconnecté" in page_text(client.get("/logged-out?reason=autre"))


def test_logged_out_page_redirects_a_logged_in_user_home(logged_in_client):
    response = logged_in_client.get("/logged-out?reason=inactivity")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert is_logged_in(logged_in_client)


def test_logout_closes_the_session(logged_in_client):
    response = logged_in_client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/logged-out"
    assert not is_logged_in(logged_in_client)


def test_logout_without_session_redirects(client):
    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/logged-out"


def test_logout_refuses_get(logged_in_client):
    assert logged_in_client.get("/logout").status_code == 405
    assert is_logged_in(logged_in_client)


def test_session_expires_after_30_minutes_of_inactivity(clock, logged_in_client):
    clock.advance(31 * MINUTE)

    assert not is_logged_in(logged_in_client)


def test_activity_extends_the_session(clock, logged_in_client):
    for _ in range(3):
        clock.advance(20 * MINUTE)
        assert is_logged_in(logged_in_client)
