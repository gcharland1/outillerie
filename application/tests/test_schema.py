import flask_migrate
import pytest
from sqlalchemy import text

from app import create_app
from app.extensions import db
from tests.conftest import app_config

EXPECTED_CONSTRAINT_NAMES = {
    "user": {"pk_user", "uq_user_username", "uq_user_email_lower"},
    "tool": {"pk_tool", "fk_tool_owner_id_user", "ix_tool_owner_id", "ck_tool_tool_condition"},
    "tool_photo": {"pk_tool_photo", "fk_tool_photo_tool_id_tool"},
    "loan": {
        "pk_loan",
        "fk_loan_tool_id_tool",
        "fk_loan_borrower_id_user",
        "ix_loan_tool_id",
        "ix_loan_borrower_id",
        "ck_loan_loan_status",
        "ck_loan_end_after_start",
        "excl_loan_tool_dates",
    },
    "contact_request": {
        "pk_contact_request",
        "fk_contact_request_requester_id_user",
        "fk_contact_request_recipient_id_user",
        "ix_contact_request_requester_id",
        "ix_contact_request_recipient_id",
        "ck_contact_request_not_self",
        "uq_contact_request_pair",
    },
    "contact_relation": {
        "pk_contact_relation",
        "fk_contact_relation_user_a_id_user",
        "fk_contact_relation_user_b_id_user",
        "ix_contact_relation_user_b_id",
        "ck_contact_relation_ordered_pair",
    },
}


def drop_schema():
    db.drop_all()
    db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
    db.session.execute(text("DROP EXTENSION IF EXISTS btree_gist"))
    db.session.commit()


@pytest.fixture
def migrated_app():
    """An app whose database is built by the Alembic revisions, not by db.create_all()"""
    app = create_app(app_config())
    with app.app_context():
        drop_schema()
        flask_migrate.upgrade()
    yield app
    with app.app_context():
        db.session.remove()
        flask_migrate.downgrade(revision="base")
        drop_schema()


def constraint_names(table):
    """Names of every constraint and index Postgres holds for the table"""
    rows = db.session.execute(
        text(
            "SELECT conname FROM pg_constraint WHERE conrelid = CAST(:table AS regclass) "
            "UNION SELECT indexname FROM pg_indexes WHERE tablename = :name"
        ),
        {"table": f'"{table}"', "name": table},
    )
    return {row[0] for row in rows}


def test_revisions_create_exactly_the_expected_constraints(migrated_app):
    with migrated_app.app_context():
        assert {table: constraint_names(table) for table in EXPECTED_CONSTRAINT_NAMES} == (
            EXPECTED_CONSTRAINT_NAMES
        )


def test_revisions_create_the_btree_gist_extension(migrated_app):
    with migrated_app.app_context():
        assert "btree_gist" in {
            row[0] for row in db.session.execute(text("SELECT extname FROM pg_extension"))
        }
