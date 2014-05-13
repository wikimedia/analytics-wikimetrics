"""Added tag and cohort_tag databases

Revision ID: 2f1dcf6b94a9
Revises: 865af32ca5e
Create Date: 2014-05-08 20:13:12.215671

"""

# revision identifiers, used by Alembic.
revision = '2f1dcf6b94a9'
down_revision = '865af32ca5e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import VARBINARY


def upgrade():
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', VARBINARY(50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'cohort_tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cohort_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohort.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint(
        'uix_tag',
        'tag',
        ['name']
    )


def downgrade():
    op.drop_index('uix_tag', 'tag')
    op.drop_table('cohort_tag')
    op.drop_table('tag')
