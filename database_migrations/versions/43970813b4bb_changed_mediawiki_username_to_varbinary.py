"""Changed mediawiki_username to VARBINARY

Revision ID: 43970813b4bb
Revises: 1a5740750a28
Create Date: 2014-04-25 10:27:08.597354

"""

# revision identifiers, used by Alembic.
revision = '43970813b4bb'
down_revision = '1a5740750a28'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import VARBINARY
from sqlalchemy import Column, Integer, String, Boolean


def upgrade():
    op.alter_column('wiki_user', 'mediawiki_username', type_=VARBINARY(255),
                    existing_type=String(255), existing_nullable=True)
    ## end Alembic commands ###


def downgrade():
    op.alter_column('wiki_user', 'mediawiki_username', type_=String(255),
                    existing_type=VARBINARY(255), existing_nullable=True)
    ### end Alembic commands ###
