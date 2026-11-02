import re
from datetime import timedelta
from html import unescape

import pytest

from app import catalog
from app.extensions import db
from models import Loan, LoanStatus, ToolCondition
from tests.conftest import USER_PASSWORD, add_loan, add_tool, log_in_with_page_token, token_in
from tests.factories import make_contact_relation, make_contact_request, user_id

TODAY = catalog.site_today()


def page_text(response):
    return unescape(response.get_data(as_text=True))


def login(client, username):
    client.post("/login", data={"username": username, "password": USER_PASSWORD})
    return client


def days(offset):
    return TODAY + timedelta(days=offset)


def loan_form(start=0, end=2, message="", **fields):
    return {
        "start": days(start).isoformat(),
        "end": days(end).isoformat(),
        "message": message,
        **fields,
    }


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {name: user_id(name) for name in (user, bob, carole)}


@pytest.fixture
def contacts(mock_app, ids):
    """Alice and Bob are contacts, and so are Bob and Carole; Alice and Carole are not"""
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
        make_contact_relation(ids["bob"], ids["carole"])
    return ids


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice")


@pytest.fixture
def as_bob(mock_app, ids):
    return login(mock_app.test_client(), "bob")


@pytest.fixture
def as_carole(mock_app, ids):
    return login(mock_app.test_client(), "carole")


@pytest.fixture
def drill(mock_app, contacts):
    """Bob's drill"""
    return add_tool(
        mock_app,
        contacts["bob"],
        description="Perceuse sans fil " + "x" * 200,
        private_notes="code du cadenas 1234",
    )


def loans(mock_app):
    with mock_app.app_context():
        return [
            (loan.borrower_id, loan.status, loan.start_date, loan.end_date, loan.message)
            for loan in Loan.query.order_by(Loan.id)
        ]


def status_of(mock_app, loan_id):
    with mock_app.app_context():
        return db.session.get(Loan, loan_id).status


def request_drill(client, drill, **form):
    return client.post(f"/loans/new/{drill}", data=loan_form(**form))


# Confirmation page


def test_confirmation_page(mock_app, drill, as_alice):
    text = page_text(as_alice.get(f"/loans/new/{drill}"))

    assert "Emprunter « Perceuse »" in text
    assert "Perceuse sans fil " + "x" * 200 in text
    assert "État : Fonctionnel" in text
    assert "Propriétaire : Bob Gagnon" in text
    assert f'name="start" value="{TODAY.isoformat()}"' in text
    assert 'name="end" value=""' in text
    assert "Message pour Bob Gagnon (facultatif)" in text
    assert "code du cadenas 1234" not in text
    assert loans(mock_app) == []


@pytest.mark.parametrize("method", ["get", "post"])
def test_tools_that_cannot_be_requested_are_404(mock_app, contacts, as_alice, method):
    tool_ids = [
        add_tool(mock_app, contacts["alice"], name="Mienne"),
        add_tool(mock_app, contacts["carole"], name="Non-contact"),
        add_tool(mock_app, contacts["bob"], name="Retirée", is_active=False),
        add_tool(mock_app, contacts["bob"], name="Cassée", condition=ToolCondition.OUT_OF_ORDER),
        999_999,
    ]

    for tool_id in tool_ids:
        response = getattr(as_alice, method)(f"/loans/new/{tool_id}", data=loan_form())
        assert response.status_code == 404
    assert loans(mock_app) == []


def test_visitor_is_sent_to_login(client, drill):
    response = client.get(f"/loans/new/{drill}")

    assert response.status_code == 302
    assert response.location.startswith("/login")


def test_unavailable_tool_page_goes_back(mock_app, contacts, drill, as_alice):
    add_loan(mock_app, drill, contacts["carole"], days(0), days(2), LoanStatus.LENT)

    response = as_alice.get(f"/loans/new/{drill}?origin=find&q=perc")

    assert response.status_code == 302
    assert response.location == "/tools/find?q=perc"
    assert "Cet outil n'est plus disponible" in page_text(as_alice.get(response.location))


