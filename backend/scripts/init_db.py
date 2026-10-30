"""Database Schema Initializer.

Creates required PostgreSQL extensions (uuid-ossp, pgcrypto, postgis)
and initializes all tables defined in SQLAlchemy models.
"""

import asyncio
import logging
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine, Base
import app.models  # Load all models into Base.metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")


async def init_database():
    logger.info("Connecting to database at %s...", engine.url)
    try:
        async with engine.begin() as conn:
            logger.info("Enabling PostgreSQL extensions (uuid-ossp, pgcrypto, postgis)...")
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "postgis";'))
            
            logger.info("Creating all tables from SQLAlchemy metadata...")
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Configuring tenant RLS parameter default...")
            try:
                await conn.execute(text('ALTER DATABASE zuigo_attendance SET "app.current_tenant_id" TO "";'))
            except Exception as e:
                logger.warning("Could not set database level RLS variable (non-critical in dev): %s", e)

        logger.info("✅ Database initialization successfully completed!")
        logger.info("Tables created: %s", ", ".join(Base.metadata.tables.keys()))
    except Exception as e:
        logger.error("❌ Failed to initialize database: %s", e)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())
