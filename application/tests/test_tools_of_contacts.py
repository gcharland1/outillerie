import re
from datetime import date, timedelta
from html import unescape

import pytest

from app import catalog, photos
from app.extensions import db
from models import LoanStatus, Tool, ToolCondition, User
from tests.conftest import USER_PASSWORD, add_loan
from tests.factories import make_contact_relation, make_contact_request, make_tool, user_id

TODAY = catalog.site_today()


def page_text(response):
    return unescape(response.get_data(as_text=True))


def login(client, username):
    client.post("/login", data={"username": username, "password": USER_PASSWORD})
    return client


def card_names(text):
    return re.findall(r'<article class="card tool-card">.*?<h4>(.*?)</h4>', text, re.DOTALL)


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {name: user_id(name) for name in (user, bob, carole)}


@pytest.fixture
def contacts(mock_app, ids):
    """Alice and Bob are contacts; Carole is neither's"""
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    return ids


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice")


def add_tool(mock_app, owner_id, name="Perceuse", **fields):
    with mock_app.app_context():
        return make_tool(owner_id, name=name, **fields).id


def add_photo(mock_app, tool_id, jpeg):
    with mock_app.app_context():
        photos.save_photo(db.session.get(Tool, tool_id), jpeg)
        db.session.commit()


def find(client, **params):
    return page_text(client.get("/tools/find", query_string=params))


def test_find_a_tool_shows_a_card_per_visible_tool(mock_app, contacts, as_alice, jpeg_photo):
    tool_id = add_tool(mock_app, contacts["bob"], description="Perceuse sans fil 18 V")
    add_photo(mock_app, tool_id, jpeg_photo)
    add_tool(mock_app, contacts["carole"], name="Ponceuse")
    add_tool(mock_app, contacts["alice"], name="Scie")

    text = find(as_alice)

    assert "<h2>Trouver un outil</h2>" in text
    assert card_names(text) == ["Perceuse"]
    assert f'src="/tools/{tool_id}/photo" alt="Perceuse"' in text
    assert f'<a href="/contacts/{contacts["bob"]}">Bob Gagnon</a>' in text
    assert "Perceuse sans fil 18 V" in text
    assert "<p>Fonctionnel</p>" in text
    assert '<p class="status-available">Disponible</p>' in text
    assert (
        f'<a class="button primary" href="/loans/new/{tool_id}?origin=find">Emprunter</a>' in text
    )
    assert "Bientôt disponible" not in text


