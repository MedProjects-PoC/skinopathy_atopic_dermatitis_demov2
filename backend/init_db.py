"""
Initialize database tables
Run this script to create all database tables
"""
from app.models.database import Base, engine, init_db
from loguru import logger

if __name__ == "__main__":
    logger.info("Creating database tables...")
    try:
        init_db()
        logger.success("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
