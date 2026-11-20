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
    # Accounts created since the upgrade have none; an old sign-up may already hold "user<id>".
    connection = op.get_bind()
    taken = set(
        connection.scalars(sa.text('SELECT username FROM "user" WHERE username IS NOT NULL'))
    )
    nameless = connection.scalars(
        sa.text('SELECT id FROM "user" WHERE username IS NULL ORDER BY id')
    )
    for user_id in nameless.all():
        username = f"user{user_id}"
        while username in taken:
            username += "_"
        taken.add(username)
        connection.execute(
            sa.text('UPDATE "user" SET username = :username WHERE id = :id'),
            {"username": username, "id": user_id},
        )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.VARCHAR(length=250), nullable=False)
