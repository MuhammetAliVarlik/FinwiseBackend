"""Initial database schema for stocks table.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2025-03-30

This migration creates the base schema for the Finwise Scribe platform,
starting with the stocks table for storing market data.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial schema with stocks table."""
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol'),
    )


def downgrade() -> None:
    """Drop the stocks table and indices."""
    op.drop_table('stocks')
