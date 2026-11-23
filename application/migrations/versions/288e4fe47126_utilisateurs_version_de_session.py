"""Utilisateurs : version de session

Revision ID: 288e4fe47126
Revises: 8af64a316b37
Create Date: 2026-11-22 19:38:10.831543

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "288e4fe47126"
down_revision = "8af64a316b37"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("session_version", sa.Integer(), server_default="0", nullable=False)
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("session_version")
