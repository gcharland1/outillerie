"""Utilisateurs : nom d'utilisateur facultatif

Revision ID: 43880597035b
Revises: a6a1140da310
Create Date: 2026-11-20 13:24:10.779538

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "43880597035b"
down_revision = "a6a1140da310"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.VARCHAR(length=250), nullable=True)


def downgrade():
    # Accounts created since the upgrade have none; 'user' || id cannot collide (ADR 0020).
    op.execute("UPDATE \"user\" SET username = 'user' || id WHERE username IS NULL")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.VARCHAR(length=250), nullable=False)
