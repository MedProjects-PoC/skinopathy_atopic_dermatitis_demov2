"""
Initialize database tables for Skinopathy AD Demo
Run this script after deploying to create all required tables
"""
from app.models.database import init_db
from loguru import logger

if __name__ == "__main__":
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database tables created successfully!")
    logger.info("Tables: users, sessions, questionnaires, ai_results, reports, alerts")
