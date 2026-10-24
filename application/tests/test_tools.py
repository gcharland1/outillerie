import re
from html import unescape

import pytest

from app.extensions import db
from app.tools import _read_tool_form
from models import Tool, ToolCondition, User
from tests.factories import make_tool

ALREADY_RETIRED = "Cet outil est déjà retiré"
STAYS_RECORDED = (
    "L'outil restera enregistré ; vous pourrez le remettre en circulation depuis "
    "« Mes outils retirés »."
)
ERASE_NOTES = "Effacer définitivement mes notes privées"


def page_text(response):
    return unescape(response.get_data(as_text=True))


def user_id(mock_app, username):
    with mock_app.app_context():
        return User.query.filter_by(username=username).one().id


@pytest.fixture
def alice_id(mock_app, user):
    return user_id(mock_app, user)


@pytest.fixture
def bob_id(mock_app, bob):
    return user_id(mock_app, bob)


def add_tool(mock_app, owner_id, name="Perceuse", **fields):
    with mock_app.app_context():
        return make_tool(owner_id, name=name, **fields).id


def stored(mock_app, tool_id):
    """The tool's fields as the database holds them, or None if it is gone"""
    with mock_app.app_context():
        tool = db.session.get(Tool, tool_id)
        if tool is None:
            return None
        return {
            "owner_id": tool.owner_id,
            "name": tool.name,
            "description": tool.description,
            "condition": tool.condition,
            "private_notes": tool.private_notes,
            "is_active": tool.is_active,
        }


def tool_count(mock_app):
    with mock_app.app_context():
        return Tool.query.count()


def tool_form(**fields):
    return {
        "name": "Perceuse",
        "description": "Perceuse sans fil 18 V",
        "condition": "functional",
        "private_notes": "",
        **fields,
    }


def test_visitor_is_sent_to_login_with_a_french_message(client):
    response = client.get("/tools/mine")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login")
    assert "Veuillez vous connecter pour accéder à cette page" in page_text(
        client.get(response.headers["Location"])
    )


def test_list_shows_only_my_tools_in_circulation(mock_app, logged_in_client, alice_id, bob_id):
    add_tool(mock_app, alice_id, "Perceuse")
    add_tool(mock_app, alice_id, "Scie")
    add_tool(mock_app, alice_id, "Ponceuse", is_active=False)
    add_tool(mock_app, bob_id, "Tondeuse")

    text = page_text(logged_in_client.get("/tools/mine"))

    assert "Perceuse" in text
    assert "Scie" in text
    assert "Ponceuse" not in text
    assert "Tondeuse" not in text


def test_list_is_sorted_by_name_regardless_of_case(mock_app, logged_in_client, alice_id):
    for name in ["scie", "Perceuse", "marteau"]:
        add_tool(mock_app, alice_id, name)

    text = page_text(logged_in_client.get("/tools/mine"))

    assert text.index("marteau") < text.index("Perceuse") < text.index("scie")


def test_list_offers_the_actions(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    text = page_text(logged_in_client.get("/tools/mine"))

    assert f'href="/tools/{tool_id}/edit">Modifier<' in text
    assert f'href="/tools/{tool_id}/retire">Retirer<' in text
    assert "Enregistrer un outil" in text
    assert "Voir mes outils retirés" in text


def test_empty_inventory(logged_in_client):
    text = page_text(logged_in_client.get("/tools/mine"))

    assert "Vous n'avez encore enregistré aucun outil" in text
    assert 'href="/tools/new"' in text


def test_condition_is_shown_in_french(mock_app, logged_in_client, alice_id):
    add_tool(mock_app, alice_id, condition=ToolCondition.NEEDS_REPAIR)

    assert "À réparer" in page_text(logged_in_client.get("/tools/mine"))


def test_form_values_are_cleaned():
    values, error = _read_tool_form(
        tool_form(name="  Perceuse ", description=" Sans fil ", private_notes="   ")
    )

    assert error is None
    assert values == {
        "name": "Perceuse",
        "description": "Sans fil",
        "condition": ToolCondition.FUNCTIONAL,
        "private_notes": None,
    }


def test_form_accepts_a_name_of_250_characters():
    assert _read_tool_form(tool_form(name="a" * 250))[1] is None


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"name": "   "}, "Le nom et la description sont obligatoires"),
        ({"description": ""}, "Le nom et la description sont obligatoires"),
        ({"description": "   "}, "Le nom et la description sont obligatoires"),
        ({"name": "a" * 251}, "Le nom ne doit pas dépasser 250 caractères"),
        ({"condition": "new"}, "L'état choisi est invalide"),
    ],
    ids=["blank-name", "no-description", "blank-description", "name-too-long", "unknown-condition"],
)
def test_form_refusals(fields, message):
    assert _read_tool_form(tool_form(**fields))[1] == message


