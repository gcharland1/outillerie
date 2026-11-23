import re
from urllib.parse import parse_qs, urlparse

import pytest

from app.extensions import db
from tests.factories import make_contact_relation, make_contact_request, make_tool, make_user
from tests.test_search import ids, page_text, result_rows
from tests.test_search import names as name_cells

USERS = "<h3>Utilisateurs</h3>"
TOOLS = "<h3>Outils</h3>"


def results(client, q, **params):
    return page_text(client.get("/search", query_string={"q": q, **params}))


def users_section(text):
    return text[text.index(USERS) : text.index(TOOLS)]


def tools_section(text):
    return text[text.index(TOOLS) :]


def names(section):
    """Each listed user's name, without the link a contact's name carries"""
    return [re.sub(r"<[^>]+>", "", cell) for cell in name_cells(section)]


def more_links(section):
    return re.findall(r'<a class="button primary" href="([^"]*)">Voir plus</a>', section)


def counts(section):
    return re.findall(r"<p>(\d+ de (?:plus de )?\d+)</p>", section)


@pytest.fixture
def as_alice(logged_in_client, bob):
    return logged_in_client


@pytest.fixture
def gagnons(mock_app):
    """Adds that many other accounts named Gagnon, sorted by first name after Bob"""

    def add(count):
        with mock_app.app_context():
            for number in range(count):
                db.session.add(
                    make_user(f"gagnon{number}@example.com", first_name=f"Gagnon{number:02}")
                )
            db.session.commit()

    return add


# Section « Utilisateurs » : compteur et « Voir plus »


def test_both_sections_in_this_order(as_alice):
    text = results(as_alice, "gagnon")

    assert text.index(USERS) < text.index(TOOLS)


def test_five_accounts_or_fewer_are_all_listed(as_alice, gagnons):
    gagnons(2)

    section = users_section(results(as_alice, "gagnon"))

    assert len(names(section)) == 3
    assert counts(section) == ["3 de 3"]
    assert more_links(section) == []


def test_more_than_five_accounts_show_five_and_see_more(as_alice, gagnons):
    gagnons(11)

    section = users_section(results(as_alice, "gagnon"))

    assert names(section)[0] == "Bob Gagnon"
    assert len(names(section)) == 5
    assert counts(section) == ["5 de 12"]
    [link] = more_links(section)
    assert parse_qs(urlparse(link).query) == {"q": ["gagnon"], "more": ["1"]}


def test_see_more_lists_every_account_on_the_same_page(as_alice, gagnons):
    gagnons(11)

    section = users_section(results(as_alice, "gagnon", more="1"))

    assert len(names(section)) == 12
    assert counts(section) == ["12 de 12"]
    assert more_links(section) == []


def test_more_than_25_accounts(as_alice, gagnons):
    gagnons(25)
    message = "Plus de 25 utilisateurs correspondent à « gagnon » ; précisez votre recherche"

    collapsed = users_section(results(as_alice, "gagnon"))
    expanded = users_section(results(as_alice, "gagnon", more="1"))

    assert counts(collapsed) == ["5 de plus de 25"]
    assert message not in collapsed
    assert len(names(expanded)) == 25
    assert counts(expanded) == ["25 de plus de 25"]
    assert message in expanded


def test_exactly_25_accounts_expanded_have_no_message(as_alice, gagnons):
    gagnons(24)

    section = users_section(results(as_alice, "gagnon", more="1"))

    assert counts(section) == ["25 de 25"]
    assert "précisez votre recherche" not in section


def test_expanded_view_with_few_accounts(as_alice, gagnons):
    gagnons(2)

    section = users_section(results(as_alice, "gagnon", more="1"))

    assert counts(section) == ["3 de 3"]
    assert more_links(section) == []


@pytest.mark.parametrize("more", ["tout", "0", "true"])
def test_unknown_expanded_state_is_collapsed(as_alice, gagnons, more):
    gagnons(11)

    assert len(names(users_section(results(as_alice, "gagnon", more=more)))) == 5


# Filtre de relation


