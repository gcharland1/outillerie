"""Extensions de recherche floue : pg_trgm et unaccent

Revision ID: 9654b00a97c3
Revises: 72500f67d13d
Create Date: 2026-11-01 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9654b00a97c3"
down_revision = "72500f67d13d"
branch_labels = None
depends_on = None


def upgrade():
    # Hand-written: autogenerate does not see extensions (ADR 0007, ADR 0016).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade():
    # pg_trgm and unaccent are left installed, like btree_gist: other objects may depend on them.
    pass
