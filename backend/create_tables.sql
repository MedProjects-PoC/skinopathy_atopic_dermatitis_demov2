-- Skinopathy AD Demo Database Schema
-- 6 tables: users, sessions, questionnaires, ai_results, reports, alerts

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Table 2: sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    image_path VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_user_created ON sessions(user_id, created_at);

-- Table 3: questionnaires (12 AD questions)
CREATE TABLE IF NOT EXISTS questionnaires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE NOT NULL REFERENCES sessions(id),

    -- DDx Questions (7)
    itch_intensity INTEGER,
    chronic_relapsing BOOLEAN,
    atopic_triad_history BOOLEAN,
    primary_location VARCHAR(50),
    household_itchy_or_nighttime_worse BOOLEAN,
    new_exposure_trigger BOOLEAN,
    thick_silvery_scales BOOLEAN,

    -- Clinical Data (3)
    nights_sleep_disturbed INTEGER,
    oozing_honey_crusts BOOLEAN,
    steroid_use_last_2weeks BOOLEAN,

    -- Management & Lifestyle (2)
    moisturizer_frequency VARCHAR(20),
    recent_stress_level INTEGER
);

-- Table 4: ai_results
CREATE TABLE IF NOT EXISTS ai_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE NOT NULL REFERENCES sessions(id),

    -- AD assessment metrics
    severity_score FLOAT,
    affected_area_pct FLOAT,
    inflammation_score FLOAT,
    dryness_score FLOAT,
    lichenification_score FLOAT,
    excoriation_detected BOOLEAN,
    flare_status VARCHAR(20),
    body_regions JSONB,
    saliency_map_path VARCHAR(500),
    cnn_confidence FLOAT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    report_type VARCHAR(10) NOT NULL,
    content JSONB,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table 6: alerts
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    alert_type VARCHAR(50),
    severity VARCHAR(10),
    message TEXT,
    recommendations TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

-- Verify tables created
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