@pytest.fixture
def relations(mock_app, as_alice, carole):
    """Bob is Alice's contact, Alice asked Carole, Dave asked Alice, Eve is a stranger"""
    with mock_app.app_context():
        db.session.add(make_user("dave@example.com", first_name="Dave", last_name="Gagnon"))
        db.session.add(make_user("eve@example.com", first_name="Eve", last_name="Gagnon"))
        db.session.commit()
    alice_id, bob_id, carole_id, dave_id = ids(mock_app, "alice", "bob", "carole", "dave")
    with mock_app.app_context():
        db.session.execute(
            db.text("UPDATE \"user\" SET last_name = 'Gagnon' WHERE id = :id"), {"id": carole_id}
        )
        db.session.commit()
        make_contact_relation(alice_id, bob_id)
        make_contact_request(alice_id, carole_id)
        make_contact_request(dave_id, alice_id)
    return as_alice


def test_all_users_by_default(relations):
    section = users_section(results(relations, "gagnon"))

    assert names(section) == ["Bob Gagnon", "Carole Gagnon", "Dave Gagnon", "Eve Gagnon"]
    assert '<option value="all" selected>Tous les utilisateurs</option>' in section


def test_my_contacts_only(relations):
    section = users_section(results(relations, "gagnon", relation="contacts"))

    assert names(section) == ["Bob Gagnon"]
    assert counts(section) == ["1 de 1"]
    assert '<option value="contacts" selected>Mes contacts uniquement</option>' in section


def test_not_in_contact_only_keeps_pending_requests(relations):
    section = users_section(results(relations, "gagnon", relation="others"))

    assert names(section) == ["Carole Gagnon", "Dave Gagnon", "Eve Gagnon"]


def test_unknown_relation_lists_all_users(relations):
    response = relations.get("/search", query_string={"q": "gagnon", "relation": "amis"})

    assert response.status_code == 200
    assert names(users_section(page_text(response))) == names(
        users_section(results(relations, "gagnon"))
    )


def test_filter_without_result_stays_shown_and_chosen(as_alice):
    section = users_section(results(as_alice, "gagnon", relation="contacts"))

    assert "Aucun résultat d'utilisateur" in section
    assert counts(section) == []
    assert '<option value="contacts" selected>Mes contacts uniquement</option>' in section


def test_filter_comes_before_the_cap(mock_app, as_alice, gagnons):
    gagnons(26)
    alice_id, bob_id = ids(mock_app, "alice", "bob")
    with mock_app.app_context():
        make_contact_relation(alice_id, bob_id)

    section = users_section(results(as_alice, "gagnon", relation="contacts"))

    assert names(section) == ["Bob Gagnon"]
    assert counts(section) == ["1 de 1"]


def test_filter_form_is_a_get_that_keeps_the_text_and_expanded_state(as_alice):
    section = users_section(results(as_alice, "gagnon", more="1"))
    [form] = re.findall(r'<form class="tool-filters".*?</form>', section, re.DOTALL)

    assert 'method="get"' in form
    assert '<input type="hidden" name="q" value="gagnon">' in form
    assert '<input type="hidden" name="more" value="1">' in form
    assert '<button type="submit" class="button primary">Filtrer</button>' in form
    assert "csrf_token" not in form


def test_distance_selector_is_greyed_and_upcoming(as_alice):
    section = users_section(results(as_alice, "gagnon"))

    assert "Dans un rayon de" in section
    assert re.search(r"<select disabled[^>]*>", section)
    for distance in ("1km", "3km", "5km", "10km"):
        assert f"<option>{distance}</option>" in section
    assert "<option selected>Aucune limite</option>" in section
    assert "à venir" in section


def test_distance_in_the_address_is_ignored(relations):
    assert names(users_section(results(relations, "gagnon", distance="1km"))) == names(
        users_section(results(relations, "gagnon"))
    )


# Section « Outils »


def add_tools(mock_app, owner_email, count, name="Perceuse"):
    with mock_app.app_context():
        [owner_id] = ids(mock_app, owner_email.partition("@")[0])
        for number in range(count):
            make_tool(owner_id, name=f"{name} {number}")


