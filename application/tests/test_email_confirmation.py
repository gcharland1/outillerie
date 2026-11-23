import logging
import re
import smtplib
from datetime import timedelta
from html import unescape

import pytest
from sqlalchemy import text

from app import catalog, email_confirmation, mail
from app.extensions import db
from models import Loan, LoanStatus
from tests.conftest import USER_PASSWORD, add_loan, add_tool, login, token_in
from tests.factories import make_contact_relation, make_contact_request, user_id

SITE_URL = "https://outillerie.example.com"
DAY = 24 * 60 * 60
NEWCOMER = {
    "email": "eve@example.com",
    "password": "motdepasse",
    "first_name": "Ève",
    "last_name": "Lavoie",
}


def page_text(response):
    return unescape(response.get_data(as_text=True))


def badges(page):
    return re.findall(r'<span class="badge">(\d+) ', page)


def link_in(email):
    return re.search(rf"{re.escape(SITE_URL)}(/confirmer-courriel/\S+)", email.get_content())[1]


def register(client, **fields):
    return client.post("/register", data={**NEWCOMER, **fields})


@pytest.fixture
def newcomer_link(client, mail_outbox):
    """The path of the link emailed to a visitor who just registered as NEWCOMER"""
    register(client)
    return link_in(mail_outbox[-1])


def account(mock_app, email):
    with mock_app.app_context():
        return db.session.execute(
            text(
                'SELECT email_confirmed_at, email_confirmation_sent_at FROM "user" '
                "WHERE lower(email) = lower(:email)"
            ),
            {"email": email},
        ).one()


def is_confirmed(mock_app, email):
    return account(mock_app, email).email_confirmed_at is not None


def sent_minutes_ago(mock_app, email, minutes):
    with mock_app.app_context():
        db.session.execute(
            text(
                'UPDATE "user" SET email_confirmation_sent_at = now() - make_interval(mins => :m) '
                "WHERE email = :email"
            ),
            {"m": minutes, "email": email},
        )
        db.session.commit()


def confirm(client, link):
    page = client.get(link)
    return client.post("/confirmer-courriel", data={"token": token_field(page)})


def token_field(page):
    return re.search(r'name="token" value="([^"]+)"', page.get_data(as_text=True))[1]


# Registration and the email


def test_register_sends_the_confirmation_email(mock_app, client, mail_outbox):
    response = register(client)

    assert response.headers["Location"] == "/login"
    assert "Compte créé. Un courriel de confirmation a été envoyé à eve@example.com." in (
        page_text(client.get("/login"))
    )
    assert not is_confirmed(mock_app, NEWCOMER["email"])
    assert account(mock_app, NEWCOMER["email"]).email_confirmation_sent_at is not None
    assert len(mail_outbox) == 1
    assert mail_outbox[0]["To"] == "eve@example.com"
    assert mail_outbox[0]["From"] == "outillerie@example.com"


def test_email_holds_the_first_name_link_lifetime_and_nothing_else(mock_app, client, mail_outbox):
    register(client, address="12 rue des Érables")

    body = mail_outbox[0].get_content()

    assert "Ève" in body
    assert f"{SITE_URL}/confirmer-courriel/" in body
    assert "30 jours" in body
    assert "ignorez ce courriel" in body
    assert "Lavoie" not in body
    assert "Érables" not in body


def test_link_ignores_a_forged_host_header(client, mail_outbox):
    client.post("/register", data=NEWCOMER, headers={"Host": "exemple.com"})

    assert f"{SITE_URL}/confirmer-courriel/" in mail_outbox[0].get_content()
    assert "exemple.com" not in mail_outbox[0].get_content()


def test_failed_send_keeps_the_account_and_logs_without_the_link(
    mock_app, client, monkeypatch, caplog
):
    mock_app.config["TESTING"] = False

    def refuse(*args, **kwargs):
        raise smtplib.SMTPConnectError(421, "refusé")

    monkeypatch.setattr(smtplib, "SMTP", refuse)

    with caplog.at_level(logging.ERROR):
        response = register(client)

    assert response.headers["Location"] == "/login"
    assert account(mock_app, NEWCOMER["email"]) is not None
    assert "SMTPConnectError" in caplog.text
    assert "confirmer-courriel" not in caplog.text


