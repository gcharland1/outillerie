"""Utilisateurs : suppression de la colonne du nom d'utilisateur

Revision ID: e7f59596b568
Revises: 916cc286d588
Create Date: 2026-11-21 17:02:21.988070

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7f59596b568"
down_revision = "916cc286d588"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_username", type_="unique")
        batch_op.drop_column("username")


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.VARCHAR(length=250), nullable=True))
    # The recreated column is empty: no former name can already hold user<id> (ADR 0020).
    op.execute("UPDATE \"user\" SET username = 'user' || id")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_user_username", ["username"])
