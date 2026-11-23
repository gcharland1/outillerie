import re
from html import unescape

import pytest
from flask_login import login_user

from app.contacts import NO_LONGER_PENDING, NOT_A_CONTACT, relation_states
from app.extensions import db
from models import ContactRelation, ContactRequest, User
from tests.conftest import login
from tests.factories import make_contact_relation, make_contact_request, make_user, user_id


def page_text(response):
    return unescape(response.get_data(as_text=True))


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {email.partition("@")[0]: user_id(email) for email in (user, bob, carole)}


@pytest.fixture
def as_bob(mock_app, ids):
    return login(mock_app.test_client(), "bob@example.com")


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice@example.com")


def add_request(mock_app, requester_id, recipient_id):
    with mock_app.app_context():
        return make_contact_request(requester_id, recipient_id).id


def add_relation(mock_app, first_id, second_id):
    with mock_app.app_context():
        make_contact_relation(first_id, second_id)


def contact_first_names(mock_app, email):
    with mock_app.app_context():
        me = user_id(email)
        relations = ContactRelation.query.filter(
            (ContactRelation.user_a_id == me) | (ContactRelation.user_b_id == me)
        ).all()
        other_ids = [r.user_b_id if r.user_a_id == me else r.user_a_id for r in relations]
        return {db.session.get(User, other_id).first_name for other_id in other_ids}


def request_pairs(mock_app):
    with mock_app.app_context():
        return [(r.requester_id, r.recipient_id) for r in ContactRequest.query.all()]


def badges(text):
    return re.findall(r'<span class="badge">(\d+) ', text)


# « Mes contacts »


def test_visitor_is_sent_to_login(client):
    response = client.get("/contacts", follow_redirects=True)

    assert response.request.path == "/login"
    assert "Veuillez vous connecter pour accéder à cette page" in page_text(response)


def test_received_request_is_listed_with_its_actions(mock_app, ids, as_bob):
    add_request(mock_app, ids["alice"], ids["bob"])

    text = page_text(as_bob.get("/contacts"))

    assert "Demandes reçues" in text
    assert "Alice Tremblay" in text
    assert "Nom d'utilisateur" not in text
    assert ">Accepter<" in text and ">Refuser<" in text


def test_accept_is_blue_and_refuse_grey(mock_app, ids, as_bob):
    add_request(mock_app, ids["alice"], ids["bob"])

    text = page_text(as_bob.get("/contacts"))

    assert '<button type="submit" class="button primary">Accepter</button>' in text
    assert '<button type="submit" class="button">Refuser</button>' in text


def test_received_requests_are_listed_oldest_first(mock_app, ids, as_bob):
    add_request(mock_app, ids["carole"], ids["bob"])
    add_request(mock_app, ids["alice"], ids["bob"])

    text = page_text(as_bob.get("/contacts"))

    assert text.index("Carole Roy") < text.index("Alice Tremblay")


def test_sent_request_is_not_listed(mock_app, ids, as_alice):
    add_request(mock_app, ids["alice"], ids["bob"])

    text = page_text(as_alice.get("/contacts"))

    assert "Demandes reçues" not in text
    assert "Bob Gagnon" not in text


def test_contacts_are_listed_by_first_then_last_name(mock_app, ids, as_bob):
    with mock_app.app_context():
        db.session.add(make_user("elise@example.com", first_name="Élise", last_name="Roy"))
        db.session.get(User, ids["carole"]).first_name = "carole"
        db.session.commit()
        elise_id = user_id("elise@example.com")
    for other_id in (elise_id, ids["carole"], ids["alice"]):
        add_relation(mock_app, ids["bob"], other_id)

    text = page_text(as_bob.get("/contacts"))

    assert text.index(">Alice Tremblay<") < text.index(">carole Roy<") < text.index(">Élise Roy<")
    assert (
        len(re.findall(r'<a class="button error" href="/contacts/\d+/remove">Retirer</a>', text))
        == 3
    )


def test_no_contact(as_bob):
    assert "Vous n'avez encore aucun contact" in page_text(as_bob.get("/contacts"))


# Pastille


def test_badge_counts_pending_requests(mock_app, ids, as_bob):
    add_request(mock_app, ids["alice"], ids["bob"])
    add_request(mock_app, ids["carole"], ids["bob"])

    text = page_text(as_bob.get("/"))

    assert badges(text) == ["2", "2"]
    summary = re.search(r"<summary>(.*?)</summary>", text, re.DOTALL)[1]
    assert badges(summary) == ["2"]
    assert 'Mes contacts <span class="badge">2 ' in text
    assert '<span class="visually-hidden">demandes de contact en attente</span>' in text


