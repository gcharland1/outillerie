"""Utilisateurs : suppression du compte

Revision ID: 916cc286d588
Revises: 43880597035b
Create Date: 2026-11-20 17:38:07.966349

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "916cc286d588"
down_revision = "43880597035b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.alter_column("email", existing_type=sa.VARCHAR(length=250), nullable=True)


def downgrade():
    op.execute("UPDATE \"user\" SET email = 'supprime-' || id || '@invalid' WHERE email IS NULL")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("email", existing_type=sa.VARCHAR(length=250), nullable=False)
        batch_op.drop_column("deleted_at")
