import re
from html import unescape

import pytest

from app.extensions import db
from models import User
from tests.conftest import USER_PASSWORD
from tests.factories import make_contact_relation, make_contact_request, make_user, user_id

TOO_SHORT = "Saisissez au moins 3 caractères"


def page_text(response):
    return unescape(response.get_data(as_text=True))


def result_rows(text):
    """Each result row's cells, as text"""
    body = re.search(r"<tbody>(.*?)</tbody>", text, re.DOTALL)
    rows = re.findall(r"<tr>(.*?)</tr>", body[1], re.DOTALL) if body else []
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row)).strip() for row in rows]


def usernames(text):
    return [row.split(" ")[0] for row in result_rows(text)]


def search(client, q, search_type="user"):
    return page_text(client.get("/search", query_string={"type": search_type, "q": q}))


@pytest.fixture
def as_alice(logged_in_client, bob):
    return logged_in_client


def ids(mock_app, *usernames):
    with mock_app.app_context():
        return [user_id(name) for name in usernames]


def test_visitor_is_sent_to_login(client):
    response = client.get("/search?type=user&q=bob")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")


@pytest.mark.parametrize("q", ["GAGN", "  bob gagnon  ", "Bob", "bob"])
def test_matches_username_first_name_last_name_or_full_name(as_alice, q):
    assert usernames(search(as_alice, q)) == ["bob"]


def test_own_account_is_excluded(as_alice):
    assert usernames(search(as_alice, "tremblay")) == []


@pytest.mark.parametrize("q", ["50%", "b_b"])
def test_wildcards_are_searched_literally(mock_app, as_alice, q):
    with mock_app.app_context():
        db.session.add(make_user("sam500", "sam@example.com"))
        db.session.commit()

    text = search(as_alice, q)

    assert usernames(text) == []
    assert f"Aucun utilisateur ne correspond à « {q} »" in text


def test_results_are_sorted_by_username_regardless_of_case(mock_app, as_alice):
    with mock_app.app_context():
        db.session.add_all(
            [
                make_user("carole", "carole@example.com", last_name="Leclerc"),
                make_user("albert", "albert@example.com", last_name="Leclerc"),
                make_user("Bertrand", "bertrand@example.com", last_name="Leclerc"),
            ]
        )
        db.session.commit()

    assert usernames(search(as_alice, "leclerc")) == ["albert", "Bertrand", "carole"]


def test_results_hide_contact_details(mock_app, as_alice):
    with mock_app.app_context():
        bob = User.query.filter_by(username="bob").one()
        bob.address = "12 rue des Érables"
        bob.phone = "418-555-0199"
        db.session.commit()

    text = search(as_alice, "bob")

    assert result_rows(text) == ["bob Bob Gagnon Envoyer une demande"]
    for detail in ["bob@example.com", "12 rue des Érables", "418-555-0199"]:
        assert detail not in text


@pytest.mark.parametrize("q", ["  bo  ", "", "   "])
def test_text_shorter_than_three_characters_is_not_searched(as_alice, q):
    text = search(as_alice, q)

    assert TOO_SHORT in text
    assert usernames(text) == []


def test_no_result(as_alice):
    assert "Aucun utilisateur ne correspond à « zzz »" in search(as_alice, "zzz")


def test_tool_search_is_not_available_yet(as_alice):
    text = search(as_alice, "bob", search_type="tool")

    assert "Ce type de recherche n'est pas encore disponible" in text
    assert usernames(text) == []


def test_search_text_is_kept_in_the_search_bar(as_alice):
    assert 'type="search" name="q" value="gagnon"' in search(as_alice, " gagnon ")


# Action selon la relation de contact


def test_sending_from_the_results_comes_back_with_the_request_sent(mock_app, as_alice):
    [bob_id] = ids(mock_app, "bob")
    text = search(as_alice, "bob")
    assert re.search(f'name="recipient_id" value="{bob_id}"', text)
    assert 'name="q" value="bob"' in text

    response = as_alice.post(
        "/contacts/requests", data={"recipient_id": bob_id, "q": "bob"}, follow_redirects=True
    )

    assert response.request.path == "/search"
    text = page_text(response)
    assert result_rows(text) == ["bob Bob Gagnon Demande envoyée"]
    assert '<button type="button" class="button" disabled>Demande envoyée</button>' in text


def test_received_request_offers_to_answer(mock_app, as_alice):
    alice_id, bob_id = ids(mock_app, "alice", "bob")
    with mock_app.app_context():
        make_contact_request(bob_id, alice_id)

    text = search(as_alice, "bob")

    assert '<a class="button primary" href="/contacts">Répondre à sa demande</a>' in text


def test_existing_contact_is_greyed_out(mock_app, as_alice):
    alice_id, bob_id = ids(mock_app, "alice", "bob")
    with mock_app.app_context():
        make_contact_relation(alice_id, bob_id)

    text = search(as_alice, "bob")

    assert '<button type="button" class="button" disabled>Déjà en contact</button>' in text


def test_refused_request_can_be_sent_again(mock_app, as_alice):
    [bob_id] = ids(mock_app, "bob")
    as_alice.post("/contacts/requests", data={"recipient_id": bob_id, "q": "bob"})
    as_bob = mock_app.test_client()
    as_bob.post("/login", data={"username": "bob", "password": USER_PASSWORD})
    request_id = re.search(r"/contacts/requests/(\d+)/refuse", page_text(as_bob.get("/contacts")))[
        1
    ]
    as_bob.post(f"/contacts/requests/{request_id}/refuse")

    assert result_rows(search(as_alice, "bob")) == ["bob Bob Gagnon Envoyer une demande"]


# Protection CSRF


def test_every_post_form_carries_a_csrf_token(mock_app, as_alice, carole):
    with mock_app.app_context():
        db.session.add(make_user("dave", "dave@example.com", last_name="Roy"))
        db.session.commit()
    alice_id, bob_id, carole_id = ids(mock_app, "alice", "bob", "carole")
    with mock_app.app_context():
        make_contact_request(bob_id, alice_id)
        make_contact_relation(alice_id, carole_id)

    pages = [
        search(as_alice, "roy"),
        page_text(as_alice.get("/contacts")),
        page_text(as_alice.get(f"/contacts/{carole_id}/remove")),
    ]

    post_forms = [
        form
        for text in pages
        for form in re.findall(r'<form[^>]*method="post".*?</form>', text, re.DOTALL)
    ]
    # Send to dave, refuse and accept bob, confirm removing carole, and log out on each page.
    assert len(post_forms) == 4 + len(pages)
    for form in post_forms:
        assert 'name="csrf_token"' in form
    assert re.search(r'<form class="search-bar"[^>]*method="get"', pages[0])