@pytest.mark.parametrize("answer", ["accept", "refuse"])
def test_no_badge_once_requests_are_answered(mock_app, ids, as_bob, answer):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])
    as_bob.post(f"/contacts/requests/{request_id}/{answer}")

    assert badges(page_text(as_bob.get("/"))) == []


def test_no_badge_for_the_requester(mock_app, ids, as_alice):
    add_request(mock_app, ids["alice"], ids["bob"])

    assert badges(page_text(as_alice.get("/"))) == []


# Réponse aux demandes


def test_accepting_links_both_neighbours(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/requests/{request_id}/accept")

    assert response.status_code == 302
    assert response.headers["Location"] == "/contacts"
    assert request_pairs(mock_app) == []
    assert contact_first_names(mock_app, "bob@example.com") == {"Alice"}
    assert contact_first_names(mock_app, "alice@example.com") == {"Bob"}
    text = page_text(as_bob.get("/contacts"))
    assert "Demandes reçues" not in text
    assert "Alice Tremblay" in text


def test_refusing_deletes_the_request_without_linking(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/requests/{request_id}/refuse")

    assert response.headers["Location"] == "/contacts"
    assert request_pairs(mock_app) == []
    assert contact_first_names(mock_app, "bob@example.com") == set()
    assert "Demandes reçues" not in page_text(as_bob.get("/contacts"))


@pytest.mark.parametrize("answer", ["accept", "refuse"])
def test_request_addressed_to_someone_else_is_not_found(mock_app, ids, answer):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])
    as_carole = login(mock_app.test_client(), "carole@example.com")

    assert as_carole.post(f"/contacts/requests/{request_id}/{answer}").status_code == 404
    assert request_pairs(mock_app) == [(ids["alice"], ids["bob"])]
    assert contact_first_names(mock_app, "bob@example.com") == set()


def test_requester_cannot_accept_her_own_request(mock_app, ids, as_alice):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    assert as_alice.post(f"/contacts/requests/{request_id}/accept").status_code == 404
    assert contact_first_names(mock_app, "alice@example.com") == set()


def test_refusing_after_accepting_changes_nothing(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])
    as_bob.post(f"/contacts/requests/{request_id}/accept")

    response = as_bob.post(f"/contacts/requests/{request_id}/refuse", follow_redirects=True)

    assert response.request.path == "/contacts"
    assert NO_LONGER_PENDING in page_text(response)
    assert contact_first_names(mock_app, "bob@example.com") == {"Alice"}


# Envoi d'une demande


def send(client, recipient_id, q="bob"):
    return client.post("/contacts/requests", data={"recipient_id": recipient_id, "q": q})


def test_request_is_sent_and_goes_back_to_the_search(mock_app, ids, as_alice):
    response = send(as_alice, ids["bob"], q="gagnon")

    assert response.headers["Location"] == "/search?q=gagnon"
    assert request_pairs(mock_app) == [(ids["alice"], ids["bob"])]


def test_second_request_is_not_duplicated(mock_app, ids, as_alice):
    send(as_alice, ids["bob"])
    response = send(as_alice, ids["bob"])

    assert response.headers["Location"].startswith("/search")
    assert request_pairs(mock_app) == [(ids["alice"], ids["bob"])]


def test_request_to_a_contact_is_ignored(mock_app, ids, as_alice):
    add_relation(mock_app, ids["alice"], ids["bob"])

    send(as_alice, ids["bob"])

    assert request_pairs(mock_app) == []


@pytest.mark.parametrize("recipient", ["alice", "unknown", "missing"])
def test_request_to_oneself_or_an_unknown_account_is_not_found(mock_app, ids, as_alice, recipient):
    recipient_id = {"alice": ids["alice"], "unknown": 999_999, "missing": ""}[recipient]

    assert send(as_alice, recipient_id).status_code == 404
    assert request_pairs(mock_app) == []


def test_crossed_request_leads_to_my_contacts(mock_app, ids, as_alice):
    add_request(mock_app, ids["bob"], ids["alice"])

    response = send(as_alice, ids["bob"])

    assert response.headers["Location"] == "/contacts"
    assert request_pairs(mock_app) == [(ids["bob"], ids["alice"])]
    text = page_text(as_alice.get("/contacts"))
    assert "Demandes reçues" in text and "Bob Gagnon" in text and ">Accepter<" in text


def test_new_request_after_a_refusal(mock_app, ids, as_alice, as_bob):
    send(as_alice, ids["bob"])
    with mock_app.app_context():
        request_id = ContactRequest.query.one().id
    as_bob.post(f"/contacts/requests/{request_id}/refuse")

    send(as_alice, ids["bob"])

    assert request_pairs(mock_app) == [(ids["alice"], ids["bob"])]


