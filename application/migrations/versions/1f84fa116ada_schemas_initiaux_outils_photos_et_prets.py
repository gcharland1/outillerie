"""Schémas initiaux : outils, photos et prêts

Revision ID: 1f84fa116ada
Revises: a0989299c569
Create Date: 2026-10-21 07:30:17.824730

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1f84fa116ada"
down_revision = "a0989299c569"
branch_labels = None
depends_on = None

TOOL_CONDITIONS = ("fonctionnel", "a_reparer", "hors_service")
LOAN_STATUSES = ("demande", "accepte", "refuse", "annule", "remis", "rendu")


def enum_type(values, name):
    # The named CHECK is declared on the table, so the type must not add its own.
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=False, length=20)


def in_values(column, values):
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def rename_user_constraint(old, new):
    # Databases created before the naming convention hold Postgres' default names; a fresh
    # database gets the convention's names from revision a0989299c569 already.
    op.execute(
        f"""
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = '{old}' AND conrelid = '"user"'::regclass
          ) THEN
            ALTER TABLE "user" RENAME CONSTRAINT {old} TO {new};
          END IF;
        END $$
        """
    )


def upgrade():
    # Hand-written: the GiST exclusion constraint on loan compares an integer with `=`.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Hand-written: autogenerate does not detect renamed constraints (ADR 0007).
    rename_user_constraint("user_pkey", "pk_user")
    rename_user_constraint("user_username_key", "uq_user_username")

    op.create_table(
        "tool",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "condition",
            enum_type(TOOL_CONDITIONS, "tool_condition"),
            server_default="fonctionnel",
            nullable=False,
        ),
        sa.Column("private_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            in_values("condition", TOOL_CONDITIONS), name=op.f("ck_tool_tool_condition")
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], name=op.f("fk_tool_owner_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool")),
    )
    op.create_index(op.f("ix_tool_owner_id"), "tool", ["owner_id"], unique=False)

    op.create_table(
        "loan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("borrower_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            enum_type(LOAN_STATUSES, "loan_status"),
            server_default="demande",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        postgresql.ExcludeConstraint(
            (sa.column("tool_id"), "="),
            (sa.literal_column("daterange(start_date, end_date, '[]')"), "&&"),
            where=sa.text("status IN ('accepte', 'remis')"),
            using="gist",
            name="excl_loan_tool_dates",
        ),
        sa.CheckConstraint(in_values("status", LOAN_STATUSES), name=op.f("ck_loan_loan_status")),
        sa.CheckConstraint("end_date >= start_date", name=op.f("ck_loan_end_after_start")),
        sa.ForeignKeyConstraint(
            ["borrower_id"], ["user.id"], name=op.f("fk_loan_borrower_id_user")
        ),
        sa.ForeignKeyConstraint(["tool_id"], ["tool.id"], name=op.f("fk_loan_tool_id_tool")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_loan")),
    )
    op.create_index(op.f("ix_loan_borrower_id"), "loan", ["borrower_id"], unique=False)
    op.create_index(op.f("ix_loan_tool_id"), "loan", ["tool_id"], unique=False)

    op.create_table(
        "tool_photo",
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"], ["tool.id"], name=op.f("fk_tool_photo_tool_id_tool"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("tool_id", name=op.f("pk_tool_photo")),
    )

    op.alter_column(
        "user",
        "phone",
        existing_type=sa.VARCHAR(length=11),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
    # Fails if two existing accounts share an email in different cases; there is no production
    # database yet.
    op.create_index("uq_user_email_lower", "user", [sa.literal_column("lower(email)")], unique=True)


def downgrade():
    op.drop_index("uq_user_email_lower", table_name="user")
    # Fails if a phone number longer than 11 characters was stored since the upgrade.
    op.alter_column(
        "user",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.VARCHAR(length=11),
        existing_nullable=True,
    )

    op.drop_table("tool_photo")
    op.drop_index(op.f("ix_loan_tool_id"), table_name="loan")
    op.drop_index(op.f("ix_loan_borrower_id"), table_name="loan")
    op.drop_table("loan")
    op.drop_index(op.f("ix_tool_owner_id"), table_name="tool")
    op.drop_table("tool")

    rename_user_constraint("uq_user_username", "user_username_key")
    rename_user_constraint("pk_user", "user_pkey")
    # btree_gist is left installed: other objects may depend on it.
