"""Add index on reports.recurrent

Revision ID: 1ba1b62367d4
Revises: 2f1dcf6b94a9
Create Date: 2014-09-12 13:16:20.754399

"""

# revision identifiers, used by Alembic.
revision = '1ba1b62367d4'
down_revision = '2f1dcf6b94a9'

from alembic import op


def upgrade():
    op.create_index(
        'ix_report_recurrent',
        'report',
        ['recurrent']
    )


def downgrade():
    op.drop_index('ix_report_recurrent', 'report')
