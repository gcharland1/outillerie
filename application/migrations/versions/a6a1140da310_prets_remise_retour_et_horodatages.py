"""Prêts : remise, retour et horodatages

Revision ID: a6a1140da310
Revises: 13db5eeed32b
Create Date: 2026-11-12 19:36:01.470206

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a6a1140da310"
down_revision = "13db5eeed32b"
branch_labels = None
depends_on = None

OLD_STATUSES = ("requested", "accepted", "refused", "canceled", "lent", "returned")
NEW_STATUSES = (
    "requested",
    "accepted",
    "refused",
    "canceled",
    "handover_claimed",
    "lent",
    "return_claimed",
    "returned",
)
OLD_COMMITTED = ("accepted", "lent")
NEW_COMMITTED = ("accepted", "handover_claimed", "lent", "return_claimed")


def in_values(column, values):
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def replace_constraints(statuses, committed):
    # Hand-written: autogenerate sees neither the CHECK nor the exclusion's WHERE (ADR 0007).
    op.drop_constraint(op.f("ck_loan_loan_status"), "loan", type_="check")
    op.create_check_constraint(op.f("ck_loan_loan_status"), "loan", in_values("status", statuses))
    op.drop_constraint(op.f("excl_loan_tool_dates"), "loan")
    op.create_exclude_constraint(
        op.f("excl_loan_tool_dates"),
        "loan",
        (sa.column("tool_id"), "="),
        (sa.literal_column("daterange(start_date, end_date, '[]')"), "&&"),
        where=sa.text(in_values("status", committed)),
        using="gist",
    )


def upgrade():
    with op.batch_alter_table("loan", schema=None) as batch_op:
        batch_op.add_column(sa.Column("lent_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True))

    replace_constraints(NEW_STATUSES, NEW_COMMITTED)


def downgrade():
    # Each claim goes back to the step before it, which the old code knows.
    op.execute("UPDATE loan SET status = 'accepted' WHERE status = 'handover_claimed'")
    op.execute("UPDATE loan SET status = 'lent' WHERE status = 'return_claimed'")
    replace_constraints(OLD_STATUSES, OLD_COMMITTED)

    with op.batch_alter_table("loan", schema=None) as batch_op:
        batch_op.drop_column("returned_at")
        batch_op.drop_column("lent_at")
