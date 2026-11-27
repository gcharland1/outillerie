from app import mail
from app.extensions import db
from models.user import User
from tests.conftest import (
    MINUTE,
    USER_PASSWORD,
    log_in_with_page_token,
    login,
    token_in,
    user_id_in,
)
from tests.test_remember import login_remembered, remember_cookie, remember_cookie_header
from tests.test_session import page_text

CARD = "Déconnecter tous mes appareils"
NOTICE = "Tous vos appareils ont été déconnectés"


def session_version(mock_app, email):
    with mock_app.app_context():
        return db.session.get(User, user_id_in(mock_app, email)).session_version


def is_recognized(client):
    return client.get("/profile").status_code == 200


# Section et page de confirmation


def test_card_precedes_the_deletion(logged_in_client):
    text = page_text(logged_in_client.get("/profile"))

    assert text.index(CARD) < text.index("<h3>Supprimer mon compte</h3>")
    assert '<a class="button error" href="/profile/logout-all">' in text


def test_card_is_shown_to_an_unconfirmed_account(client, unconfirmed):
    assert CARD in page_text(login(client, unconfirmed).get("/profile"))


def test_confirmation_page_logs_nothing_out(mock_app, client, user):
    phone = login(mock_app.test_client(), user)
    computer = login(client, user)

    text = page_text(computer.get("/profile/logout-all"))

    assert "Tous vos appareils, celui-ci compris, seront déconnectés." in text
    assert '<a class="button" href="/profile">Annuler</a>' in text
    assert f'<button type="submit" class="button error">{CARD}</button>' in text
    assert is_recognized(phone) and is_recognized(computer)
    assert session_version(mock_app, user) == 0


def test_visitor_is_sent_to_login(client):
    for response in (client.get("/profile/logout-all"), client.post("/profile/logout-all")):
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/login")


# Effet


def test_other_device_is_logged_out(mock_app, client, user):
    phone = login(mock_app.test_client(), user)

    login(client, user).post("/profile/logout-all")

    assert not is_recognized(phone)
    assert session_version(mock_app, user) == 1


def test_remember_cookie_of_another_device_is_revoked(clock, mock_app, client, user):
    phone = mock_app.test_client()
    login_remembered(phone, user)

    login(client, user).post("/profile/logout-all")
    clock.advance(31 * MINUTE)
    phone.delete_cookie("session")

    assert not is_recognized(phone)


def test_current_device_is_logged_out_with_a_notice(mock_app, client, user):
    login_remembered(client, user)

    response = client.post("/profile/logout-all")

    assert response.headers["Location"] == "/logged-out?reason=all-devices"
    assert remember_cookie_header(response).startswith("remember_token=;")
    assert remember_cookie(client) is None
    assert NOTICE in page_text(client.get("/logged-out?reason=all-devices"))
    assert not is_recognized(client)


def test_user_logs_in_again(client, user):
    login(client, user).post("/profile/logout-all")

    assert is_recognized(login(client, user))


def test_deleted_account_is_not_changed(mock_app, client, user):
    login(client, user)
    with mock_app.app_context():
        db.session.get(User, user_id_in(mock_app, user)).deleted_at = db.func.now()
        db.session.commit()

    response = client.post("/profile/logout-all")

    assert response.headers["Location"].startswith("/login")
    with mock_app.app_context():
        assert db.session.get(User, user_id_in(mock_app, user)).session_version == 0


def test_get_with_parameters_logs_nothing_out(mock_app, logged_in_client, user):
    logged_in_client.get("/profile/logout-all?confirm=1")

    assert session_version(mock_app, user) == 0


def test_without_csrf_token_is_refused(mock_app, csrf_client, user):
    log_in_with_page_token(csrf_client, user, USER_PASSWORD)

    response = csrf_client.post("/profile/logout-all")

    assert response.status_code == 400
    assert session_version(mock_app, user) == 0


def test_with_page_token(mock_app, csrf_client, user):
    log_in_with_page_token(csrf_client, user, USER_PASSWORD)
    token = token_in(csrf_client.get("/profile/logout-all"))

    csrf_client.post("/profile/logout-all", data={"csrf_token": token})

    assert session_version(mock_app, user) == 1


# Avis


def test_notice_is_emailed_without_link(logged_in_client, user, mail_outbox):
    logged_in_client.post("/profile/logout-all")

    assert len(mail_outbox) == 1
    email = mail_outbox[0]
    body = email.get_content()
    assert email["To"] == user
    assert email["Subject"] == "Vos appareils ont été déconnectés"
    assert body.startswith("Bonjour Alice,")
    assert "http" not in body and "/" not in body


def test_failed_send_still_logs_out(monkeypatch, mock_app, client, user, mail_outbox):
    phone = login(mock_app.test_client(), user)

    def fail(*args):
        raise OSError

    monkeypatch.setattr(mail, "_message", fail)

    response = login(client, user).post("/profile/logout-all")

    assert response.headers["Location"] == "/logged-out?reason=all-devices"
    assert not is_recognized(phone)
    assert mail_outbox == []


def test_unconfirmed_account_receives_nothing(mock_app, client, unconfirmed, mail_outbox):
    login(client, unconfirmed).post("/profile/logout-all")

    assert session_version(mock_app, unconfirmed) == 1
    assert mail_outbox == []
