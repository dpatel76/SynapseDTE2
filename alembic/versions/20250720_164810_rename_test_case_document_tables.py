"""rename test case document tables

Revision ID: 20250720_164810
Revises: 2025_07_20_phase_id_refactoring
Create Date: 2025-07-20 16:48:10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250720_164810'
down_revision = '2025_07_20_phase_id_refactoring'
branch_labels = None
depends_on = None


def upgrade():
    # Rename tables to be more descriptive
    op.rename_table('cycle_report_document_submissions', 'cycle_report_test_case_document_submissions')
    op.rename_table('document_revisions', 'cycle_report_test_case_document_revisions')
    op.rename_table('document_revision_history', 'cycle_report_test_case_document_revision_history')


def downgrade():
    # Rename tables back to original names
    op.rename_table('cycle_report_test_case_document_submissions', 'cycle_report_document_submissions')
    op.rename_table('cycle_report_test_case_document_revisions', 'document_revisions')
    op.rename_table('cycle_report_test_case_document_revision_history', 'document_revision_history')