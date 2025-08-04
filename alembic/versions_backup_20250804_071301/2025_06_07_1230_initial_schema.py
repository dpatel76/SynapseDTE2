"""Initial database schema

Revision ID: 2025_06_07_1230_initial_schema
Revises: 
Create Date: 2025-06-07 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2025_06_07_1230_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables and relationships using SQLAlchemy metadata"""
    
    # Import all models to register them with metadata
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # Import core modules
    from app.core.database import Base
    from alembic import context
    
    # Import all model modules explicitly to register with metadata
    import app.models.base
    import app.models.lob
    import app.models.user
    import app.models.rbac
    import app.models.rbac_resource
    import app.models.report
    import app.models.test_cycle
    import app.models.cycle_report
    import app.models.workflow
    import app.models.document
    import app.models.report_attribute
    import app.models.scoping
    import app.models.data_owner
    import app.models.sample_selection
    import app.models.testing
    import app.models.audit
    import app.models.sla
    import app.models.request_info
    import app.models.testing_execution
    import app.models.observation_management
    
    # Get the connection from the current context
    connection = context.get_bind()
    
    # Use SQLAlchemy to create all tables
    Base.metadata.create_all(bind=connection)


def downgrade() -> None:
    """Drop all tables"""
    
    # Import models
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from app.core.database import Base
    from alembic import context
    
    # Import all model modules explicitly to register with metadata
    import app.models.base
    import app.models.lob
    import app.models.user
    import app.models.rbac
    import app.models.rbac_resource
    import app.models.report
    import app.models.test_cycle
    import app.models.cycle_report
    import app.models.workflow
    import app.models.document
    import app.models.report_attribute
    import app.models.scoping
    import app.models.data_owner
    import app.models.sample_selection
    import app.models.testing
    import app.models.audit
    import app.models.sla
    import app.models.request_info
    import app.models.testing_execution
    import app.models.observation_management
    
    # Get the connection from the current context
    connection = context.get_bind()
    
    # Drop all tables
    Base.metadata.drop_all(bind=connection) 