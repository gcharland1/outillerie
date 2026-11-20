import re
from html import unescape

import pytest
from werkzeug.security import check_password_hash

from app import auth as auth_module
from models.user import User
from tests.conftest import USER_PASSWORD

SIGN_UP_FORM = {
    "email": "bob@example.com",
    "password": "motdepasse",
    "confirm_password": "motdepasse",
    "first_name": "Bob",
    "last_name": "Gagnon",
}


def page_text(response):
    return unescape(response.get_data(as_text=True))


def without_csrf_token(response):
    """Page body with the CSRF token masked: its signature embeds the current second"""
    return re.sub(rb'name="csrf_token" value="[^"]*"', b'name="csrf_token"', response.get_data())


def log_in(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def test_register_creates_account_and_redirects_to_login(mock_app, client):
    response = client.post("/register", data=SIGN_UP_FORM)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with mock_app.app_context():
        user = User.query.filter_by(email="bob@example.com").one()
    assert (user.first_name, user.last_name, user.username) == ("Bob", "Gagnon", None)


def test_register_form_asks_no_username(client):
    text = page_text(client.get("/register"))

    assert 'name="email"' in text
    assert "Nom d'utilisateur" not in text
    assert 'name="username"' not in text


def test_register_strips_the_email(mock_app, client):
    client.post("/register", data={**SIGN_UP_FORM, "email": " bob@example.com "})

    with mock_app.app_context():
        assert User.query.filter_by(email="bob@example.com").count() == 1


def test_register_stores_only_a_password_hash(mock_app, client):
    client.post("/register", data=SIGN_UP_FORM)

    with mock_app.app_context():
        stored = User.query.filter_by(email="bob@example.com").one().password
    assert stored != SIGN_UP_FORM["password"]
    assert check_password_hash(stored, SIGN_UP_FORM["password"])


@pytest.mark.parametrize("email", ["Alice@Example.com", " alice@example.com "])
def test_register_with_taken_email_shows_error(mock_app, client, user, email):
    response = client.post("/register", data={**SIGN_UP_FORM, "email": email})

    assert response.status_code == 200
    assert "Le courriel est déjà utilisé" in page_text(response)
    with mock_app.app_context():
        assert User.query.count() == 1


def test_login_with_valid_credentials(client, user):
    response = log_in(client, user, USER_PASSWORD)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert client.get("/").status_code == 200


def test_login_ignores_case_and_spaces_of_the_email(client, user):
    response = log_in(client, " Alice@Example.COM ", USER_PASSWORD)

    assert response.headers["Location"] == "/"
    assert client.get("/").status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("inconnu@example.com", USER_PASSWORD),
        ("alice@example.com", "mauvais"),
        ("alice", USER_PASSWORD),
    ],
    ids=["unknown-email", "wrong-password", "username"],
)
def test_login_with_invalid_credentials(client, user, email, password):
    response = log_in(client, email, password)

    assert response.status_code == 200
    text = page_text(response)
    assert "Le courriel ou le mot de passe est invalide" in text
    assert f'name="email" id="email" value="{email}"' in text
    assert password not in text
    assert client.get("/").status_code == 302


def test_unknown_email_is_indistinguishable_from_wrong_password(client, user, monkeypatch):
    checked_hashes = []
    real_check = auth_module.check_password_hash

    def spy(password_hash, password):
        checked_hashes.append(password_hash)
        return real_check(password_hash, password)

    monkeypatch.setattr(auth_module, "check_password_hash", spy)

    unknown = log_in(client, "inconnu@example.com", "mauvais")
    wrong_password = log_in(client, user, "mauvais")

    assert len(checked_hashes) == 2
    assert checked_hashes[0].split("$")[0] == checked_hashes[1].split("$")[0]
    assert unknown.status_code == wrong_password.status_code
    typed = rb'name="email" id="email" value="[^"]*"'
    assert re.sub(typed, b"", without_csrf_token(unknown)) == re.sub(
        typed, b"", without_csrf_token(wrong_password)
    )
