"""
Database models using SQLAlchemy ORM
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, TIMESTAMP, ForeignKey, ARRAY, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)
    role = Column(String(20))  # 'user' or 'hcp'
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class Session(Base):
    """Analysis session model"""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_path = Column(String(500))
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    questionnaire = relationship("Questionnaire", back_populates="session", uselist=False)
    ai_result = relationship("AIResult", back_populates="session", uselist=False)
    reports = relationship("Report", back_populates="session")

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )


class Questionnaire(Base):
    """AD-specific questionnaire - 12 clinically validated questions"""
    __tablename__ = "questionnaires"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), unique=True)

    # === DDx Questions (7) ===
    # Q1: Pruritus Baseline (DDx)
    itch_intensity = Column(Integer)  # 0-10 scale over last 3 days

    # Q2: Chronicity & Pattern (DDx)
    chronic_relapsing = Column(Boolean)  # >6 months, comes and goes in flare-ups

    # Q3: Atopic Triad (DDx/History)
    atopic_triad_history = Column(Boolean)  # Self or family history of asthma/hay fever/childhood eczema

    # Q4: Anatomical Distribution (DDx)
    primary_location = Column(String(50))  # 'flexural', 'extensor', 'scalp_hairline', 'webs_waistband'

    # Q5: Scabies Differentiator (DDx - Red Flag)
    household_itchy_or_nighttime_worse = Column(Boolean)  # Household involvement or nighttime itch

    # Q6: Contact vs Endogenous (DDx)
    new_exposure_trigger = Column(Boolean)  # Appeared after new soap/jewelry/detergent/outdoors

    # Q7: Psoriasis Differentiator (DDx)
    thick_silvery_scales = Column(Boolean)  # Clearly defined with thick silvery-white scale

    # === Clinical Data Capture (3) ===
    # Q8: Sleep Disruption (Data Capture)
    nights_sleep_disturbed = Column(Integer)  # 0-7 nights in last week

    # Q9: Infection Risk (Data Capture)
    oozing_honey_crusts = Column(Boolean)  # Oozing, weeping, or golden/honey-colored crusts

    # Q10: Treatment History (Data Capture)
    steroid_use_last_2weeks = Column(Boolean)  # Used hydrocortisone or other steroid creams

    # === My 2 Additions for AD Management ===
    # Q11: Treatment Adherence Tracking
    moisturizer_frequency = Column(String(20))  # 'none', 'once_daily', 'twice_daily', 'more'

    # Q12: Stress as AD Trigger
    recent_stress_level = Column(Integer)  # 0-10 scale

    # Relationship
    session = relationship("Session", back_populates="questionnaire")


class AIResult(Base):
    """AI analysis results (AD-specific)"""
    __tablename__ = "ai_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), unique=True)

    # AD assessment metrics
    severity_score = Column(Float)  # 0-100 EASI-like composite
    affected_area_pct = Column(Float)  # % of visible skin
    inflammation_score = Column(Float)  # 0-100 (erythema)
    dryness_score = Column(Float)  # 0-100 (xerosis/scaling)
    lichenification_score = Column(Float)  # 0-100 (thickening)
    excoriation_detected = Column(Boolean)  # Scratch marks
    flare_status = Column(String(20))  # 'active', 'pre_flare', 'improving', 'stable'
    body_regions = Column(JSON)  # Distribution map
    saliency_map_path = Column(String(500))
    cnn_confidence = Column(Float)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="ai_result")


class Report(Base):
    """Dual reports (user and HCP)"""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    report_type = Column(String(10))  # 'user' or 'hcp'
    content = Column(JSON)  # Structured report data
    generated_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="reports")


class Alert(Base):
    """Tracking alerts and warnings"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    alert_type = Column(String(50))  # 'pre_flare', 'improvement', etc.
    severity = Column(String(10))  # 'low', 'medium', 'high'
    message = Column(String)
    recommendations = Column(ARRAY(String), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="alerts")


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
