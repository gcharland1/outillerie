import re
from datetime import UTC, date, datetime, timedelta
from html import unescape

import pytest
from sqlalchemy import event

from app import catalog
from app.extensions import db
from models import ContactRelation, Loan, LoanStatus, ToolCondition
from tests.conftest import USER_PASSWORD, add_loan, add_tool, log_in_with_page_token
from tests.factories import make_contact_relation, make_contact_request, user_id

TODAY = catalog.site_today()
S = LoanStatus


def page_text(response):
    return unescape(response.get_data(as_text=True))


def login(client, username):
    client.post("/login", data={"username": username, "password": USER_PASSWORD})
    return client


def days(offset):
    return TODAY + timedelta(days=offset)


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {name: user_id(name) for name in (user, bob, carole)}


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice")


def section(text, title):
    """The HTML of one dashboard section"""
    return re.search(rf"<h3>{title}</h3>(.*?)</section>", text, re.DOTALL)[1]


def loans_section(client):
    return section(page_text(client.get("/")), "Gestion des prêts")


def row_names(html):
    return re.findall(r"<tr(?: class=\"loan-overdue\")?>\s*<td>(.*?)</td>", html)


def group(html, title):
    return re.search(rf"<h4>{title}</h4>(.*?)(?=<h4>|$)", html, re.DOTALL)[1]


def loan(mock_app, owner_id, borrower_id, name, status, start=-2, end=2, message=None):
    tool_id = add_tool(mock_app, owner_id, name=name)
    return add_loan(mock_app, tool_id, borrower_id, days(start), days(end), status, message)


# Gestion des prêts


def test_groups_in_order(mock_app, ids, as_alice):
    loan(mock_app, ids["alice"], ids["carole"], "Scie", S.REQUESTED, start=1, end=2)
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.LENT)
    loan(mock_app, ids["alice"], ids["bob"], "Rabot", S.LENT)

    html = loans_section(as_alice)

    assert row_names(html) == ["Scie", "Perceuse", "Rabot"]
    titles = re.findall(r"<h4>(.*?)</h4>", html)
    assert titles == ["Demandes reçues", "Mes emprunts", "Mes prêts"]


def test_overdue_first_and_highlighted(mock_app, ids, as_alice):
    loan(mock_app, ids["carole"], ids["alice"], "Ponceuse", S.LENT, end=1)
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.LENT, end=-1)

    html = loans_section(as_alice)

    assert row_names(html) == ["Perceuse", "Ponceuse"]
    overdue = re.search(r'<tr class="loan-overdue">(.*?)</tr>', html, re.DOTALL)[1]
    assert "<td>Perceuse</td>" in overdue
    assert "En retard" in overdue


def test_claimed_handover_past_its_end_is_overdue(mock_app, ids, as_alice):
    loan(mock_app, ids["carole"], ids["alice"], "Ponceuse", S.HANDOVER_CLAIMED, end=3)
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.HANDOVER_CLAIMED, end=-1)

    html = loans_section(as_alice)

    assert row_names(html) == ["Perceuse", "Ponceuse"]
    overdue = re.search(r'<tr class="loan-overdue">(.*?)</tr>', html, re.DOTALL)[1]
    assert "Confirmer la réception" in overdue
    assert "Pas reçu" in overdue


def test_borrower_categories(mock_app, ids, as_alice):
    loan(mock_app, ids["bob"], ids["alice"], "Scie", S.LENT, end=1)
    loan(mock_app, ids["carole"], ids["alice"], "Ponceuse", S.HANDOVER_CLAIMED, end=5)
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.RETURN_CLAIMED, end=3)

    assert row_names(loans_section(as_alice)) == ["Ponceuse", "Perceuse", "Scie"]


