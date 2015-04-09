"""add task_error table

Revision ID: 4a2162ae3e84
Revises: 483df9b9a389
Create Date: 2015-04-08 18:59:24.222047

"""

# revision identifiers, used by Alembic.
revision = '4a2162ae3e84'
down_revision = '483df9b9a389'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_table(
        'task_error',
        sa.Column('task_type', sa.String(length=50), nullable=False,
                  primary_key=True, autoincrement=False),
        sa.Column('task_id', sa.Integer(), nullable=False,
                  primary_key=True, autoincrement=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('message', sa.String(length=100), nullable=False),
        sa.Column('traceback', sa.String(length=3000), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['report.id'])
    )


def downgrade():
    op.drop_table('task_error')
