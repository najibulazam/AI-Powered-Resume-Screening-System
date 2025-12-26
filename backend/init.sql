-- Initialize database schema for resume screening system

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Screening results table
CREATE TABLE IF NOT EXISTS screening_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    decision VARCHAR(20) NOT NULL CHECK (decision IN ('HIRE', 'MAYBE', 'REJECT')),
    overall_score DECIMAL(5,2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    
    -- Skills
    matched_skills TEXT[] DEFAULT '{}',
    missing_skills TEXT[] DEFAULT '{}',
    
    -- Metadata
    human_review_required BOOLEAN DEFAULT false,
    review_priority VARCHAR(20) CHECK (review_priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    -- Cost tracking
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
    
    -- Performance metrics
    processing_time_ms INTEGER NOT NULL,
    
    -- Feedback (optional)
    feedback TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    CONSTRAINT valid_score CHECK (overall_score >= 0 AND overall_score <= 100)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_screening_decision ON screening_results(decision);
CREATE INDEX IF NOT EXISTS idx_screening_score ON screening_results(overall_score);
CREATE INDEX IF NOT EXISTS idx_screening_created_at ON screening_results(created_at);
CREATE INDEX IF NOT EXISTS idx_screening_job_title ON screening_results(job_title);
CREATE INDEX IF NOT EXISTS idx_screening_human_review ON screening_results(human_review_required);

-- GIN index for array columns (skill searches)
CREATE INDEX IF NOT EXISTS idx_screening_matched_skills ON screening_results USING GIN(matched_skills);
CREATE INDEX IF NOT EXISTS idx_screening_missing_skills ON screening_results USING GIN(missing_skills);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_screening_results_updated_at 
    BEFORE UPDATE ON screening_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for analytics dashboard
CREATE OR REPLACE VIEW analytics_dashboard AS
SELECT 
    COUNT(*) as total_screenings,
    COUNT(*) FILTER (WHERE decision = 'HIRE') as hire_count,
    COUNT(*) FILTER (WHERE decision = 'MAYBE') as maybe_count,
    COUNT(*) FILTER (WHERE decision = 'REJECT') as reject_count,
    ROUND(AVG(overall_score), 2) as avg_score,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY overall_score), 2) as median_score,
    COUNT(*) FILTER (WHERE human_review_required = true) as human_review_count,
    SUM(cost_usd) as total_cost,
    ROUND(AVG(cost_usd), 6) as avg_cost_per_candidate,
    ROUND(AVG(processing_time_ms), 0) as avg_processing_time_ms,
    DATE_TRUNC('day', CURRENT_TIMESTAMP) as calculated_at
FROM screening_results;

-- Skill gap analysis view
CREATE OR REPLACE VIEW skill_gap_analysis AS
SELECT 
    skill,
    COUNT(*) as gap_frequency,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM screening_results), 2) as gap_percent,
    COUNT(*) FILTER (WHERE decision = 'HIRE') as hire_with_gap,
    COUNT(*) FILTER (WHERE decision = 'REJECT') as reject_with_gap
FROM screening_results, UNNEST(missing_skills) as skill
GROUP BY skill
ORDER BY gap_frequency DESC;

-- Grant permissions (adjust username as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO resume_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO resume_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO resume_user;