# Dates and message


@pytest.mark.parametrize(
    ("form", "error"),
    [
        ({"start": -1}, "La date de début ne peut pas être passée"),
        ({"start": 15, "end": 15}, "La date de début doit être dans les 14 prochains jours"),
        ({"start": 2, "end": 1}, "La date de fin ne peut pas précéder la date de début"),
        ({"start": 0, "end": 30}, "Un prêt dure au plus 30 jours"),
    ],
)
def test_dates_are_checked(mock_app, drill, as_alice, form, error):
    text = page_text(request_drill(as_alice, drill, message="je passe samedi", **form))

    assert error in text
    assert "je passe samedi" in text
    assert loans(mock_app) == []


@pytest.mark.parametrize("end", ["", "demain"])
def test_invalid_dates_are_refused(mock_app, drill, as_alice, end):
    form = {**loan_form(message="je passe samedi"), "end": end}
    text = page_text(as_alice.post(f"/loans/new/{drill}", data=form))

    assert "Indiquez des dates valides" in text
    assert "je passe samedi" in text
    assert loans(mock_app) == []


def test_the_longest_loan_and_the_furthest_start_are_accepted(mock_app, contacts, as_alice):
    first = add_tool(mock_app, contacts["bob"], name="Scie")
    second = add_tool(mock_app, contacts["bob"], name="Ponceuse")

    request_drill(as_alice, first, start=0, end=29)
    request_drill(as_alice, second, start=14, end=14)

    assert len(loans(mock_app)) == 2


def test_message_too_long(mock_app, drill, as_alice):
    text = page_text(request_drill(as_alice, drill, message="m" * 501))

    assert "Le message ne doit pas dépasser 500 caractères" in text
    assert loans(mock_app) == []


@pytest.mark.parametrize(
    ("message", "stored"),
    [("   ", None), ("  bonjour\r\nmerci  ", "bonjour\nmerci"), ("m" * 500, "m" * 500)],
)
def test_message_is_cleaned(mock_app, contacts, drill, as_alice, message, stored):
    request_drill(as_alice, drill, message=message)

    assert loans(mock_app) == [(contacts["alice"], LoanStatus.REQUESTED, days(0), days(2), stored)]


# Sending a request


def test_request_is_sent_and_goes_back_to_the_filtered_list(mock_app, contacts, drill, as_alice):
    response = request_drill(as_alice, drill, origin="find", q="perc", available="1")

    assert response.status_code == 302
    assert response.location == "/tools/find?q=perc&available=1"
    assert loans(mock_app) == [(contacts["alice"], LoanStatus.REQUESTED, days(0), days(2), None)]
    text = page_text(as_alice.get(response.location))
    assert '<div class="flash flash-success">Demande envoyée à Bob Gagnon</div>' in text


def test_request_from_the_contact_page_goes_back_there(mock_app, contacts, drill, as_alice):
    response = request_drill(as_alice, drill, origin="contact")

    assert response.location == f"/contacts/{contacts['bob']}"


@pytest.mark.parametrize("origin", ["https://exemple.com", "contacts", ""])
def test_unknown_origin_goes_back_to_find_a_tool(mock_app, drill, as_alice, origin):
    assert request_drill(as_alice, drill, origin=origin).location == "/tools/find"


def test_cancel_goes_back_without_creating_anything(mock_app, contacts, drill, as_alice):
    text = page_text(as_alice.get(f"/loans/new/{drill}?origin=contact&q=perc"))

    assert f'<a class="button" href="/contacts/{contacts["bob"]}?q=perc">Annuler</a>' in text
    assert loans(mock_app) == []


def test_borrow_link_carries_the_list_it_came_from(mock_app, contacts, drill, as_alice):
    find = page_text(as_alice.get("/tools/find?q=perc&available=1"))
    contact = page_text(as_alice.get(f"/contacts/{contacts['bob']}"))

    assert f"/loans/new/{drill}?origin=find&q=perc&available=1" in find
    assert f"/loans/new/{drill}?origin=contact" in contact