@pytest.fixture
def bob_is_a_contact(mock_app, as_alice):
    alice_id, bob_id = ids(mock_app, "alice", "bob")
    with mock_app.app_context():
        make_contact_relation(alice_id, bob_id)
    return as_alice


def test_six_tools_or_fewer(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 2)

    section = tools_section(results(bob_is_a_contact, "perceuse"))

    assert section.count('class="card tool-card"') == 2
    assert counts(section) == ["2 de 2"]
    assert more_links(section) == []


def test_more_than_six_tools(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 8)

    section = tools_section(results(bob_is_a_contact, "perceuse"))

    assert section.count('class="card tool-card"') == 6
    assert counts(section) == ["6 de 8"]
    assert more_links(section) == ["/tools/find?q=perceuse"]


def test_see_more_tools_lands_on_find_a_tool_with_the_text(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 8)
    [link] = more_links(tools_section(results(bob_is_a_contact, "perceuse")))

    text = page_text(bob_is_a_contact.get(link))

    assert "<h2>Trouver un outil</h2>" in text
    assert 'name="q" value="perceuse"' in text
    assert 'name="available" value="1">' in text


def test_tool_of_a_non_contact_is_not_shown(mock_app, as_alice):
    add_tools(mock_app, "bob@example.com", 1)

    assert "Aucun résultat d'outil" in tools_section(results(as_alice, "perceuse"))


def test_no_matching_tool(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 1)

    assert "Aucun résultat d'outil" in tools_section(results(bob_is_a_contact, "zzz"))


def test_relation_filter_does_not_touch_tools(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 2)

    assert tools_section(results(bob_is_a_contact, "perceuse", relation="others")) == (
        tools_section(results(bob_is_a_contact, "perceuse"))
    )


def test_cancelled_borrow_goes_back_to_find_a_tool_with_the_text(mock_app, bob_is_a_contact):
    add_tools(mock_app, "bob@example.com", 1)
    borrow_url = re.search(
        r'href="(/loans/new[^"]*)"', tools_section(results(bob_is_a_contact, "perceuse"))
    )[1].replace("&amp;", "&")

    cancel = re.search(r'href="([^"]*)"[^>]*>Annuler', page_text(bob_is_a_contact.get(borrow_url)))

    assert cancel[1].replace("&amp;", "&") == "/tools/find?q=perceuse"


# Retour après une demande de contact


def test_request_from_a_filtered_expanded_view_comes_back_to_it(mock_app, as_alice):
    [bob_id] = ids(mock_app, "bob")
    section = users_section(results(as_alice, "gagnon", relation="others", more="1"))
    assert '<input type="hidden" name="relation" value="others">' in section
    assert '<input type="hidden" name="more" value="1">' in section

    response = as_alice.post(
        "/contacts/requests",
        data={"recipient_id": bob_id, "q": "gagnon", "relation": "others", "more": "1"},
    )

    query = parse_qs(urlparse(response.location).query)
    assert urlparse(response.location).path == "/search"
    assert query == {"q": ["gagnon"], "relation": ["others"], "more": ["1"]}


def test_forged_return_values_are_dropped(mock_app, as_alice):
    [bob_id] = ids(mock_app, "bob")

    response = as_alice.post(
        "/contacts/requests",
        data={"recipient_id": bob_id, "q": "gagnon", "relation": "amis", "more": "oui"},
    )

    assert response.location == "/search?q=gagnon"
    assert result_rows(users_section(page_text(as_alice.get(response.location)))) == [
        "Bob Gagnon Demande envoyée"
    ]


def test_filter_and_each_see_more_are_blue_in_their_own_group(mock_app, bob_is_a_contact, gagnons):
    gagnons(5)
    add_tools(mock_app, "bob@example.com", 7, name="Gagnon")

    text = results(bob_is_a_contact, "gagnon")

    groups = re.findall(r'<div class="actions">\s*(<a [^>]*>Voir plus</a>)\s*</div>', text)
    assert len(groups) == 2
    assert all('class="button primary"' in group for group in groups)
