"""Prêts : message de la demande

Revision ID: 13db5eeed32b
Revises: 9654b00a97c3
Create Date: 2026-11-01 11:32:48.864827

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "13db5eeed32b"
down_revision = "9654b00a97c3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("loan", schema=None) as batch_op:
        batch_op.add_column(sa.Column("message", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("loan", schema=None) as batch_op:
        batch_op.drop_column("message")
