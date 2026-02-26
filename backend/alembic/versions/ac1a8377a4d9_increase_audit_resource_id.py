"""increase_audit_resource_id

Revision ID: ac1a8377a4d9
Revises: 6174b387852f
Create Date: 2026-02-26 20:37:42.852658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac1a8377a4d9'
down_revision: Union[str, Sequence[str], None] = '6174b387852f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('audit_logs', 'resource_id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=128),
               existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('audit_logs', 'resource_id',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=36),
               existing_nullable=True)
