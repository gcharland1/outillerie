from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.extensions import db
from models.user import User
from tests.conftest import MINUTE, USER_PASSWORD, login, user_id_in
from tests.test_navigation import REFRESH_TAG
from tests.test_profile import delete_account
from tests.test_session import is_logged_in, page_text


def login_remembered(client, email, remember="1"):
    data = {"email": email, "password": USER_PASSWORD, "remember": remember}
    return client.post("/login", data=data)


def remember_cookie_header(response):
    return next((c for c in response.headers.getlist("Set-Cookie") if "remember_token=" in c), None)


def remember_cookie(client):
    return client.get_cookie("remember_token")


def days_left(cookie):
    return (cookie.expires - datetime.now(UTC)) / timedelta(days=1)


def test_checkbox_is_shown_unchecked(client):
    text = page_text(client.get("/login"))

    assert "Rester connecté sur cet appareil" in text
    assert '<input type="checkbox" name="remember" value="1" />' in text


def test_checked_login_sets_a_30_day_cookie(client, user):
    login_remembered(client, user)

    assert 29.9 < days_left(remember_cookie(client)) <= 30


def test_remember_cookie_is_httponly_and_samesite_lax(client, user):
    cookie = remember_cookie_header(login_remembered(client, user))

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_remembered_user_is_recognized_after_the_session_expires(clock, client, user):
    login_remembered(client, user)
    clock.advance(31 * MINUTE)

    response = client.get("/")

    assert 'class="account-menu"' in page_text(response)
    assert remember_cookie_header(response) is not None
    assert 29.9 < days_left(remember_cookie(client)) <= 30


def test_expired_remember_cookie_leads_to_login_without_message(clock, client, user):
    login_remembered(client, user)
    clock.advance(31 * MINUTE)
    client.get("/")
    client.delete_cookie("remember_token")
    clock.advance(31 * MINUTE)

    response = client.get("/", follow_redirects=True)

    assert response.request.path == "/login"
    assert 'class="account-menu"' not in page_text(response)
    assert 'class="flash' not in page_text(response)


def test_each_page_renews_the_remember_cookie(client, user):
    login_remembered(client, user)

    for page in ("/", "/profile", "/contacts"):
        assert remember_cookie_header(client.get(page)) is not None


def test_unchecked_login_sets_no_remember_cookie(clock, client, user):
    data = {"email": user, "password": USER_PASSWORD}
    responses = [client.post("/login", data=data), client.get("/"), client.get("/profile")]

    for response in responses:
        header = remember_cookie_header(response)
        assert header is None or header.startswith("remember_token=;")
    assert remember_cookie(client) is None
    clock.advance(31 * MINUTE)
    assert not is_logged_in(client)


def test_unchecked_login_erases_another_accounts_cookie(clock, client, user, bob):
    login_remembered(client, bob)
    client.post("/logout")
    login_remembered(client, bob)

    login(client, user)

    assert remember_cookie(client) is None
    clock.advance(31 * MINUTE)
    assert not is_logged_in(client)


def test_unexpected_checkbox_value_counts_as_unchecked(client, user):
    login_remembered(client, user, remember="on")

    assert is_logged_in(client)
    assert remember_cookie(client) is None


def test_failed_login_keeps_the_box_checked_and_sets_no_cookie(client, user):
    data = {"email": user, "password": "wrong", "remember": "1"}
    response = client.post("/login", data=data)

    assert '<input type="checkbox" name="remember" value="1" checked />' in page_text(response)
    assert remember_cookie_header(response) is None


def test_session_opened_before_the_deployment_stays_open(mock_app, client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id_in(mock_app, user))

    assert is_logged_in(client)


def test_malformed_session_id_is_a_visitors(mock_app, client, user):
    with client.session_transaction() as session:
        session["_user_id"] = f"{user_id_in(mock_app, user)}:x"

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def bump_session_version(mock_app, email):
    with mock_app.app_context():
        db.session.execute(
            update(User).where(User.email == email).values(session_version=User.session_version + 1)
        )
        db.session.commit()


def test_another_session_version_ends_session_and_erases_cookie(clock, mock_app, client, user):
    login_remembered(client, user)
    bump_session_version(mock_app, user)
    clock.advance(31 * MINUTE)

    response = client.get("/")

    assert response.headers["Location"] == "/login"
    assert remember_cookie(client) is None


def test_logout_erases_the_remember_cookie(clock, client, user):
    login_remembered(client, user)

    client.post("/logout")

    assert remember_cookie(client) is None
    clock.advance(31 * MINUTE)
    assert not is_logged_in(client)


def test_account_deletion_erases_the_remember_cookie(client, user):
    login_remembered(client, user)

    delete_account(client)

    assert remember_cookie(client) is None


def test_copied_remember_cookie_of_a_deleted_account_is_a_visitors(mock_app, client, user):
    login_remembered(client, user)
    cookie = remember_cookie(client).value
    delete_account(client)

    replay = mock_app.test_client()
    replay.set_cookie("remember_token", cookie)

    assert replay.get("/profile").headers["Location"].startswith("/login")


def test_remembered_pages_have_no_expiry_refresh(client, user):
    login_remembered(client, user)

    assert REFRESH_TAG not in page_text(client.get("/"))


def test_unremembered_pages_keep_the_expiry_refresh(client, user):
    login(client, user)

    assert REFRESH_TAG in page_text(client.get("/"))