def test_request_needs_the_csrf_token(mock_app, drill, csrf_client):
    log_in_with_page_token(csrf_client, "alice", USER_PASSWORD)

    response = csrf_client.post(f"/loans/new/{drill}", data=loan_form())

    assert response.status_code == 400
    assert loans(mock_app) == []


def test_request_with_the_csrf_token(mock_app, drill, csrf_client):
    log_in_with_page_token(csrf_client, "alice", USER_PASSWORD)
    token = token_in(csrf_client.get(f"/loans/new/{drill}"))

    response = csrf_client.post(f"/loans/new/{drill}", data=loan_form(csrf_token=token))

    assert response.status_code == 302
    assert len(loans(mock_app)) == 1


# One request at a time


def test_second_tab_does_not_create_a_second_request(mock_app, drill, as_alice):
    request_drill(as_alice, drill)
    response = request_drill(as_alice, drill, origin="find")

    assert response.location == "/tools/find"
    assert "Cet outil n'est plus disponible" in page_text(as_alice.get(response.location))
    assert len(loans(mock_app)) == 1


def test_a_second_borrower_cannot_request_a_requested_tool(
    mock_app, contacts, drill, as_alice, as_carole
):
    request_drill(as_alice, drill)
    request_drill(as_carole, drill)

    assert [loan[0] for loan in loans(mock_app)] == [contacts["alice"]]


# Cards


def test_cards_after_a_request(mock_app, drill, as_alice, as_carole):
    request_drill(as_alice, drill)

    mine = page_text(as_alice.get("/tools/find"))
    theirs = page_text(as_carole.get("/tools/find"))

    assert '<button type="button" class="button" disabled>Demande envoyée</button>' in mine
    assert "En attente de prêt" in theirs
    assert '<button type="button" class="button" disabled>Emprunter</button>' in theirs
    assert "Demande envoyée" not in theirs


def test_an_expired_request_frees_the_tool(mock_app, contacts, drill, as_carole):
    add_loan(mock_app, drill, contacts["alice"], days(-1), days(3))

    text = page_text(as_carole.get("/tools/find"))

    assert '<p class="status-available">Disponible</p>' in text
    assert f'href="/loans/new/{drill}?origin=find"' in text


# My loans page


def test_my_loans_lists_received_and_sent_requests(mock_app, contacts, drill, as_alice):
    saw = add_tool(mock_app, contacts["alice"], name="Scie")
    add_loan(mock_app, drill, contacts["alice"], days(1), days(3), message="je passe samedi")
    add_loan(mock_app, saw, contacts["bob"], days(2), days(4))

    text = page_text(as_alice.get("/loans"))

    assert "<h2>Mes prêts</h2>" in text
    received, sent = text.split("<h3>Mes demandes</h3>")
    assert "Scie" in received and "Bob Gagnon" in received
    assert "Perceuse" in sent and "je passe samedi" in sent
    assert f"du {catalog.french_date(days(1))} au {catalog.french_date(days(3))}" in sent
    assert "Accepter" in received and "Retirer ma demande" in sent


def test_account_menu_offers_my_loans(mock_app, ids, as_alice):
    menu = re.search(
        r'<div class="account-menu-items">(.*?)</div>', page_text(as_alice.get("/")), re.DOTALL
    )[1]

    assert '<a href="/loans">Mes prêts</a>' in menu


def test_message_markup_is_shown_as_text(mock_app, contacts, drill, as_alice, as_bob):
    request_drill(as_alice, drill, message="<b>merci</b>")

    raw = as_bob.get("/loans").get_data(as_text=True)

    assert "&lt;b&gt;merci&lt;/b&gt;" in raw
    assert "<b>merci</b>" not in raw


