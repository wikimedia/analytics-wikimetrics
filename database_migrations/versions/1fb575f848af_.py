"""
Added public field to the report table

Revision ID: 1fb575f848af
Revises: 492fe78451c6
Create Date: 2014-02-28 02:14:43.655893

"""

# revision identifiers, used by Alembic.
revision = '1fb575f848af'
down_revision = '492fe78451c6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('report', sa.Column('public', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('report', 'public')
    ### end Alembic commands ###
