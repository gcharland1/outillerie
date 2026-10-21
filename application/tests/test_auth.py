from html import unescape

import pytest
from werkzeug.security import check_password_hash

import app as app_module
from models.user import User
from tests.conftest import USER_PASSWORD

SIGN_UP_FORM = {
    "username": "bob",
    "password": "motdepasse",
    "confirm_password": "motdepasse",
    "first_name": "Bob",
    "last_name": "Gagnon",
    "email": "bob@example.com",
}


def page_text(response):
    return unescape(response.get_data(as_text=True))


def log_in(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_register_creates_account_and_redirects_to_login(mock_app, client):
    response = client.post("/register", data=SIGN_UP_FORM)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with mock_app.app_context():
        user = User.query.filter_by(username="bob").one()
    assert (user.first_name, user.last_name, user.email) == ("Bob", "Gagnon", "bob@example.com")


def test_register_stores_only_a_password_hash(mock_app, client):
    client.post("/register", data=SIGN_UP_FORM)

    with mock_app.app_context():
        stored = User.query.filter_by(username="bob").one().password
    assert stored != SIGN_UP_FORM["password"]
    assert check_password_hash(stored, SIGN_UP_FORM["password"])


def test_register_with_taken_username_shows_error(mock_app, client, user):
    response = client.post("/register", data={**SIGN_UP_FORM, "username": user})

    assert response.status_code == 200
    assert "Le nom d'utilisateur est déjà utilisé" in page_text(response)
    with mock_app.app_context():
        assert User.query.filter_by(username=user).count() == 1


def test_login_with_valid_credentials(client, user):
    response = log_in(client, user, USER_PASSWORD)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert f"Rebonjour {user}" in page_text(client.get("/"))


@pytest.mark.parametrize(
    ("username", "password"),
    [("inconnu", USER_PASSWORD), ("alice", "mauvais")],
    ids=["unknown-username", "wrong-password"],
)
def test_login_with_invalid_credentials(client, user, username, password):
    response = log_in(client, username, password)

    assert response.status_code == 200
    assert "Le nom d'utilisateur ou le mot de passe est invalide" in page_text(response)
    assert "Rebonjour" not in page_text(client.get("/"))


def test_unknown_username_is_indistinguishable_from_wrong_password(client, user, monkeypatch):
    checked_hashes = []
    real_check = app_module.check_password_hash

    def spy(password_hash, password):
        checked_hashes.append(password_hash)
        return real_check(password_hash, password)

    monkeypatch.setattr(app_module, "check_password_hash", spy)

    unknown = log_in(client, "inconnu", "mauvais")
    wrong_password = log_in(client, user, "mauvais")

    assert len(checked_hashes) == 2
    assert checked_hashes[0].split("$")[0] == checked_hashes[1].split("$")[0]
    assert unknown.status_code == wrong_password.status_code
    assert unknown.get_data() == wrong_password.get_data()