def test_message_is_private(mock_app, contacts, drill, as_alice, as_carole):
    request_drill(as_alice, drill, message="je passe samedi")

    for path in ("/tools/find", f"/contacts/{contacts['bob']}", "/loans"):
        assert "je passe samedi" not in page_text(as_carole.get(path))


def test_expired_request_has_no_buttons(mock_app, contacts, drill, as_bob):
    add_loan(mock_app, drill, contacts["alice"], days(-1), days(3))

    text = page_text(as_bob.get("/loans"))

    assert "Expirée" in text
    assert "Accepter" not in text


def test_my_loans_sends_a_visitor_to_login(client):
    assert client.get("/loans").location.startswith("/login")


# Answers


@pytest.fixture
def request_id(mock_app, contacts, drill):
    """Alice's pending request for Bob's drill"""
    return add_loan(mock_app, drill, contacts["alice"], days(1), days(3))


def test_owner_accepts(mock_app, request_id, as_bob, as_carole):
    response = as_bob.post(f"/loans/{request_id}/accept")

    assert response.location == "/loans"
    assert status_of(mock_app, request_id) is LoanStatus.ACCEPTED
    assert "En attente de prêt" in page_text(as_carole.get("/tools/find"))


def test_owner_refuses(mock_app, request_id, as_bob, as_carole):
    as_bob.post(f"/loans/{request_id}/refuse")

    assert status_of(mock_app, request_id) is LoanStatus.REFUSED
    assert '<p class="status-available">Disponible</p>' in page_text(as_carole.get("/tools/find"))


@pytest.mark.parametrize("action", ["accept", "refuse"])
def test_only_the_owner_answers(mock_app, request_id, as_alice, as_carole, action):
    assert as_alice.post(f"/loans/{request_id}/{action}").status_code == 404
    assert as_carole.post(f"/loans/{request_id}/{action}").status_code == 404
    assert status_of(mock_app, request_id) is LoanStatus.REQUESTED


def test_second_answer_changes_nothing(mock_app, request_id, as_bob):
    as_bob.post(f"/loans/{request_id}/refuse")
    response = as_bob.post(f"/loans/{request_id}/accept")

    assert response.location == "/loans"
    assert "Cette demande n'est plus en attente" in page_text(as_bob.get("/loans"))
    assert status_of(mock_app, request_id) is LoanStatus.REFUSED


def test_expired_request_cannot_be_accepted(mock_app, contacts, drill, as_bob):
    expired = add_loan(mock_app, drill, contacts["alice"], days(-1), days(3))

    as_bob.post(f"/loans/{expired}/accept")

    assert status_of(mock_app, expired) is LoanStatus.REQUESTED
    assert "Cette demande n'est plus en attente" in page_text(as_bob.get("/loans"))


def test_accepting_taken_dates_is_refused(mock_app, contacts, drill, request_id, as_bob):
    add_loan(mock_app, drill, contacts["carole"], days(2), days(5), LoanStatus.ACCEPTED)

    as_bob.post(f"/loans/{request_id}/accept")

    assert status_of(mock_app, request_id) is LoanStatus.REQUESTED
    assert "Ces dates ne sont plus libres" in page_text(as_bob.get("/loans"))


def test_borrower_withdraws(mock_app, request_id, as_alice, as_carole):
    as_alice.post(f"/loans/{request_id}/withdraw")

    assert status_of(mock_app, request_id) is LoanStatus.CANCELED
    assert '<p class="status-available">Disponible</p>' in page_text(as_carole.get("/tools/find"))


def test_only_the_borrower_withdraws(mock_app, request_id, as_bob):
    assert as_bob.post(f"/loans/{request_id}/withdraw").status_code == 404
    assert status_of(mock_app, request_id) is LoanStatus.REQUESTED


def test_second_withdrawal_changes_nothing(mock_app, request_id, as_alice):
    as_alice.post(f"/loans/{request_id}/withdraw")
    as_alice.post(f"/loans/{request_id}/withdraw")

    assert "Cette demande n'est plus en attente" in page_text(as_alice.get("/loans"))


