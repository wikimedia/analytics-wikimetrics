"""change report parameters to varbinary
Revision ID: 6f1b895840a
Revises: 1d86908ac3bc
Create Date: 2015-06-16 09:58:57.874087
"""

# revision identifiers, used by Alembic.
revision = '6f1b895840a'
down_revision = '1d86908ac3bc'


from alembic import op
from sqlalchemy.dialects.mysql import VARBINARY
from sqlalchemy import String


def upgrade():
    op.alter_column('report', 'parameters', type_=VARBINARY(4000),
                    existing_type=String(4000, collation='utf8_general_ci'),
                    existing_nullable=True)


def downgrade():
    op.alter_column('report', 'parameters',
                    type_=String(4000, collation='utf8_general_ci'),
                    existing_type=VARBINARY(4000), existing_nullable=True)
