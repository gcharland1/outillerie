import re
import threading
import time
from datetime import timedelta
from html import unescape

import pytest
from sqlalchemy import select, text
from werkzeug.security import check_password_hash, generate_password_hash

from app import catalog, photos, profile
from app.contacts import lock_live_accounts
from app.extensions import db
from models import ContactRelation, ContactRequest, Loan, LoanStatus, Tool, ToolCondition, User
from tests.conftest import USER_PASSWORD, add_loan, add_tool, log_in_with_page_token, login
from tests.factories import make_contact_relation, make_contact_request, user_id

SAVED = "Votre profil a été enregistré"
BLOCKED = "Tous vos prêts en cours doivent être complétés avant de supprimer votre compte"
MISMATCH = "Le nom ou le mot de passe ne correspond pas"
TODAY = catalog.site_today()


def days(offset):
    return TODAY + timedelta(days=offset)


def page_text(response):
    return unescape(response.get_data(as_text=True))


def account(mock_app, account_id):
    """The account's fields as the database holds them"""
    with mock_app.app_context():
        user = db.session.get(User, account_id)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "address": user.address,
            "phone": user.phone,
            "deleted_at": user.deleted_at,
        }


def set_account(mock_app, account_id, **fields):
    with mock_app.app_context():
        user = db.session.get(User, account_id)
        for name, value in fields.items():
            setattr(user, name, value)
        db.session.commit()


def field_value(text, name):
    return unescape(re.search(rf'name="{name}" value="([^"]*)"', text)[1])


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {email.partition("@")[0]: user_id(email) for email in (user, bob, carole)}


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice@example.com")


# Profil réservé à un utilisateur connecté


def test_visitor_is_sent_to_login(client):
    response = client.get("/profile", follow_redirects=True)

    assert response.request.path == "/login"
    assert "Veuillez vous connecter pour accéder à cette page" in page_text(response)


