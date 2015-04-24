"""Add column raw_id_or_name to wiki_user

Revision ID: 35adbe20f3d
Revises: 4a2162ae3e84
Create Date: 2015-04-24 01:17:39.039813

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import VARBINARY

# revision identifiers, used by Alembic.
revision = '35adbe20f3d'
down_revision = '4a2162ae3e84'

update_wiki_user_sql = """
--Run this SQL on the wikimetrics database to populate the raw_id_or_name
--column correctly.

UPDATE wiki_user wu
INNER JOIN cohort c ON wu.validating_cohort = c.id
SET wu.raw_id_or_name =
    CASE
        WHEN wu.valid THEN if(c.validate_as_user_ids, wu.mediawiki_userid,
            wu.mediawiki_username)
        ELSE wu.mediawiki_username
    END;

--Uncomment and run this after making sure all the raw_id_or_name values are populated.

--UPDATE wiki_user
--SET mediawiki_username = NULL,
--    mediawiki_userid = NULL
--WHERE VALID = 0;
"""


def upgrade():
    op.add_column('wiki_user', sa.Column(
        'raw_id_or_name', VARBINARY(length=255), nullable=True))
    print update_wiki_user_sql


def downgrade():
    op.drop_column('wiki_user', 'raw_id_or_name')
