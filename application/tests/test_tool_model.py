import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError, StatementError

from app.extensions import db
from models import Loan, LoanStatus, Tool, ToolCondition, ToolPhoto, User
from tests.factories import a_day, make_tool, make_user


@pytest.fixture
def owner_id(mock_app, user):
    with mock_app.app_context():
        return User.query.filter_by(username=user).one().id


def test_complete_tool_is_stored(mock_app, owner_id):
    with mock_app.app_context():
        tool_id = make_tool(owner_id, name="Perceuse", description="Perceuse sans fil 18 V").id
        db.session.expire_all()
        tool = db.session.get(Tool, tool_id)
        assert (tool.owner_id, tool.name, tool.description) == (
            owner_id,
            "Perceuse",
            "Perceuse sans fil 18 V",
        )


@pytest.mark.parametrize("owner", [None, 999_999])
def test_tool_without_existing_owner_is_refused(mock_app, owner):
    with mock_app.app_context():
        db.session.add(Tool(owner_id=owner, name="Scie", description="Scie ronde"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert Tool.query.count() == 0


@pytest.mark.parametrize("missing", ["name", "description"])
def test_tool_without_name_or_description_is_refused(mock_app, owner_id, missing):
    fields = {"name": "Scie", "description": "Scie ronde", missing: None}
    with mock_app.app_context():
        db.session.add(Tool(owner_id=owner_id, **fields))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert Tool.query.count() == 0


def test_tool_condition_defaults_to_fonctionnel(mock_app, owner_id):
    with mock_app.app_context():
        assert make_tool(owner_id).condition is ToolCondition.FONCTIONNEL
        db.session.execute(
            text("INSERT INTO tool (owner_id, name, description) VALUES (:owner, 'Scie', 'Ronde')"),
            {"owner": owner_id},
        )
        assert (
            db.session.execute(text("SELECT condition FROM tool WHERE name = 'Scie'")).scalar_one()
            == "fonctionnel"
        )


def test_unknown_condition_is_refused_by_the_orm(mock_app, owner_id):
    with mock_app.app_context():
        db.session.add(Tool(owner_id=owner_id, name="Scie", description="Ronde", condition="neuf"))
        with pytest.raises(StatementError):
            db.session.commit()


def test_unknown_condition_is_refused_by_the_database(mock_app, owner_id):
    with mock_app.app_context(), pytest.raises(IntegrityError, match="ck_tool_tool_condition"):
        db.session.execute(
            text(
                "INSERT INTO tool (owner_id, name, description, condition) "
                "VALUES (:owner, 'Scie', 'Ronde', 'neuf')"
            ),
            {"owner": owner_id},
        )


def test_tool_without_private_notes_is_stored(mock_app, owner_id):
    with mock_app.app_context():
        tool_id = make_tool(owner_id).id
        db.session.expire_all()
        assert db.session.get(Tool, tool_id).private_notes is None


def test_new_tool_is_in_circulation(mock_app, owner_id):
    with mock_app.app_context():
        assert make_tool(owner_id).is_active is True
        db.session.execute(
            text("INSERT INTO tool (owner_id, name, description) VALUES (:owner, 'Scie', 'Ronde')"),
            {"owner": owner_id},
        )
        assert (
            db.session.execute(text("SELECT is_active FROM tool WHERE name = 'Scie'")).scalar_one()
            is True
        )


def test_retired_tool_keeps_its_photo_and_loans(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"photo", content_type="image/jpeg")
        db.session.add(
            Loan(
                tool=tool,
                borrower=make_user("bob", "bob@example.com"),
                start_date=a_day(3),
                end_date=a_day(5),
                status=LoanStatus.RENDU,
            )
        )
        tool.is_active = False
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(Tool, tool.id).is_active is False
        assert db.session.get(ToolPhoto, tool.id).content == b"photo"
        assert Loan.query.filter_by(tool_id=tool.id).count() == 1


def test_photo_is_stored_with_its_content_type(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"\xff\xd8\xff", content_type="image/jpeg")
        db.session.commit()
        db.session.expire_all()
        photo = db.session.get(ToolPhoto, tool.id)
        assert (photo.content, photo.content_type) == (b"\xff\xd8\xff", "image/jpeg")


def test_new_photo_replaces_the_previous_one(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"jpeg", content_type="image/jpeg")
        db.session.commit()
        tool.photo = ToolPhoto(content=b"png", content_type="image/png")
        db.session.commit()
        tool_id = tool.id
        db.session.expunge_all()

        photos = ToolPhoto.query.filter_by(tool_id=tool_id).all()
        assert [(photo.content, photo.content_type) for photo in photos] == [(b"png", "image/png")]


def test_photo_added_beside_the_existing_one_is_refused(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"first", content_type="image/jpeg")
        db.session.commit()
        tool_id = tool.id
        db.session.expunge_all()

        db.session.add(ToolPhoto(tool_id=tool_id, content=b"second", content_type="image/png"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.get(ToolPhoto, tool_id).content == b"first"


def test_deleting_a_tool_deletes_its_photo(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"photo", content_type="image/jpeg")
        db.session.commit()
        tool_id = tool.id
        db.session.expunge_all()

        db.session.delete(db.session.get(Tool, tool_id))
        db.session.commit()
        assert ToolPhoto.query.count() == 0


def test_loading_a_tool_does_not_read_its_photo(mock_app, owner_id):
    with mock_app.app_context():
        tool = make_tool(owner_id)
        tool.photo = ToolPhoto(content=b"photo", content_type="image/jpeg")
        db.session.commit()
        tool_id = tool.id
        db.session.expunge_all()

        statements = []
        listener = lambda *args: statements.append(args[2])  # noqa: E731
        event.listen(db.engine, "before_cursor_execute", listener)
        try:
            db.session.get(Tool, tool_id)
            Tool.query.all()
        finally:
            event.remove(db.engine, "before_cursor_execute", listener)
        assert statements
        assert not [s for s in statements if "tool_photo" in s]
