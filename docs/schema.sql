-- ─────────────────────────────────────────────────────────────────────────────
-- CareerGuide India — Complete Supabase PostgreSQL Schema
-- Run this in your Supabase SQL Editor (Project → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis"; -- optional: for geo queries

-- ─── ENUM types ───────────────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('student', 'parent', 'counselor', 'admin');
CREATE TYPE notif_channel AS ENUM ('email', 'sms', 'whatsapp', 'inapp');
CREATE TYPE college_type AS ENUM ('government', 'private', 'aided', 'autonomous');
CREATE TYPE admission_status AS ENUM ('shortlisted', 'applied', 'admitted', 'rejected');

-- ─── Users ───────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    supabase_uid    UUID UNIQUE,
    email           TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    role            user_role NOT NULL DEFAULT 'student',
    phone           TEXT,
    preferred_language TEXT DEFAULT 'en',
    password_hash   TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    avatar_url      TEXT,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Students ────────────────────────────────────────────────────────────────
CREATE TABLE students (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    student_class           SMALLINT CHECK (student_class IN (10, 12)),
    board                   TEXT,
    school_name             TEXT,
    school_type             TEXT DEFAULT 'government',
    marks                   JSONB DEFAULT '{}',
    aggregate_percentage    NUMERIC(5,2),
    district                TEXT,
    state                   TEXT,
    pincode                 TEXT,
    latitude                NUMERIC(9,6),
    longitude               NUMERIC(9,6),
    travel_radius_km        NUMERIC(6,2) DEFAULT 50,
    preferred_language      TEXT DEFAULT 'en',
    stream_preference       TEXT,
    interests               JSONB DEFAULT '[]',
    career_goals            JSONB DEFAULT '[]',
    annual_family_income    NUMERIC(12,2),
    budget_for_education    NUMERIC(12,2),
    needs_hostel            BOOLEAN DEFAULT FALSE,
    needs_scholarship       BOOLEAN DEFAULT FALSE,
    onboarding_complete     BOOLEAN DEFAULT FALSE,
    quiz_complete           BOOLEAN DEFAULT FALSE,
    profile_score           NUMERIC(4,2) DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Parents ─────────────────────────────────────────────────────────────────
CREATE TABLE parents (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    linked_student_id   BIGINT REFERENCES students(id) ON DELETE SET NULL,
    occupation          TEXT,
    annual_income       NUMERIC(12,2),
    education_level     TEXT,
    preferred_language  TEXT DEFAULT 'en',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Quiz Attempts ────────────────────────────────────────────────────────────
CREATE TABLE quiz_attempts (
    id                  BIGSERIAL PRIMARY KEY,
    student_id          BIGINT REFERENCES students(id) ON DELETE CASCADE,
    responses           JSONB DEFAULT '[]',
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    time_taken_seconds  INTEGER,
    is_complete         BOOLEAN DEFAULT FALSE
);

-- ─── Aptitude Scores ─────────────────────────────────────────────────────────
CREATE TABLE aptitude_scores (
    id                  BIGSERIAL PRIMARY KEY,
    student_id          BIGINT UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    quiz_attempt_id     BIGINT REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    logical             NUMERIC(5,2) DEFAULT 0,
    verbal              NUMERIC(5,2) DEFAULT 0,
    quantitative        NUMERIC(5,2) DEFAULT 0,
    social              NUMERIC(5,2) DEFAULT 0,
    creative            NUMERIC(5,2) DEFAULT 0,
    technical           NUMERIC(5,2) DEFAULT 0,
    composite           NUMERIC(5,2) DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Colleges ─────────────────────────────────────────────────────────────────
CREATE TABLE colleges (
    id                      BIGSERIAL PRIMARY KEY,
    name                    TEXT NOT NULL,
    slug                    TEXT UNIQUE NOT NULL,
    college_type            college_type DEFAULT 'government',
    accreditation           TEXT,
    district                TEXT NOT NULL,
    state                   TEXT NOT NULL,
    pincode                 TEXT,
    address                 TEXT,
    latitude                NUMERIC(9,6),
    longitude               NUMERIC(9,6),
    google_place_id         TEXT,
    courses_offered         JSONB DEFAULT '[]',
    cutoff_data             JSONB DEFAULT '{}',
    annual_fees_min         NUMERIC(10,2),
    annual_fees_max         NUMERIC(10,2),
    has_hostel              BOOLEAN DEFAULT FALSE,
    has_transport           BOOLEAN DEFAULT FALSE,
    medium_of_instruction   JSONB DEFAULT '[]',
    website                 TEXT,
    phone                   TEXT,
    email                   TEXT,
    established_year        SMALLINT,
    total_seats             INTEGER,
    image_url               TEXT,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Scholarships ────────────────────────────────────────────────────────────
CREATE TABLE scholarships (
    id                      BIGSERIAL PRIMARY KEY,
    name                    TEXT NOT NULL,
    provider                TEXT NOT NULL,
    scheme_type             TEXT,
    eligibility_criteria    JSONB DEFAULT '{}',
    amount                  NUMERIC(12,2),
    amount_description      TEXT,
    deadline                TIMESTAMPTZ,
    application_link        TEXT,
    description             TEXT,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Recommendations ─────────────────────────────────────────────────────────
CREATE TABLE recommendations (
    id                      BIGSERIAL PRIMARY KEY,
    student_id              BIGINT REFERENCES students(id) ON DELETE CASCADE,
    recommended_stream      TEXT,
    stream_confidence       NUMERIC(5,4),
    top_courses             JSONB DEFAULT '[]',
    career_clusters         JSONB DEFAULT '[]',
    explanations            JSONB DEFAULT '{}',
    scholarship_matches     JSONB DEFAULT '[]',
    model_version           TEXT DEFAULT 'v1',
    viewed_at               TIMESTAMPTZ,
    shortlisted_courses     JSONB DEFAULT '[]',
    rejected_courses        JSONB DEFAULT '[]',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Model Feedback ──────────────────────────────────────────────────────────
CREATE TABLE model_feedback (
    id                      BIGSERIAL PRIMARY KEY,
    recommendation_id       BIGINT REFERENCES recommendations(id) ON DELETE CASCADE,
    student_id              BIGINT REFERENCES students(id) ON DELETE CASCADE,
    recommended_course      TEXT,
    accepted                BOOLEAN,
    actual_course_enrolled  TEXT,
    actual_college          TEXT,
    outcome_satisfied       BOOLEAN,
    outcome_notes           TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Counselor Feedback ──────────────────────────────────────────────────────
CREATE TABLE counselor_feedback (
    id                  BIGSERIAL PRIMARY KEY,
    student_id          BIGINT REFERENCES students(id) ON DELETE CASCADE,
    counselor_id        BIGINT REFERENCES users(id),
    recommendation_id   BIGINT REFERENCES recommendations(id),
    notes               TEXT NOT NULL,
    override_stream     TEXT,
    reviewed_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Admission Events ────────────────────────────────────────────────────────
CREATE TABLE admission_events (
    id                      BIGSERIAL PRIMARY KEY,
    student_id              BIGINT REFERENCES students(id) ON DELETE CASCADE,
    college_id              BIGINT REFERENCES colleges(id),
    course_name             TEXT,
    status                  admission_status DEFAULT 'shortlisted',
    applied_at              TIMESTAMPTZ,
    admission_confirmed_at  TIMESTAMPTZ,
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Notifications ───────────────────────────────────────────────────────────
CREATE TABLE notifications (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT REFERENCES users(id) ON DELETE CASCADE,
    channel             notif_channel NOT NULL,
    notification_type   TEXT,
    title               TEXT NOT NULL,
    body                TEXT,
    payload             JSONB DEFAULT '{}',
    is_read             BOOLEAN DEFAULT FALSE,
    sent_at             TIMESTAMPTZ,
    status              TEXT DEFAULT 'pending',
    error_message       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Districts ───────────────────────────────────────────────────────────────
CREATE TABLE districts (
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    state   TEXT NOT NULL,
    UNIQUE(name, state)
);

-- ─── Languages ───────────────────────────────────────────────────────────────
CREATE TABLE languages (
    id      SERIAL PRIMARY KEY,
    code    TEXT UNIQUE NOT NULL,  -- 'en', 'ta', 'hi'
    label   TEXT NOT NULL          -- 'English', 'தமிழ்', 'हिंदी'
);

INSERT INTO languages (code, label) VALUES ('en', 'English'), ('ta', 'தமிழ்'), ('hi', 'हिंदी');

-- ─── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_students_district ON students(district, state);
CREATE INDEX idx_students_onboarding ON students(onboarding_complete, quiz_complete);
CREATE INDEX idx_colleges_district ON colleges(district, state);
CREATE INDEX idx_colleges_geo ON colleges(latitude, longitude) WHERE latitude IS NOT NULL;
CREATE INDEX idx_recommendations_student ON recommendations(student_id, created_at DESC);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, channel);
CREATE INDEX idx_model_feedback_rec ON model_feedback(recommendation_id);

-- ─── Updated_at triggers ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_students_updated BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_colleges_updated BEFORE UPDATE ON colleges FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY (RLS) STRATEGY
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Users: can only see/edit their own row
CREATE POLICY "users_own_row" ON users
    USING (supabase_uid = auth.uid());

-- Students: own row + counselors/admins can see all
CREATE POLICY "students_own_row" ON students
    USING (
        user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid())
        OR EXISTS (
            SELECT 1 FROM users u WHERE u.supabase_uid = auth.uid() AND u.role IN ('counselor', 'admin')
        )
    );

-- Recommendations: own student's data + counselors/admins
CREATE POLICY "recommendations_own" ON recommendations
    USING (
        student_id IN (SELECT id FROM students WHERE user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()))
        OR EXISTS (SELECT 1 FROM users u WHERE u.supabase_uid = auth.uid() AND u.role IN ('counselor', 'admin'))
    );

-- Notifications: only own notifications
CREATE POLICY "notifications_own" ON notifications
    USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));

-- Colleges and scholarships are publicly readable
ALTER TABLE colleges ENABLE ROW LEVEL SECURITY;
CREATE POLICY "colleges_public_read" ON colleges FOR SELECT USING (is_active = TRUE);
ALTER TABLE scholarships ENABLE ROW LEVEL SECURITY;
CREATE POLICY "scholarships_public_read" ON scholarships FOR SELECT USING (is_active = TRUE);