@pytest.mark.parametrize(
    "email", ["eve@example.com, mallory@example.org", "eve@example.com\r\nBcc: m@example.org"]
)
def test_email_that_is_not_one_address_gets_no_link(mock_app, client, mail_outbox, email):
    response = register(client, email=email)

    assert response.headers["Location"] == "/login"
    assert mail_outbox == []


def test_any_send_failure_keeps_the_account(mock_app, client, monkeypatch):
    mock_app.config["TESTING"] = False

    def broken(*args, **kwargs):
        raise RuntimeError("panne")

    monkeypatch.setattr(smtplib, "SMTP", broken)

    assert register(client).headers["Location"] == "/login"
    assert account(mock_app, NEWCOMER["email"]) is not None


# Sending


class FakeSmtp:
    instances = []

    def __init__(self, host, port, timeout):
        self.calls = [("connect", host, port)]
        FakeSmtp.instances.append(self)

    def starttls(self):
        self.calls.append(("starttls",))

    def login(self, username, password):
        self.calls.append(("login", username, password))

    def send_message(self, email, to_addrs):
        self.calls.append(("send", to_addrs))

    def close(self):
        self.calls.append(("close",))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@pytest.fixture
def fake_smtp(mock_app, monkeypatch):
    FakeSmtp.instances = []
    monkeypatch.setattr(smtplib, "SMTP", FakeSmtp)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSmtp)
    mock_app.config["TESTING"] = False
    return FakeSmtp.instances


@pytest.mark.parametrize(
    ("port", "starttls"), [(587, [("starttls",)]), (465, [])], ids=["starttls", "ssl"]
)
def test_send_uses_smtp_with_the_configured_account(mock_app, fake_smtp, port, starttls):
    mock_app.config["SMTP_PORT"] = port
    with mock_app.app_context():
        mail.send("alice@example.com", "Sujet", "Corps")

    assert fake_smtp[0].calls == [
        ("connect", "smtp.example.com", port),
        *starttls,
        ("login", "outillerie", "smtp-secret"),
        ("send", ["alice@example.com"]),
        ("close",),
    ]


def test_development_without_smtp_logs_the_email(mock_app, caplog):
    mock_app.config.update(TESTING=False, SMTP_HOST=None)

    with mock_app.app_context():
        mail.send("alice@example.com", "Sujet", "Le lien")

    assert "Le lien" in caplog.text


# The confirmation page


def test_link_opens_a_page_with_the_button_without_confirming(mock_app, client, newcomer_link):
    response = client.get(newcomer_link)

    assert response.status_code == 200
    assert "Confirmer mon courriel" in page_text(response)
    assert '<button type="submit" class="button primary">Confirmer mon courriel' in (
        page_text(response)
    )
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert not is_confirmed(mock_app, NEWCOMER["email"])


def test_expired_link_shows_its_message_without_button(client, mail_outbox, clock):
    register(client)
    clock.advance(31 * DAY)

    text_ = page_text(client.get(link_in(mail_outbox[0])))

    assert email_confirmation.EXPIRED in text_
    assert "button primary" not in text_.split("<main")[1]


def altered(link):
    return link[:-3] + ("abc" if not link.endswith("abc") else "xyz")


def deleted(mock_app):
    with mock_app.app_context():
        db.session.execute(
            text('UPDATE "user" SET email = NULL, deleted_at = now() WHERE email = :e'),
            {"e": NEWCOMER["email"]},
        )
        db.session.commit()


def changed_email(mock_app):
    with mock_app.app_context():
        db.session.execute(
            text('UPDATE "user" SET email = :new WHERE email = :e'),
            {"e": NEWCOMER["email"], "new": "autre@example.com"},
        )
        db.session.commit()


@pytest.mark.parametrize("break_link", ["altered", "deleted", "changed_email"])
def test_invalid_link_shows_its_message_without_button(mock_app, client, newcomer_link, break_link):
    link = newcomer_link
    if break_link == "altered":
        link = altered(link)
    elif break_link == "deleted":
        deleted(mock_app)
    else:
        changed_email(mock_app)

    text_ = page_text(client.get(link))

    assert email_confirmation.INVALID in text_
    assert "button primary" not in text_.split("<main")[1]