def test_new_tool_is_recorded(mock_app, logged_in_client, alice_id):
    response = logged_in_client.post(
        "/tools/new",
        data=tool_form(condition="needs_repair", private_notes="Mèche de 8 dans le coffre"),
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/tools/mine"
    with mock_app.app_context():
        tool_id = Tool.query.one().id
    assert stored(mock_app, tool_id) == {
        "owner_id": alice_id,
        "name": "Perceuse",
        "description": "Perceuse sans fil 18 V",
        "condition": ToolCondition.NEEDS_REPAIR,
        "private_notes": "Mèche de 8 dans le coffre",
        "is_active": True,
    }
    assert "Perceuse" in page_text(logged_in_client.get("/tools/mine"))


def test_new_tool_without_condition_is_functional(mock_app, logged_in_client):
    form = tool_form()
    del form["condition"]

    logged_in_client.post("/tools/new", data=form)

    with mock_app.app_context():
        assert Tool.query.one().condition == ToolCondition.FUNCTIONAL


def test_new_tool_with_empty_notes_has_none(mock_app, logged_in_client):
    logged_in_client.post("/tools/new", data=tool_form(private_notes=""))

    with mock_app.app_context():
        assert Tool.query.one().private_notes is None


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"name": "   "}, "Le nom et la description sont obligatoires"),
        ({"name": "a" * 251}, "Le nom ne doit pas dépasser 250 caractères"),
        ({"condition": "new"}, "L'état choisi est invalide"),
    ],
    ids=["blank-name", "name-too-long", "unknown-condition"],
)
def test_invalid_new_tool_is_refused(mock_app, logged_in_client, fields, message):
    response = logged_in_client.post("/tools/new", data=tool_form(**fields))

    assert response.status_code == 200
    text = page_text(response)
    assert message in text
    assert "Perceuse sans fil 18 V" in text
    assert tool_count(mock_app) == 0