def test_lender_categories(mock_app, ids, as_alice):
    loan(mock_app, ids["alice"], ids["bob"], "Scie", S.LENT, end=1)
    loan(mock_app, ids["alice"], ids["carole"], "Rabot", S.ACCEPTED, start=3, end=5)
    loan(mock_app, ids["alice"], ids["carole"], "Ponceuse", S.RETURN_CLAIMED, end=3)

    assert row_names(loans_section(as_alice)) == ["Rabot", "Ponceuse", "Scie"]


def test_received_requests_by_first_day(mock_app, ids, as_alice):
    loan(mock_app, ids["alice"], ids["bob"], "Scie", S.REQUESTED, start=6, end=7)
    loan(mock_app, ids["alice"], ids["carole"], "Rabot", S.REQUESTED, start=2, end=9)

    assert row_names(loans_section(as_alice)) == ["Rabot", "Scie"]


def test_nearest_last_day_first_within_a_category(mock_app, ids, as_alice):
    loan(mock_app, ids["alice"], ids["bob"], "Rabot", S.ACCEPTED, start=1, end=10)
    loan(mock_app, ids["alice"], ids["carole"], "Scie", S.ACCEPTED, start=1, end=5)

    assert row_names(loans_section(as_alice)) == ["Scie", "Rabot"]


def test_finished_loans_are_left_out(mock_app, ids, as_alice):
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.RETURNED)
    loan(mock_app, ids["bob"], ids["alice"], "Scie", S.REFUSED, start=1, end=2)
    loan(mock_app, ids["bob"], ids["alice"], "Rabot", S.CANCELED, start=1, end=2)
    loan(mock_app, ids["bob"], ids["alice"], "Ponceuse", S.REQUESTED, start=-1, end=2)
    loan(mock_app, ids["alice"], ids["bob"], "Tondeuse", S.ACCEPTED, start=-3, end=-1)

    html = loans_section(as_alice)

    assert row_names(html) == []
    assert "Aucun prêt en cours" in html


def test_a_former_contacts_loan_stays(mock_app, ids, as_alice):
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.LENT)

    html = loans_section(as_alice)

    assert row_names(html) == ["Perceuse"]
    assert "J'ai rendu l'outil" in html


def test_other_peoples_loans_are_not_shown(mock_app, ids, as_alice):
    loan(mock_app, ids["bob"], ids["carole"], "Perceuse", S.LENT, message="Merci Bob")

    html = loans_section(as_alice)

    assert row_names(html) == []
    assert "Merci Bob" not in html


def test_home_buttons_bring_back_home(mock_app, ids, as_alice):
    loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.LENT)

    html = loans_section(as_alice)

    assert '<input type="hidden" name="origin" value="home">' in html


def test_confirmed_return_leaves_home(mock_app, ids, as_alice):
    loan_id = loan(mock_app, ids["alice"], ids["bob"], "Perceuse", S.RETURN_CLAIMED)

    response = as_alice.post(f"/loans/{loan_id}/take-back", data={"origin": "home"})

    text = page_text(as_alice.get(response.location))
    assert row_names(section(text, "Gestion des prêts")) == []
    assert '<div class="flash flash-success">Outil reçu, prêt complété</div>' in text


@pytest.mark.parametrize(("count", "more"), [(5, False), (6, True)])
def test_each_group_shows_five_rows(mock_app, ids, as_alice, count, more):
    for number in range(count):
        loan(mock_app, ids["alice"], ids["bob"], f"Outil {number}", S.REQUESTED, start=1, end=2)

    received = group(loans_section(as_alice), "Demandes reçues")

    assert len(row_names(received)) == 5
    assert ("Voir tous mes prêts" in received) == more
    if more:
        assert 'href="/loans"' in received


def test_more_button_under_its_group_only(mock_app, ids, as_alice):
    for number in range(6):
        loan(mock_app, ids["bob"], ids["alice"], f"Emprunt {number}", S.LENT)
    for number in range(2):
        loan(mock_app, ids["alice"], ids["bob"], f"Prêt {number}", S.LENT)

    html = loans_section(as_alice)

    assert "Voir tous mes prêts" in group(html, "Mes emprunts")
    assert "Voir tous mes prêts" not in group(html, "Mes prêts")