# Badges


def badges(text):
    return re.findall(r'<span class="badge">(\d+) ', text)


def test_badge_next_to_my_loans(mock_app, request_id, as_bob):
    text = page_text(as_bob.get("/"))

    assert re.search(r'Mes prêts <span class="badge">1 ', text)
    assert badges(text) == ["1", "1"]


def test_expired_request_is_not_counted(mock_app, contacts, drill, as_bob):
    add_loan(mock_app, drill, contacts["alice"], days(-1), days(3))

    assert badges(page_text(as_bob.get("/"))) == []


def test_username_badge_adds_contact_and_loan_requests(mock_app, ids, as_bob):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
        make_contact_request(ids["carole"], ids["bob"])
    drill = add_tool(mock_app, ids["bob"])
    add_loan(mock_app, drill, ids["alice"], days(1), days(3))

    text = page_text(as_bob.get("/"))

    summary = re.search(r"<summary>(.*?)</summary>", text, re.DOTALL)[1]
    assert badges(summary) == ["2"]
    assert re.search(r'Mes contacts <span class="badge">1 ', text)
    assert re.search(r'Mes prêts <span class="badge">1 ', text)


# Automatic cancellation


def test_retiring_a_tool_cancels_its_requests(mock_app, contacts, drill, request_id, as_bob):
    accepted = add_loan(
        mock_app, drill, contacts["carole"], days(10), days(12), LoanStatus.ACCEPTED
    )

    text = page_text(as_bob.get(f"/tools/{drill}/retire"))
    as_bob.post(f"/tools/{drill}/retire")

    assert "1 demande d'emprunt en attente sera annulée" in text
    assert status_of(mock_app, request_id) is LoanStatus.CANCELED
    assert status_of(mock_app, accepted) is LoanStatus.ACCEPTED


def test_retire_page_without_requests_says_nothing(mock_app, drill, as_bob):
    assert "demande d'emprunt" not in page_text(as_bob.get(f"/tools/{drill}/retire"))


def test_putting_a_tool_out_of_order_cancels_its_requests(mock_app, request_id, drill, as_bob):
    as_bob.post(
        f"/tools/{drill}/edit",
        data={"name": "Perceuse", "description": "Cassée", "condition": "out_of_order"},
    )

    assert status_of(mock_app, request_id) is LoanStatus.CANCELED


def test_editing_a_tool_keeps_its_requests(mock_app, request_id, drill, as_bob):
    as_bob.post(
        f"/tools/{drill}/edit",
        data={"name": "Perceuse", "description": "Neuve", "condition": "needs_repair"},
    )

    assert status_of(mock_app, request_id) is LoanStatus.REQUESTED


def test_removing_a_contact_cancels_requests_both_ways(mock_app, contacts, request_id, as_bob):
    saw = add_tool(mock_app, contacts["alice"], name="Scie")
    reverse = add_loan(mock_app, saw, contacts["bob"], days(1), days(2))
    carole_tool = add_tool(mock_app, contacts["carole"], name="Ponceuse")
    other = add_loan(mock_app, carole_tool, contacts["bob"], days(1), days(2))

    text = page_text(as_bob.get(f"/contacts/{contacts['alice']}/remove"))
    as_bob.post(f"/contacts/{contacts['alice']}/remove")

    assert "2 demandes d'emprunt en attente entre vous seront annulées" in text
    assert status_of(mock_app, request_id) is LoanStatus.CANCELED
    assert status_of(mock_app, reverse) is LoanStatus.CANCELED
    assert status_of(mock_app, other) is LoanStatus.REQUESTED


# Flash categories


def test_error_messages_keep_their_look(mock_app, drill, as_alice):
    text = page_text(request_drill(as_alice, drill, start=-1))

    assert '<div class="flash flash-message">La date de début ne peut pas être passée</div>' in text
