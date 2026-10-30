"""Initial schema migration: 18 tables, PostGIS extensions, and indexes.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-30 14:55:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from app.core.database import Base
import app.models  # Ensure all SQLAlchemy models are registered

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable PostgreSQL Extensions
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "postgis";'))

    # 2. Create all tables defined in SQLAlchemy Base.metadata
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