# Gestion des contacts


def contacts_section(client):
    return section(page_text(client.get("/")), "Gestion des contacts")


def relate(mock_app, first_id, second_id, days_ago=0):
    with mock_app.app_context():
        relation = make_contact_relation(first_id, second_id)
        relation.created_at = datetime.now(UTC) - timedelta(days=days_ago)
        db.session.commit()


def test_received_contact_request(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_request(ids["carole"], ids["alice"])

    html = contacts_section(as_alice)

    assert "Carole Roy" in html
    assert "Accepter" in html
    assert "Refuser" in html
    assert html.count('<input type="hidden" name="origin" value="home">') == 2


def test_new_contact_on_both_sides(mock_app, ids, as_alice):
    relate(mock_app, ids["alice"], ids["bob"], days_ago=3)
    as_bob = login(mock_app.test_client(), "bob")

    assert "Vous êtes maintenant en contact avec Bob Gagnon" in contacts_section(as_alice)
    assert "Vous êtes maintenant en contact avec Alice Tremblay" in contacts_section(as_bob)


def test_old_contact_is_not_new(mock_app, ids, as_alice):
    relate(mock_app, ids["alice"], ids["bob"], days_ago=31)

    assert "Bob Gagnon" not in contacts_section(as_alice)


def test_refusal_and_removed_contact_show_nothing(mock_app, ids, as_alice):
    with mock_app.app_context():
        request_id = make_contact_request(ids["alice"], ids["bob"]).id
    as_bob = login(mock_app.test_client(), "bob")
    as_bob.post(f"/contacts/requests/{request_id}/refuse")

    assert "Bob" not in contacts_section(as_alice)

    relate(mock_app, ids["alice"], ids["carole"])
    with mock_app.app_context():
        db.session.delete(
            db.session.get(ContactRelation, ContactRelation.pair(ids["alice"], ids["carole"]))
        )
        db.session.commit()

    assert "Carole" not in contacts_section(as_alice)


def test_contacts_section_leads_to_my_contacts(mock_app, ids, as_alice):
    html = contacts_section(as_alice)

    assert '<a class="button" href="/contacts">Mes contacts</a>' in html
    assert "Aucune demande de contact" in html


# Nouveaux outils


def tools_section(client):
    return section(page_text(client.get("/")), "Nouveaux outils")


def card_names(html):
    return re.findall(r"<h4>(.*?)</h4>", html)


def added(mock_app, owner_id, name, days_ago, **fields):
    created_at = datetime.now(UTC) - timedelta(days=days_ago)
    return add_tool(mock_app, owner_id, name=name, created_at=created_at, **fields)


@pytest.fixture
def contacts(mock_app, ids):
    """Alice and Bob are contacts"""
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    return ids


def test_recent_tools_newest_first(mock_app, contacts, as_alice):
    added(mock_app, contacts["bob"], "Scie", 5)
    added(mock_app, contacts["bob"], "Perceuse", 2)

    html = tools_section(as_alice)

    assert card_names(html) == ["Perceuse", "Scie"]
    assert re.search(r'href="/loans/new/\d+\?origin=home"', html)


def test_thirty_days_bound(mock_app, contacts, as_alice, monkeypatch):
    monkeypatch.setattr(catalog, "site_today", lambda: date(2026, 12, 1))
    evening = datetime(2026, 11, 1, 23, 30, tzinfo=catalog.SITE_TIMEZONE)
    add_tool(mock_app, contacts["bob"], name="Scie", created_at=evening)
    add_tool(mock_app, contacts["bob"], name="Ponceuse", created_at=evening - timedelta(days=1))

    assert card_names(tools_section(as_alice)) == ["Scie"]


def test_tools_that_are_not_visible(mock_app, contacts, as_alice):
    added(mock_app, contacts["alice"], "Rabot", 1)
    added(mock_app, contacts["bob"], "Scie", 1, is_active=False)
    added(mock_app, contacts["bob"], "Tondeuse", 1, condition=ToolCondition.OUT_OF_ORDER)
    added(mock_app, contacts["carole"], "Perceuse", 1)

    assert card_names(tools_section(as_alice)) == []


def test_lent_tool_shows_its_status(mock_app, contacts, as_alice):
    tool_id = added(mock_app, contacts["bob"], "Perceuse", 2)
    add_loan(mock_app, tool_id, contacts["carole"], days(-1), days(3), S.LENT)

    html = tools_section(as_alice)

    assert "Prêté jusqu'au" in html
    assert '<button type="button" class="button" disabled>Emprunter</button>' in html


def test_only_the_date_added_counts(mock_app, ids, as_alice):
    added(mock_app, ids["bob"], "Scie", 90)
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])

    assert card_names(tools_section(as_alice)) == []


