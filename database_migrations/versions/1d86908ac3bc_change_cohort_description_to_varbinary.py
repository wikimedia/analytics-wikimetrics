"""change cohort description to varbinary
Revision ID: 1d86908ac3bc
Revises: 35adbe20f3d
Create Date: 2015-06-01 15:01:16.939794
"""

# revision identifiers, used by Alembic.
revision = '1d86908ac3bc'
down_revision = '35adbe20f3d'


from alembic import op
from sqlalchemy.dialects.mysql import VARBINARY
from sqlalchemy import String


def upgrade():
    op.alter_column('cohort', 'description', type_=VARBINARY(254),
                    existing_type=String(254), existing_nullable=True)


def downgrade():
    op.alter_column('cohort', 'description', type_=String(254),
                    existing_type=VARBINARY(254), existing_nullable=True)
