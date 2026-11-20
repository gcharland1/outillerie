import re
from datetime import timedelta
from html import unescape

import pytest
from flask import render_template_string
from flask_login import login_user

from app import catalog
from app.extensions import db
from models import LoanStatus
from models.user import User
from tests.conftest import add_loan, add_tool, login
from tests.factories import make_contact_relation, make_contact_request, user_id

CONTACT_IDS = "{{ contact_ids | sort | join(',') }}"


def render_as(mock_app, email, source, **context):
    """The template source rendered in a request of the user with this email, or of a visitor"""
    with mock_app.test_request_context():
        if email is not None:
            login_user(db.session.get(User, user_id(email)))
        return render_template_string(source, **context)


def test_contact_ids_of_a_user_with_two_contacts(mock_app, user, bob, carole):
    with mock_app.app_context():
        alice, bob_id, carole_id = (user_id(email) for email in (user, bob, carole))
        make_contact_relation(alice, bob_id)
        make_contact_relation(carole_id, alice)

    expected = ",".join(str(other) for other in sorted([bob_id, carole_id]))
    assert render_as(mock_app, user, CONTACT_IDS) == expected


def test_a_visitor_has_no_contact_ids(mock_app, user, bob):
    with mock_app.app_context():
        make_contact_relation(user_id(user), user_id(bob))

    assert render_as(mock_app, None, CONTACT_IDS) == ""


USER_NAME = '{% from "_user_name.html" import user_name with context %}[{{ user_name(other) }}]'


def rendered_name(mock_app, viewer, email):
    with mock_app.app_context():
        other = db.session.get(User, user_id(email))
    return render_as(mock_app, viewer, USER_NAME, other=other)


def test_a_contacts_name_links_to_the_contacts_page(mock_app, user, bob):
    with mock_app.app_context():
        bob_id = user_id(bob)
        make_contact_relation(user_id(user), bob_id)

    assert rendered_name(mock_app, user, bob) == f'[<a href="/contacts/{bob_id}">Bob Gagnon</a>]'


def test_a_non_contacts_name_is_text(mock_app, user, carole):
    assert rendered_name(mock_app, user, carole) == "[Carole Roy]"


def test_ones_own_name_is_text(mock_app, user):
    assert rendered_name(mock_app, user, user) == "[Alice Tremblay]"


def test_a_name_is_escaped(mock_app, user, bob):
    with mock_app.app_context():
        db.session.get(User, user_id(bob)).first_name = "<b>Bob</b>"
        db.session.commit()
        make_contact_relation(user_id(user), user_id(bob))

    assert "&lt;b&gt;Bob&lt;/b&gt; Gagnon</a>" in rendered_name(mock_app, user, bob)


def test_a_deleted_accounts_name_is_greyed_text_even_for_a_contact(mock_app, user, bob):
    with mock_app.app_context():
        bob_id = user_id(bob)
        make_contact_relation(user_id(user), bob_id)
        account = db.session.get(User, bob_id)
        account.first_name = "<b>Bob</b>"
        account.deleted_at = db.func.now()
        db.session.commit()

    assert rendered_name(mock_app, user, bob) == (
        '[<span class="user-deleted">&lt;b&gt;Bob&lt;/b&gt; Gagnon (supprimé)</span>]'
    )


# Names on the pages


@pytest.fixture
def ids(mock_app, user, bob, carole):
    with mock_app.app_context():
        return {email.partition("@")[0]: user_id(email) for email in (user, bob, carole)}


@pytest.fixture
def as_alice(mock_app, ids):
    return login(mock_app.test_client(), "alice@example.com")


def page_text(response):
    return unescape(response.get_data(as_text=True))


def bob_link(ids):
    return f'<a href="/contacts/{ids["bob"]}">Bob Gagnon</a>'


def bobs_drill_lent_to_alice(mock_app, ids, status):
    drill = add_tool(mock_app, ids["bob"])
    today = catalog.site_today()
    return add_loan(
        mock_app, drill, ids["alice"], today + timedelta(1), today + timedelta(3), status
    )


def test_a_contacts_name_in_loans(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    loan_id = bobs_drill_lent_to_alice(mock_app, ids, LoanStatus.ACCEPTED)

    for path in ("/", "/loans", f"/loans/{loan_id}/cancel"):
        assert bob_link(ids) in page_text(as_alice.get(path)), path


def test_a_former_contacts_name_in_loans(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
    bobs_drill_lent_to_alice(mock_app, ids, LoanStatus.LENT)
    as_alice.post(f"/contacts/{ids['bob']}/remove")

    for path in ("/", "/loans"):
        text = page_text(as_alice.get(path))
        assert "<td>Bob Gagnon</td>" in text, path
        assert f'href="/contacts/{ids["bob"]}"' not in text, path


def test_a_received_contact_request_names_a_non_contact(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_request(ids["carole"], ids["alice"])

    for path in ("/", "/contacts"):
        text = page_text(as_alice.get(path))
        assert "<td>Carole Roy</td>" in text, path
        assert f'href="/contacts/{ids["carole"]}"' not in text, path


def test_search_results_link_contacts_only(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])
        db.session.get(User, ids["carole"]).last_name = "Gagnon"
        db.session.commit()

    text = page_text(as_alice.get("/search", query_string={"type": "user", "q": "Gagnon"}))

    assert f"<td>{bob_link(ids)}</td>" in text
    assert "<td>Carole Gagnon</td>" in text


def test_a_contacts_page_title_is_not_a_link(mock_app, ids, as_alice):
    with mock_app.app_context():
        make_contact_relation(ids["alice"], ids["bob"])

    text = page_text(as_alice.get(f"/contacts/{ids['bob']}"))

    assert "<h2>Bob Gagnon</h2>" in text
    assert "<h3>Outils de Bob Gagnon</h3>" in text


def test_the_account_menu_name_is_not_a_link(mock_app, ids, as_alice):
    text = page_text(as_alice.get("/"))

    summary = re.search(r"<summary>(.*?)</summary>", text, re.DOTALL)[1]
    assert '<span class="account-name">Alice Tremblay</span>' in summary
    assert "<a " not in summary
