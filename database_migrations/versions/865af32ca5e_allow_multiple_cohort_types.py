"""Allow multiple Cohort types

Revision ID: 865af32ca5e
Revises: 43970813b4bb
Create Date: 2014-05-22 14:56:22.500504

"""

# revision identifiers, used by Alembic.
revision = '865af32ca5e'
down_revision = '43970813b4bb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('cohort', sa.Column(
        'class_name', sa.String(length=50), nullable=False, server_default='FixedCohort'
    ))


def downgrade():
    op.drop_column('cohort', 'class_name')