def test_card_without_photo_keeps_its_place(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"])

    text = find(as_alice)

    assert 'class="tool-card-photo tool-card-no-photo"' in text
    assert "<img" not in text


def test_private_notes_are_never_shown(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"], private_notes="code du cadenas 1234")

    assert "code du cadenas 1234" not in find(as_alice)
    assert "code du cadenas 1234" not in page_text(as_alice.get(f"/contacts/{contacts['bob']}"))


@pytest.mark.parametrize(("length", "suffix"), [(125, ""), (200, "…")])
def test_description_is_cut_after_125_characters(mock_app, contacts, as_alice, length, suffix):
    add_tool(mock_app, contacts["bob"], description="d" * length)

    assert f"<p>{'d' * 125}{suffix}</p>" in find(as_alice)


def test_lent_tool_shows_its_return_date(mock_app, contacts, as_alice):
    tool_id = add_tool(mock_app, contacts["bob"])
    add_loan(mock_app, tool_id, contacts["carole"], TODAY, date(2099, 11, 3), LoanStatus.LENT)

    assert '<p class="status-unavailable">Prêté jusqu\'au 3 novembre 2099</p>' in find(as_alice)


def test_available_only(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"], name="Perceuse")
    lent = add_tool(mock_app, contacts["bob"], name="Scie")
    pending = add_tool(mock_app, contacts["bob"], name="Ponceuse")
    add_loan(mock_app, lent, contacts["carole"], TODAY, TODAY + timedelta(3), LoanStatus.LENT)
    add_loan(mock_app, pending, contacts["carole"], TODAY, TODAY, LoanStatus.REQUESTED)

    checked = find(as_alice, available="1")
    unchecked = find(as_alice)

    assert card_names(checked) == ["Perceuse"]
    assert 'name="available" value="1" checked>' in checked
    assert card_names(unchecked) == ["Perceuse", "Ponceuse", "Scie"]
    assert "En attente de prêt" in unchecked
    assert 'name="available" value="1">' in unchecked


def test_an_unexpected_available_value_does_not_filter(mock_app, contacts, as_alice):
    lent = add_tool(mock_app, contacts["bob"])
    add_loan(mock_app, lent, contacts["carole"], TODAY, TODAY, LoanStatus.LENT)

    assert card_names(find(as_alice, available="oui")) == ["Perceuse"]


def test_text_filter_is_kept_in_its_field(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"], name="Perceuse")
    add_tool(mock_app, contacts["bob"], name="Tondeuse", description="Tondeuse à gazon")

    text = find(as_alice, q="  perseuse ")

    assert card_names(text) == ["Perceuse"]
    assert 'name="q" value="perseuse"' in text


def test_the_filter_form_stays_on_the_page(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"])

    assert '<form class="tool-filters" action="/tools/find" method="get"' in find(as_alice)
    contact_page = page_text(as_alice.get(f"/contacts/{contacts['bob']}"))
    assert f'<form class="tool-filters" action="/contacts/{contacts["bob"]}" method="get"' in (
        contact_page
    )


def test_without_contacts(mock_app, ids, as_alice):
    text = find(as_alice)

    assert "Vous n'avez encore aucun contact" in text
    assert 'href="/search?type=user"' in text


def test_contacts_without_tools(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"], condition=ToolCondition.OUT_OF_ORDER)

    assert "Vos contacts n'ont encore aucun outil à prêter" in find(as_alice)


def test_filters_without_result(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"])

    text = find(as_alice, q="tondeuse")

    assert "Aucun outil ne correspond à ces filtres" in text
    assert card_names(text) == []


def test_visitor_is_sent_to_login(client):
    response = client.get("/tools/find")

    assert response.status_code == 302
    assert response.location.startswith("/login")


def test_navigation_offers_find_a_tool(mock_app, ids, as_alice):
    account_menu = re.search(
        r'<div class="account-menu-items">(.*?)</div>', page_text(as_alice.get("/")), re.DOTALL
    )[1]
    assert '<a href="/tools/find">Trouver un outil</a>' in account_menu
    assert "Trouver un outil" not in page_text(mock_app.test_client().get("/"))


def test_contact_page(mock_app, contacts, as_alice):
    add_tool(mock_app, contacts["bob"], name="Perceuse")
    with mock_app.app_context():
        bob = db.session.get(User, contacts["bob"])
        bob.address = "12 rue des Érables"
        bob.phone = "418-555-0199"
        make_contact_relation(contacts["alice"], contacts["carole"])
    add_tool(mock_app, contacts["carole"], name="Ponceuse")

    text = page_text(as_alice.get(f"/contacts/{contacts['bob']}"))

    assert "<h2>Bob Gagnon (@bob)</h2>" in text
    assert "<h3>Outils de Bob Gagnon</h3>" in text
    assert card_names(text) == ["Perceuse"]
    for private in ("bob@example.com", "12 rue des Érables", "418-555-0199"):
        assert private not in text


def test_contact_without_tools(mock_app, contacts, as_alice):
    text = page_text(as_alice.get(f"/contacts/{contacts['bob']}"))

    assert "Bob Gagnon n'a encore aucun outil à prêter" in text


def test_contact_page_is_404_for_anyone_but_a_contact(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_request(ids["alice"], ids["carole"])

    assert as_alice.get(f"/contacts/{ids['bob']}").status_code == 404
    assert as_alice.get(f"/contacts/{ids['carole']}").status_code == 404
    assert as_alice.get(f"/contacts/{ids['alice']}").status_code == 404
    assert as_alice.get("/contacts/999999").status_code == 404


def test_contact_page_sends_a_visitor_to_login(client, contacts):
    response = client.get(f"/contacts/{contacts['bob']}")

    assert response.status_code == 302
    assert response.location.startswith("/login")


def test_my_contacts_link_to_their_page(mock_app, contacts, as_alice):
    text = page_text(as_alice.get("/contacts"))

    assert f'<a href="/contacts/{contacts["bob"]}">Bob Gagnon</a>' in text


@pytest.fixture
def bobs_drill(mock_app, contacts, jpeg_photo):
    tool_id = add_tool(mock_app, contacts["bob"])
    add_photo(mock_app, tool_id, jpeg_photo)
    return tool_id


def test_a_contact_sees_the_photo(bobs_drill, as_alice):
    response = as_alice.get(f"/tools/{bobs_drill}/photo")

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"


@pytest.mark.parametrize(
    "change", [{"is_active": False}, {"condition": ToolCondition.OUT_OF_ORDER}]
)
def test_a_contact_does_not_see_a_hidden_tools_photo(mock_app, bobs_drill, as_alice, change):
    with mock_app.app_context():
        tool = db.session.get(Tool, bobs_drill)
        for field, value in change.items():
            setattr(tool, field, value)
        db.session.commit()

    assert as_alice.get(f"/tools/{bobs_drill}/photo").status_code == 404


def test_a_former_contact_no_longer_sees_the_photo(mock_app, contacts, bobs_drill, as_alice):
    etag = as_alice.get(f"/tools/{bobs_drill}/photo").headers["ETag"]
    as_alice.post(f"/contacts/{contacts['bob']}/remove")

    response = as_alice.get(f"/tools/{bobs_drill}/photo", headers={"If-None-Match": etag})

    assert response.status_code == 404


def test_a_non_contact_does_not_see_the_photo(mock_app, bobs_drill, contacts):
    as_carole = login(mock_app.test_client(), "carole")

    assert as_carole.get(f"/tools/{bobs_drill}/photo").status_code == 404
