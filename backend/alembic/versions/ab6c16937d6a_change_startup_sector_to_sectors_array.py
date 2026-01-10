"""change_startup_sector_to_sectors_array

Revision ID: ab6c16937d6a
Revises: 8b3d5f9e2a4c
Create Date: 2026-01-10 00:55:28.396972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab6c16937d6a'
down_revision: Union[str, None] = '8b3d5f9e2a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new sectors column (ARRAY type)
    op.add_column('startups', sa.Column('sectors', sa.ARRAY(sa.String()), nullable=True))

    # Migrate existing sector data to sectors array
    # For SQLite, we need to handle this differently since it doesn't support ARRAY
    connection = op.get_bind()
    if connection.dialect.name == 'sqlite':
        # For SQLite, store as JSON string
        connection.execute(
            sa.text("UPDATE startups SET sectors = '[\"' || sector || '\"]' WHERE sector IS NOT NULL AND sector != ''")
        )
    else:
        # For PostgreSQL
        connection.execute(
            sa.text("UPDATE startups SET sectors = ARRAY[sector] WHERE sector IS NOT NULL AND sector != ''")
        )

    # Drop the old sector column
    op.drop_column('startups', 'sector')


def downgrade() -> None:
    # Add back the sector column
    op.add_column('startups', sa.Column('sector', sa.String(100), nullable=True))

    # Migrate sectors array back to single sector (take first one)
    connection = op.get_bind()
    if connection.dialect.name == 'sqlite':
        # For SQLite
        connection.execute(
            sa.text("UPDATE startups SET sector = json_extract(sectors, '$[0]') WHERE sectors IS NOT NULL")
        )
    else:
        # For PostgreSQL
        connection.execute(
            sa.text("UPDATE startups SET sector = sectors[1] WHERE sectors IS NOT NULL AND array_length(sectors, 1) > 0")
        )

    # Drop the sectors column
    op.drop_column('startups', 'sectors')