def test_relation_states(mock_app, ids):
    with mock_app.app_context():
        db.session.add_all([make_user("dave@example.com"), make_user("eve@example.com")])
        db.session.commit()
        dave_id, eve_id = user_id("dave@example.com"), user_id("eve@example.com")
    add_request(mock_app, ids["alice"], ids["bob"])
    add_request(mock_app, ids["carole"], ids["alice"])
    add_relation(mock_app, ids["alice"], dave_id)

    with mock_app.test_request_context():
        login_user(db.session.get(User, ids["alice"]))
        states = relation_states([ids["bob"], ids["carole"], dave_id, eve_id])

    assert states == {
        ids["bob"]: "sent",
        ids["carole"]: "received",
        dave_id: "contact",
        eve_id: "none",
    }


# Retrait d'un contact


def test_remove_page_asks_for_confirmation(mock_app, ids, as_bob):
    add_relation(mock_app, ids["alice"], ids["bob"])

    text = page_text(as_bob.get(f"/contacts/{ids['alice']}/remove"))

    assert (
        f'Retirer <a href="/contacts/{ids["alice"]}">Alice Tremblay</a> de vos contacts ?' in text
    )
    assert '<a class="button" href="/contacts">Annuler</a>' in text
    assert '<button type="submit" class="button error">Retirer</button>' in text
    assert contact_first_names(mock_app, "bob@example.com") == {"Alice"}


def test_confirmed_removal_unlinks_both_sides(mock_app, ids, as_bob):
    add_relation(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/{ids['alice']}/remove")

    assert response.headers["Location"] == "/contacts"
    assert contact_first_names(mock_app, "bob@example.com") == set()
    assert contact_first_names(mock_app, "alice@example.com") == set()


@pytest.mark.parametrize("method", ["get", "post"])
def test_removing_someone_who_is_not_a_contact_changes_nothing(mock_app, ids, as_bob, method):
    add_relation(mock_app, ids["alice"], ids["carole"])

    response = getattr(as_bob, method)(f"/contacts/{ids['alice']}/remove", follow_redirects=True)

    assert response.request.path == "/contacts"
    assert NOT_A_CONTACT in page_text(response)
    assert contact_first_names(mock_app, "alice@example.com") == {"Carole"}


def test_second_removal_changes_nothing(mock_app, ids, as_bob):
    add_relation(mock_app, ids["alice"], ids["bob"])
    as_bob.post(f"/contacts/{ids['alice']}/remove")

    response = as_bob.post(f"/contacts/{ids['alice']}/remove", follow_redirects=True)

    assert response.request.path == "/contacts"
    assert NOT_A_CONTACT in page_text(response)


@pytest.mark.parametrize("method", ["get", "post"])
def test_removing_an_unknown_account_is_not_found(as_bob, method):
    assert getattr(as_bob, method)("/contacts/999999/remove").status_code == 404


def test_badge_label_is_singular_for_one_request(mock_app, ids, as_bob):
    add_request(mock_app, ids["alice"], ids["bob"])

    assert '<span class="visually-hidden">demande de contact en attente</span>' in page_text(
        as_bob.get("/")
    )


# Answering from home, success messages


def flash_success(text):
    return re.findall(r'<div class="flash flash-success">(.*?)</div>', text)


def test_accepting_says_so(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/requests/{request_id}/accept")

    assert response.location == "/contacts"
    text = page_text(as_bob.get(response.location))
    assert flash_success(text) == ["Vous êtes maintenant en contact avec Alice Tremblay"]


def test_refusing_says_so_to_the_one_who_refuses(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/requests/{request_id}/refuse")

    assert flash_success(page_text(as_bob.get(response.location))) == ["Demande refusée"]


@pytest.mark.parametrize("answer", ["accept", "refuse"])
def test_answer_from_home_goes_back_home(mock_app, ids, as_bob, answer):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(f"/contacts/requests/{request_id}/{answer}", data={"origin": "home"})

    assert response.location == "/"


def test_answer_again_from_home_goes_back_home(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])
    as_bob.post(f"/contacts/requests/{request_id}/accept", data={"origin": "home"})

    response = as_bob.post(f"/contacts/requests/{request_id}/refuse", data={"origin": "home"})

    assert response.location == "/"
    assert "Cette demande n'est plus en attente" in page_text(as_bob.get("/"))
    assert contact_first_names(mock_app, "bob@example.com") == {"Alice"}


def test_unknown_origin_goes_back_to_my_contacts(mock_app, ids, as_bob):
    request_id = add_request(mock_app, ids["alice"], ids["bob"])

    response = as_bob.post(
        f"/contacts/requests/{request_id}/refuse", data={"origin": "https://exemple.com"}
    )

    assert response.location == "/contacts"
