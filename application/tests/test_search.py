import re
from html import unescape

import pytest

from app import search as search_module
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


def names(text):
    """Each result's name, its first cell"""
    return re.findall(r"<tr>\s*<td>(.*?)</td>", text)


def search(client, q, search_type="user"):
    return page_text(client.get("/search", query_string={"type": search_type, "q": q}))


@pytest.fixture
def as_alice(logged_in_client, bob):
    return logged_in_client


def ids(mock_app, *first_names):
    with mock_app.app_context():
        return [user_id(f"{name}@example.com") for name in first_names]


def test_visitor_is_sent_to_login(client):
    response = client.get("/search?type=user&q=bob")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")


@pytest.mark.parametrize("q", ["GAGN", "  bob gagnon  ", "Bob", "bob"])
def test_matches_first_name_last_name_or_full_name(as_alice, q):
    assert names(search(as_alice, q)) == ["Bob Gagnon"]


@pytest.fixture
def named(mock_app):
    """Adds accounts named (first name, last name)"""

    def add(*accounts):
        with mock_app.app_context():
            for first_name, last_name in accounts:
                email = f"{User.query.count()}@example.com"
                db.session.add(make_user(email, first_name=first_name, last_name=last_name))
                db.session.commit()

    return add


@pytest.mark.parametrize(
    ("account", "q"),
    [
        (("Fréd", "Côté"), "fred cote"),
        (("Fred", "Cote"), "FRÉD CÔTÉ"),
        (("Jean-Pierre", "Roy"), "jean pierre"),
        (("Frédéric", "Lavoie"), "frederik"),
    ],
)
def test_accents_hyphens_and_typos_are_forgiven(as_alice, named, account, q):
    named(account)
    assert names(search(as_alice, q)) == [" ".join(account)]


@pytest.mark.parametrize("q", ["bob    gagnon", "gagnion", "gagnon bob"])
def test_bob_is_found_despite_spaces_typos_or_order(as_alice, q):
    assert names(search(as_alice, q)) == ["Bob Gagnon"]


@pytest.mark.parametrize("q", ["gax", "ga\u0301x"])
def test_no_resemblance_below_four_normalized_characters(as_alice, q):
    assert names(search(as_alice, q)) == []


def test_email_is_not_searched(mock_app, as_alice):
    with mock_app.app_context():
        User.query.filter_by(email="bob@example.com").one().email = "courrielbob@example.com"
        db.session.commit()

    assert names(search(as_alice, "courrielbob")) == []


@pytest.mark.parametrize("q", ["％％％", "%%%"])
def test_full_width_wildcards_are_searched_literally(as_alice, named, q):
    named(("Sam", "Cinq"))
    assert names(search(as_alice, q)) == []


def test_wildcards_in_a_name_are_found(as_alice, named):
    named(("Bob", "Gagnon%%%"))
    assert names(search(as_alice, "%%%")) == ["Bob Gagnon%%%"]


def test_contained_comes_before_resembling(as_alice, named):
    named(("Albert", "Gagnon"), ("Zoé", "Gagné"))
    assert names(search(as_alice, "gagne")) == ["Zoé Gagné", "Albert Gagnon", "Bob Gagnon"]


def test_own_account_is_excluded(as_alice):
    assert names(search(as_alice, "tremblay")) == []


@pytest.mark.parametrize("q", ["50%", "b_b"])
def test_wildcards_are_searched_literally(mock_app, as_alice, q):
    with mock_app.app_context():
        db.session.add(make_user("sam@example.com"))
        db.session.commit()

    text = search(as_alice, q)

    assert names(text) == []
    assert f"Aucun utilisateur ne correspond à « {q} »" in text


def test_results_are_sorted_by_first_then_last_name(as_alice, named):
    named(("Carole", "Leclerc"), ("bob", "Leclerc"), ("Élise", "Leclerc"), ("Albert", "Leclerc"))

    assert names(search(as_alice, "leclerc")) == [
        "Albert Leclerc",
        "bob Leclerc",
        "Carole Leclerc",
        "Élise Leclerc",
    ]


def test_homonyms_oldest_account_first(mock_app, as_alice, named):
    named(("Bob", "Gagnon"))
    with mock_app.app_context():
        oldest_first = [
            user.id for user in User.query.filter_by(first_name="Bob").order_by(User.id)
        ]

    text = search(as_alice, "gagnon")

    assert names(text) == ["Bob Gagnon", "Bob Gagnon"]
    assert [int(i) for i in re.findall(r'name="recipient_id" value="(\d+)"', text)] == oldest_first


# Nombre de comptes listés


def too_many(text):
    return f"Plus de 3 utilisateurs correspondent à « {text} » ; précisez votre recherche"


@pytest.fixture
def cap_of_three(monkeypatch):
    monkeypatch.setattr(search_module, "USER_RESULTS_MAX", 3)