@pytest.mark.parametrize("path", ["/profile/delete"])
def test_visitor_cannot_open_the_confirmation(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")


def test_visitor_posts_change_nothing(mock_app, ids, csrf_client):
    token = re.search(r'name="csrf_token" value="([^"]+)"', page_text(csrf_client.get("/login")))[1]
    before = account(mock_app, ids["alice"])

    for path, data in [
        ("/profile/delete", {"name": "Alice Tremblay", "password": USER_PASSWORD}),
        ("/profile", {"address": "8 avenue du Parc", "phone": ""}),
    ]:
        response = csrf_client.post(path, data={**data, "csrf_token": token})
        assert response.status_code == 302, path
        assert response.headers["Location"].startswith("/login"), path

    assert account(mock_app, ids["alice"]) == before


# Informations du profil


def test_profile_page_shows_name_and_email_as_text(mock_app, ids, as_alice):
    set_account(mock_app, ids["alice"], address="12 rue des Érables")

    text = page_text(as_alice.get("/profile"))

    assert "<h3>Alice Tremblay</h3>" in text
    assert "alice@example.com" in text
    assert field_value(text, "address") == "12 rue des Érables"
    assert field_value(text, "phone") == ""
    for name in ("first_name", "last_name", "email"):
        assert f'name="{name}"' not in text
    assert '<button type="submit" class="button primary">Enregistrer</button>' in text


def test_own_name_is_not_a_link(as_alice):
    text = page_text(as_alice.get("/profile"))

    assert "<h3>Alice Tremblay</h3>" in text
    assert 'href="/contacts/' not in text


# Modification de l'adresse et du téléphone


def save(client, address="", phone="", **fields):
    return client.post("/profile", data={"address": address, "phone": phone, **fields})


def test_phone_is_stripped_and_kept_as_typed(mock_app, ids, as_alice):
    response = as_alice.post(
        "/profile", data={"address": "", "phone": " (418) 555-0123 "}, follow_redirects=True
    )

    assert account(mock_app, ids["alice"])["phone"] == "(418) 555-0123"
    assert response.request.path == "/profile"
    assert f'<div class="flash flash-success">{SAVED}</div>' in page_text(response)


def test_address_is_replaced(mock_app, ids, as_alice):
    set_account(mock_app, ids["alice"], address="12 rue des Érables")

    save(as_alice, address="8 avenue du Parc")

    assert account(mock_app, ids["alice"])["address"] == "8 avenue du Parc"


@pytest.mark.parametrize("address", ["", "   "])
def test_empty_address_is_removed(mock_app, ids, as_alice, address):
    set_account(mock_app, ids["alice"], address="12 rue des Érables", phone="418")

    save(as_alice, address=address, phone="")

    assert account(mock_app, ids["alice"])["address"] is None
    assert account(mock_app, ids["alice"])["phone"] is None


def test_name_and_email_sent_are_ignored(mock_app, ids, as_alice):
    save(
        as_alice,
        address="8 avenue du Parc",
        first_name="Eve",
        last_name="Roy",
        email="eve@example.com",
    )

    stored = account(mock_app, ids["alice"])
    assert (stored["first_name"], stored["last_name"], stored["email"]) == (
        "Alice",
        "Tremblay",
        "alice@example.com",
    )
    assert stored["address"] == "8 avenue du Parc"


# Validation de l'adresse et du téléphone


def test_limits_are_the_columns_lengths():
    assert (profile.ADDRESS_MAX_LENGTH, profile.PHONE_MAX_LENGTH) == (250, 20)


def test_too_long_address_saves_nothing(mock_app, ids, as_alice):
    set_account(mock_app, ids["alice"], address="12 rue des Érables", phone="418")
    address = "a" * 251

    text = page_text(save(as_alice, address=f" {address} ", phone="(418) 555-0123"))

    assert "L'adresse ne doit pas dépasser 250 caractères" in text
    assert SAVED not in text
    assert field_value(text, "address") == address
    assert field_value(text, "phone") == "(418) 555-0123"
    stored = account(mock_app, ids["alice"])
    assert (stored["address"], stored["phone"]) == ("12 rue des Érables", "418")


def test_limit_lengths_are_accepted(mock_app, ids, as_alice):
    save(as_alice, address="a" * 250, phone="1" * 20)

    stored = account(mock_app, ids["alice"])
    assert (stored["address"], stored["phone"]) == ("a" * 250, "1" * 20)


def test_too_long_phone_is_refused(mock_app, ids, as_alice):
    text = page_text(save(as_alice, phone="1" * 21))

    assert "Le téléphone ne doit pas dépasser 20 caractères" in text
    assert account(mock_app, ids["alice"])["phone"] is None


def test_phone_with_other_characters_is_refused(mock_app, ids, as_alice):
    text = page_text(save(as_alice, phone="418-555-0123 poste 4"))

    assert (
        "Le téléphone ne peut contenir que des chiffres, des espaces et les caractères + - ( ) ."
        in text
    )
    assert account(mock_app, ids["alice"])["phone"] is None
    assert field_value(text, "phone") == "418-555-0123 poste 4"


def test_every_error_is_shown(mock_app, ids, as_alice):
    text = page_text(save(as_alice, address="a" * 251, phone="x" * 21))

    assert len(re.findall(r'<div class="flash flash-message">', text)) == 3


def test_address_is_shown_as_text(mock_app, ids, as_alice):
    save(as_alice, address="<script>alert(1)</script>")

    raw = as_alice.get("/profile").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in raw
    assert 'value="&lt;script&gt;alert(1)&lt;/script&gt;"' in raw


def test_profile_without_csrf_token_is_refused(mock_app, ids, csrf_client):
    log_in_with_page_token(csrf_client, "alice@example.com", USER_PASSWORD)

    response = save(csrf_client, address="8 avenue du Parc")

    assert response.status_code == 400
    assert account(mock_app, ids["alice"])["address"] is None


# Section « Supprimer mon compte »

DELETE_LINK = '<a class="button error" href="/profile/delete">Supprimer mon compte</a>'
DISABLED_BUTTON = '<button type="button" class="button" disabled>Supprimer mon compte</button>'


def deletion_section(text):
    return re.search(r"<h3>Supprimer mon compte</h3>(.*?)</section>", text, re.DOTALL)[1]


def section_rows(text):
    rows = re.findall(r"<tr>(.*?)</tr>", deletion_section(text), re.DOTALL)[1:]
    return [re.findall(r"<td>(.*?)</td>", row, re.DOTALL) for row in rows]


def test_section_without_loan_in_progress(as_alice):
    text = page_text(as_alice.get("/profile"))

    assert "<section" not in text.split("<h3>Supprimer mon compte</h3>")[1]
    section = deletion_section(text)
    assert "La suppression de votre compte est irréversible." in section
    assert DELETE_LINK in section
    assert BLOCKED not in section


def test_borrowing_in_progress_blocks_the_deletion(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    add_loan(mock_app, drill, ids["alice"], days(-1), days(2), LoanStatus.LENT)

    section = deletion_section(page_text(as_alice.get("/profile")))

    assert DISABLED_BUTTON in section
    assert DELETE_LINK not in section
    assert BLOCKED in section
    assert section_rows(page_text(as_alice.get("/profile"))) == [
        ["Perceuse", "Bob Gagnon", "Prêté"]
    ]
    assert '<a class="button" href="/loans">Mes prêts</a>' in section


def test_overdue_loan_blocks_the_deletion(mock_app, ids, as_alice):
    saw = add_tool(mock_app, ids["alice"], "Scie")
    add_loan(mock_app, saw, ids["bob"], days(-5), days(-1), LoanStatus.LENT)

    text = page_text(as_alice.get("/profile"))

    assert section_rows(text) == [["Scie", "Bob Gagnon", "En retard"]]
    assert DISABLED_BUTTON in deletion_section(text)


def test_claimed_handover_and_return_block_the_deletion(mock_app, ids, as_alice):
    plane = add_tool(mock_app, ids["alice"], "Rabot")
    sander = add_tool(mock_app, ids["alice"], "Ponceuse")
    add_loan(mock_app, plane, ids["bob"], days(0), days(2), LoanStatus.HANDOVER_CLAIMED)
    add_loan(mock_app, sander, ids["carole"], days(-3), days(3), LoanStatus.RETURN_CLAIMED)

    text = page_text(as_alice.get("/profile"))

    assert sorted(section_rows(text)) == [
        ["Ponceuse", "Carole Roy", "Retour à confirmer"],
        ["Rabot", "Bob Gagnon", "Remise à confirmer"],
    ]
    assert DISABLED_BUTTON in deletion_section(text)


def test_requests_and_acceptances_do_not_block(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    saw = add_tool(mock_app, ids["alice"], "Scie")
    add_loan(mock_app, drill, ids["alice"], days(1), days(2))
    add_loan(mock_app, saw, ids["carole"], days(1), days(2), LoanStatus.ACCEPTED)

    section = deletion_section(page_text(as_alice.get("/profile")))

    assert DELETE_LINK in section
    assert BLOCKED not in section


def test_confirmation_with_a_loan_in_progress_goes_back_to_profile(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    add_loan(mock_app, drill, ids["alice"], days(-1), days(2), LoanStatus.LENT)

    response = as_alice.get("/profile/delete", follow_redirects=True)

    assert response.request.path == "/profile"
    assert f'<div class="flash flash-message">{BLOCKED}</div>' in page_text(response)


# Page de confirmation de la suppression


def test_confirmation_page_without_cancellation(mock_app, ids, as_alice):
    text = page_text(as_alice.get("/profile/delete"))

    assert "La suppression de votre compte est irréversible." in text
    assert re.search(r'<input type="text" id="name" name="name" value=""', text)
    assert 'autocomplete="off"' in text
    assert (
        '<input type="password" id="password" name="password" autocomplete="current-password"'
        in text
    )
    assert '<a class="button" href="/profile">Annuler</a>' in text
    assert '<button type="submit" class="button error">Confirmer la suppression</button>' in text
    assert "annulé" not in text
    assert account(mock_app, ids["alice"])["deleted_at"] is None


def test_confirmation_announces_the_cancellations(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    saw = add_tool(mock_app, ids["alice"], "Scie")
    add_loan(mock_app, drill, ids["alice"], days(1), days(2))
    add_loan(mock_app, saw, ids["carole"], days(1), days(2), LoanStatus.ACCEPTED)

    text = page_text(as_alice.get("/profile/delete"))

    assert "1 demande d'emprunt en attente et 1 prêt accepté seront annulés" in text


def test_cancel_leads_back_to_profile_without_deleting(mock_app, ids, as_alice):
    text = page_text(as_alice.get("/profile/delete"))
    cancel_url = re.search(r'<a class="button" href="([^"]+)">Annuler</a>', text)[1]

    assert as_alice.get(cancel_url).status_code == 200
    assert cancel_url == "/profile"
    assert account(mock_app, ids["alice"])["deleted_at"] is None


# Vérification avant la suppression


def delete_account(client, name="Alice Tremblay", password=USER_PASSWORD, **options):
    return client.post("/profile/delete", data={"name": name, "password": password}, **options)


def is_deleted(mock_app, account_id):
    return account(mock_app, account_id)["deleted_at"] is not None


def add_account(mock_app, email, first_name, last_name):
    with mock_app.app_context():
        user = User(
            password=generate_password_hash(USER_PASSWORD, method="pbkdf2:sha256"),
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def test_name_without_accents_nor_capitals(mock_app):
    elise = add_account(mock_app, "elise@example.com", "Élise", "Côté-Roy")
    client = login(mock_app.test_client(), "elise@example.com")

    delete_account(client, name="  elise cote   roy ")

    assert is_deleted(mock_app, elise)


def test_wrong_name_deletes_nothing(mock_app, ids, as_alice):
    response = delete_account(as_alice, name="Alice")

    text = page_text(response)
    assert response.status_code == 200
    assert MISMATCH in text
    assert field_value(text, "name") == "Alice"
    assert re.search(r'<input type="password" id="password" name="password" autocomplete', text)
    assert USER_PASSWORD not in text
    assert not is_deleted(mock_app, ids["alice"])


def test_wrong_password_deletes_nothing(mock_app, ids, as_alice):
    text = page_text(delete_account(as_alice, password="mauvais"))

    assert MISMATCH in text
    assert not is_deleted(mock_app, ids["alice"])


def test_empty_fields_delete_nothing(mock_app, ids, as_alice):
    text = page_text(delete_account(as_alice, name="", password=""))

    assert MISMATCH in text
    assert not is_deleted(mock_app, ids["alice"])


def test_name_of_spaces_only_never_matches(mock_app, ids, as_alice):
    set_account(mock_app, ids["alice"], first_name=" ", last_name="-")

    assert MISMATCH in page_text(delete_account(as_alice, name="  "))
    assert not is_deleted(mock_app, ids["alice"])


def test_get_deletes_nothing(mock_app, ids, as_alice):
    as_alice.get("/profile/delete")
    as_alice.get("/profile/delete?name=Alice+Tremblay&password=" + USER_PASSWORD)

    assert not is_deleted(mock_app, ids["alice"])


def test_deletion_without_csrf_token_is_refused(mock_app, ids, csrf_client):
    log_in_with_page_token(csrf_client, "alice@example.com", USER_PASSWORD)

    response = delete_account(csrf_client)

    assert response.status_code == 400
    assert not is_deleted(mock_app, ids["alice"])


def test_deletion_with_page_token(mock_app, ids, csrf_client):
    log_in_with_page_token(csrf_client, "alice@example.com", USER_PASSWORD)
    token = re.search(
        r'name="csrf_token" value="([^"]+)"', page_text(csrf_client.get("/profile/delete"))
    )[1]

    csrf_client.post(
        "/profile/delete",
        data={"name": "Alice Tremblay", "password": USER_PASSWORD, "csrf_token": token},
    )

    assert is_deleted(mock_app, ids["alice"])


def loan_status(mock_app, loan_id):
    with mock_app.app_context():
        return db.session.get(Loan, loan_id).status


def test_forged_deletion_with_a_loan_in_progress(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    loan = add_loan(mock_app, drill, ids["alice"], days(-1), days(2), LoanStatus.LENT)

    response = delete_account(as_alice)

    assert response.headers["Location"] == "/profile"
    assert not is_deleted(mock_app, ids["alice"])
    assert loan_status(mock_app, loan) == LoanStatus.LENT


def test_handover_claimed_after_opening_the_confirmation(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    loan = add_loan(mock_app, drill, ids["alice"], days(0), days(2), LoanStatus.ACCEPTED)
    as_alice.get("/profile/delete")
    as_bob = login(mock_app.test_client(), "bob@example.com")
    as_bob.post(f"/loans/{loan}/hand-over")

    response = delete_account(as_alice, follow_redirects=True)

    assert response.request.path == "/profile"
    assert BLOCKED in page_text(response)
    assert not is_deleted(mock_app, ids["alice"])
    assert loan_status(mock_app, loan) == LoanStatus.HANDOVER_CLAIMED


# Effet de la suppression


def test_personal_data_are_erased(mock_app, ids, as_alice):
    set_account(mock_app, ids["alice"], address="12 rue des Érables", phone="418 555-0123")

    delete_account(as_alice)

    stored = account(mock_app, ids["alice"])
    assert stored["deleted_at"] is not None
    assert (stored["email"], stored["address"], stored["phone"]) == (None, None, None)
    assert (stored["first_name"], stored["last_name"]) == ("Alice", "Tremblay")
    with mock_app.app_context():
        password = db.session.get(User, ids["alice"]).password
    assert not check_password_hash(password, USER_PASSWORD)


def test_contacts_are_undone_both_ways(mock_app, ids, as_alice):
    denis = add_account(mock_app, "denis@example.com", "Denis", "Roy")
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
        make_contact_relation(ids["bob"], ids["carole"])
        make_contact_request(ids["carole"], ids["alice"])
        make_contact_request(ids["alice"], denis)
        make_contact_request(ids["bob"], denis)

    delete_account(as_alice)

    with mock_app.app_context():
        relations = db.session.execute(
            select(ContactRelation.user_a_id, ContactRelation.user_b_id)
        ).all()
        requests = db.session.execute(
            select(ContactRequest.requester_id, ContactRequest.recipient_id)
        ).all()
    assert relations == [tuple(sorted((ids["bob"], ids["carole"])))]
    assert requests == [(ids["bob"], denis)]
    as_bob = login(mock_app.test_client(), "bob@example.com")
    assert "Alice Tremblay" not in page_text(as_bob.get("/contacts"))


def test_tools_are_retired_and_emptied(mock_app, ids, as_alice, jpeg_photo):
    drill = add_tool(
        mock_app,
        ids["alice"],
        "Perceuse",
        description="Perceuse sans fil",
        private_notes="Achetée en 2020",
        condition=ToolCondition.NEEDS_REPAIR,
    )
    with mock_app.app_context():
        photos.save_photo(db.session.get(Tool, drill), jpeg_photo)
        db.session.commit()

    delete_account(as_alice)

    with mock_app.app_context():
        tool = db.session.get(Tool, drill)
        assert (tool.name, tool.condition) == ("Perceuse", ToolCondition.NEEDS_REPAIR)
        assert (tool.is_active, tool.description, tool.private_notes) == (False, "", None)
        assert photos.tool_ids_with_photo([drill]) == set()


def test_unstarted_loans_are_cancelled_both_ways(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    saw = add_tool(mock_app, ids["alice"], "Scie")
    request = add_loan(mock_app, drill, ids["alice"], days(1), days(2))
    acceptance = add_loan(mock_app, saw, ids["carole"], days(1), days(2), LoanStatus.ACCEPTED)

    delete_account(as_alice)

    assert loan_status(mock_app, request) == LoanStatus.CANCELED
    assert loan_status(mock_app, acceptance) == LoanStatus.CANCELED


def test_alices_messages_are_erased_others_kept(mock_app, ids, as_alice):
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    saw = add_tool(mock_app, ids["alice"], "Scie")
    borrowed = add_loan(
        mock_app, drill, ids["alice"], days(-9), days(-8), LoanStatus.RETURNED, "Pour la terrasse"
    )
    lent = add_loan(mock_app, saw, ids["bob"], days(-7), days(-6), LoanStatus.RETURNED, "Merci")

    delete_account(as_alice)

    with mock_app.app_context():
        assert db.session.get(Loan, borrowed).message is None
        assert db.session.get(Loan, lent).message == "Merci"
        assert {loan.status for loan in Loan.query.all()} == {LoanStatus.RETURNED}


def test_two_deletions(mock_app, ids, as_alice):
    delete_account(as_alice)
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")

    assert is_deleted(mock_app, ids["alice"])
    assert is_deleted(mock_app, ids["bob"])


# Fin de session après la suppression


def test_deletion_ends_the_session(mock_app, ids, as_alice):
    response = delete_account(as_alice)

    assert response.headers["Location"] == "/logged-out?reason=account-deleted"
    assert "Votre compte a été supprimé" in page_text(as_alice.get(response.headers["Location"]))
    followed = as_alice.get("/profile")
    assert followed.headers["Location"].startswith("/login")


# Écritures concurrentes


def waits_for_a_lock(mock_app, thread):
    """Whether a session of the test database comes to wait for a lock before the thread ends"""
    with mock_app.app_context():
        engine = db.engine
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and thread.is_alive():
        with engine.connect() as connection:
            waiting = connection.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
        if waiting:
            return True
        time.sleep(0.05)
    return False


def in_thread(function):
    """The started thread running the function, and the list that gets its result or error"""
    results = []

    def run():
        try:
            results.append(function())
        except Exception as error:
            results.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    return thread, results


def test_deletion_waits_for_a_handover_then_is_refused(mock_app, ids, as_alice):
    saw = add_tool(mock_app, ids["alice"], "Scie")
    loan = add_loan(mock_app, saw, ids["bob"], days(0), days(2), LoanStatus.ACCEPTED)
    with mock_app.app_context():
        engine = db.engine

    with engine.connect() as handover:
        handover.execute(
            text("UPDATE loan SET status = 'handover_claimed' WHERE id = :id"), {"id": loan}
        )
        thread, results = in_thread(lambda: delete_account(as_alice))
        try:
            assert waits_for_a_lock(mock_app, thread)
            handover.commit()
        finally:
            handover.rollback()
            thread.join(10)

    assert results[0].headers["Location"] == "/profile"
    assert not is_deleted(mock_app, ids["alice"])
    assert loan_status(mock_app, loan) == LoanStatus.HANDOVER_CLAIMED


def test_profile_sent_during_a_deletion_writes_nothing(mock_app, ids, monkeypatch):
    first_tab = login(mock_app.test_client(), "alice@example.com")
    second_tab = login(mock_app.test_client(), "alice@example.com")
    locked, resume = threading.Event(), threading.Event()
    cancel_unstarted_loans = catalog.cancel_unstarted_loans

    def pausing(*conditions):
        locked.set()
        resume.wait(10)
        return cancel_unstarted_loans(*conditions)

    monkeypatch.setattr(catalog, "cancel_unstarted_loans", pausing)
    deletion, deleted = in_thread(lambda: delete_account(first_tab))
    sending, sent = None, []
    try:
        assert locked.wait(10)
        sending, sent = in_thread(
            lambda: save(second_tab, address="8 avenue du Parc", phone="418 555-0123")
        )
        assert waits_for_a_lock(mock_app, sending)
    finally:
        resume.set()
        deletion.join(10)
        if sending is not None:
            sending.join(10)

    stored = account(mock_app, ids["alice"])
    assert (stored["address"], stored["phone"]) == (None, None)
    assert stored["deleted_at"] is not None
    assert deleted[0].headers["Location"] == "/logged-out?reason=account-deleted"
    assert sent[0].headers["Location"].startswith("/login")
    assert second_tab.get("/profile").headers["Location"].startswith("/login")


# Sessions d'un compte supprimé


def test_session_in_another_browser_ends(mock_app, ids):
    computer = login(mock_app.test_client(), "alice@example.com")
    phone = login(mock_app.test_client(), "alice@example.com")
    assert phone.get("/profile").status_code == 200

    delete_account(computer)

    assert phone.get("/profile").headers["Location"].startswith("/login")


def test_copied_cookie_is_a_visitors(mock_app, ids, as_alice):
    cookie = as_alice.get_cookie("session").value
    delete_account(as_alice)

    replay = mock_app.test_client()
    replay.set_cookie("session", cookie)

    assert replay.get("/profile").headers["Location"].startswith("/login")
    assert 'class="account-menu"' not in page_text(replay.get("/login"))


def test_deleted_account_cannot_log_in(mock_app, ids, as_alice):
    delete_account(as_alice)
    client = mock_app.test_client()

    deleted = client.post("/login", data={"email": "alice@example.com", "password": USER_PASSWORD})
    unknown = client.post("/login", data={"email": "eve@example.com", "password": USER_PASSWORD})

    assert deleted.status_code == unknown.status_code == 200
    assert "Le courriel ou le mot de passe est invalide" in page_text(deleted)
    assert page_text(deleted).replace("alice@example.com", "eve@example.com") == page_text(unknown)


# Courriel d'un compte supprimé


def test_deleted_accounts_email_is_free(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    add_tool(mock_app, ids["alice"], "Scie")
    delete_account(as_alice)

    mock_app.test_client().post(
        "/register",
        data={
            "email": "alice@example.com",
            "password": USER_PASSWORD,
            "first_name": "Alice",
            "last_name": "Tremblay",
        },
    )

    with mock_app.app_context():
        new_id = user_id("alice@example.com")
        assert new_id != ids["alice"]
        assert not catalog.has_contacts(new_id)
        assert Tool.query.filter_by(owner_id=new_id).count() == 0
        assert Loan.query.filter_by(borrower_id=new_id).count() == 0


# Recherche


def search_names(client, q):
    text = page_text(client.get("/search", query_string={"type": "user", "q": q}))
    return re.findall(r"<tr>\s*<td>(.*?)</td>", text), text


def test_deleted_account_is_not_found(mock_app, ids):
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")
    as_alice = login(mock_app.test_client(), "alice@example.com")

    names, text = search_names(as_alice, "gagnon")

    assert names == []
    assert "Aucun utilisateur ne correspond à « gagnon »" in text


def test_deleted_account_does_not_count_in_the_cap(mock_app, ids):
    with mock_app.app_context():
        for number in range(24):
            db.session.add(
                User(
                    password="hash",
                    email=f"g{number}@example.com",
                    first_name=f"G{number:02}",
                    last_name="Gagnon",
                )
            )
        db.session.add(
            User(
                password="hash",
                email=None,
                first_name="Aaron",
                last_name="Gagnon",
                deleted_at=db.func.now(),
            )
        )
        db.session.commit()
    as_alice = login(mock_app.test_client(), "alice@example.com")

    names, text = search_names(as_alice, "gagnon")

    assert len(names) == 25
    assert "Aaron Gagnon" not in names
    assert "précisez votre recherche" not in text


# Contacts


def test_contact_request_to_a_deleted_account(mock_app, ids):
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")
    as_alice = login(mock_app.test_client(), "alice@example.com")

    response = as_alice.post("/contacts/requests", data={"recipient_id": ids["bob"], "q": "bob"})

    assert response.status_code == 404
    with mock_app.app_context():
        assert ContactRequest.query.count() == 0


def test_former_contacts_page_after_deletion(mock_app, ids):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")
    as_alice = login(mock_app.test_client(), "alice@example.com")

    assert as_alice.get(f"/contacts/{ids['bob']}").status_code == 404


def test_deleted_contact_page_is_404_even_with_a_relation(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    set_account(mock_app, ids["bob"], deleted_at=db.func.now())

    assert as_alice.get(f"/contacts/{ids['bob']}").status_code == 404


def test_accepting_a_request_of_a_deleted_requester(mock_app, ids, as_alice):
    with mock_app.app_context():
        request_id = make_contact_request(ids["bob"], ids["alice"]).id
    as_alice.get("/contacts")
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")

    response = as_alice.post(f"/contacts/requests/{request_id}/accept", follow_redirects=True)

    assert response.request.path == "/contacts"
    assert "Cette demande n'est plus en attente" in page_text(response)
    with mock_app.app_context():
        assert ContactRelation.query.count() == 0


# Demandes d'emprunt


def test_loan_request_to_a_deleted_accounts_tool(mock_app, ids):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    drill = add_tool(mock_app, ids["bob"], "Perceuse")
    as_alice = login(mock_app.test_client(), "alice@example.com")
    assert as_alice.get(f"/loans/new/{drill}").status_code == 200
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")

    response = as_alice.post(
        f"/loans/new/{drill}",
        data={"start": days(0).isoformat(), "end": days(2).isoformat(), "message": ""},
    )

    assert response.status_code == 404
    with mock_app.app_context():
        assert Loan.query.count() == 0


def test_only_live_accounts_pass_the_lock(mock_app, ids):
    set_account(mock_app, ids["bob"], deleted_at=db.func.now())

    with mock_app.app_context():
        assert lock_live_accounts(ids["alice"], ids["carole"])
        assert lock_live_accounts(ids["alice"], ids["alice"])
        assert not lock_live_accounts(ids["alice"], ids["bob"])
        assert not lock_live_accounts(ids["alice"], 999_999)


# Nom d'un compte supprimé


def test_deleted_accounts_name_in_my_loans(mock_app, ids, as_alice):
    saw = add_tool(mock_app, ids["alice"], "Scie")
    add_loan(mock_app, saw, ids["bob"], days(-9), days(-8), LoanStatus.RETURNED)
    as_bob = login(mock_app.test_client(), "bob@example.com")
    delete_account(as_bob, name="Bob Gagnon")

    text = page_text(as_alice.get("/loans"))

    assert '<td><span class="user-deleted">Bob Gagnon (supprimé)</span></td>' in text
    assert f'href="/contacts/{ids["bob"]}"' not in text
