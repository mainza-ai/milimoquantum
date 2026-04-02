"""add project_id to audit and FK constraints to existing columns

Revision ID: bc4da2a3b28a
Revises: add_projects_related
Create Date: 2026-03-13 14:04:05.838803

Note: The project_id columns on conversations, experiments, and benchmark_results
are already created by the add_projects_related migration. This migration only
adds the FK constraints to those existing columns, plus the audit_logs column+FK.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc4da2a3b28a'
down_revision: Union[str, Sequence[str], None] = 'add_projects_related'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # audit_logs: needs both column AND FK (not touched by previous migration)
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_audit_logs_project_id_projects', 'projects', ['project_id'], ['id'])

    # conversations, experiments, benchmark_results: column already exists,
    # only add FK constraints
    with op.batch_alter_table('benchmark_results', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_benchmark_results_project_id_projects', 'projects', ['project_id'], ['id'])

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_conversations_project_id_projects', 'projects', ['project_id'], ['id'])

    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_experiments_project_id_projects', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_experiments_project_id_projects', type_='foreignkey')

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_conversations_project_id_projects', type_='foreignkey')

    with op.batch_alter_table('benchmark_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_benchmark_results_project_id_projects', type_='foreignkey')

    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_audit_logs_project_id_projects', type_='foreignkey')
        batch_op.drop_column('project_id')
