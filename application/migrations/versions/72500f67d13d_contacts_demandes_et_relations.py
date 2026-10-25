"""Contacts : demandes et relations

Revision ID: 72500f67d13d
Revises: 1f84fa116ada
Create Date: 2026-10-25 09:54:48.356728

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "72500f67d13d"
down_revision = "1f84fa116ada"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contact_relation",
        sa.Column("user_a_id", sa.Integer(), nullable=False),
        sa.Column("user_b_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("user_a_id < user_b_id", name=op.f("ck_contact_relation_ordered_pair")),
        sa.ForeignKeyConstraint(
            ["user_a_id"], ["user.id"], name=op.f("fk_contact_relation_user_a_id_user")
        ),
        sa.ForeignKeyConstraint(
            ["user_b_id"], ["user.id"], name=op.f("fk_contact_relation_user_b_id_user")
        ),
        sa.PrimaryKeyConstraint("user_a_id", "user_b_id", name=op.f("pk_contact_relation")),
    )
    op.create_index(
        op.f("ix_contact_relation_user_b_id"), "contact_relation", ["user_b_id"], unique=False
    )

    op.create_table(
        "contact_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "requester_id <> recipient_id", name=op.f("ck_contact_request_not_self")
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"], ["user.id"], name=op.f("fk_contact_request_recipient_id_user")
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"], ["user.id"], name=op.f("fk_contact_request_requester_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contact_request")),
    )
    op.create_index(
        op.f("ix_contact_request_recipient_id"), "contact_request", ["recipient_id"], unique=False
    )
    op.create_index(
        op.f("ix_contact_request_requester_id"), "contact_request", ["requester_id"], unique=False
    )
    op.create_index(
        "uq_contact_request_pair",
        "contact_request",
        [
            sa.literal_column("least(requester_id, recipient_id)"),
            sa.literal_column("greatest(requester_id, recipient_id)"),
        ],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_contact_request_pair", table_name="contact_request")
    op.drop_index(op.f("ix_contact_request_requester_id"), table_name="contact_request")
    op.drop_index(op.f("ix_contact_request_recipient_id"), table_name="contact_request")

    op.drop_table("contact_request")
    op.drop_index(op.f("ix_contact_relation_user_b_id"), table_name="contact_relation")

    op.drop_table("contact_relation")