@pytest.mark.parametrize(("count", "more"), [(6, False), (7, True)])
def test_six_tools_then_see_more(mock_app, contacts, as_alice, count, more):
    for number in range(count):
        added(mock_app, contacts["bob"], f"Outil {number}", number + 1)

    html = tools_section(as_alice)

    assert card_names(html) == [f"Outil {number}" for number in range(6)]
    assert ('href="/tools/find?sort=added-desc">Voir plus</a>' in html) == more


# Sections vides


def test_new_account(mock_app, ids, as_alice):
    response = as_alice.get("/")

    assert response.status_code == 200
    text = page_text(response)
    assert "Aucun prêt en cours" in text
    assert "Aucune demande de contact" in text
    assert "Vous n'avez encore aucun contact" in section(text, "Nouveaux outils")
    assert "ouvrez la recherche d'utilisateurs" in text


def test_contacts_without_new_tools(mock_app, contacts, as_alice):
    assert "Aucun nouvel outil depuis 30 jours" in tools_section(as_alice)


# Requêtes et jeton


def queries_of_home(mock_app, client):
    statements = []

    def record(*args):
        statements.append(args[2])

    with mock_app.app_context():
        event.listen(db.engine, "before_cursor_execute", record)
    try:
        assert client.get("/").status_code == 200
    finally:
        with mock_app.app_context():
            event.remove(db.engine, "before_cursor_execute", record)
    return len(statements)


def fill(mock_app, ids, count, tag):
    for number in range(count):
        loan(mock_app, ids["alice"], ids["bob"], f"{tag} demande {number}", S.REQUESTED, 1, 2)
        loan(mock_app, ids["bob"], ids["alice"], f"{tag} emprunt {number}", S.LENT)
        loan(mock_app, ids["alice"], ids["bob"], f"{tag} prêt {number}", S.LENT)
        added(mock_app, ids["bob"], f"{tag} outil {number}", 1)


def test_home_query_count_does_not_grow(mock_app, contacts, as_alice):
    fill(mock_app, contacts, 1, "a")
    with mock_app.app_context():
        make_contact_request(contacts["carole"], contacts["alice"])
    few = queries_of_home(mock_app, as_alice)

    fill(mock_app, contacts, 8, "b")

    assert queries_of_home(mock_app, as_alice) == few


def test_home_action_without_token(mock_app, ids, csrf_client):
    loan_id = loan(mock_app, ids["bob"], ids["alice"], "Perceuse", S.LENT)
    log_in_with_page_token(csrf_client, "alice", USER_PASSWORD)

    response = csrf_client.post(f"/loans/{loan_id}/give-back", data={"origin": "home"})

    assert response.status_code == 400
    with mock_app.app_context():
        assert db.session.get(Loan, loan_id).status == S.LENT
