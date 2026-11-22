"""Utilisateurs : confirmation du courriel

Revision ID: 8af64a316b37
Revises: e7f59596b568
Create Date: 2026-11-22 10:41:17.947051

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8af64a316b37"
down_revision = "e7f59596b568"
branch_labels = None
depends_on = None


def upgrade():
    # No default: existing accounts stay unconfirmed.
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("email_confirmed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("email_confirmation_sent_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("email_confirmation_sent_at")
        batch_op.drop_column("email_confirmed_at")