# Confirming


def test_confirming_without_session_leads_to_login_without_one(mock_app, client, newcomer_link):
    response = confirm(client, newcomer_link)

    assert response.headers["Location"] == "/login"
    assert is_confirmed(mock_app, NEWCOMER["email"])
    assert email_confirmation.CONFIRMED in page_text(client.get("/login"))
    assert client.get("/profile").headers["Location"].startswith("/login")


def test_confirming_with_another_session_confirms_the_link_account(
    mock_app, client, mail_outbox, unconfirmed
):
    register(client)
    link = link_in(mail_outbox[0])
    as_denis = login(mock_app.test_client(), unconfirmed)

    response = confirm(as_denis, link)

    assert response.headers["Location"] == "/profile"
    assert is_confirmed(mock_app, NEWCOMER["email"])
    assert not is_confirmed(mock_app, unconfirmed)
    assert email_confirmation.CONFIRMED in page_text(as_denis.get("/profile"))


def test_confirming_twice_confirms_once(mock_app, client, newcomer_link):
    page = client.get(newcomer_link)
    token = token_field(page)

    client.post("/confirmer-courriel", data={"token": token})
    first = account(mock_app, NEWCOMER["email"]).email_confirmed_at
    second = client.post("/confirmer-courriel", data={"token": token})

    assert second.headers["Location"] == "/login"
    assert email_confirmation.CONFIRMED in page_text(client.get("/login"))
    assert account(mock_app, NEWCOMER["email"]).email_confirmed_at == first


def referer_sent_by_a_browser(page, page_url):
    """The Referer a browser sends to the same site from this page, following its policy"""
    policy = page.headers.get("Referrer-Policy", "strict-origin-when-cross-origin")
    return None if policy == "no-referrer" else page_url


def test_confirming_over_https_passes_the_csrf_check(mock_app, client, newcomer_link):
    # Over HTTPS, Flask-WTF also requires a same-origin Referer (WTF_CSRF_SSL_STRICT).
    mock_app.config["WTF_CSRF_ENABLED"] = True
    page_url = f"https://localhost{newcomer_link}"
    page = client.get(page_url)
    referer = referer_sent_by_a_browser(page, page_url)

    response = client.post(
        "https://localhost/confirmer-courriel",
        data={"token": token_field(page), "csrf_token": token_in(page)},
        headers={"Referer": referer} if referer else {},
    )

    assert response.status_code == 302
    assert is_confirmed(mock_app, NEWCOMER["email"])


def test_confirming_requires_the_csrf_token(mock_app, client, newcomer_link):
    mock_app.config["WTF_CSRF_ENABLED"] = True
    page = client.get(newcomer_link)

    refused = client.post("/confirmer-courriel", data={"token": token_field(page)})

    assert refused.status_code == 400
    assert not is_confirmed(mock_app, NEWCOMER["email"])
    client.post(
        "/confirmer-courriel", data={"token": token_field(page), "csrf_token": token_in(page)}
    )
    assert is_confirmed(mock_app, NEWCOMER["email"])


def test_link_expired_between_opening_and_sending(mock_app, client, mail_outbox, clock):
    register(client)
    page = client.get(link_in(mail_outbox[0]))
    clock.advance(31 * DAY)

    response = client.post("/confirmer-courriel", data={"token": token_field(page)})

    assert email_confirmation.EXPIRED in page_text(response)
    assert not is_confirmed(mock_app, NEWCOMER["email"])


def test_request_line_logged_without_the_token(mock_app, caplog):
    with caplog.at_level(logging.INFO, logger="werkzeug"):
        logging.getLogger("werkzeug").info(
            "%s - - [%s] %s",
            "127.0.0.1",
            "22/Nov/2026 10:00:00",
            '"GET /confirmer-courriel/eyJpZCI6MX0.abc.def HTTP/1.1" 200 -',
        )

    assert "/confirmer-courriel/…" in caplog.text
    assert "eyJpZCI6MX0" not in caplog.text


# Profile, badge and resending


