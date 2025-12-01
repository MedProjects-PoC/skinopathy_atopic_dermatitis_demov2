"""
Reset database - drops all tables and recreates them
WARNING: This will delete all data!
"""
from app.models.database import Base, engine
from loguru import logger

if __name__ == "__main__":
    logger.warning("Dropping all database tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.success("All tables dropped!")

        logger.info("Creating new database tables...")
        Base.metadata.create_all(bind=engine)
        logger.success("Database tables created successfully with new 12-question schema!")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise
