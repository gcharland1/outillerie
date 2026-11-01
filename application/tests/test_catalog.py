from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import event

from app import catalog
from app.extensions import db
from models import Loan, LoanStatus, ToolCondition
from tests.factories import make_contact_relation, make_contact_request, make_tool, user_id

TODAY = catalog.site_today()


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


def visible_names(user_id, **filters):
    return [tool.name for tool in catalog.visible_tools(user_id, **filters)]


def add_loan(tool, borrower_id, status, first_day, last_day):
    db.session.add(
        Loan(
            tool_id=tool.id,
            borrower_id=borrower_id,
            status=status,
            start_date=first_day,
            end_date=last_day,
        )
    )
    db.session.commit()


def test_a_contacts_tool_is_visible(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Perceuse")
        assert visible_names(contacts["alice"]) == ["Perceuse"]


def test_own_tools_are_not_visible(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["alice"], name="Scie")
        assert visible_names(contacts["alice"]) == []


def test_a_non_contacts_tool_is_not_visible(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["carole"], name="Ponceuse")
        assert visible_names(contacts["alice"]) == []


def test_a_pending_contact_request_shows_no_tool(mock_app, ids):
    with mock_app.app_context():
        make_contact_request(ids["alice"], ids["carole"])
        make_tool(ids["carole"], name="Ponceuse")
        assert visible_names(ids["alice"]) == []
        assert visible_names(ids["carole"]) == []


def test_retired_and_out_of_order_tools_are_not_visible(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Retirée", is_active=False)
        make_tool(contacts["bob"], name="Cassée", condition=ToolCondition.OUT_OF_ORDER)
        assert visible_names(contacts["alice"]) == []


def test_a_tool_needing_repair_is_visible(mock_app, contacts):
    with mock_app.app_context():
        tool = make_tool(contacts["bob"], condition=ToolCondition.NEEDS_REPAIR)
        [card] = catalog.tool_cards([tool])
        assert card.condition == "À réparer"


def test_tools_seen_both_ways_of_the_relation(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["alice"], name="Scie")
        assert visible_names(contacts["bob"]) == ["Scie"]


def test_owner_filter_keeps_one_contacts_tools(mock_app, contacts):
    with mock_app.app_context():
        make_contact_relation(contacts["alice"], contacts["carole"])
        make_tool(contacts["bob"], name="Perceuse")
        make_tool(contacts["carole"], name="Ponceuse")
        assert visible_names(contacts["alice"], owner_id=contacts["bob"]) == ["Perceuse"]


def test_is_contact(mock_app, contacts):
    with mock_app.app_context():
        assert catalog.is_contact(contacts["alice"], contacts["bob"])
        assert catalog.is_contact(contacts["bob"], contacts["alice"])
        assert not catalog.is_contact(contacts["alice"], contacts["carole"])
        assert not catalog.is_contact(contacts["alice"], contacts["alice"])


@pytest.mark.parametrize(
    ("status", "first_day", "last_day", "label"),
    [
        (
            LoanStatus.LENT,
            TODAY - timedelta(days=1),
            date(2099, 11, 3),
            "Prêté jusqu'au 3 novembre 2099",
        ),
        (LoanStatus.LENT, TODAY - timedelta(days=9), TODAY - timedelta(days=2), "Prêté jusqu'au"),
        (LoanStatus.REQUESTED, TODAY, TODAY + timedelta(days=2), "En attente de prêt"),
        (
            LoanStatus.ACCEPTED,
            TODAY + timedelta(days=10),
            TODAY + timedelta(days=12),
            "En attente de prêt",
        ),
        (LoanStatus.RETURNED, TODAY - timedelta(days=9), TODAY - timedelta(days=2), "Disponible"),
        (LoanStatus.REFUSED, TODAY, TODAY + timedelta(days=2), "Disponible"),
        (LoanStatus.CANCELED, TODAY, TODAY + timedelta(days=2), "Disponible"),
        (LoanStatus.REQUESTED, TODAY - timedelta(days=9), TODAY - timedelta(days=2), "Disponible"),
    ],
)
def test_loan_status(mock_app, contacts, status, first_day, last_day, label):
    with mock_app.app_context():
        tool = make_tool(contacts["bob"])
        add_loan(tool, contacts["alice"], status, first_day, last_day)
        [card] = catalog.tool_cards([tool])
        assert card.status.startswith(label)
        assert card.available == (label == "Disponible")


def test_a_loan_ends_at_midnight_where_its_users_live(mock_app, contacts, monkeypatch):
    class EveningInQuebec(datetime):
        @classmethod
        def now(cls, tz=None):
            # 21 h on November 3 in Québec is already November 4 in UTC.
            return datetime(2026, 11, 4, 2, 0, tzinfo=UTC).astimezone(tz)

    monkeypatch.setattr(catalog, "datetime", EveningInQuebec)
    with mock_app.app_context():
        tool = make_tool(contacts["bob"])
        add_loan(
            tool, contacts["alice"], LoanStatus.REQUESTED, date(2026, 11, 2), date(2026, 11, 3)
        )
        assert catalog.site_today() == date(2026, 11, 3)
        assert catalog.loan_statuses([tool.id]) == {tool.id: "En attente de prêt"}


def test_lent_wins_over_a_pending_request(mock_app, contacts):
    with mock_app.app_context():
        tool = make_tool(contacts["bob"])
        add_loan(tool, contacts["alice"], LoanStatus.REQUESTED, TODAY, TODAY + timedelta(days=30))
        add_loan(tool, contacts["carole"], LoanStatus.LENT, TODAY, date(2099, 11, 3))
        assert catalog.loan_statuses([tool.id]) == {tool.id: "Prêté jusqu'au 3 novembre 2099"}


def test_french_date():
    assert catalog.french_date(date(2026, 11, 3)) == "3 novembre 2026"
    assert catalog.french_date(date(2027, 8, 15)) == "15 août 2027"


def test_available_only_hides_lent_and_pending_tools(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Perceuse")
        lent = make_tool(contacts["bob"], name="Scie")
        pending = make_tool(contacts["bob"], name="Ponceuse")
        add_loan(lent, contacts["alice"], LoanStatus.LENT, TODAY, TODAY + timedelta(days=3))
        add_loan(pending, contacts["alice"], LoanStatus.REQUESTED, TODAY, TODAY + timedelta(days=3))
        assert visible_names(contacts["alice"], available_only=True) == ["Perceuse"]
        assert visible_names(contacts["alice"]) == ["Perceuse", "Ponceuse", "Scie"]


@pytest.mark.parametrize(
    ("name", "description", "searched"),
    [
        ("Perceuse", "Sans fil", "perseuse"),
        ("Scie à métaux", "Lame neuve", "scie a metaux"),
        ("Coffret", "Embouts de vissage", "vissage"),
        ("Perceuse", "Sans fil", "PERCEUSE"),
        ("Perceuse", "Sans fil", "ce"),
    ],
)
def test_text_finds(mock_app, contacts, name, description, searched):
    with mock_app.app_context():
        make_tool(contacts["bob"], name=name, description=description)
        assert visible_names(contacts["alice"], text=searched) == [name]


@pytest.mark.parametrize("searched", ["tondeuse", "50%", "%", "_", "a_b", "zz"])
def test_text_leaves_out(mock_app, contacts, searched):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Perceuse", description="Sans fil, avec batterie")
        assert visible_names(contacts["alice"], text=searched) == []


def test_private_notes_are_not_searched(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Perceuse", private_notes="code du cadenas")
        assert visible_names(contacts["alice"], text="cadenas") == []


def test_exact_name_match_comes_first(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Robot culinaire", description="Mélangeur")
        make_tool(contacts["bob"], name="Rabot électrique", description="Pour le bois")
        assert visible_names(contacts["alice"], text="rabot")[0] == "Rabot électrique"


def test_name_match_comes_before_description_match(mock_app, contacts):
    with mock_app.app_context():
        make_tool(contacts["bob"], name="Établi", description="Idéal pour la scie")
        make_tool(contacts["bob"], name="Scie sauteuse", description="Lames fournies")
        assert visible_names(contacts["alice"], text="scie") == ["Scie sauteuse", "Établi"]


def test_without_text_tools_are_sorted_by_name(mock_app, contacts):
    with mock_app.app_context():
        for name in ("carotteuse", "Bêche", "agrafeuse"):
            make_tool(contacts["bob"], name=name)
        assert visible_names(contacts["alice"]) == ["agrafeuse", "Bêche", "carotteuse"]


@pytest.mark.parametrize(
    ("length", "shown"),
    [(125, "x" * 125), (200, "x" * 125 + "…")],
)
def test_short_description(length, shown):
    assert catalog.short_description("x" * length) == shown


def count_queries(work):
    statements = []

    def record(*args):
        statements.append(args[2])

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        work()
    finally:
        event.remove(db.engine, "before_cursor_execute", record)
    return len(statements)


def test_the_number_of_queries_does_not_grow_with_the_tools(mock_app, contacts):
    def cards():
        db.session.expire_all()
        for card in catalog.tool_cards(catalog.visible_tools(contacts["alice"])):
            assert card.tool.owner.first_name

    with mock_app.app_context():
        tool = make_tool(contacts["bob"])
        add_loan(tool, contacts["alice"], LoanStatus.REQUESTED, TODAY, TODAY + timedelta(days=2))
        one_tool = count_queries(cards)
        make_contact_relation(contacts["alice"], contacts["carole"])
        for number in range(9):
            make_tool(contacts["bob" if number % 2 else "carole"], name=f"Outil {number}")
        assert count_queries(cards) == one_tool
