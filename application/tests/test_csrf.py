import re
from html import unescape

import pytest

from models import Tool, User
from tests.conftest import MINUTE, USER_PASSWORD

CSRF_FIELD = 'name="csrf_token"'
REFUSAL_MESSAGE = "Le formulaire a expiré ou est invalide. Rechargez la page et réessayez."


def page_text(response):
    return unescape(response.get_data(as_text=True))


def token_in(response):
    return re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))[1]


def is_logged_in(client):
    return "Rebonjour" in page_text(client.get("/"))


@pytest.fixture
def csrf_client(mock_app, client):
    """A client of an app that checks CSRF tokens, as in production"""
    mock_app.config["WTF_CSRF_ENABLED"] = True
    return client


def log_in_with_page_token(client, username, password):
    token = token_in(client.get("/login"))
    return client.post(
        "/login", data={"username": username, "password": password, "csrf_token": token}
    )


@pytest.mark.parametrize("path", ["/login", "/register"])
def test_visitor_forms_carry_a_token(client, path):
    assert CSRF_FIELD in client.get(path).get_data(as_text=True)


def test_logout_button_carries_a_token(logged_in_client):
    assert CSRF_FIELD in logged_in_client.get("/").get_data(as_text=True)


def test_login_without_token_is_refused(csrf_client, user):
    response = csrf_client.post("/login", data={"username": user, "password": USER_PASSWORD})

    assert response.status_code == 400
    assert REFUSAL_MESSAGE in page_text(response)
    assert not is_logged_in(csrf_client)


def test_register_without_token_creates_no_account(mock_app, csrf_client):
    response = csrf_client.post(
        "/register",
        data={
            "username": "bob",
            "password": "motdepasse",
            "first_name": "Bob",
            "last_name": "Gagnon",
            "email": "bob@example.com",
        },
    )

    assert response.status_code == 400
    with mock_app.app_context():
        assert User.query.count() == 0


def test_logout_without_token_keeps_the_session(csrf_client, user):
    log_in_with_page_token(csrf_client, user, USER_PASSWORD)

    response = csrf_client.post("/logout")

    assert response.status_code == 400
    assert is_logged_in(csrf_client)


def test_login_with_the_page_token(csrf_client, user):
    response = log_in_with_page_token(csrf_client, user, USER_PASSWORD)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert is_logged_in(csrf_client)


def test_login_page_open_twenty_minutes_is_accepted(clock, csrf_client, user):
    token = token_in(csrf_client.get("/login"))
    clock.advance(20 * MINUTE)

    response = csrf_client.post(
        "/login", data={"username": user, "password": USER_PASSWORD, "csrf_token": token}
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert is_logged_in(csrf_client)


def test_login_page_open_too_long_is_refused(clock, csrf_client, user):
    token = token_in(csrf_client.get("/login"))
    clock.advance(31 * MINUTE)

    response = csrf_client.post(
        "/login", data={"username": user, "password": USER_PASSWORD, "csrf_token": token}
    )

    assert response.status_code == 400
    assert REFUSAL_MESSAGE in page_text(response)
    assert not is_logged_in(csrf_client)


def test_tool_form_with_a_tampered_token_is_refused(mock_app, csrf_client, user):
    log_in_with_page_token(csrf_client, user, USER_PASSWORD)
    token = token_in(csrf_client.get("/tools/new"))

    response = csrf_client.post(
        "/tools/new",
        data={
            "name": "Perceuse",
            "description": "Perceuse sans fil",
            "condition": "functional",
            "csrf_token": token[:-4] + "abcd",
        },
    )

    assert response.status_code == 400
    with mock_app.app_context():
        assert Tool.query.count() == 0
