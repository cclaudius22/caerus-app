"""add_profile_management_fields

Revision ID: c9f2d8a3e5b1
Revises: ab6c16937d6a
Create Date: 2026-01-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9f2d8a3e5b1'
down_revision: Union[str, None] = 'ab6c16937d6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_hidden column for hiding profile from feeds/search
    op.add_column('users', sa.Column('is_hidden', sa.Boolean(), nullable=True, server_default='false'))

    # Add scheduled_deletion_date for 30-day grace period deletion
    op.add_column('users', sa.Column('scheduled_deletion_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'scheduled_deletion_date')
    op.drop_column('users', 'is_hidden')