def test_edit_form_is_prefilled(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(
        mock_app,
        alice_id,
        description="Sans fil",
        condition=ToolCondition.NEEDS_REPAIR,
        private_notes="Coffre rouge",
    )

    text = page_text(logged_in_client.get(f"/tools/{tool_id}/edit"))

    assert 'value="Perceuse"' in text
    assert ">Sans fil</textarea>" in text
    assert '<option value="needs_repair" selected>' in text
    assert ">Coffre rouge</textarea>" in text


def test_edit_saves_the_changes(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, private_notes="Coffre rouge")

    response = logged_in_client.post(
        f"/tools/{tool_id}/edit", data=tool_form(condition="out_of_order", private_notes="")
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/tools/mine"
    tool = stored(mock_app, tool_id)
    assert tool["condition"] == ToolCondition.OUT_OF_ORDER
    assert tool["private_notes"] is None


def test_invalid_edit_leaves_the_tool_intact(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, description="Sans fil")

    response = logged_in_client.post(f"/tools/{tool_id}/edit", data=tool_form(description=""))

    assert "Le nom et la description sont obligatoires" in page_text(response)
    assert stored(mock_app, tool_id)["description"] == "Sans fil"


@pytest.mark.parametrize("case", ["bobs-tool", "unknown-id", "retired"])
def test_edit_is_not_found(mock_app, logged_in_client, alice_id, bob_id, case):
    tool_id = {
        "bobs-tool": lambda: add_tool(mock_app, bob_id),
        "unknown-id": lambda: 999_999,
        "retired": lambda: add_tool(mock_app, alice_id, is_active=False),
    }[case]()

    assert logged_in_client.get(f"/tools/{tool_id}/edit").status_code == 404
    assert logged_in_client.post(f"/tools/{tool_id}/edit", data=tool_form()).status_code == 404


def test_confirmation_page_changes_nothing(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    text = page_text(logged_in_client.get(f"/tools/{tool_id}/retire"))

    assert "« Perceuse »" in text
    assert STAYS_RECORDED in text
    assert "Confirmer le retrait" in text
    assert 'href="/tools/mine"' in text
    assert stored(mock_app, tool_id)["is_active"] is True


def test_confirmed_retire_keeps_the_tool_recorded(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, private_notes="Coffre rouge")

    response = logged_in_client.post(f"/tools/{tool_id}/retire")

    assert response.status_code == 302
    assert response.headers["Location"] == "/tools/mine"
    tool = stored(mock_app, tool_id)
    assert tool["is_active"] is False
    assert (tool["name"], tool["private_notes"]) == ("Perceuse", "Coffre rouge")
    assert "Perceuse" not in page_text(logged_in_client.get("/tools/mine"))


@pytest.mark.parametrize("method", ["get", "post"])
def test_retiring_bobs_tool_is_not_found(mock_app, logged_in_client, bob_id, method):
    tool_id = add_tool(mock_app, bob_id)

    assert getattr(logged_in_client, method)(f"/tools/{tool_id}/retire").status_code == 404
    assert stored(mock_app, tool_id)["is_active"] is True


@pytest.mark.parametrize("action", ["retire", "restore"])
def test_unknown_tool_is_not_found(logged_in_client, action):
    assert logged_in_client.post(f"/tools/999999/{action}").status_code == 404


def test_checked_box_erases_the_notes(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(
        mock_app, alice_id, condition=ToolCondition.NEEDS_REPAIR, private_notes="Code 1234"
    )

    logged_in_client.post(f"/tools/{tool_id}/retire", data={"erase_private_notes": "1"})

    tool = stored(mock_app, tool_id)
    assert tool["is_active"] is False
    assert tool["private_notes"] is None
    assert (tool["name"], tool["description"], tool["condition"]) == (
        "Perceuse",
        "Perceuse sans fil",
        ToolCondition.NEEDS_REPAIR,
    )


def test_confirmation_offers_the_box_only_with_notes(mock_app, logged_in_client, alice_id):
    with_notes = add_tool(mock_app, alice_id, private_notes="Code 1234")
    without_notes = add_tool(mock_app, alice_id, "Scie")

    with_box = page_text(logged_in_client.get(f"/tools/{with_notes}/retire"))
    assert ERASE_NOTES in with_box
    assert re.search(r'<input type="checkbox" name="erase_private_notes"[^>]*>', with_box)
    assert "checked" not in re.search(r'<input type="checkbox"[^>]*>', with_box)[0]
    assert ERASE_NOTES not in page_text(logged_in_client.get(f"/tools/{without_notes}/retire"))


def test_back_to_the_confirmation_after_a_retire(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)
    logged_in_client.post(f"/tools/{tool_id}/retire")

    response = logged_in_client.get(f"/tools/{tool_id}/retire")

    assert response.status_code == 302
    assert response.headers["Location"] == "/tools/mine"
    assert ALREADY_RETIRED in page_text(logged_in_client.get("/tools/mine"))


def test_second_submit_changes_nothing(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, private_notes="Code 1234")
    logged_in_client.post(f"/tools/{tool_id}/retire")

    response = logged_in_client.post(f"/tools/{tool_id}/retire", data={"erase_private_notes": "1"})

    assert response.headers["Location"] == "/tools/mine"
    assert ALREADY_RETIRED in page_text(logged_in_client.get("/tools/mine"))
    tool = stored(mock_app, tool_id)
    assert (tool["is_active"], tool["private_notes"]) == (False, "Code 1234")


def test_retired_list_shows_only_retired_tools(mock_app, logged_in_client, alice_id):
    add_tool(mock_app, alice_id, "Ponceuse", is_active=False)
    add_tool(mock_app, alice_id, "Perceuse")

    text = page_text(logged_in_client.get("/tools/mine/retired"))

    assert "Ponceuse" in text
    assert "Perceuse" not in text
    assert "Remettre en circulation" in text
    assert 'href="/tools/mine"' in text


def test_retired_list_is_sorted_by_name_regardless_of_case(mock_app, logged_in_client, alice_id):
    for name in ["scie", "Perceuse", "marteau"]:
        add_tool(mock_app, alice_id, name, is_active=False)

    text = page_text(logged_in_client.get("/tools/mine/retired"))

    assert text.index("marteau") < text.index("Perceuse") < text.index("scie")


def test_restoring_a_tool_in_circulation_is_not_found(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    assert logged_in_client.post(f"/tools/{tool_id}/restore").status_code == 404
    assert stored(mock_app, tool_id)["is_active"] is True


def test_no_retired_tool(logged_in_client):
    assert "Aucun outil retiré" in page_text(logged_in_client.get("/tools/mine/retired"))


def test_restore_keeps_the_condition(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(
        mock_app, alice_id, "Ponceuse", condition=ToolCondition.NEEDS_REPAIR, is_active=False
    )

    response = logged_in_client.post(f"/tools/{tool_id}/restore")

    assert response.headers["Location"] == "/tools/mine/retired"
    tool = stored(mock_app, tool_id)
    assert (tool["is_active"], tool["condition"]) == (True, ToolCondition.NEEDS_REPAIR)
    assert "Ponceuse" in page_text(logged_in_client.get("/tools/mine"))


def test_restore_after_erasing_has_no_notes(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, private_notes="Code 1234")
    logged_in_client.post(f"/tools/{tool_id}/retire", data={"erase_private_notes": "1"})

    logged_in_client.post(f"/tools/{tool_id}/restore")

    tool = stored(mock_app, tool_id)
    assert (tool["is_active"], tool["private_notes"]) == (True, None)


def test_restoring_bobs_tool_is_not_found(mock_app, logged_in_client, bob_id):
    tool_id = add_tool(mock_app, bob_id, is_active=False)

    assert logged_in_client.post(f"/tools/{tool_id}/restore").status_code == 404
    assert stored(mock_app, tool_id)["is_active"] is False


def test_every_post_form_of_the_tool_pages_carries_a_token(mock_app, logged_in_client, alice_id):
    active = add_tool(mock_app, alice_id, private_notes="Code 1234")
    add_tool(mock_app, alice_id, "Ponceuse", is_active=False)
    pages = [
        "/tools/mine",
        "/tools/mine/retired",
        "/tools/new",
        f"/tools/{active}/edit",
        f"/tools/{active}/retire",
    ]

    for page in pages:
        html = logged_in_client.get(page).get_data(as_text=True)
        forms = re.findall(r'<form [^>]*method="post"[^>]*>(.*?)</form>', html, re.DOTALL)
        assert forms, page
        for form in forms:
            assert 'name="csrf_token"' in form, page
