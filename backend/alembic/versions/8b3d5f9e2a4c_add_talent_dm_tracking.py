"""add talent dm tracking fields

Revision ID: 8b3d5f9e2a4c
Revises: 6a27a7dcb943
Create Date: 2026-01-09 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b3d5f9e2a4c'
down_revision: Union[str, None] = '6a27a7dcb943'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add talent DM tracking fields to founder_profiles
    op.add_column('founder_profiles', sa.Column('talent_dms_this_month', sa.Integer(), nullable=True, default=0))
    op.add_column('founder_profiles', sa.Column('talent_dms_reset_month', sa.Integer(), nullable=True))
    op.add_column('founder_profiles', sa.Column('talent_dms_reset_year', sa.Integer(), nullable=True))

    # Add talent DM tracking fields to investor_profiles
    op.add_column('investor_profiles', sa.Column('talent_dms_this_month', sa.Integer(), nullable=True, default=0))
    op.add_column('investor_profiles', sa.Column('talent_dms_reset_month', sa.Integer(), nullable=True))
    op.add_column('investor_profiles', sa.Column('talent_dms_reset_year', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns from founder_profiles
    op.drop_column('founder_profiles', 'talent_dms_this_month')
    op.drop_column('founder_profiles', 'talent_dms_reset_month')
    op.drop_column('founder_profiles', 'talent_dms_reset_year')

    # Remove columns from investor_profiles
    op.drop_column('investor_profiles', 'talent_dms_this_month')
    op.drop_column('investor_profiles', 'talent_dms_reset_month')
    op.drop_column('investor_profiles', 'talent_dms_reset_year')