def test_unconfirmed_account_has_a_badge_on_my_profile(mock_app, unconfirmed):
    page = page_text(login(mock_app.test_client(), unconfirmed).get("/profile"))

    assert re.search(
        r'Mon profil <span class="badge">1 <span class="visually-hidden">courriel', page
    )
    assert badges(page) == ["1", "1"]


def test_confirmed_account_has_no_badge(logged_in_client):
    page = page_text(logged_in_client.get("/profile"))

    assert badges(page) == []
    assert "Renvoyer le courriel" not in page
    assert "n'est pas confirmé" not in page


def test_account_badge_counts_the_email_to_confirm(mock_app, user, unconfirmed):
    with mock_app.app_context():
        make_contact_request(user_id(user), user_id(unconfirmed))

    page = page_text(login(mock_app.test_client(), unconfirmed).get("/"))

    summary = page.split("<summary>")[1].split("</summary>")[0]
    assert badges(summary) == ["2"]


def test_unconfirmed_profile_starts_with_the_banner(mock_app, unconfirmed):
    page = page_text(login(mock_app.test_client(), unconfirmed).get("/profile"))

    content = page.split("<h2>Mon profil</h2>")[1]
    assert content.index("Votre courriel n'est pas confirmé. Confirmez-le avec le lien reçu à ") < (
        content.index("Courriel : ")
    )
    assert "denis@example.com pour emprunter et accepter des demandes." in content
    assert '<button type="submit" class="button primary">Renvoyer le courriel</button>' in content


def resend(client):
    return client.post("/profile/courriel/renvoyer")


def test_resend_after_the_delay(mock_app, unconfirmed, mail_outbox):
    sent_minutes_ago(mock_app, unconfirmed, 6)
    as_denis = login(mock_app.test_client(), unconfirmed)

    response = resend(as_denis)

    assert response.headers["Location"] == "/profile"
    assert [email["To"] for email in mail_outbox] == [unconfirmed]
    assert "Courriel de confirmation envoyé à denis@example.com." in page_text(
        as_denis.get("/profile")
    )


def test_resend_too_soon_sends_nothing(mock_app, unconfirmed, mail_outbox):
    sent_minutes_ago(mock_app, unconfirmed, 2)
    as_denis = login(mock_app.test_client(), unconfirmed)

    resend(as_denis)

    assert mail_outbox == []
    assert (
        "Un courriel vous a été envoyé il y a moins de 5 minutes. Réessayez dans 3 minute(s)."
        in page_text(as_denis.get("/profile"))
    )


def test_two_resends_in_a_row_send_once(mock_app, unconfirmed, mail_outbox):
    as_denis = login(mock_app.test_client(), unconfirmed)

    resend(as_denis)
    resend(as_denis)

    assert len(mail_outbox) == 1


def test_resend_for_a_confirmed_account_sends_nothing(logged_in_client, mail_outbox):
    resend(logged_in_client)

    assert mail_outbox == []
    assert email_confirmation.ALREADY_CONFIRMED in page_text(logged_in_client.get("/profile"))


def test_old_link_still_confirms_after_a_resend(mock_app, client, mail_outbox, clock):
    register(client)
    old_link = link_in(mail_outbox[0])
    clock.advance(10 * DAY)
    sent_minutes_ago(mock_app, NEWCOMER["email"], 10 * 24 * 60)
    as_eve = mock_app.test_client()
    as_eve.post("/login", data={"email": NEWCOMER["email"], "password": NEWCOMER["password"]})
    resend(as_eve)
    assert len(mail_outbox) == 2

    confirm(mock_app.test_client(), old_link)

    assert is_confirmed(mock_app, NEWCOMER["email"])


def test_resend_requires_the_csrf_token(mock_app, unconfirmed, mail_outbox):
    mock_app.config["WTF_CSRF_ENABLED"] = True
    as_denis = mock_app.test_client()
    page = as_denis.get("/login")
    as_denis.post(
        "/login",
        data={"email": unconfirmed, "password": USER_PASSWORD, "csrf_token": token_in(page)},
    )

    assert resend(as_denis).status_code == 400
    assert mail_outbox == []


# Borrowing and accepting


