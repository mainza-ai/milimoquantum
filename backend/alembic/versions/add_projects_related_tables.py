"""add projects and related tables

Revision ID: add_projects_related
Revises: ac1a8377a4d9
Create Date: 2026-03-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_projects_related'
down_revision: Union[str, Sequence[str], None] = 'ac1a8377a4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('conversation_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_tenant_id'), 'projects', ['tenant_id'], unique=False)

    # Create benchmark_results table
    op.create_table('benchmark_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('benchmark_name', sa.String(length=128), nullable=False),
        sa.Column('problem_size', sa.Integer(), nullable=False),
        sa.Column('backend', sa.String(length=64), nullable=False),
        sa.Column('shots', sa.Integer(), nullable=True),
        sa.Column('preparation_time', sa.Float(), nullable=True),
        sa.Column('quantum_exec_time', sa.Float(), nullable=True),
        sa.Column('classical_sim_time', sa.Float(), nullable=True),
        sa.Column('classification', sa.String(length=32), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('result_summary', sa.String(length=128), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create marketplace_plugins table
    op.create_table('marketplace_plugins',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('author', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=32), nullable=True),
        sa.Column('downloads', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_plugins table
    op.create_table('user_plugins',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('plugin_id', sa.String(length=64), nullable=False),
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['marketplace_plugins.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add project_id column to conversations (for foreign key in next migration)
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))

    # Add project_id column to experiments (for foreign key in next migration)
    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.drop_column('project_id')

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_column('project_id')

    op.drop_table('user_plugins')
    op.drop_table('marketplace_plugins')
    op.drop_table('benchmark_results')
    op.drop_index(op.f('ix_projects_tenant_id'), table_name='projects')
    op.drop_table('projects')
