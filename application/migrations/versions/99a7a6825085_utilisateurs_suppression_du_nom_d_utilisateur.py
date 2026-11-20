"""Utilisateurs : suppression du nom d'utilisateur

Revision ID: 99a7a6825085
Revises: 43880597035b
Create Date: 2026-11-20 17:09:19.295942

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "99a7a6825085"
down_revision = "43880597035b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_username", type_="unique")
        batch_op.drop_column("username")


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.VARCHAR(length=250), nullable=True))
    op.execute("UPDATE \"user\" SET username = 'user' || id")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_user_username", ["username"])
