-- Complete Database Redesign: Audit Tables
-- Separate from version history to track all changes

-- =====================================================
-- AUDIT TABLES
-- =====================================================

-- Universal audit log for all database changes
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    changed_fields JSONB,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Phase transition audit
CREATE TABLE phase_transition_audit (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    from_phase VARCHAR(50),
    to_phase VARCHAR(50),
    transition_reason TEXT,
    transitioned_by INTEGER REFERENCES users(id),
    transitioned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Approval audit trail
CREATE TABLE approval_audit (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- APPROVED, REJECTED, RECALLED
    comments TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data access audit for sensitive data
CREATE TABLE data_access_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    access_type VARCHAR(20), -- VIEW, EXPORT, MODIFY
    data_classification security_classification_enum,
    query_text TEXT,
    row_count INTEGER,
    access_granted BOOLEAN,
    denial_reason TEXT,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

-- User activity audit
CREATE TABLE user_activity_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    activity_type VARCHAR(50), -- LOGIN, LOGOUT, PASSWORD_CHANGE, ROLE_CHANGE
    activity_details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    failure_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- SLA violation audit
CREATE TABLE sla_violation_audit (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER REFERENCES cycle_reports(id),
    phase VARCHAR(50),
    expected_completion DATE,
    actual_completion DATE,
    violation_days INTEGER,
    escalation_level INTEGER,
    notified_users INTEGER[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- WORKFLOW AND NOTIFICATION TABLES
-- =====================================================

-- Workflow configuration
CREATE TABLE workflow_configuration (
    id SERIAL PRIMARY KEY,
    phase_name VARCHAR(50) NOT NULL,
    phase_order INTEGER NOT NULL,
    required_role user_role_enum,
    approval_required BOOLEAN DEFAULT false,
    approver_role user_role_enum,
    sla_days INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Email notifications
CREATE TABLE email_notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INTEGER REFERENCES users(id),
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    notification_type VARCHAR(50), -- ASSIGNMENT, APPROVAL_REQUEST, SLA_WARNING, etc.
    related_table VARCHAR(100),
    related_id INTEGER,
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    email_notifications BOOLEAN DEFAULT true,
    sla_warnings BOOLEAN DEFAULT true,
    daily_digest BOOLEAN DEFAULT false,
    notification_frequency VARCHAR(20) DEFAULT 'immediate', -- immediate, hourly, daily
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- REFERENCE DATA TABLES
-- =====================================================

-- Regulatory requirements reference
CREATE TABLE regulatory_requirements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    effective_date DATE,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Report regulatory mapping
CREATE TABLE report_regulatory_mapping (
    report_id INTEGER NOT NULL REFERENCES report_inventory(id),
    requirement_id INTEGER NOT NULL REFERENCES regulatory_requirements(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (report_id, requirement_id)
);

-- Test templates
CREATE TABLE test_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50), -- Completeness, Accuracy, Validity, etc.
    test_query TEXT,
    expected_result_pattern TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- =====================================================
-- PERFORMANCE AND MONITORING TABLES
-- =====================================================

-- System performance metrics
CREATE TABLE system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_type VARCHAR(50), -- QUERY_TIME, PAGE_LOAD, API_RESPONSE
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(20), -- seconds, milliseconds, count
    context_data JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Error logs
CREATE TABLE error_logs (
    id BIGSERIAL PRIMARY KEY,
    error_type VARCHAR(50),
    error_message TEXT,
    stack_trace TEXT,
    user_id INTEGER REFERENCES users(id),
    request_url TEXT,
    request_method VARCHAR(10),
    request_body TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit tables
CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
CREATE INDEX idx_data_access_audit_user ON data_access_audit(user_id);
CREATE INDEX idx_data_access_audit_classification ON data_access_audit(data_classification);
CREATE INDEX idx_user_activity_audit_user ON user_activity_audit(user_id);
CREATE INDEX idx_user_activity_audit_type ON user_activity_audit(activity_type);
CREATE INDEX idx_email_notifications_recipient ON email_notifications(recipient_id);
CREATE INDEX idx_email_notifications_type ON email_notifications(notification_type);
CREATE INDEX idx_error_logs_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_occurred ON error_logs(occurred_at);

-- Comments
COMMENT ON TABLE audit_log IS 'Universal audit trail for all database changes';
COMMENT ON TABLE data_access_audit IS 'Track access to sensitive data for compliance';
COMMENT ON TABLE phase_transition_audit IS 'Track workflow phase transitions';
COMMENT ON TABLE email_notifications IS 'Email notification queue and history';