@pytest.fixture
def denis_and_bob(mock_app, bob, unconfirmed):
    """Denis, unconfirmed, and Bob are contacts; each has a drill"""
    with mock_app.app_context():
        ids = {"bob": user_id(bob), "denis": user_id(unconfirmed)}
        make_contact_relation(ids["bob"], ids["denis"])
    ids["bob_drill"] = add_tool(mock_app, ids["bob"])
    ids["denis_drill"] = add_tool(mock_app, ids["denis"])
    return ids


@pytest.fixture
def as_denis(mock_app, denis_and_bob, unconfirmed):
    return login(mock_app.test_client(), unconfirmed)


def loan_count(mock_app):
    with mock_app.app_context():
        return Loan.query.count()


def test_unconfirmed_card_greys_out_borrow(as_denis, denis_and_bob):
    page = page_text(as_denis.get(f"/contacts/{denis_and_bob['bob']}"))

    assert '<button type="button" class="button" disabled>Emprunter</button>' in page
    assert f"/loans/new/{denis_and_bob['bob_drill']}" not in page


def test_unconfirmed_request_page_sends_back(as_denis, denis_and_bob):
    response = as_denis.get(f"/loans/new/{denis_and_bob['bob_drill']}")

    assert response.headers["Location"] == "/tools/find"
    assert email_confirmation.TO_BORROW in page_text(as_denis.get("/tools/find"))


def test_unconfirmed_forged_request_creates_nothing(mock_app, as_denis, denis_and_bob):
    today = catalog.site_today()
    response = as_denis.post(
        f"/loans/new/{denis_and_bob['bob_drill']}",
        data={
            "start": today.isoformat(),
            "end": (today + timedelta(days=2)).isoformat(),
            "origin": "contact",
        },
    )

    assert response.headers["Location"] == f"/contacts/{denis_and_bob['bob']}"
    assert loan_count(mock_app) == 0
    assert email_confirmation.TO_BORROW in page_text(as_denis.get("/"))


@pytest.fixture
def bob_asks_denis(mock_app, denis_and_bob):
    today = catalog.site_today()
    return add_loan(
        mock_app,
        denis_and_bob["denis_drill"],
        denis_and_bob["bob"],
        today + timedelta(days=1),
        today + timedelta(days=3),
    )


def loan_status(mock_app, loan_id):
    with mock_app.app_context():
        return db.session.get(Loan, loan_id).status


def test_unconfirmed_owner_sees_accept_greyed_out(as_denis, bob_asks_denis):
    for path in ("/loans", "/"):
        page = page_text(as_denis.get(path))

        assert '<button type="button" class="button" disabled>Accepter</button>' in page
        assert f"/loans/{bob_asks_denis}/refuse" in page
        assert f"/loans/{bob_asks_denis}/accept" not in page


def test_unconfirmed_forged_acceptance_changes_nothing(mock_app, as_denis, bob_asks_denis):
    response = as_denis.post(f"/loans/{bob_asks_denis}/accept")

    assert response.headers["Location"] == "/loans"
    assert loan_status(mock_app, bob_asks_denis) == LoanStatus.REQUESTED
    assert email_confirmation.TO_ACCEPT in page_text(as_denis.get("/loans"))


def test_unconfirmed_owner_may_refuse(mock_app, as_denis, bob_asks_denis):
    as_denis.post(f"/loans/{bob_asks_denis}/refuse")

    assert loan_status(mock_app, bob_asks_denis) == LoanStatus.REFUSED


def test_unconfirmed_owner_follows_an_accepted_loan(mock_app, as_denis, bob_asks_denis):
    with mock_app.app_context():
        db.session.get(Loan, bob_asks_denis).status = LoanStatus.ACCEPTED
        db.session.commit()

    as_denis.post(f"/loans/{bob_asks_denis}/hand-over")

    assert loan_status(mock_app, bob_asks_denis) == LoanStatus.HANDOVER_CLAIMED


def test_confirmed_borrower_still_requests(mock_app, bob, denis_and_bob):
    as_bob = login(mock_app.test_client(), bob)
    today = catalog.site_today()

    as_bob.post(
        f"/loans/new/{denis_and_bob['denis_drill']}",
        data={"start": today.isoformat(), "end": (today + timedelta(days=2)).isoformat()},
    )

    assert loan_count(mock_app) == 1