def test_more_than_the_cap_lists_the_first_ones(as_alice, named, cap_of_three):
    named(("Albert", "Gagnon"), ("Carole", "Gagnon"), ("Denis", "Gagnon"))

    text = search(as_alice, "gagnon")

    assert names(text) == ["Albert Gagnon", "Bob Gagnon", "Carole Gagnon"]
    assert too_many("gagnon") in text
    assert text.index(too_many("gagnon")) < text.index("<table>")


def test_exactly_the_cap_has_no_message(as_alice, named, cap_of_three):
    named(("Albert", "Gagnon"), ("Carole", "Gagnon"))

    text = search(as_alice, "gagnon")

    assert names(text) == ["Albert Gagnon", "Bob Gagnon", "Carole Gagnon"]
    assert "précisez votre recherche" not in text


def test_the_cap_keeps_contained_names(as_alice, named, cap_of_three):
    named(("Albert", "Gagnion"), ("Carole", "Gagnion"), ("Denis", "Gagnion"))

    assert names(search(as_alice, "gagnon"))[0] == "Bob Gagnon"


def test_cap_message_escapes_the_text(as_alice, named, cap_of_three):
    named(*[("<b>gagnon</b>", str(number)) for number in range(4)])

    raw = as_alice.get("/search", query_string={"type": "user", "q": "<b>gagnon</b>"})

    assert "&lt;b&gt;gagnon&lt;/b&gt; » ; précisez" in raw.get_data(as_text=True)


def test_the_real_cap_is_25():
    assert search_module.USER_RESULTS_MAX == 25


def test_results_hide_contact_details(mock_app, as_alice):
    with mock_app.app_context():
        bob = User.query.filter_by(email="bob@example.com").one()
        bob.address = "12 rue des Érables"
        bob.phone = "418-555-0199"
        db.session.commit()

    text = search(as_alice, "bob")

    assert result_rows(text) == ["Bob Gagnon Envoyer une demande"]
    for detail in ["bob@example.com", "12 rue des Érables", "418-555-0199"]:
        assert detail not in text


@pytest.mark.parametrize("q", ["  bo  ", "", "   ", "---", "–––", "e\u0301\u0301\u0301"])
def test_text_shorter_than_three_characters_is_not_searched(as_alice, q):
    text = search(as_alice, q)

    assert TOO_SHORT in text
    assert names(text) == []


def test_tool_search_of_hyphens_only_is_too_short(as_alice):
    response = as_alice.get("/search", query_string={"type": "tool", "q": "---"})

    assert response.status_code == 200
    assert TOO_SHORT in page_text(response)


def test_no_result(as_alice):
    assert "Aucun utilisateur ne correspond à « zzz »" in search(as_alice, "zzz")


def test_tool_search_leads_to_find_a_tool(as_alice):
    response = as_alice.get("/search", query_string={"type": "tool", "q": "  perceuse  "})

    assert response.status_code == 302
    assert response.location == "/tools/find?q=perceuse"


def test_tool_search_lands_on_the_filtered_page(as_alice):
    response = as_alice.get(
        "/search", query_string={"type": "tool", "q": "perceuse"}, follow_redirects=True
    )

    text = page_text(response)
    assert "<h2>Trouver un outil</h2>" in text
    assert 'name="q" value="perceuse"' in text
    assert 'name="available" value="1">' in text


def test_tool_search_needs_three_characters(as_alice):
    assert TOO_SHORT in search(as_alice, "pe", search_type="tool")


def test_unknown_search_type_is_not_available(as_alice):
    text = search(as_alice, "bob", search_type="lieu")

    assert "Ce type de recherche n'est pas disponible" in text
    assert names(text) == []
    assert '<option value="tool" selected>Outil</option>' in text


def test_search_text_and_type_are_kept_in_the_search_bar(as_alice):
    text = search(as_alice, " gagnon ")

    assert 'type="search" name="q" value="gagnon"' in text
    assert '<option value="user" selected>Utilisateur</option>' in text
    assert '<option value="tool">Outil</option>' in text


def test_short_tool_search_keeps_the_tool_type(as_alice):
    assert '<option value="tool" selected>Outil</option>' in search(as_alice, "pe", "tool")


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
    assert result_rows(text) == ["Bob Gagnon Demande envoyée"]
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
    as_bob.post("/login", data={"email": "bob@example.com", "password": USER_PASSWORD})
    request_id = re.search(r"/contacts/requests/(\d+)/refuse", page_text(as_bob.get("/contacts")))[
        1
    ]
    as_bob.post(f"/contacts/requests/{request_id}/refuse")

    assert result_rows(search(as_alice, "bob")) == ["Bob Gagnon Envoyer une demande"]


# Protection CSRF


def test_every_post_form_carries_a_csrf_token(mock_app, as_alice, carole):
    with mock_app.app_context():
        db.session.add(make_user("dave@example.com", last_name="Roy"))
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
