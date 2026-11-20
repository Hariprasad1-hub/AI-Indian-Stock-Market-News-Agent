"""add_price_status_and_message_status

Revision ID: 5137688f4f5c
Revises: 0253d4609e15
Create Date: 2026-11-20 09:19:27.489062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5137688f4f5c'
down_revision: Union[str, Sequence[str], None] = '0253d4609e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with server_defaults for SQLite compatibility."""
    op.add_column('agent_messages', sa.Column('status', sa.String(length=20), server_default='DELIVERED', nullable=False))
    op.add_column('agent_messages', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('stocks', sa.Column('price_status', sa.String(length=20), server_default='LIVE', nullable=False))
    op.add_column('stocks', sa.Column('price_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('trading_decisions', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trading_decisions', 'rejection_reason')
    op.drop_column('stocks', 'price_updated_at')
    op.drop_column('stocks', 'price_status')
    op.drop_column('agent_messages', 'error_message')
    op.drop_column('agent_messages', 'status')
