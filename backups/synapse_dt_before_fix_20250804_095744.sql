--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: activity_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.activity_status_enum AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'REVISION_REQUESTED',
    'BLOCKED',
    'SKIPPED'
);


ALTER TYPE public.activity_status_enum OWNER TO synapse_user;

--
-- Name: activity_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.activity_type_enum AS ENUM (
    'START',
    'TASK',
    'REVIEW',
    'APPROVAL',
    'COMPLETE',
    'CUSTOM'
);


ALTER TYPE public.activity_type_enum OWNER TO synapse_user;

--
-- Name: activitystatus; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.activitystatus AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'REVISION_REQUESTED',
    'BLOCKED',
    'SKIPPED'
);


ALTER TYPE public.activitystatus OWNER TO synapse_user;

--
-- Name: activitytype; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.activitytype AS ENUM (
    'START',
    'TASK',
    'REVIEW',
    'APPROVAL',
    'COMPLETE',
    'CUSTOM'
);


ALTER TYPE public.activitytype OWNER TO synapse_user;

--
-- Name: analysis_method_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.analysis_method_enum AS ENUM (
    'LLM Analysis',
    'Database Query',
    'Manual Review',
    'Automated Comparison'
);


ALTER TYPE public.analysis_method_enum OWNER TO synapse_user;

--
-- Name: approval_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.approval_status_enum AS ENUM (
    'Pending',
    'Approved',
    'Declined',
    'Needs Revision'
);


ALTER TYPE public.approval_status_enum OWNER TO synapse_user;

--
-- Name: assignment_priority_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.assignment_priority_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical'
);


ALTER TYPE public.assignment_priority_enum OWNER TO synapse_user;

--
-- Name: assignment_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.assignment_status_enum AS ENUM (
    'Assigned',
    'In Progress',
    'Completed',
    'Overdue'
);


ALTER TYPE public.assignment_status_enum OWNER TO synapse_user;

--
-- Name: assignment_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.assignment_type_enum AS ENUM (
    'Data Upload Request',
    'File Review',
    'Documentation Review',
    'Approval Required',
    'Information Request',
    'Phase Review'
);


ALTER TYPE public.assignment_type_enum OWNER TO synapse_user;

--
-- Name: cycle_report_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.cycle_report_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


ALTER TYPE public.cycle_report_status_enum OWNER TO synapse_user;

--
-- Name: data_source_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.data_source_type_enum AS ENUM (
    'Document',
    'Database'
);


ALTER TYPE public.data_source_type_enum OWNER TO synapse_user;

--
-- Name: data_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.data_type_enum AS ENUM (
    'String',
    'Integer',
    'Decimal',
    'Date',
    'DateTime',
    'Boolean',
    'JSON'
);


ALTER TYPE public.data_type_enum OWNER TO synapse_user;

--
-- Name: document_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.document_type_enum AS ENUM (
    'Source Document',
    'Supporting Evidence',
    'Data Extract',
    'Query Result',
    'Other'
);


ALTER TYPE public.document_type_enum OWNER TO synapse_user;

--
-- Name: escalation_level_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.escalation_level_enum AS ENUM (
    'None',
    'Level 1',
    'Level 2',
    'Level 3'
);


ALTER TYPE public.escalation_level_enum OWNER TO synapse_user;

--
-- Name: escalationlevel; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.escalationlevel AS ENUM (
    'LEVEL_1',
    'LEVEL_2',
    'LEVEL_3',
    'LEVEL_4'
);


ALTER TYPE public.escalationlevel OWNER TO synapse_user;

--
-- Name: impact_level_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.impact_level_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical'
);


ALTER TYPE public.impact_level_enum OWNER TO synapse_user;

--
-- Name: impactcategoryenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.impactcategoryenum AS ENUM (
    'FINANCIAL',
    'REGULATORY',
    'OPERATIONAL',
    'REPUTATIONAL',
    'STRATEGIC',
    'CUSTOMER'
);


ALTER TYPE public.impactcategoryenum OWNER TO synapse_user;

--
-- Name: mandatory_flag_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.mandatory_flag_enum AS ENUM (
    'Mandatory',
    'Conditional',
    'Optional'
);


ALTER TYPE public.mandatory_flag_enum OWNER TO synapse_user;

--
-- Name: observation_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observation_status_enum AS ENUM (
    'Open',
    'In Review',
    'Approved',
    'Rejected',
    'Resolved'
);


ALTER TYPE public.observation_status_enum OWNER TO synapse_user;

--
-- Name: observation_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observation_type_enum AS ENUM (
    'Data Quality',
    'Documentation'
);


ALTER TYPE public.observation_type_enum OWNER TO synapse_user;

--
-- Name: observationapprovalstatusenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observationapprovalstatusenum AS ENUM (
    'PENDING_REVIEW',
    'PENDING_REPORT_OWNER_APPROVAL',
    'PENDING_DATA_EXECUTIVE_APPROVAL',
    'APPROVED_BY_REPORT_OWNER',
    'APPROVED_BY_DATA_EXECUTIVE',
    'FULLY_APPROVED',
    'REJECTED_BY_REPORT_OWNER',
    'REJECTED_BY_DATA_EXECUTIVE',
    'NEEDS_CLARIFICATION',
    'FINALIZED'
);


ALTER TYPE public.observationapprovalstatusenum OWNER TO synapse_user;

--
-- Name: observationratingenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observationratingenum AS ENUM (
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE public.observationratingenum OWNER TO synapse_user;

--
-- Name: observationseverityenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observationseverityenum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW',
    'INFORMATIONAL'
);


ALTER TYPE public.observationseverityenum OWNER TO synapse_user;

--
-- Name: observationstatusenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observationstatusenum AS ENUM (
    'DETECTED',
    'UNDER_REVIEW',
    'CONFIRMED',
    'DISPUTED',
    'APPROVED',
    'REJECTED',
    'IN_REMEDIATION',
    'RESOLVED',
    'CLOSED'
);


ALTER TYPE public.observationstatusenum OWNER TO synapse_user;

--
-- Name: observationtypeenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.observationtypeenum AS ENUM (
    'DATA_QUALITY',
    'PROCESS_CONTROL',
    'REGULATORY_COMPLIANCE',
    'SYSTEM_CONTROL',
    'DOCUMENTATION',
    'CALCULATION_ERROR',
    'TIMING_ISSUE',
    'ACCESS_CONTROL'
);


ALTER TYPE public.observationtypeenum OWNER TO synapse_user;

--
-- Name: phase_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.phase_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Pending Approval',
    'Complete'
);


ALTER TYPE public.phase_status_enum OWNER TO synapse_user;

--
-- Name: profilingrulestatus; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.profilingrulestatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'draft',
    'under_review',
    'needs_revision',
    'resubmitted'
);


ALTER TYPE public.profilingrulestatus OWNER TO synapse_user;

--
-- Name: profilingruletype; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.profilingruletype AS ENUM (
    'COMPLETENESS',
    'VALIDITY',
    'ACCURACY',
    'CONSISTENCY',
    'UNIQUENESS',
    'TIMELINESS',
    'REGULATORY'
);


ALTER TYPE public.profilingruletype OWNER TO synapse_user;

--
-- Name: reportownerdecision; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.reportownerdecision AS ENUM (
    'APPROVED',
    'REJECTED',
    'REVISION_REQUIRED'
);


ALTER TYPE public.reportownerdecision OWNER TO synapse_user;

--
-- Name: request_info_phase_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.request_info_phase_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


ALTER TYPE public.request_info_phase_status_enum OWNER TO synapse_user;

--
-- Name: resolutionstatusenum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.resolutionstatusenum AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'PENDING_VALIDATION',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);


ALTER TYPE public.resolutionstatusenum OWNER TO synapse_user;

--
-- Name: review_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.review_status_enum AS ENUM (
    'Pending',
    'In Review',
    'Approved',
    'Rejected',
    'Requires Revision'
);


ALTER TYPE public.review_status_enum OWNER TO synapse_user;

--
-- Name: sample_approval_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.sample_approval_status_enum AS ENUM (
    'Pending',
    'Approved',
    'Rejected',
    'Needs Changes'
);


ALTER TYPE public.sample_approval_status_enum OWNER TO synapse_user;

--
-- Name: sample_generation_method_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.sample_generation_method_enum AS ENUM (
    'LLM Generated',
    'Manual Upload',
    'Hybrid'
);


ALTER TYPE public.sample_generation_method_enum OWNER TO synapse_user;

--
-- Name: sample_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.sample_status_enum AS ENUM (
    'Draft',
    'Pending Approval',
    'Approved',
    'Rejected',
    'Revision Required'
);


ALTER TYPE public.sample_status_enum OWNER TO synapse_user;

--
-- Name: sample_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.sample_type_enum AS ENUM (
    'Population Sample',
    'Targeted Sample',
    'Exception Sample',
    'Control Sample'
);


ALTER TYPE public.sample_type_enum OWNER TO synapse_user;

--
-- Name: sample_validation_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.sample_validation_status_enum AS ENUM (
    'Valid',
    'Invalid',
    'Warning',
    'Needs Review'
);


ALTER TYPE public.sample_validation_status_enum OWNER TO synapse_user;

--
-- Name: scoping_decision_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.scoping_decision_enum AS ENUM (
    'Accept',
    'Decline',
    'Override'
);


ALTER TYPE public.scoping_decision_enum OWNER TO synapse_user;

--
-- Name: scoping_recommendation_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.scoping_recommendation_enum AS ENUM (
    'Test',
    'Skip'
);


ALTER TYPE public.scoping_recommendation_enum OWNER TO synapse_user;

--
-- Name: slatype; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.slatype AS ENUM (
    'DATA_PROVIDER_IDENTIFICATION',
    'DATA_PROVIDER_RESPONSE',
    'DOCUMENT_SUBMISSION',
    'TESTING_COMPLETION',
    'OBSERVATION_RESPONSE',
    'ISSUE_RESOLUTION'
);


ALTER TYPE public.slatype OWNER TO synapse_user;

--
-- Name: steptype; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.steptype AS ENUM (
    'PHASE',
    'ACTIVITY',
    'TRANSITION',
    'DECISION',
    'PARALLEL_BRANCH',
    'SUB_WORKFLOW'
);


ALTER TYPE public.steptype OWNER TO synapse_user;

--
-- Name: submission_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.submission_status_enum AS ENUM (
    'Pending',
    'In Progress',
    'Evidence Uploaded',
    'In Testing',
    'Submitted',
    'Validated',
    'Requires Revision',
    'Overdue'
);


ALTER TYPE public.submission_status_enum OWNER TO synapse_user;

--
-- Name: submission_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.submission_type_enum AS ENUM (
    'Document',
    'Database',
    'Mixed'
);


ALTER TYPE public.submission_type_enum OWNER TO synapse_user;

--
-- Name: submissionstatus; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.submissionstatus AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'REJECTED',
    'REVISION_REQUIRED'
);


ALTER TYPE public.submissionstatus OWNER TO synapse_user;

--
-- Name: test_case_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.test_case_status_enum AS ENUM (
    'Pending',
    'Submitted',
    'Overdue'
);


ALTER TYPE public.test_case_status_enum OWNER TO synapse_user;

--
-- Name: test_result_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.test_result_enum AS ENUM (
    'Pass',
    'Fail',
    'Exception',
    'Inconclusive',
    'Pending Review'
);


ALTER TYPE public.test_result_enum OWNER TO synapse_user;

--
-- Name: test_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.test_status_enum AS ENUM (
    'Pending',
    'Running',
    'Completed',
    'Failed',
    'Cancelled',
    'Requires Review'
);


ALTER TYPE public.test_status_enum OWNER TO synapse_user;

--
-- Name: test_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.test_type_enum AS ENUM (
    'Document Based',
    'Database Based',
    'Hybrid'
);


ALTER TYPE public.test_type_enum OWNER TO synapse_user;

--
-- Name: testerdecision; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.testerdecision AS ENUM (
    'INCLUDE',
    'EXCLUDE',
    'REVIEW_REQUIRED'
);


ALTER TYPE public.testerdecision OWNER TO synapse_user;

--
-- Name: universal_assignment_priority_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.universal_assignment_priority_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical',
    'Urgent'
);


ALTER TYPE public.universal_assignment_priority_enum OWNER TO synapse_user;

--
-- Name: universal_assignment_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.universal_assignment_status_enum AS ENUM (
    'Assigned',
    'Acknowledged',
    'In Progress',
    'Completed',
    'Approved',
    'Rejected',
    'Cancelled',
    'Overdue',
    'Escalated',
    'On Hold',
    'Delegated'
);


ALTER TYPE public.universal_assignment_status_enum OWNER TO synapse_user;

--
-- Name: universal_assignment_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.universal_assignment_type_enum AS ENUM (
    'Data Upload Request',
    'File Review',
    'File Approval',
    'Document Review',
    'Data Validation',
    'Scoping Approval',
    'Sample Selection Approval',
    'Rule Approval',
    'Observation Approval',
    'Report Approval',
    'Version Approval',
    'Phase Review',
    'Phase Approval',
    'Phase Completion',
    'Workflow Progression',
    'LOB Assignment',
    'Test Execution Review',
    'Quality Review',
    'Compliance Review',
    'Risk Assessment',
    'Information Request',
    'Clarification Required',
    'Additional Data Required',
    'Role Assignment',
    'Permission Grant',
    'System Configuration'
);


ALTER TYPE public.universal_assignment_type_enum OWNER TO synapse_user;

--
-- Name: universal_context_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.universal_context_type_enum AS ENUM (
    'Test Cycle',
    'Report',
    'Phase',
    'Attribute',
    'Sample',
    'Rule',
    'Observation',
    'File',
    'System',
    'User'
);


ALTER TYPE public.universal_context_type_enum OWNER TO synapse_user;

--
-- Name: user_role_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.user_role_enum AS ENUM (
    'Tester',
    'Test Executive',
    'Report Owner',
    'Report Executive',
    'Data Owner',
    'Data Executive',
    'Admin'
);


ALTER TYPE public.user_role_enum OWNER TO synapse_user;

--
-- Name: validation_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.validation_status_enum AS ENUM (
    'Pending',
    'Passed',
    'Failed',
    'Warning'
);


ALTER TYPE public.validation_status_enum OWNER TO synapse_user;

--
-- Name: version_change_type_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.version_change_type_enum AS ENUM (
    'created',
    'updated',
    'approved',
    'rejected',
    'archived',
    'restored'
);


ALTER TYPE public.version_change_type_enum OWNER TO synapse_user;

--
-- Name: workflow_phase_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.workflow_phase_enum AS ENUM (
    'Planning',
    'Data Profiling',
    'Scoping',
    'Data Provider ID',
    'Sampling',
    'Request Info',
    'Testing',
    'Observations',
    'Sample Selection',
    'Data Owner ID',
    'Test Execution',
    'Preparing Test Report',
    'Finalize Test Report'
);


ALTER TYPE public.workflow_phase_enum OWNER TO synapse_user;

--
-- Name: workflow_phase_state_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.workflow_phase_state_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


ALTER TYPE public.workflow_phase_state_enum OWNER TO synapse_user;

--
-- Name: workflow_phase_status_enum; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.workflow_phase_status_enum AS ENUM (
    'On Track',
    'At Risk',
    'Past Due'
);


ALTER TYPE public.workflow_phase_status_enum OWNER TO synapse_user;

--
-- Name: workflowexecutionstatus; Type: TYPE; Schema: public; Owner: synapse_user
--

CREATE TYPE public.workflowexecutionstatus AS ENUM (
    'PENDING',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED',
    'TIMED_OUT'
);


ALTER TYPE public.workflowexecutionstatus OWNER TO synapse_user;

--
-- Name: auto_skip_upload_files_activity(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.auto_skip_upload_files_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if data source exists for this cycle/report
    IF EXISTS (
        SELECT 1 FROM data_source_configs 
        WHERE cycle_id = NEW.cycle_id 
        AND report_id = NEW.report_id 
        AND is_active = true
    ) AND NEW.code = 'upload_data_files' AND NEW.status = 'pending' THEN
        -- Auto-skip the activity
        NEW.status = 'skipped';
        NEW.completed_at = CURRENT_TIMESTAMP;
        NEW.completed_by_id = NEW.assigned_to_id;
        NEW.notes = 'Auto-skipped: Data source is configured';
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.auto_skip_upload_files_activity() OWNER TO synapse_user;

--
-- Name: create_evidence_revision(integer, text, timestamp with time zone, integer); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.create_evidence_revision(p_test_case_id integer, p_revision_reason text, p_revision_deadline timestamp with time zone, p_requested_by integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_new_evidence_id INTEGER;
    v_current_evidence RECORD;
BEGIN
    -- Get current evidence
    SELECT * INTO v_current_evidence
    FROM cycle_report_rfi_evidence
    WHERE test_case_id = p_test_case_id
    AND is_current = true
    LIMIT 1;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No current evidence found for test case %', p_test_case_id;
    END IF;
    
    -- Mark current as not current
    UPDATE cycle_report_rfi_evidence
    SET is_current = false,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_current_evidence.id;
    
    -- Create revision request in current record
    UPDATE cycle_report_rfi_evidence
    SET tester_decision = 'requires_revision',
        tester_notes = p_revision_reason,
        decided_by = p_requested_by,
        decided_at = CURRENT_TIMESTAMP,
        requires_resubmission = true,
        resubmission_deadline = p_revision_deadline
    WHERE id = v_current_evidence.id;
    
    RETURN v_current_evidence.id;
END;
$$;


ALTER FUNCTION public.create_evidence_revision(p_test_case_id integer, p_revision_reason text, p_revision_deadline timestamp with time zone, p_requested_by integer) OWNER TO synapse_user;

--
-- Name: handle_document_versioning(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.handle_document_versioning() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- If this is a new version of an existing document, mark others as not latest
    IF NEW.parent_document_id IS NOT NULL AND NEW.is_latest_version = TRUE THEN
        UPDATE cycle_report_documents 
        SET is_latest_version = FALSE 
        WHERE parent_document_id = NEW.parent_document_id 
        AND id != NEW.id;
    END IF;
    
    -- If no parent but same filename exists, this is a new version
    IF NEW.parent_document_id IS NULL AND NEW.is_latest_version = TRUE THEN
        UPDATE cycle_report_documents 
        SET is_latest_version = FALSE 
        WHERE cycle_id = NEW.cycle_id 
        AND report_id = NEW.report_id 
        AND phase_id = NEW.phase_id 
        AND original_filename = NEW.original_filename 
        AND id != NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.handle_document_versioning() OWNER TO synapse_user;

--
-- Name: prevent_duplicate_activities(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.prevent_duplicate_activities() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if an activity already exists
    IF EXISTS (
        SELECT 1 FROM workflow_activities
        WHERE cycle_id = NEW.cycle_id
        AND report_id = NEW.report_id
        AND phase_name = NEW.phase_name
        AND activity_name = NEW.activity_name
        AND activity_id != COALESCE(NEW.activity_id, -1)
    ) THEN
        RAISE EXCEPTION 'Duplicate activity state already exists for cycle_id=%, report_id=%, phase=%, activity=%',
            NEW.cycle_id, NEW.report_id, NEW.phase_name, NEW.activity_name;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.prevent_duplicate_activities() OWNER TO synapse_user;

--
-- Name: reset_phase_activities(integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.reset_phase_activities(p_cycle_id integer, p_report_id integer, p_phase_name character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Delete existing activities for the phase
    DELETE FROM workflow_activities
    WHERE cycle_id = p_cycle_id
    AND report_id = p_report_id
    AND phase_name = p_phase_name;
    
    -- Re-create activities from templates
    INSERT INTO workflow_activities (
        cycle_id,
        report_id,
        phase_name,
        activity_name,
        activity_type,
        status,
        activity_order,
        is_optional,
        is_manual,
        created_at,
        updated_at
    )
    SELECT 
        p_cycle_id,
        p_report_id,
        wat.phase_name,
        wat.activity_name,
        wat.activity_type,
        'NOT_STARTED',
        wat.activity_order,
        wat.is_optional,
        wat.is_manual,
        NOW(),
        NOW()
    FROM workflow_activity_templates wat
    WHERE wat.phase_name = p_phase_name
    AND wat.is_active = true
    ORDER BY wat.activity_order;
END;
$$;


ALTER FUNCTION public.reset_phase_activities(p_cycle_id integer, p_report_id integer, p_phase_name character varying) OWNER TO synapse_user;

--
-- Name: update_cycle_report_document_updated_at(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_cycle_report_document_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_cycle_report_document_updated_at() OWNER TO synapse_user;

--
-- Name: update_cycle_report_documents_updated_at(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_cycle_report_documents_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_cycle_report_documents_updated_at() OWNER TO synapse_user;

--
-- Name: update_document_access_stats(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_document_access_stats() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- This will be called from application code when tracking access
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_document_access_stats() OWNER TO synapse_user;

--
-- Name: update_observation_group_count(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_observation_group_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count + 1
        WHERE id = NEW.group_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count - 1
        WHERE id = OLD.group_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.update_observation_group_count() OWNER TO synapse_user;

--
-- Name: update_observation_group_count_unified(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_observation_group_count_unified() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count + 1
        WHERE id = NEW.group_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count - 1
        WHERE id = OLD.group_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.update_observation_group_count_unified() OWNER TO synapse_user;

--
-- Name: update_pde_mapping_review_status(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_pde_mapping_review_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.is_latest = TRUE THEN
        UPDATE cycle_report_pde_mappings
        SET latest_review_status = NEW.review_status,
            latest_review_id = NEW.id
        WHERE id = NEW.pde_mapping_id;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_pde_mapping_review_status() OWNER TO synapse_user;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO synapse_user;

--
-- Name: update_updated_at_column_unified(); Type: FUNCTION; Schema: public; Owner: synapse_user
--

CREATE FUNCTION public.update_updated_at_column_unified() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column_unified() OWNER TO synapse_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(255) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO synapse_user;

--
-- Name: assignment_templates; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.assignment_templates (
    template_id character varying(36) NOT NULL,
    template_name character varying(255) NOT NULL,
    assignment_type public.universal_assignment_type_enum NOT NULL,
    from_role character varying(50) NOT NULL,
    to_role character varying(50) NOT NULL,
    title_template character varying(255) NOT NULL,
    description_template text,
    task_instructions_template text,
    default_priority public.universal_assignment_priority_enum NOT NULL,
    default_due_days integer,
    requires_approval boolean NOT NULL,
    approval_role character varying(50),
    context_type public.universal_context_type_enum NOT NULL,
    workflow_step character varying(100),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.assignment_templates OWNER TO synapse_user;

--
-- Name: attribute_lob_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_lob_assignments (
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    lob_id integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    assignment_rationale text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.attribute_lob_assignments OWNER TO synapse_user;

--
-- Name: attribute_lob_assignments_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.attribute_lob_assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attribute_lob_assignments_assignment_id_seq OWNER TO synapse_user;

--
-- Name: attribute_lob_assignments_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.attribute_lob_assignments_assignment_id_seq OWNED BY public.attribute_lob_assignments.assignment_id;


--
-- Name: attribute_profiling_scores; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_profiling_scores (
    score_id integer NOT NULL,
    phase_id integer NOT NULL,
    attribute_id integer NOT NULL,
    overall_quality_score double precision,
    completeness_score double precision,
    validity_score double precision,
    accuracy_score double precision,
    consistency_score double precision,
    uniqueness_score double precision,
    total_rules_executed integer,
    rules_passed integer,
    rules_failed integer,
    total_values integer,
    null_count integer,
    unique_count integer,
    data_type_detected character varying(50),
    pattern_detected character varying(255),
    distribution_type character varying(50),
    has_anomalies boolean,
    anomaly_count integer,
    anomaly_types json,
    testing_recommendation text,
    risk_assessment text,
    calculated_at timestamp without time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.attribute_profiling_scores OWNER TO synapse_user;

--
-- Name: attribute_profiling_scores_score_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.attribute_profiling_scores_score_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attribute_profiling_scores_score_id_seq OWNER TO synapse_user;

--
-- Name: attribute_profiling_scores_score_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.attribute_profiling_scores_score_id_seq OWNED BY public.attribute_profiling_scores.score_id;


--
-- Name: attribute_scoping_recommendation_versions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_scoping_recommendation_versions (
    recommendation_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    recommendation_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    llm_recommendation boolean NOT NULL,
    llm_confidence_score double precision,
    llm_reasoning text,
    llm_provider character varying(50),
    tester_decision boolean,
    tester_reasoning text,
    decision_timestamp timestamp with time zone,
    is_override boolean,
    override_justification text,
    risk_indicators jsonb,
    testing_complexity character varying(20),
    estimated_effort_hours double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.attribute_scoping_recommendation_versions OWNER TO synapse_user;

--
-- Name: attribute_scoping_recommendations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_scoping_recommendations (
    recommendation_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    recommendation_score double precision NOT NULL,
    recommendation public.scoping_recommendation_enum NOT NULL,
    rationale text NOT NULL,
    expected_source_documents json NOT NULL,
    search_keywords json NOT NULL,
    other_reports_using json,
    risk_factors json,
    priority_level character varying(20) NOT NULL,
    llm_provider character varying(50) NOT NULL,
    processing_time_ms integer NOT NULL,
    llm_request_payload json,
    llm_response_payload json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.attribute_scoping_recommendations OWNER TO synapse_user;

--
-- Name: attribute_scoping_recommendations_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.attribute_scoping_recommendations_recommendation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attribute_scoping_recommendations_recommendation_id_seq OWNER TO synapse_user;

--
-- Name: attribute_scoping_recommendations_recommendation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.attribute_scoping_recommendations_recommendation_id_seq OWNED BY public.attribute_scoping_recommendations.recommendation_id;


--
-- Name: attribute_version_change_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_version_change_logs (
    log_id integer NOT NULL,
    attribute_id integer NOT NULL,
    change_type public.version_change_type_enum NOT NULL,
    version_number integer NOT NULL,
    change_notes text,
    changed_at timestamp without time zone NOT NULL,
    changed_by integer NOT NULL,
    field_changes text,
    impact_assessment text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.attribute_version_change_logs OWNER TO synapse_user;

--
-- Name: attribute_version_change_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.attribute_version_change_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attribute_version_change_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: attribute_version_change_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.attribute_version_change_logs_log_id_seq OWNED BY public.attribute_version_change_logs.log_id;


--
-- Name: attribute_version_comparisons; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.attribute_version_comparisons (
    comparison_id integer NOT NULL,
    version_a_id integer NOT NULL,
    version_b_id integer NOT NULL,
    differences_found integer NOT NULL,
    comparison_summary text,
    impact_score double precision,
    compared_at timestamp without time zone NOT NULL,
    compared_by integer NOT NULL,
    comparison_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.attribute_version_comparisons OWNER TO synapse_user;

--
-- Name: attribute_version_comparisons_comparison_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.attribute_version_comparisons_comparison_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attribute_version_comparisons_comparison_id_seq OWNER TO synapse_user;

--
-- Name: attribute_version_comparisons_comparison_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.attribute_version_comparisons_comparison_id_seq OWNED BY public.attribute_version_comparisons.comparison_id;


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.audit_log (
    audit_id integer NOT NULL,
    user_id integer,
    action character varying(100) NOT NULL,
    table_name character varying(100),
    record_id integer,
    old_values jsonb,
    new_values jsonb,
    "timestamp" timestamp with time zone NOT NULL,
    session_id character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_log OWNER TO synapse_user;

--
-- Name: audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_log_audit_id_seq OWNER TO synapse_user;

--
-- Name: audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.audit_log_audit_id_seq OWNED BY public.audit_log.audit_id;


--
-- Name: bulk_test_executions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.bulk_test_executions (
    bulk_execution_id integer NOT NULL,
    phase_id character varying(36) NOT NULL,
    execution_mode character varying(20) NOT NULL,
    max_concurrent_tests integer NOT NULL,
    total_tests integer NOT NULL,
    tests_started integer NOT NULL,
    tests_completed integer NOT NULL,
    tests_failed integer NOT NULL,
    execution_ids jsonb NOT NULL,
    status character varying(50) NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_time_ms integer,
    initiated_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.bulk_test_executions OWNER TO synapse_user;

--
-- Name: bulk_test_executions_bulk_execution_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.bulk_test_executions_bulk_execution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bulk_test_executions_bulk_execution_id_seq OWNER TO synapse_user;

--
-- Name: bulk_test_executions_bulk_execution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.bulk_test_executions_bulk_execution_id_seq OWNED BY public.bulk_test_executions.bulk_execution_id;


--
-- Name: cdo_notifications; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.cdo_notifications (
    notification_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    cdo_id integer NOT NULL,
    lob_id integer NOT NULL,
    notification_sent_at timestamp with time zone NOT NULL,
    assignment_deadline timestamp with time zone NOT NULL,
    sla_hours integer NOT NULL,
    notification_data jsonb,
    responded_at timestamp with time zone,
    is_complete boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.cdo_notifications OWNER TO synapse_user;

--
-- Name: cdo_notifications_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.cdo_notifications_notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cdo_notifications_notification_id_seq OWNER TO synapse_user;

--
-- Name: cdo_notifications_notification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.cdo_notifications_notification_id_seq OWNED BY public.cdo_notifications.notification_id;


--
-- Name: cycle_reports; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.cycle_reports (
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    tester_id integer,
    status public.cycle_report_status_enum NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    workflow_id character varying(255)
);


ALTER TABLE public.cycle_reports OWNER TO synapse_user;

--
-- Name: data_owner_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_owner_assignments (
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    lob_id integer,
    cdo_id integer,
    data_owner_id integer,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    status public.assignment_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_owner_assignments OWNER TO synapse_user;

--
-- Name: data_owner_assignments_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_owner_assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_owner_assignments_assignment_id_seq OWNER TO synapse_user;

--
-- Name: data_owner_assignments_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_owner_assignments_assignment_id_seq OWNED BY public.data_owner_assignments.assignment_id;


--
-- Name: data_owner_escalation_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_owner_escalation_log (
    email_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    violation_ids jsonb NOT NULL,
    escalation_level public.escalation_level_enum NOT NULL,
    sent_by integer NOT NULL,
    sent_to jsonb NOT NULL,
    cc_recipients jsonb,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    sent_at timestamp with time zone NOT NULL,
    delivery_status character varying(50) NOT NULL,
    custom_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_owner_escalation_log OWNER TO synapse_user;

--
-- Name: data_owner_escalation_log_email_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_owner_escalation_log_email_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_owner_escalation_log_email_id_seq OWNER TO synapse_user;

--
-- Name: data_owner_escalation_log_email_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_owner_escalation_log_email_id_seq OWNED BY public.data_owner_escalation_log.email_id;


--
-- Name: data_owner_notifications; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_owner_notifications (
    notification_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_attributes jsonb NOT NULL,
    sample_count integer NOT NULL,
    submission_deadline timestamp with time zone NOT NULL,
    portal_access_url character varying(500) NOT NULL,
    custom_instructions text,
    notification_sent_at timestamp with time zone,
    first_access_at timestamp with time zone,
    last_access_at timestamp with time zone,
    access_count integer NOT NULL,
    is_acknowledged boolean NOT NULL,
    acknowledged_at timestamp with time zone,
    status public.submission_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.data_owner_notifications OWNER TO synapse_user;

--
-- Name: data_owner_phase_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_owner_phase_audit_log (
    audit_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_owner_phase_audit_log OWNER TO synapse_user;

--
-- Name: data_owner_phase_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_owner_phase_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_owner_phase_audit_log_audit_id_seq OWNER TO synapse_user;

--
-- Name: data_owner_phase_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_owner_phase_audit_log_audit_id_seq OWNED BY public.data_owner_phase_audit_log.audit_id;


--
-- Name: data_owner_sla_violations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_owner_sla_violations (
    violation_id integer NOT NULL,
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    cdo_id integer NOT NULL,
    violation_detected_at timestamp with time zone NOT NULL,
    original_deadline timestamp with time zone NOT NULL,
    hours_overdue double precision NOT NULL,
    escalation_level public.escalation_level_enum NOT NULL,
    last_escalation_at timestamp with time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_owner_sla_violations OWNER TO synapse_user;

--
-- Name: data_owner_sla_violations_violation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_owner_sla_violations_violation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_owner_sla_violations_violation_id_seq OWNER TO synapse_user;

--
-- Name: data_owner_sla_violations_violation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_owner_sla_violations_violation_id_seq OWNED BY public.data_owner_sla_violations.violation_id;


--
-- Name: data_profiling_files; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_profiling_files (
    file_id integer NOT NULL,
    phase_id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path text NOT NULL,
    file_size integer NOT NULL,
    file_format character varying(50) NOT NULL,
    delimiter character varying(10),
    row_count integer,
    column_count integer,
    columns_metadata json,
    is_validated boolean,
    validation_errors json,
    missing_attributes json,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp without time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_profiling_files OWNER TO synapse_user;

--
-- Name: data_profiling_files_file_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_profiling_files_file_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_profiling_files_file_id_seq OWNER TO synapse_user;

--
-- Name: data_profiling_files_file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_profiling_files_file_id_seq OWNED BY public.data_profiling_files.file_id;


--
-- Name: data_profiling_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_profiling_phases (
    phase_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    status character varying(50) NOT NULL,
    data_requested_at timestamp without time zone,
    data_received_at timestamp without time zone,
    rules_generated_at timestamp without time zone,
    profiling_executed_at timestamp without time zone,
    phase_completed_at timestamp without time zone,
    started_by integer,
    data_requested_by integer,
    completed_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_profiling_phases OWNER TO synapse_user;

--
-- Name: data_profiling_phases_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_profiling_phases_phase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_profiling_phases_phase_id_seq OWNER TO synapse_user;

--
-- Name: data_profiling_phases_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_profiling_phases_phase_id_seq OWNED BY public.data_profiling_phases.phase_id;


--
-- Name: data_profiling_rule_versions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_profiling_rule_versions (
    rule_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    rule_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    rule_type character varying(50) NOT NULL,
    rule_definition jsonb NOT NULL,
    rule_description text,
    threshold_value double precision,
    threshold_type character varying(20),
    execution_status character varying(50),
    execution_results jsonb,
    issues_found integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.data_profiling_rule_versions OWNER TO synapse_user;

--
-- Name: data_provider_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_assignments (
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    lob_id integer,
    data_provider_id integer,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    status public.assignment_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    cdo_id integer
);


ALTER TABLE public.data_provider_assignments OWNER TO synapse_user;

--
-- Name: data_provider_assignments_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_provider_assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_provider_assignments_assignment_id_seq OWNER TO synapse_user;

--
-- Name: data_provider_assignments_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_provider_assignments_assignment_id_seq OWNED BY public.data_provider_assignments.assignment_id;


--
-- Name: data_provider_escalation_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_escalation_log (
    email_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    violation_ids jsonb NOT NULL,
    escalation_level public.escalation_level_enum NOT NULL,
    sent_by integer NOT NULL,
    sent_to jsonb NOT NULL,
    cc_recipients jsonb,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    sent_at timestamp with time zone NOT NULL,
    delivery_status character varying(50) NOT NULL,
    custom_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_provider_escalation_log OWNER TO synapse_user;

--
-- Name: data_provider_escalation_log_email_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_provider_escalation_log_email_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_provider_escalation_log_email_id_seq OWNER TO synapse_user;

--
-- Name: data_provider_escalation_log_email_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_provider_escalation_log_email_id_seq OWNED BY public.data_provider_escalation_log.email_id;


--
-- Name: data_provider_notifications; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_notifications (
    notification_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    assigned_attributes jsonb NOT NULL,
    sample_count integer NOT NULL,
    submission_deadline timestamp with time zone NOT NULL,
    portal_access_url character varying(500) NOT NULL,
    custom_instructions text,
    notification_sent_at timestamp with time zone,
    first_access_at timestamp with time zone,
    last_access_at timestamp with time zone,
    access_count integer NOT NULL,
    is_acknowledged boolean NOT NULL,
    acknowledged_at timestamp with time zone,
    status public.submission_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.data_provider_notifications OWNER TO synapse_user;

--
-- Name: data_provider_phase_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_phase_audit_log (
    audit_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_provider_phase_audit_log OWNER TO synapse_user;

--
-- Name: data_provider_phase_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_provider_phase_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_provider_phase_audit_log_audit_id_seq OWNER TO synapse_user;

--
-- Name: data_provider_phase_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_provider_phase_audit_log_audit_id_seq OWNED BY public.data_provider_phase_audit_log.audit_id;


--
-- Name: data_provider_sla_violations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_sla_violations (
    violation_id integer NOT NULL,
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    cdo_id integer NOT NULL,
    violation_detected_at timestamp with time zone NOT NULL,
    original_deadline timestamp with time zone NOT NULL,
    hours_overdue double precision NOT NULL,
    escalation_level public.escalation_level_enum NOT NULL,
    last_escalation_at timestamp with time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_provider_sla_violations OWNER TO synapse_user;

--
-- Name: data_provider_sla_violations_violation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_provider_sla_violations_violation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_provider_sla_violations_violation_id_seq OWNER TO synapse_user;

--
-- Name: data_provider_sla_violations_violation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_provider_sla_violations_violation_id_seq OWNED BY public.data_provider_sla_violations.violation_id;


--
-- Name: data_provider_submissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_provider_submissions (
    submission_id integer NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    submission_type public.submission_type_enum NOT NULL,
    status public.submission_status_enum NOT NULL,
    document_ids jsonb,
    database_submission_id character varying(36),
    expected_value character varying(500),
    confidence_level character varying(20),
    notes text,
    validation_status public.validation_status_enum NOT NULL,
    validation_messages jsonb,
    validation_score double precision,
    submitted_at timestamp with time zone,
    validated_at timestamp with time zone,
    last_updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_provider_submissions OWNER TO synapse_user;

--
-- Name: data_provider_submissions_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_provider_submissions_submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_provider_submissions_submission_id_seq OWNER TO synapse_user;

--
-- Name: data_provider_submissions_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_provider_submissions_submission_id_seq OWNED BY public.data_provider_submissions.submission_id;


--
-- Name: data_sources; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.data_sources (
    data_source_id integer NOT NULL,
    data_source_name character varying(255) NOT NULL,
    database_type character varying(50) NOT NULL,
    database_url text NOT NULL,
    database_user character varying(255) NOT NULL,
    database_password_encrypted text NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    description text
);


ALTER TABLE public.data_sources OWNER TO synapse_user;

--
-- Name: data_sources_data_source_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.data_sources_data_source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_sources_data_source_id_seq OWNER TO synapse_user;

--
-- Name: data_sources_data_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.data_sources_data_source_id_seq OWNED BY public.data_sources.data_source_id;


--
-- Name: database_submissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.database_submissions (
    db_submission_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    database_name character varying(255) NOT NULL,
    table_name character varying(255) NOT NULL,
    column_name character varying(255) NOT NULL,
    primary_key_column character varying(255) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    query_filter text,
    connection_details jsonb,
    expected_value character varying(500),
    confidence_level character varying(20),
    notes text,
    validation_status public.validation_status_enum NOT NULL,
    validation_messages jsonb,
    connectivity_test_passed boolean,
    connectivity_test_at timestamp with time zone,
    submitted_at timestamp with time zone NOT NULL,
    validated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.database_submissions OWNER TO synapse_user;

--
-- Name: database_tests; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.database_tests (
    test_id integer NOT NULL,
    database_submission_id character varying(36) NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    test_query text,
    connection_timeout integer NOT NULL,
    query_timeout integer NOT NULL,
    connection_successful boolean NOT NULL,
    query_successful boolean NOT NULL,
    retrieved_value text,
    record_count integer,
    execution_time_ms integer NOT NULL,
    error_message text,
    connection_string_hash character varying(64),
    database_version character varying(100),
    actual_query_executed text,
    query_plan text,
    tested_at timestamp with time zone NOT NULL,
    tested_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.database_tests OWNER TO synapse_user;

--
-- Name: database_tests_test_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.database_tests_test_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.database_tests_test_id_seq OWNER TO synapse_user;

--
-- Name: database_tests_test_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.database_tests_test_id_seq OWNED BY public.database_tests.test_id;


--
-- Name: document_access_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.document_access_logs (
    log_id integer NOT NULL,
    document_id integer NOT NULL,
    user_id integer NOT NULL,
    access_type character varying(20) NOT NULL,
    accessed_at timestamp without time zone NOT NULL,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.document_access_logs OWNER TO synapse_user;

--
-- Name: document_access_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.document_access_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_access_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: document_access_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.document_access_logs_log_id_seq OWNED BY public.document_access_logs.log_id;


--
-- Name: document_analyses; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.document_analyses (
    analysis_id integer NOT NULL,
    submission_document_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    analysis_prompt text,
    expected_value character varying(500),
    confidence_threshold double precision NOT NULL,
    extracted_value text,
    confidence_score double precision NOT NULL,
    analysis_rationale text NOT NULL,
    matches_expected boolean,
    validation_notes jsonb,
    llm_model_used character varying(100),
    llm_tokens_used integer,
    llm_response_raw text,
    analyzed_at timestamp with time zone NOT NULL,
    analysis_duration_ms integer NOT NULL,
    analyzed_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.document_analyses OWNER TO synapse_user;

--
-- Name: document_analyses_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.document_analyses_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_analyses_analysis_id_seq OWNER TO synapse_user;

--
-- Name: document_analyses_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.document_analyses_analysis_id_seq OWNED BY public.document_analyses.analysis_id;


--
-- Name: document_extractions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.document_extractions (
    extraction_id integer NOT NULL,
    document_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    extracted_value text,
    confidence_score integer,
    extraction_method character varying(50),
    source_location text,
    supporting_context text,
    data_quality_flags json,
    alternative_values json,
    is_validated boolean NOT NULL,
    validated_by_user_id integer,
    validation_notes text,
    extracted_at timestamp without time zone NOT NULL,
    llm_provider character varying(50),
    llm_model character varying(100),
    processing_time_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.document_extractions OWNER TO synapse_user;

--
-- Name: document_extractions_extraction_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.document_extractions_extraction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_extractions_extraction_id_seq OWNER TO synapse_user;

--
-- Name: document_extractions_extraction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.document_extractions_extraction_id_seq OWNED BY public.document_extractions.extraction_id;


--
-- Name: document_revisions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.document_revisions (
    revision_id integer NOT NULL,
    test_case_id character varying(36) NOT NULL,
    document_id integer NOT NULL,
    revision_number integer NOT NULL,
    revision_reason text NOT NULL,
    requested_by integer NOT NULL,
    requested_at timestamp without time zone,
    uploaded_by integer,
    uploaded_at timestamp without time zone,
    upload_notes text,
    previous_document_id integer,
    status character varying,
    reviewed_by integer,
    reviewed_at timestamp without time zone,
    review_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.document_revisions OWNER TO synapse_user;

--
-- Name: document_revisions_revision_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.document_revisions_revision_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_revisions_revision_id_seq OWNER TO synapse_user;

--
-- Name: document_revisions_revision_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.document_revisions_revision_id_seq OWNED BY public.document_revisions.revision_id;


--
-- Name: document_submissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.document_submissions (
    submission_id character varying(36) NOT NULL,
    test_case_id character varying(36) NOT NULL,
    data_provider_id integer NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size_bytes integer NOT NULL,
    document_type public.document_type_enum NOT NULL,
    mime_type character varying(100) NOT NULL,
    submission_notes text,
    submitted_at timestamp with time zone NOT NULL,
    is_valid boolean NOT NULL,
    validation_notes text,
    validated_by integer,
    validated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    revision_number integer DEFAULT 1 NOT NULL,
    parent_submission_id character varying(36),
    is_current boolean DEFAULT true NOT NULL,
    notes text,
    data_owner_id integer
);


ALTER TABLE public.document_submissions OWNER TO synapse_user;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.documents (
    document_id integer NOT NULL,
    document_name character varying(255) NOT NULL,
    document_type character varying(50) NOT NULL,
    file_path text NOT NULL,
    file_size bigint NOT NULL,
    mime_type character varying(100) NOT NULL,
    report_id integer NOT NULL,
    cycle_id integer,
    uploaded_by_user_id integer NOT NULL,
    status character varying(20) NOT NULL,
    processing_notes text,
    file_hash character varying(64) NOT NULL,
    is_encrypted boolean NOT NULL,
    encryption_key_id character varying(100),
    document_metadata json,
    tags json,
    description text,
    business_date timestamp without time zone,
    parent_document_id integer,
    version integer NOT NULL,
    is_latest_version boolean NOT NULL,
    is_confidential boolean NOT NULL,
    access_level character varying(20) NOT NULL,
    uploaded_at timestamp without time zone NOT NULL,
    last_accessed_at timestamp without time zone,
    expires_at timestamp without time zone,
    is_archived boolean NOT NULL,
    archived_at timestamp without time zone,
    retention_date timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.documents OWNER TO synapse_user;

--
-- Name: documents_document_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.documents_document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.documents_document_id_seq OWNER TO synapse_user;

--
-- Name: documents_document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.documents_document_id_seq OWNED BY public.documents.document_id;


--
-- Name: escalation_email_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.escalation_email_logs (
    log_id integer NOT NULL,
    sla_violation_id integer NOT NULL,
    escalation_rule_id integer NOT NULL,
    report_id integer NOT NULL,
    sent_at timestamp without time zone NOT NULL,
    sent_to_emails text NOT NULL,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    delivery_status character varying(50) NOT NULL,
    delivery_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.escalation_email_logs OWNER TO synapse_user;

--
-- Name: escalation_email_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.escalation_email_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.escalation_email_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: escalation_email_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.escalation_email_logs_log_id_seq OWNED BY public.escalation_email_logs.log_id;


--
-- Name: historical_data_owner_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.historical_data_owner_assignments (
    history_id integer NOT NULL,
    report_name character varying(255) NOT NULL,
    attribute_name character varying(255) NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_by integer NOT NULL,
    cycle_id integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    completion_status character varying(50) NOT NULL,
    completion_time_hours double precision,
    success_rating double precision,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.historical_data_owner_assignments OWNER TO synapse_user;

--
-- Name: historical_data_owner_assignments_history_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.historical_data_owner_assignments_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.historical_data_owner_assignments_history_id_seq OWNER TO synapse_user;

--
-- Name: historical_data_owner_assignments_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.historical_data_owner_assignments_history_id_seq OWNED BY public.historical_data_owner_assignments.history_id;


--
-- Name: historical_data_provider_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.historical_data_provider_assignments (
    history_id integer NOT NULL,
    report_name character varying(255) NOT NULL,
    attribute_name character varying(255) NOT NULL,
    data_provider_id integer NOT NULL,
    assigned_by integer NOT NULL,
    cycle_id integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    completion_status character varying(50) NOT NULL,
    completion_time_hours double precision,
    success_rating double precision,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.historical_data_provider_assignments OWNER TO synapse_user;

--
-- Name: historical_data_provider_assignments_history_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.historical_data_provider_assignments_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.historical_data_provider_assignments_history_id_seq OWNER TO synapse_user;

--
-- Name: historical_data_provider_assignments_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.historical_data_provider_assignments_history_id_seq OWNED BY public.historical_data_provider_assignments.history_id;


--
-- Name: individual_samples; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.individual_samples (
    id integer NOT NULL,
    sample_id character varying,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    primary_key_value character varying NOT NULL,
    sample_data json NOT NULL,
    generation_method character varying NOT NULL,
    generated_at timestamp with time zone DEFAULT now(),
    generated_by_user_id integer,
    tester_decision public.testerdecision,
    tester_decision_date timestamp with time zone,
    tester_decision_by_user_id integer,
    tester_notes text,
    report_owner_decision public.reportownerdecision,
    report_owner_feedback text,
    is_submitted boolean,
    submission_id integer,
    version_number integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.individual_samples OWNER TO synapse_user;

--
-- Name: individual_samples_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.individual_samples_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.individual_samples_id_seq OWNER TO synapse_user;

--
-- Name: individual_samples_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.individual_samples_id_seq OWNED BY public.individual_samples.id;


--
-- Name: llm_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.llm_audit_log (
    log_id integer NOT NULL,
    cycle_id integer,
    report_id integer,
    llm_provider character varying(50) NOT NULL,
    prompt_template character varying(255) NOT NULL,
    request_payload jsonb NOT NULL,
    response_payload jsonb NOT NULL,
    execution_time_ms integer,
    token_usage jsonb,
    executed_at timestamp with time zone NOT NULL,
    executed_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.llm_audit_log OWNER TO synapse_user;

--
-- Name: llm_audit_log_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.llm_audit_log_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_audit_log_log_id_seq OWNER TO synapse_user;

--
-- Name: llm_audit_log_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.llm_audit_log_log_id_seq OWNED BY public.llm_audit_log.log_id;


--
-- Name: llm_sample_generations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.llm_sample_generations (
    generation_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    requested_sample_size integer NOT NULL,
    actual_samples_generated integer NOT NULL,
    generation_prompt text,
    selection_criteria jsonb NOT NULL,
    risk_focus_areas jsonb,
    exclude_criteria jsonb,
    include_edge_cases boolean NOT NULL,
    randomization_seed integer,
    llm_model_used character varying(100),
    generation_rationale text NOT NULL,
    confidence_score double precision NOT NULL,
    risk_coverage jsonb,
    estimated_testing_time integer,
    llm_metadata jsonb,
    generated_by integer NOT NULL,
    generated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.llm_sample_generations OWNER TO synapse_user;

--
-- Name: lobs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.lobs (
    lob_id integer NOT NULL,
    lob_name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.lobs OWNER TO synapse_user;

--
-- Name: lobs_lob_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.lobs_lob_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lobs_lob_id_seq OWNER TO synapse_user;

--
-- Name: lobs_lob_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.lobs_lob_id_seq OWNED BY public.lobs.lob_id;


--
-- Name: metrics_execution; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.metrics_execution (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    activity_name character varying(100) NOT NULL,
    user_id character varying(255),
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    duration_minutes double precision,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.metrics_execution OWNER TO synapse_user;

--
-- Name: metrics_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.metrics_phases (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    lob_name character varying(100),
    total_attributes integer,
    approved_attributes integer,
    attributes_with_issues integer,
    primary_keys integer,
    non_pk_attributes integer,
    total_samples integer,
    approved_samples integer,
    failed_samples integer,
    total_test_cases integer,
    completed_test_cases integer,
    passed_test_cases integer,
    failed_test_cases integer,
    total_observations integer,
    approved_observations integer,
    completion_time_minutes double precision,
    on_time_completion boolean,
    submissions_for_approval integer,
    data_providers_assigned integer,
    changes_to_data_providers integer,
    rfi_sent integer,
    rfi_completed integer,
    rfi_pending integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.metrics_phases OWNER TO synapse_user;

--
-- Name: observation_approvals; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_approvals (
    approval_id integer NOT NULL,
    observation_id integer NOT NULL,
    approval_status character varying NOT NULL,
    approval_level character varying NOT NULL,
    approver_comments text,
    approval_rationale text,
    severity_assessment character varying,
    impact_validation boolean,
    evidence_sufficiency boolean,
    regulatory_significance boolean,
    requires_escalation boolean,
    recommended_action character varying,
    priority_level character varying,
    estimated_effort character varying,
    target_resolution_date timestamp without time zone,
    approval_criteria_met json,
    approval_checklist json,
    conditional_approval boolean,
    conditions json,
    approved_by integer,
    approved_at timestamp without time zone,
    escalated_to integer,
    escalated_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_approvals OWNER TO synapse_user;

--
-- Name: observation_approvals_approval_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_approvals_approval_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_approvals_approval_id_seq OWNER TO synapse_user;

--
-- Name: observation_approvals_approval_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_approvals_approval_id_seq OWNED BY public.observation_approvals.approval_id;


--
-- Name: observation_clarifications; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_clarifications (
    clarification_id integer NOT NULL,
    group_id integer NOT NULL,
    clarification_text text NOT NULL,
    supporting_documents json,
    requested_by_role character varying NOT NULL,
    requested_by_user_id integer NOT NULL,
    requested_at timestamp without time zone,
    response_text text,
    response_documents json,
    responded_by integer,
    responded_at timestamp without time zone,
    status character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_clarifications OWNER TO synapse_user;

--
-- Name: observation_clarifications_clarification_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_clarifications_clarification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_clarifications_clarification_id_seq OWNER TO synapse_user;

--
-- Name: observation_clarifications_clarification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_clarifications_clarification_id_seq OWNED BY public.observation_clarifications.clarification_id;


--
-- Name: observation_groups; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_groups (
    group_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    issue_type character varying NOT NULL,
    first_detected_at timestamp without time zone,
    last_updated_at timestamp without time zone,
    total_test_cases integer,
    total_samples integer,
    rating public.observationratingenum,
    approval_status public.observationapprovalstatusenum,
    report_owner_approved boolean,
    report_owner_approved_by integer,
    report_owner_approved_at timestamp without time zone,
    report_owner_comments text,
    data_executive_approved boolean,
    data_executive_approved_by integer,
    data_executive_approved_at timestamp without time zone,
    data_executive_comments text,
    finalized boolean,
    finalized_by integer,
    finalized_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_groups OWNER TO synapse_user;

--
-- Name: observation_groups_group_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_groups_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_groups_group_id_seq OWNER TO synapse_user;

--
-- Name: observation_groups_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_groups_group_id_seq OWNED BY public.observation_groups.group_id;


--
-- Name: observation_impact_assessments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_impact_assessments (
    assessment_id integer NOT NULL,
    observation_id integer NOT NULL,
    impact_category public.impactcategoryenum NOT NULL,
    impact_severity character varying NOT NULL,
    impact_likelihood character varying NOT NULL,
    impact_score double precision NOT NULL,
    financial_impact_min double precision,
    financial_impact_max double precision,
    financial_impact_currency character varying,
    regulatory_requirements_affected json,
    regulatory_deadlines json,
    potential_penalties double precision,
    process_disruption_level character varying,
    system_availability_impact character varying,
    resource_requirements json,
    resolution_time_estimate integer,
    business_disruption_duration integer,
    assessment_method character varying,
    assessment_confidence double precision,
    assessment_rationale text,
    assessment_assumptions json,
    assessed_by integer,
    assessed_at timestamp without time zone,
    reviewed_by integer,
    reviewed_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_impact_assessments OWNER TO synapse_user;

--
-- Name: observation_impact_assessments_assessment_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_impact_assessments_assessment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_impact_assessments_assessment_id_seq OWNER TO synapse_user;

--
-- Name: observation_impact_assessments_assessment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_impact_assessments_assessment_id_seq OWNED BY public.observation_impact_assessments.assessment_id;


--
-- Name: observation_management_audit_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_management_audit_logs (
    log_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying,
    observation_id integer,
    action character varying NOT NULL,
    entity_type character varying NOT NULL,
    entity_id character varying,
    old_values json,
    new_values json,
    changes_summary text,
    performed_by integer NOT NULL,
    performed_at timestamp without time zone,
    user_role character varying,
    ip_address character varying,
    user_agent character varying,
    session_id character varying,
    notes text,
    execution_time_ms integer,
    business_justification text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    source_test_execution_id integer
);


ALTER TABLE public.observation_management_audit_logs OWNER TO synapse_user;

--
-- Name: observation_management_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_management_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_management_audit_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: observation_management_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_management_audit_logs_log_id_seq OWNED BY public.observation_management_audit_logs.log_id;


--
-- Name: observation_management_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_management_phases (
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying NOT NULL,
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    observation_deadline timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    observation_strategy text,
    detection_criteria json,
    approval_threshold double precision,
    instructions text,
    notes text,
    started_by integer,
    completed_by integer,
    assigned_testers json,
    total_observations integer,
    auto_detected_observations integer,
    manual_observations integer,
    approved_observations integer,
    rejected_observations integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_management_phases OWNER TO synapse_user;

--
-- Name: observation_records; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_records (
    observation_id integer NOT NULL,
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    observation_title character varying NOT NULL,
    observation_description text NOT NULL,
    observation_type public.observationtypeenum NOT NULL,
    severity public.observationseverityenum NOT NULL,
    status public.observationstatusenum,
    source_test_execution_id integer,
    source_sample_record_id character varying,
    source_attribute_id integer,
    detection_method character varying,
    detection_confidence double precision,
    impact_description text,
    impact_categories json,
    financial_impact_estimate double precision,
    regulatory_risk_level character varying,
    affected_processes json,
    affected_systems json,
    evidence_documents json,
    supporting_data json,
    screenshots json,
    related_observations json,
    detected_by integer,
    assigned_to integer,
    detected_at timestamp without time zone,
    assigned_at timestamp without time zone,
    auto_detection_rules json,
    auto_detection_score double precision,
    manual_validation_required boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_records OWNER TO synapse_user;

--
-- Name: observation_records_backup; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_records_backup (
    observation_id integer NOT NULL,
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    observation_title character varying NOT NULL,
    observation_description text NOT NULL,
    observation_type public.observationtypeenum NOT NULL,
    severity public.observationseverityenum NOT NULL,
    status public.observationstatusenum,
    source_test_execution_id integer,
    source_sample_record_id character varying,
    source_attribute_id integer,
    detection_method character varying,
    detection_confidence double precision,
    impact_description text,
    impact_categories json,
    financial_impact_estimate double precision,
    regulatory_risk_level character varying,
    affected_processes json,
    affected_systems json,
    evidence_documents json,
    supporting_data json,
    screenshots json,
    related_observations json,
    detected_by integer,
    assigned_to integer,
    detected_at timestamp without time zone,
    assigned_at timestamp without time zone,
    auto_detection_rules json,
    auto_detection_score double precision,
    manual_validation_required boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_records_backup OWNER TO synapse_user;

--
-- Name: observation_records_observation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_records_observation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_records_observation_id_seq OWNER TO synapse_user;

--
-- Name: observation_records_observation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_records_observation_id_seq OWNED BY public.observation_records_backup.observation_id;


--
-- Name: observation_records_observation_id_seq1; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_records_observation_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_records_observation_id_seq1 OWNER TO synapse_user;

--
-- Name: observation_records_observation_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_records_observation_id_seq1 OWNED BY public.observation_records.observation_id;


--
-- Name: observation_resolutions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_resolutions (
    resolution_id integer NOT NULL,
    observation_id integer NOT NULL,
    resolution_strategy character varying NOT NULL,
    resolution_description text,
    resolution_steps json,
    success_criteria json,
    validation_requirements json,
    resolution_status public.resolutionstatusenum,
    progress_percentage double precision,
    current_step character varying,
    planned_start_date timestamp without time zone,
    planned_completion_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_completion_date timestamp without time zone,
    assigned_resources json,
    estimated_effort_hours integer,
    actual_effort_hours integer,
    budget_allocated double precision,
    budget_spent double precision,
    implemented_controls json,
    process_changes json,
    system_changes json,
    documentation_updates json,
    training_requirements json,
    validation_tests_planned json,
    validation_tests_completed json,
    validation_results json,
    effectiveness_metrics json,
    resolution_owner integer,
    created_by integer,
    created_at timestamp without time zone,
    validated_by integer,
    validated_at timestamp without time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observation_resolutions OWNER TO synapse_user;

--
-- Name: observation_resolutions_resolution_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observation_resolutions_resolution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observation_resolutions_resolution_id_seq OWNER TO synapse_user;

--
-- Name: observation_resolutions_resolution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observation_resolutions_resolution_id_seq OWNED BY public.observation_resolutions.resolution_id;


--
-- Name: observation_versions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observation_versions (
    observation_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    observation_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    observation_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    title character varying(500) NOT NULL,
    description text NOT NULL,
    impact_description text,
    affected_attributes jsonb,
    affected_samples jsonb,
    affected_lobs jsonb,
    resolution_status character varying(50),
    resolution_description text,
    resolution_date timestamp with time zone,
    resolved_by character varying(255),
    group_id uuid,
    is_group_parent boolean,
    evidence_links jsonb,
    supporting_documents jsonb,
    tracking_metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.observation_versions OWNER TO synapse_user;

--
-- Name: observations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.observations (
    observation_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    observation_type public.observation_type_enum NOT NULL,
    description text NOT NULL,
    impact_level public.impact_level_enum NOT NULL,
    samples_impacted integer NOT NULL,
    status public.observation_status_enum NOT NULL,
    tester_comments text,
    report_owner_comments text,
    resolution_rationale text,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.observations OWNER TO synapse_user;

--
-- Name: observations_observation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.observations_observation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.observations_observation_id_seq OWNER TO synapse_user;

--
-- Name: observations_observation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.observations_observation_id_seq OWNED BY public.observations.observation_id;


--
-- Name: permission_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.permission_audit_log (
    audit_id integer NOT NULL,
    action_type character varying(50) NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id integer NOT NULL,
    permission_id integer,
    role_id integer,
    performed_by integer,
    performed_at timestamp without time zone DEFAULT now() NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.permission_audit_log OWNER TO synapse_user;

--
-- Name: permission_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.permission_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permission_audit_log_audit_id_seq OWNER TO synapse_user;

--
-- Name: permission_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.permission_audit_log_audit_id_seq OWNED BY public.permission_audit_log.audit_id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.permissions (
    permission_id integer NOT NULL,
    resource character varying(100) NOT NULL,
    action character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.permissions OWNER TO synapse_user;

--
-- Name: permissions_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.permissions_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permissions_permission_id_seq OWNER TO synapse_user;

--
-- Name: permissions_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.permissions_permission_id_seq OWNED BY public.permissions.permission_id;


--
-- Name: profiling_results; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.profiling_results (
    result_id integer NOT NULL,
    phase_id integer NOT NULL,
    rule_id integer NOT NULL,
    attribute_id integer NOT NULL,
    execution_status character varying(50) NOT NULL,
    execution_time_ms integer,
    executed_at timestamp without time zone NOT NULL,
    passed_count integer,
    failed_count integer,
    total_count integer,
    pass_rate double precision,
    result_summary json,
    failed_records json,
    result_details text,
    quality_impact double precision,
    severity character varying(50),
    has_anomaly boolean,
    anomaly_description text,
    anomaly_marked_by integer,
    anomaly_marked_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.profiling_results OWNER TO synapse_user;

--
-- Name: profiling_results_result_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.profiling_results_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.profiling_results_result_id_seq OWNER TO synapse_user;

--
-- Name: profiling_results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.profiling_results_result_id_seq OWNED BY public.profiling_results.result_id;


--
-- Name: profiling_rules; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.profiling_rules (
    rule_id integer NOT NULL,
    phase_id integer NOT NULL,
    attribute_id integer NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_type public.profilingruletype NOT NULL,
    rule_description text,
    rule_code text NOT NULL,
    rule_parameters json,
    llm_provider character varying(50),
    llm_rationale text,
    regulatory_reference text,
    status public.profilingrulestatus NOT NULL,
    approved_by integer,
    approved_at timestamp without time zone,
    approval_notes text,
    is_executable boolean,
    execution_order integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer DEFAULT 1,
    is_current_version boolean DEFAULT true,
    business_key character varying(255) NOT NULL,
    version_created_at timestamp without time zone,
    version_created_by integer,
    effective_from timestamp without time zone,
    effective_to timestamp without time zone,
    rejected_by integer,
    rejected_at timestamp without time zone,
    rejection_reason text,
    rejection_notes text,
    revision_notes text,
    cycle_id integer,
    report_id integer,
    created_by integer,
    updated_by integer,
    rule_logic text,
    expected_result text,
    severity character varying(50)
);


ALTER TABLE public.profiling_rules OWNER TO synapse_user;

--
-- Name: profiling_rules_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.profiling_rules_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.profiling_rules_rule_id_seq OWNER TO synapse_user;

--
-- Name: profiling_rules_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.profiling_rules_rule_id_seq OWNED BY public.profiling_rules.rule_id;


--
-- Name: regulatory_data_dictionary; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.regulatory_data_dictionary (
    dict_id integer NOT NULL,
    report_name character varying(255) NOT NULL,
    schedule_name character varying(255) NOT NULL,
    line_item_number character varying(50),
    line_item_name character varying(500) NOT NULL,
    technical_line_item_name character varying(500),
    mdrm character varying(50),
    description text,
    static_or_dynamic character varying(20),
    mandatory_or_optional character varying(20),
    format_specification character varying(200),
    num_reports_schedules_used character varying(50),
    other_schedule_reference text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.regulatory_data_dictionary OWNER TO synapse_user;

--
-- Name: regulatory_data_dictionary_dict_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.regulatory_data_dictionary_dict_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.regulatory_data_dictionary_dict_id_seq OWNER TO synapse_user;

--
-- Name: regulatory_data_dictionary_dict_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.regulatory_data_dictionary_dict_id_seq OWNED BY public.regulatory_data_dictionary.dict_id;


--
-- Name: report_attributes; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.report_attributes (
    attribute_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    description text,
    data_type public.data_type_enum,
    mandatory_flag public.mandatory_flag_enum NOT NULL,
    cde_flag boolean NOT NULL,
    historical_issues_flag boolean NOT NULL,
    is_scoped boolean NOT NULL,
    llm_generated boolean NOT NULL,
    llm_rationale text,
    tester_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    validation_rules text,
    typical_source_documents text,
    keywords_to_look_for text,
    testing_approach text,
    risk_score double precision,
    llm_risk_rationale text,
    is_primary_key boolean DEFAULT false NOT NULL,
    primary_key_order integer,
    approval_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    master_attribute_id integer,
    version_number integer DEFAULT 1 NOT NULL,
    is_latest_version boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    version_notes text,
    change_reason character varying(100),
    replaced_attribute_id integer,
    version_created_at timestamp without time zone DEFAULT now() NOT NULL,
    version_created_by integer DEFAULT 1 NOT NULL,
    approved_at timestamp without time zone,
    approved_by integer,
    archived_at timestamp without time zone,
    archived_by integer,
    line_item_number character varying(20),
    technical_line_item_name character varying(255),
    mdrm character varying(50)
);


ALTER TABLE public.report_attributes OWNER TO synapse_user;

--
-- Name: COLUMN report_attributes.risk_score; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.risk_score IS 'LLM-provided risk score (0-10) based on regulatory importance';


--
-- Name: COLUMN report_attributes.llm_risk_rationale; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.llm_risk_rationale IS 'LLM explanation for the assigned risk score';


--
-- Name: COLUMN report_attributes.is_primary_key; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.is_primary_key IS 'Whether this attribute is part of the primary key';


--
-- Name: COLUMN report_attributes.primary_key_order; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.primary_key_order IS 'Order of this attribute in composite primary key (1-based)';


--
-- Name: COLUMN report_attributes.approval_status; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.approval_status IS 'Approval status: pending, approved, rejected';


--
-- Name: COLUMN report_attributes.version_number; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.version_number IS 'Version number of this attribute';


--
-- Name: COLUMN report_attributes.is_latest_version; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.is_latest_version IS 'Whether this is the latest version';


--
-- Name: COLUMN report_attributes.is_active; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.is_active IS 'Whether this version is active';


--
-- Name: COLUMN report_attributes.version_notes; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.version_notes IS 'Notes about what changed in this version';


--
-- Name: COLUMN report_attributes.change_reason; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.change_reason IS 'Reason for creating new version';


--
-- Name: COLUMN report_attributes.line_item_number; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.line_item_number IS 'Regulatory line item number from data dictionary';


--
-- Name: COLUMN report_attributes.technical_line_item_name; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.technical_line_item_name IS 'Technical line item name from data dictionary';


--
-- Name: COLUMN report_attributes.mdrm; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.report_attributes.mdrm IS 'MDRM code from regulatory data dictionary';


--
-- Name: report_attributes_attribute_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.report_attributes_attribute_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_attributes_attribute_id_seq OWNER TO synapse_user;

--
-- Name: report_attributes_attribute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.report_attributes_attribute_id_seq OWNED BY public.report_attributes.attribute_id;


--
-- Name: report_owner_assignment_history; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.report_owner_assignment_history (
    history_id integer NOT NULL,
    assignment_id integer NOT NULL,
    changed_by integer NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    field_changed character varying(100) NOT NULL,
    old_value text,
    new_value text,
    change_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.report_owner_assignment_history OWNER TO synapse_user;

--
-- Name: report_owner_assignment_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.report_owner_assignment_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_owner_assignment_history_history_id_seq OWNER TO synapse_user;

--
-- Name: report_owner_assignment_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.report_owner_assignment_history_history_id_seq OWNED BY public.report_owner_assignment_history.history_id;


--
-- Name: report_owner_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.report_owner_assignments (
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    assignment_type public.assignment_type_enum NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    assigned_to integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    due_date timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    status public.assignment_status_enum NOT NULL,
    priority public.assignment_priority_enum NOT NULL,
    completed_by integer,
    completion_notes text,
    completion_attachments text,
    escalated boolean NOT NULL,
    escalated_at timestamp with time zone,
    escalation_reason text,
    assignment_metadata text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.report_owner_assignments OWNER TO synapse_user;

--
-- Name: report_owner_assignments_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.report_owner_assignments_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_owner_assignments_assignment_id_seq OWNER TO synapse_user;

--
-- Name: report_owner_assignments_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.report_owner_assignments_assignment_id_seq OWNED BY public.report_owner_assignments.assignment_id;


--
-- Name: report_owner_executives; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.report_owner_executives (
    executive_id integer NOT NULL,
    report_owner_id integer NOT NULL
);


ALTER TABLE public.report_owner_executives OWNER TO synapse_user;

--
-- Name: report_owner_scoping_reviews; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.report_owner_scoping_reviews (
    review_id integer NOT NULL,
    submission_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    approval_status public.approval_status_enum NOT NULL,
    review_comments text,
    requested_changes json,
    resource_impact_assessment text,
    risk_coverage_assessment text,
    reviewed_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.report_owner_scoping_reviews OWNER TO synapse_user;

--
-- Name: report_owner_scoping_reviews_review_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.report_owner_scoping_reviews_review_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_owner_scoping_reviews_review_id_seq OWNER TO synapse_user;

--
-- Name: report_owner_scoping_reviews_review_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.report_owner_scoping_reviews_review_id_seq OWNED BY public.report_owner_scoping_reviews.review_id;


--
-- Name: reports; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.reports (
    report_id integer NOT NULL,
    report_name character varying(255) NOT NULL,
    regulation character varying(255),
    description text,
    frequency character varying(100),
    report_owner_id integer NOT NULL,
    lob_id integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.reports OWNER TO synapse_user;

--
-- Name: reports_report_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.reports_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_report_id_seq OWNER TO synapse_user;

--
-- Name: reports_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.reports_report_id_seq OWNED BY public.reports.report_id;


--
-- Name: request_info_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.request_info_audit_log (
    audit_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(36),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.request_info_audit_log OWNER TO synapse_user;

--
-- Name: request_info_audit_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.request_info_audit_logs (
    log_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.request_info_audit_logs OWNER TO synapse_user;

--
-- Name: request_info_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.request_info_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.request_info_audit_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: request_info_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.request_info_audit_logs_log_id_seq OWNED BY public.request_info_audit_logs.log_id;


--
-- Name: request_info_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.request_info_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    submission_deadline timestamp with time zone NOT NULL,
    reminder_schedule jsonb,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.request_info_phases OWNER TO synapse_user;

--
-- Name: resource_permissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.resource_permissions (
    resource_permission_id integer NOT NULL,
    user_id integer NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted boolean NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.resource_permissions OWNER TO synapse_user;

--
-- Name: resource_permissions_resource_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.resource_permissions_resource_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.resource_permissions_resource_permission_id_seq OWNER TO synapse_user;

--
-- Name: resource_permissions_resource_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.resource_permissions_resource_permission_id_seq OWNED BY public.resource_permissions.resource_permission_id;


--
-- Name: resources; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.resources (
    resource_id integer NOT NULL,
    resource_name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    resource_type character varying(50) NOT NULL,
    parent_resource_id integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.resources OWNER TO synapse_user;

--
-- Name: resources_resource_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.resources_resource_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.resources_resource_id_seq OWNER TO synapse_user;

--
-- Name: resources_resource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.resources_resource_id_seq OWNED BY public.resources.resource_id;


--
-- Name: role_hierarchy; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.role_hierarchy (
    parent_role_id integer NOT NULL,
    child_role_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.role_hierarchy OWNER TO synapse_user;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.role_permissions (
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO synapse_user;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.roles (
    role_id integer NOT NULL,
    role_name character varying(100) NOT NULL,
    description text,
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.roles OWNER TO synapse_user;

--
-- Name: roles_role_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.roles_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_role_id_seq OWNER TO synapse_user;

--
-- Name: roles_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.roles_role_id_seq OWNED BY public.roles.role_id;


--
-- Name: sample_approval_history; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_approval_history (
    approval_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    approval_step character varying(100) NOT NULL,
    decision character varying(50) NOT NULL,
    approved_by integer NOT NULL,
    approved_at timestamp with time zone NOT NULL,
    feedback text,
    requested_changes jsonb,
    conditional_approval boolean NOT NULL,
    approval_conditions jsonb,
    previous_status public.sample_status_enum,
    new_status public.sample_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sample_approval_history OWNER TO synapse_user;

--
-- Name: sample_audit_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_audit_logs (
    id integer NOT NULL,
    sample_id integer,
    submission_id integer,
    action character varying NOT NULL,
    action_details json,
    user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.sample_audit_logs OWNER TO synapse_user;

--
-- Name: sample_audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sample_audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_audit_logs_id_seq OWNER TO synapse_user;

--
-- Name: sample_audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sample_audit_logs_id_seq OWNED BY public.sample_audit_logs.id;


--
-- Name: sample_feedback; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_feedback (
    id integer NOT NULL,
    sample_id integer NOT NULL,
    submission_id integer NOT NULL,
    feedback_type character varying NOT NULL,
    feedback_text text NOT NULL,
    severity character varying,
    is_blocking boolean,
    is_resolved boolean,
    resolved_at timestamp with time zone,
    resolved_by_user_id integer,
    resolution_notes text,
    created_by_user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.sample_feedback OWNER TO synapse_user;

--
-- Name: sample_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sample_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_feedback_id_seq OWNER TO synapse_user;

--
-- Name: sample_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sample_feedback_id_seq OWNED BY public.sample_feedback.id;


--
-- Name: sample_records; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_records (
    record_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    sample_identifier character varying(255) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    sample_data jsonb NOT NULL,
    risk_score double precision,
    validation_status public.sample_validation_status_enum NOT NULL,
    validation_score double precision,
    selection_rationale text,
    data_source_info jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    approval_status public.sample_approval_status_enum DEFAULT 'Pending'::public.sample_approval_status_enum NOT NULL,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    change_requests jsonb
);


ALTER TABLE public.sample_records OWNER TO synapse_user;

--
-- Name: sample_selection_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_selection_audit_log (
    audit_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    set_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(36),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sample_selection_audit_log OWNER TO synapse_user;

--
-- Name: sample_selection_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_selection_phases (
    phase_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50),
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_end_date timestamp without time zone,
    target_sample_size integer,
    sampling_methodology character varying(100),
    sampling_criteria json,
    llm_generation_enabled boolean,
    llm_provider character varying(50),
    llm_model character varying(100),
    llm_confidence_threshold double precision,
    manual_upload_enabled boolean,
    upload_template_url character varying(500),
    samples_generated integer,
    samples_validated integer,
    samples_approved integer,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer,
    updated_by integer,
    id integer NOT NULL
);


ALTER TABLE public.sample_selection_phases OWNER TO synapse_user;

--
-- Name: sample_selection_phases_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sample_selection_phases_phase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_selection_phases_phase_id_seq OWNER TO synapse_user;

--
-- Name: sample_selection_phases_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sample_selection_phases_phase_id_seq OWNED BY public.sample_selection_phases.phase_id;


--
-- Name: sample_sets; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_sets (
    set_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    set_name character varying(255) NOT NULL,
    description text,
    generation_method public.sample_generation_method_enum NOT NULL,
    sample_type public.sample_type_enum NOT NULL,
    status public.sample_status_enum NOT NULL,
    target_sample_size integer,
    actual_sample_size integer NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    approved_by integer,
    approved_at timestamp with time zone,
    approval_notes text,
    generation_rationale text,
    selection_criteria jsonb,
    quality_score double precision,
    sample_metadata jsonb,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    master_set_id character varying(36),
    version_number integer DEFAULT 1 NOT NULL,
    is_latest_version boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    version_notes text,
    change_reason character varying(100),
    replaced_set_id character varying(36),
    version_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version_created_by integer DEFAULT 1 NOT NULL,
    archived_at timestamp without time zone,
    archived_by integer
);


ALTER TABLE public.sample_sets OWNER TO synapse_user;

--
-- Name: sample_submission_items; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_submission_items (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    sample_id integer NOT NULL,
    tester_decision public.testerdecision NOT NULL,
    primary_key_value character varying NOT NULL,
    sample_data_snapshot json NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.sample_submission_items OWNER TO synapse_user;

--
-- Name: sample_submission_items_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sample_submission_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_submission_items_id_seq OWNER TO synapse_user;

--
-- Name: sample_submission_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sample_submission_items_id_seq OWNED BY public.sample_submission_items.id;


--
-- Name: sample_submissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_submissions (
    id integer NOT NULL,
    submission_id character varying,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    version_number integer NOT NULL,
    submitted_at timestamp with time zone DEFAULT now(),
    submitted_by_user_id integer,
    submission_notes text,
    status public.submissionstatus,
    reviewed_at timestamp with time zone,
    reviewed_by_user_id integer,
    review_decision public.reportownerdecision,
    review_feedback text,
    is_official_version boolean,
    total_samples integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.sample_submissions OWNER TO synapse_user;

--
-- Name: sample_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sample_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_submissions_id_seq OWNER TO synapse_user;

--
-- Name: sample_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sample_submissions_id_seq OWNED BY public.sample_submissions.id;


--
-- Name: sample_upload_history; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_upload_history (
    upload_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    upload_method character varying(50) NOT NULL,
    original_filename character varying(255),
    file_size_bytes integer,
    total_rows integer NOT NULL,
    valid_rows integer NOT NULL,
    invalid_rows integer NOT NULL,
    primary_key_column character varying(255) NOT NULL,
    data_mapping jsonb,
    validation_rules_applied jsonb,
    data_quality_score double precision NOT NULL,
    upload_summary jsonb,
    processing_time_ms integer NOT NULL,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sample_upload_history OWNER TO synapse_user;

--
-- Name: sample_validation_issues; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_validation_issues (
    issue_id character varying(36) NOT NULL,
    validation_id character varying(36) NOT NULL,
    record_id character varying(36) NOT NULL,
    issue_type character varying(100) NOT NULL,
    severity character varying(50) NOT NULL,
    field_name character varying(255),
    issue_description text NOT NULL,
    suggested_fix text,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    resolved_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sample_validation_issues OWNER TO synapse_user;

--
-- Name: sample_validation_results; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sample_validation_results (
    validation_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    validation_type character varying(100) NOT NULL,
    validation_rules jsonb NOT NULL,
    overall_status public.sample_validation_status_enum NOT NULL,
    total_samples integer NOT NULL,
    valid_samples integer NOT NULL,
    invalid_samples integer NOT NULL,
    warning_samples integer NOT NULL,
    overall_quality_score double precision NOT NULL,
    validation_summary jsonb,
    recommendations jsonb,
    validated_by integer NOT NULL,
    validated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sample_validation_results OWNER TO synapse_user;

--
-- Name: samples; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.samples (
    sample_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    primary_key_name character varying(100) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    sample_data jsonb NOT NULL,
    llm_rationale text,
    tester_rationale text,
    status public.sample_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.samples OWNER TO synapse_user;

--
-- Name: samples_sample_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.samples_sample_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.samples_sample_id_seq OWNER TO synapse_user;

--
-- Name: samples_sample_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.samples_sample_id_seq OWNED BY public.samples.sample_id;


--
-- Name: scoping_audit_log; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.scoping_audit_log (
    audit_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    performed_by integer NOT NULL,
    details json NOT NULL,
    previous_values json,
    new_values json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.scoping_audit_log OWNER TO synapse_user;

--
-- Name: scoping_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.scoping_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scoping_audit_log_audit_id_seq OWNER TO synapse_user;

--
-- Name: scoping_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.scoping_audit_log_audit_id_seq OWNED BY public.scoping_audit_log.audit_id;


--
-- Name: scoping_decision_versions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.scoping_decision_versions (
    decision_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    decision_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    is_in_scope boolean NOT NULL,
    scope_reason text,
    testing_approach character varying(100),
    sample_size_override integer,
    special_instructions text,
    risk_level character varying(20),
    risk_factors jsonb,
    assigned_lobs jsonb,
    depends_on_attributes jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.scoping_decision_versions OWNER TO synapse_user;

--
-- Name: scoping_submissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.scoping_submissions (
    submission_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    submission_notes text,
    total_attributes integer NOT NULL,
    scoped_attributes integer NOT NULL,
    skipped_attributes integer NOT NULL,
    submitted_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    previous_version_id integer,
    changes_from_previous json,
    revision_reason text
);


ALTER TABLE public.scoping_submissions OWNER TO synapse_user;

--
-- Name: scoping_submissions_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.scoping_submissions_submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scoping_submissions_submission_id_seq OWNER TO synapse_user;

--
-- Name: scoping_submissions_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.scoping_submissions_submission_id_seq OWNED BY public.scoping_submissions.submission_id;


--
-- Name: sla_configurations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sla_configurations (
    sla_config_id integer NOT NULL,
    sla_type public.slatype NOT NULL,
    sla_hours integer NOT NULL,
    warning_hours integer,
    escalation_enabled boolean NOT NULL,
    is_active boolean NOT NULL,
    business_hours_only boolean NOT NULL,
    weekend_excluded boolean NOT NULL,
    auto_escalate_on_breach boolean NOT NULL,
    escalation_interval_hours integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sla_configurations OWNER TO synapse_user;

--
-- Name: sla_configurations_sla_config_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sla_configurations_sla_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sla_configurations_sla_config_id_seq OWNER TO synapse_user;

--
-- Name: sla_configurations_sla_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sla_configurations_sla_config_id_seq OWNED BY public.sla_configurations.sla_config_id;


--
-- Name: sla_escalation_rules; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sla_escalation_rules (
    escalation_rule_id integer NOT NULL,
    sla_config_id integer NOT NULL,
    escalation_level public.escalationlevel NOT NULL,
    escalation_order integer NOT NULL,
    escalate_to_role character varying(100) NOT NULL,
    escalate_to_user_id integer,
    hours_after_breach integer NOT NULL,
    email_template_subject character varying(255) NOT NULL,
    email_template_body text NOT NULL,
    include_managers boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sla_escalation_rules OWNER TO synapse_user;

--
-- Name: sla_escalation_rules_escalation_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sla_escalation_rules_escalation_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sla_escalation_rules_escalation_rule_id_seq OWNER TO synapse_user;

--
-- Name: sla_escalation_rules_escalation_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sla_escalation_rules_escalation_rule_id_seq OWNED BY public.sla_escalation_rules.escalation_rule_id;


--
-- Name: sla_violation_tracking; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.sla_violation_tracking (
    violation_id integer NOT NULL,
    sla_config_id integer NOT NULL,
    report_id integer NOT NULL,
    cycle_id integer NOT NULL,
    started_at timestamp without time zone NOT NULL,
    due_date timestamp without time zone NOT NULL,
    warning_date timestamp without time zone,
    completed_at timestamp without time zone,
    is_violated boolean NOT NULL,
    violated_at timestamp without time zone,
    violation_hours integer,
    current_escalation_level public.escalationlevel,
    escalation_count integer NOT NULL,
    last_escalated_at timestamp without time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp without time zone,
    resolution_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sla_violation_tracking OWNER TO synapse_user;

--
-- Name: sla_violation_tracking_violation_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.sla_violation_tracking_violation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sla_violation_tracking_violation_id_seq OWNER TO synapse_user;

--
-- Name: sla_violation_tracking_violation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.sla_violation_tracking_violation_id_seq OWNED BY public.sla_violation_tracking.violation_id;


--
-- Name: submission_documents; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.submission_documents (
    document_id integer NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    document_type public.document_type_enum NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size integer NOT NULL,
    file_hash character varying(64) NOT NULL,
    mime_type character varying(100) NOT NULL,
    sample_records jsonb NOT NULL,
    attributes jsonb NOT NULL,
    description text NOT NULL,
    notes text,
    validation_status public.validation_status_enum NOT NULL,
    validation_messages jsonb,
    validation_score double precision,
    uploaded_at timestamp with time zone NOT NULL,
    validated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.submission_documents OWNER TO synapse_user;

--
-- Name: submission_documents_document_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.submission_documents_document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.submission_documents_document_id_seq OWNER TO synapse_user;

--
-- Name: submission_documents_document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.submission_documents_document_id_seq OWNED BY public.submission_documents.document_id;


--
-- Name: submission_reminders; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.submission_reminders (
    reminder_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    data_provider_id integer NOT NULL,
    reminder_type character varying(50) NOT NULL,
    custom_message text,
    days_before_deadline integer,
    scheduled_at timestamp with time zone NOT NULL,
    sent_at timestamp with time zone,
    delivery_status character varying(50) NOT NULL,
    delivery_attempts integer NOT NULL,
    error_message text,
    viewed_at timestamp with time zone,
    responded_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.submission_reminders OWNER TO synapse_user;

--
-- Name: submission_validations; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.submission_validations (
    validation_id character varying(36) NOT NULL,
    submission_id integer NOT NULL,
    validation_type character varying(100) NOT NULL,
    status public.validation_status_enum NOT NULL,
    message text NOT NULL,
    severity character varying(20) NOT NULL,
    recommendation text,
    rule_applied character varying(200),
    validated_at timestamp with time zone NOT NULL,
    validated_by character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.submission_validations OWNER TO synapse_user;

--
-- Name: test_cases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_cases (
    test_case_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_id character varying(36) NOT NULL,
    sample_identifier character varying(255) NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    attribute_name character varying(255) NOT NULL,
    primary_key_attributes jsonb NOT NULL,
    expected_evidence_type character varying(100),
    special_instructions text,
    status public.test_case_status_enum NOT NULL,
    submission_deadline timestamp with time zone,
    submitted_at timestamp with time zone,
    acknowledged_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.test_cases OWNER TO synapse_user;

--
-- Name: test_comparisons; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_comparisons (
    comparison_id integer NOT NULL,
    execution_ids jsonb NOT NULL,
    comparison_criteria jsonb NOT NULL,
    comparison_results jsonb NOT NULL,
    consistency_score double precision NOT NULL,
    differences_found jsonb,
    recommendations jsonb,
    analysis_method_used character varying(100),
    statistical_metrics jsonb,
    compared_at timestamp with time zone NOT NULL,
    comparison_duration_ms integer NOT NULL,
    compared_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_comparisons OWNER TO synapse_user;

--
-- Name: test_comparisons_comparison_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_comparisons_comparison_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_comparisons_comparison_id_seq OWNER TO synapse_user;

--
-- Name: test_comparisons_comparison_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_comparisons_comparison_id_seq OWNED BY public.test_comparisons.comparison_id;


--
-- Name: test_cycles; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_cycles (
    cycle_id integer NOT NULL,
    cycle_name character varying(255) NOT NULL,
    description text,
    test_manager_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    start_date date NOT NULL,
    end_date date,
    status character varying(50) NOT NULL,
    workflow_id character varying(255)
);


ALTER TABLE public.test_cycles OWNER TO synapse_user;

--
-- Name: COLUMN test_cycles.workflow_id; Type: COMMENT; Schema: public; Owner: synapse_user
--

COMMENT ON COLUMN public.test_cycles.workflow_id IS 'Temporal workflow ID for tracking workflow execution';


--
-- Name: test_cycles_cycle_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_cycles_cycle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_cycles_cycle_id_seq OWNER TO synapse_user;

--
-- Name: test_cycles_cycle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_cycles_cycle_id_seq OWNED BY public.test_cycles.cycle_id;


--
-- Name: test_execution_audit_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_execution_audit_logs (
    log_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    execution_time_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_execution_audit_logs OWNER TO synapse_user;

--
-- Name: test_execution_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_execution_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_execution_audit_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: test_execution_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_execution_audit_logs_log_id_seq OWNED BY public.test_execution_audit_logs.log_id;


--
-- Name: test_execution_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_execution_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    testing_deadline timestamp with time zone NOT NULL,
    test_strategy text,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.test_execution_phases OWNER TO synapse_user;

--
-- Name: test_execution_versions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_execution_versions (
    execution_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    execution_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_id integer NOT NULL,
    test_results jsonb NOT NULL,
    document_results jsonb,
    database_results jsonb,
    overall_result character varying(20),
    confidence_score double precision,
    issues_identified jsonb,
    requires_resubmission boolean,
    resubmission_reason text,
    evidence_files jsonb,
    screenshots jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.test_execution_versions OWNER TO synapse_user;

--
-- Name: test_executions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_executions (
    execution_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    sample_id integer,
    attribute_id integer,
    test_run_number integer NOT NULL,
    source_value text,
    expected_value text,
    test_result public.test_result_enum,
    discrepancy_details text,
    data_source_type public.data_source_type_enum,
    data_source_id integer,
    document_id integer,
    table_name character varying(255),
    column_name character varying(255),
    executed_at timestamp with time zone NOT NULL,
    executed_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_executions OWNER TO synapse_user;

--
-- Name: test_executions_execution_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_executions_execution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_executions_execution_id_seq OWNER TO synapse_user;

--
-- Name: test_executions_execution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_executions_execution_id_seq OWNED BY public.test_executions.execution_id;


--
-- Name: test_report_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_report_phases (
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    include_executive_summary boolean,
    include_phase_artifacts boolean,
    include_detailed_observations boolean,
    include_metrics_dashboard boolean,
    report_title character varying,
    report_period character varying,
    regulatory_references json,
    final_report_document_id integer,
    report_generated_at timestamp without time zone,
    report_approved_by json,
    status character varying
);


ALTER TABLE public.test_report_phases OWNER TO synapse_user;

--
-- Name: test_report_sections; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_report_sections (
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    section_id integer NOT NULL,
    phase_id character varying NOT NULL,
    section_name character varying NOT NULL,
    section_order integer NOT NULL,
    section_type character varying NOT NULL,
    content_text text,
    content_data json,
    artifacts json,
    metrics_summary json
);


ALTER TABLE public.test_report_sections OWNER TO synapse_user;

--
-- Name: test_report_sections_section_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_report_sections_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_report_sections_section_id_seq OWNER TO synapse_user;

--
-- Name: test_report_sections_section_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_report_sections_section_id_seq OWNED BY public.test_report_sections.section_id;


--
-- Name: test_result_reviews; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.test_result_reviews (
    review_id integer NOT NULL,
    execution_id integer NOT NULL,
    reviewer_id integer NOT NULL,
    review_result public.review_status_enum NOT NULL,
    reviewer_comments text NOT NULL,
    recommended_action character varying(200),
    requires_retest boolean NOT NULL,
    accuracy_score double precision,
    completeness_score double precision,
    consistency_score double precision,
    overall_score double precision,
    review_criteria_used jsonb,
    supporting_evidence text,
    reviewed_at timestamp with time zone NOT NULL,
    review_duration_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_result_reviews OWNER TO synapse_user;

--
-- Name: test_result_reviews_review_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.test_result_reviews_review_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_result_reviews_review_id_seq OWNER TO synapse_user;

--
-- Name: test_result_reviews_review_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.test_result_reviews_review_id_seq OWNED BY public.test_result_reviews.review_id;


--
-- Name: tester_scoping_decisions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.tester_scoping_decisions (
    decision_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    recommendation_id integer,
    decision public.scoping_decision_enum NOT NULL,
    final_scoping boolean NOT NULL,
    tester_rationale text,
    override_reason text,
    decided_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tester_scoping_decisions OWNER TO synapse_user;

--
-- Name: tester_scoping_decisions_decision_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.tester_scoping_decisions_decision_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tester_scoping_decisions_decision_id_seq OWNER TO synapse_user;

--
-- Name: tester_scoping_decisions_decision_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.tester_scoping_decisions_decision_id_seq OWNED BY public.tester_scoping_decisions.decision_id;


--
-- Name: testing_execution_audit_logs; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.testing_execution_audit_logs (
    log_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    execution_time_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.testing_execution_audit_logs OWNER TO synapse_user;

--
-- Name: testing_execution_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.testing_execution_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.testing_execution_audit_logs_log_id_seq OWNER TO synapse_user;

--
-- Name: testing_execution_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.testing_execution_audit_logs_log_id_seq OWNED BY public.testing_execution_audit_logs.log_id;


--
-- Name: testing_execution_phases; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.testing_execution_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    testing_deadline timestamp with time zone NOT NULL,
    test_strategy text,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.testing_execution_phases OWNER TO synapse_user;

--
-- Name: testing_test_executions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.testing_test_executions (
    execution_id integer NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    test_type public.test_type_enum NOT NULL,
    analysis_method public.analysis_method_enum NOT NULL,
    priority character varying(20) NOT NULL,
    custom_instructions text,
    status public.test_status_enum NOT NULL,
    result public.test_result_enum,
    confidence_score double precision,
    execution_summary text,
    error_message text,
    document_analysis_id integer,
    database_test_id integer,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_time_ms integer,
    assigned_tester_id integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    data_source_id integer,
    sample_id integer,
    executed_by integer
);


ALTER TABLE public.testing_test_executions OWNER TO synapse_user;

--
-- Name: testing_test_executions_execution_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.testing_test_executions_execution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.testing_test_executions_execution_id_seq OWNER TO synapse_user;

--
-- Name: testing_test_executions_execution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.testing_test_executions_execution_id_seq OWNED BY public.testing_test_executions.execution_id;


--
-- Name: universal_assignment_history; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.universal_assignment_history (
    history_id integer NOT NULL,
    assignment_id character varying(36) NOT NULL,
    changed_by_user_id integer NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    action character varying(50) NOT NULL,
    field_changed character varying(100),
    old_value text,
    new_value text,
    change_reason text,
    change_metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.universal_assignment_history OWNER TO synapse_user;

--
-- Name: universal_assignment_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.universal_assignment_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.universal_assignment_history_history_id_seq OWNER TO synapse_user;

--
-- Name: universal_assignment_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.universal_assignment_history_history_id_seq OWNED BY public.universal_assignment_history.history_id;


--
-- Name: universal_assignments; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.universal_assignments (
    assignment_id character varying(36) NOT NULL,
    assignment_type public.universal_assignment_type_enum NOT NULL,
    from_role character varying(50) NOT NULL,
    to_role character varying(50) NOT NULL,
    from_user_id integer NOT NULL,
    to_user_id integer,
    title character varying(255) NOT NULL,
    description text,
    task_instructions text,
    context_type public.universal_context_type_enum NOT NULL,
    context_data jsonb,
    status public.universal_assignment_status_enum NOT NULL,
    priority public.universal_assignment_priority_enum NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    due_date timestamp with time zone,
    acknowledged_at timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    completed_by_user_id integer,
    completion_notes text,
    completion_data jsonb,
    completion_attachments jsonb,
    requires_approval boolean NOT NULL,
    approval_role character varying(50),
    approved_by_user_id integer,
    approved_at timestamp with time zone,
    approval_notes text,
    escalated boolean NOT NULL,
    escalated_at timestamp with time zone,
    escalated_to_user_id integer,
    escalation_reason text,
    delegated_to_user_id integer,
    delegated_at timestamp with time zone,
    delegation_reason text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    assignment_metadata jsonb,
    workflow_step character varying(100),
    parent_assignment_id character varying(36)
);


ALTER TABLE public.universal_assignments OWNER TO synapse_user;

--
-- Name: user_permissions; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.user_permissions (
    user_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted boolean NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_permissions OWNER TO synapse_user;

--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_roles OWNER TO synapse_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(20),
    role public.user_role_enum NOT NULL,
    lob_id integer,
    is_active boolean NOT NULL,
    hashed_password character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO synapse_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: synapse_user
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO synapse_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: synapse_user
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: version_history; Type: TABLE; Schema: public; Owner: synapse_user
--

CREATE TABLE public.version_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    entity_name character varying(255),
    version_number integer NOT NULL,
    change_type character varying(50) NOT NULL,
    change_reason text,
    changed_by character varying(255) NOT NULL,
    changed_at timestamp with time zone,
    change_details jsonb,
    cycle_id uuid,
    report_id uuid,
    phase_name character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.version_history OWNER TO synapse_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- Data for Name: assignment_templates; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.assignment_templates (template_id, template_name, assignment_type, from_role, to_role, title_template, description_template, task_instructions_template, default_priority, default_due_days, requires_approval, approval_role, context_type, workflow_step, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attribute_lob_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_lob_assignments (assignment_id, cycle_id, report_id, attribute_id, lob_id, assigned_by, assigned_at, assignment_rationale, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attribute_profiling_scores; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_profiling_scores (score_id, phase_id, attribute_id, overall_quality_score, completeness_score, validity_score, accuracy_score, consistency_score, uniqueness_score, total_rules_executed, rules_passed, rules_failed, total_values, null_count, unique_count, data_type_detected, pattern_detected, distribution_type, has_anomalies, anomaly_count, anomaly_types, testing_recommendation, risk_assessment, calculated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attribute_scoping_recommendation_versions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_scoping_recommendation_versions (recommendation_version_id, recommendation_id, cycle_id, report_id, attribute_id, llm_recommendation, llm_confidence_score, llm_reasoning, llm_provider, tester_decision, tester_reasoning, decision_timestamp, is_override, override_justification, risk_indicators, testing_complexity, estimated_effort_hours, created_at, updated_at, version_number, is_latest_version, version_created_at, version_created_by, version_notes, change_reason, parent_version_id, version_status, approved_version_id, approved_at, approved_by) FROM stdin;
\.


--
-- Data for Name: attribute_scoping_recommendations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_scoping_recommendations (recommendation_id, cycle_id, report_id, attribute_id, recommendation_score, recommendation, rationale, expected_source_documents, search_keywords, other_reports_using, risk_factors, priority_level, llm_provider, processing_time_ms, llm_request_payload, llm_response_payload, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attribute_version_change_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_version_change_logs (log_id, attribute_id, change_type, version_number, change_notes, changed_at, changed_by, field_changes, impact_assessment, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attribute_version_comparisons; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.attribute_version_comparisons (comparison_id, version_a_id, version_b_id, differences_found, comparison_summary, impact_score, compared_at, compared_by, comparison_notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.audit_log (audit_id, user_id, action, table_name, record_id, old_values, new_values, "timestamp", session_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: bulk_test_executions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.bulk_test_executions (bulk_execution_id, phase_id, execution_mode, max_concurrent_tests, total_tests, tests_started, tests_completed, tests_failed, execution_ids, status, started_at, completed_at, processing_time_ms, initiated_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: cdo_notifications; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.cdo_notifications (notification_id, cycle_id, report_id, cdo_id, lob_id, notification_sent_at, assignment_deadline, sla_hours, notification_data, responded_at, is_complete, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: cycle_reports; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.cycle_reports (cycle_id, report_id, tester_id, status, started_at, completed_at, created_at, updated_at, workflow_id) FROM stdin;
\.


--
-- Data for Name: data_owner_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_owner_assignments (assignment_id, cycle_id, report_id, attribute_id, lob_id, cdo_id, data_owner_id, assigned_by, assigned_at, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_owner_escalation_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_owner_escalation_log (email_id, cycle_id, report_id, violation_ids, escalation_level, sent_by, sent_to, cc_recipients, email_subject, email_body, sent_at, delivery_status, custom_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_owner_notifications; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_owner_notifications (notification_id, phase_id, cycle_id, report_id, data_owner_id, assigned_attributes, sample_count, submission_deadline, portal_access_url, custom_instructions, notification_sent_at, first_access_at, last_access_at, access_count, is_acknowledged, acknowledged_at, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_owner_phase_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_owner_phase_audit_log (audit_id, cycle_id, report_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_owner_sla_violations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_owner_sla_violations (violation_id, assignment_id, cycle_id, report_id, attribute_id, cdo_id, violation_detected_at, original_deadline, hours_overdue, escalation_level, last_escalation_at, is_resolved, resolved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_profiling_files; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_profiling_files (file_id, phase_id, file_name, file_path, file_size, file_format, delimiter, row_count, column_count, columns_metadata, is_validated, validation_errors, missing_attributes, uploaded_by, uploaded_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_profiling_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_profiling_phases (phase_id, cycle_id, report_id, status, data_requested_at, data_received_at, rules_generated_at, profiling_executed_at, phase_completed_at, started_by, data_requested_by, completed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_profiling_rule_versions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_profiling_rule_versions (rule_version_id, rule_id, cycle_id, report_id, attribute_id, rule_type, rule_definition, rule_description, threshold_value, threshold_type, execution_status, execution_results, issues_found, created_at, updated_at, version_number, is_latest_version, version_created_at, version_created_by, version_notes, change_reason, parent_version_id, version_status, approved_version_id, approved_at, approved_by) FROM stdin;
\.


--
-- Data for Name: data_provider_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_assignments (assignment_id, cycle_id, report_id, attribute_id, lob_id, data_provider_id, assigned_by, assigned_at, status, created_at, updated_at, cdo_id) FROM stdin;
\.


--
-- Data for Name: data_provider_escalation_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_escalation_log (email_id, cycle_id, report_id, violation_ids, escalation_level, sent_by, sent_to, cc_recipients, email_subject, email_body, sent_at, delivery_status, custom_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_provider_notifications; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_notifications (notification_id, phase_id, cycle_id, report_id, data_provider_id, assigned_attributes, sample_count, submission_deadline, portal_access_url, custom_instructions, notification_sent_at, first_access_at, last_access_at, access_count, is_acknowledged, acknowledged_at, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_provider_phase_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_phase_audit_log (audit_id, cycle_id, report_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_provider_sla_violations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_sla_violations (violation_id, assignment_id, cycle_id, report_id, attribute_id, cdo_id, violation_detected_at, original_deadline, hours_overdue, escalation_level, last_escalation_at, is_resolved, resolved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_provider_submissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_provider_submissions (submission_id, phase_id, cycle_id, report_id, data_provider_id, attribute_id, sample_record_id, submission_type, status, document_ids, database_submission_id, expected_value, confidence_level, notes, validation_status, validation_messages, validation_score, submitted_at, validated_at, last_updated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_sources; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.data_sources (data_source_id, data_source_name, database_type, database_url, database_user, database_password_encrypted, is_active, created_at, updated_at, description) FROM stdin;
\.


--
-- Data for Name: database_submissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.database_submissions (db_submission_id, phase_id, cycle_id, report_id, data_provider_id, attribute_id, sample_record_id, database_name, table_name, column_name, primary_key_column, primary_key_value, query_filter, connection_details, expected_value, confidence_level, notes, validation_status, validation_messages, connectivity_test_passed, connectivity_test_at, submitted_at, validated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: database_tests; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.database_tests (test_id, database_submission_id, sample_record_id, attribute_id, test_query, connection_timeout, query_timeout, connection_successful, query_successful, retrieved_value, record_count, execution_time_ms, error_message, connection_string_hash, database_version, actual_query_executed, query_plan, tested_at, tested_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_access_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.document_access_logs (log_id, document_id, user_id, access_type, accessed_at, ip_address, user_agent, session_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_analyses; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.document_analyses (analysis_id, submission_document_id, sample_record_id, attribute_id, analysis_prompt, expected_value, confidence_threshold, extracted_value, confidence_score, analysis_rationale, matches_expected, validation_notes, llm_model_used, llm_tokens_used, llm_response_raw, analyzed_at, analysis_duration_ms, analyzed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_extractions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.document_extractions (extraction_id, document_id, attribute_name, extracted_value, confidence_score, extraction_method, source_location, supporting_context, data_quality_flags, alternative_values, is_validated, validated_by_user_id, validation_notes, extracted_at, llm_provider, llm_model, processing_time_ms, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_revisions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.document_revisions (revision_id, test_case_id, document_id, revision_number, revision_reason, requested_by, requested_at, uploaded_by, uploaded_at, upload_notes, previous_document_id, status, reviewed_by, reviewed_at, review_notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_submissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.document_submissions (submission_id, test_case_id, data_provider_id, original_filename, stored_filename, file_path, file_size_bytes, document_type, mime_type, submission_notes, submitted_at, is_valid, validation_notes, validated_by, validated_at, created_at, updated_at, revision_number, parent_submission_id, is_current, notes, data_owner_id) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.documents (document_id, document_name, document_type, file_path, file_size, mime_type, report_id, cycle_id, uploaded_by_user_id, status, processing_notes, file_hash, is_encrypted, encryption_key_id, document_metadata, tags, description, business_date, parent_document_id, version, is_latest_version, is_confidential, access_level, uploaded_at, last_accessed_at, expires_at, is_archived, archived_at, retention_date, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: escalation_email_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.escalation_email_logs (log_id, sla_violation_id, escalation_rule_id, report_id, sent_at, sent_to_emails, email_subject, email_body, delivery_status, delivery_error, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: historical_data_owner_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.historical_data_owner_assignments (history_id, report_name, attribute_name, data_owner_id, assigned_by, cycle_id, assigned_at, completion_status, completion_time_hours, success_rating, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: historical_data_provider_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.historical_data_provider_assignments (history_id, report_name, attribute_name, data_provider_id, assigned_by, cycle_id, assigned_at, completion_status, completion_time_hours, success_rating, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: individual_samples; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.individual_samples (id, sample_id, cycle_id, report_id, primary_key_value, sample_data, generation_method, generated_at, generated_by_user_id, tester_decision, tester_decision_date, tester_decision_by_user_id, tester_notes, report_owner_decision, report_owner_feedback, is_submitted, submission_id, version_number, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.llm_audit_log (log_id, cycle_id, report_id, llm_provider, prompt_template, request_payload, response_payload, execution_time_ms, token_usage, executed_at, executed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_sample_generations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.llm_sample_generations (generation_id, set_id, cycle_id, report_id, requested_sample_size, actual_samples_generated, generation_prompt, selection_criteria, risk_focus_areas, exclude_criteria, include_edge_cases, randomization_seed, llm_model_used, generation_rationale, confidence_score, risk_coverage, estimated_testing_time, llm_metadata, generated_by, generated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: lobs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.lobs (lob_id, lob_name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: metrics_execution; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.metrics_execution (id, cycle_id, report_id, phase_name, activity_name, user_id, start_time, end_time, duration_minutes, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: metrics_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.metrics_phases (id, cycle_id, report_id, phase_name, lob_name, total_attributes, approved_attributes, attributes_with_issues, primary_keys, non_pk_attributes, total_samples, approved_samples, failed_samples, total_test_cases, completed_test_cases, passed_test_cases, failed_test_cases, total_observations, approved_observations, completion_time_minutes, on_time_completion, submissions_for_approval, data_providers_assigned, changes_to_data_providers, rfi_sent, rfi_completed, rfi_pending, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_approvals; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_approvals (approval_id, observation_id, approval_status, approval_level, approver_comments, approval_rationale, severity_assessment, impact_validation, evidence_sufficiency, regulatory_significance, requires_escalation, recommended_action, priority_level, estimated_effort, target_resolution_date, approval_criteria_met, approval_checklist, conditional_approval, conditions, approved_by, approved_at, escalated_to, escalated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_clarifications; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_clarifications (clarification_id, group_id, clarification_text, supporting_documents, requested_by_role, requested_by_user_id, requested_at, response_text, response_documents, responded_by, responded_at, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_groups; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_groups (group_id, cycle_id, report_id, attribute_id, issue_type, first_detected_at, last_updated_at, total_test_cases, total_samples, rating, approval_status, report_owner_approved, report_owner_approved_by, report_owner_approved_at, report_owner_comments, data_executive_approved, data_executive_approved_by, data_executive_approved_at, data_executive_comments, finalized, finalized_by, finalized_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_impact_assessments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_impact_assessments (assessment_id, observation_id, impact_category, impact_severity, impact_likelihood, impact_score, financial_impact_min, financial_impact_max, financial_impact_currency, regulatory_requirements_affected, regulatory_deadlines, potential_penalties, process_disruption_level, system_availability_impact, resource_requirements, resolution_time_estimate, business_disruption_duration, assessment_method, assessment_confidence, assessment_rationale, assessment_assumptions, assessed_by, assessed_at, reviewed_by, reviewed_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_management_audit_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_management_audit_logs (log_id, cycle_id, report_id, phase_id, observation_id, action, entity_type, entity_id, old_values, new_values, changes_summary, performed_by, performed_at, user_role, ip_address, user_agent, session_id, notes, execution_time_ms, business_justification, created_at, updated_at, source_test_execution_id) FROM stdin;
\.


--
-- Data for Name: observation_management_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_management_phases (phase_id, cycle_id, report_id, phase_status, planned_start_date, planned_end_date, observation_deadline, started_at, completed_at, observation_strategy, detection_criteria, approval_threshold, instructions, notes, started_by, completed_by, assigned_testers, total_observations, auto_detected_observations, manual_observations, approved_observations, rejected_observations, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_records; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_records (observation_id, phase_id, cycle_id, report_id, observation_title, observation_description, observation_type, severity, status, source_test_execution_id, source_sample_record_id, source_attribute_id, detection_method, detection_confidence, impact_description, impact_categories, financial_impact_estimate, regulatory_risk_level, affected_processes, affected_systems, evidence_documents, supporting_data, screenshots, related_observations, detected_by, assigned_to, detected_at, assigned_at, auto_detection_rules, auto_detection_score, manual_validation_required, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_records_backup; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_records_backup (observation_id, phase_id, cycle_id, report_id, observation_title, observation_description, observation_type, severity, status, source_test_execution_id, source_sample_record_id, source_attribute_id, detection_method, detection_confidence, impact_description, impact_categories, financial_impact_estimate, regulatory_risk_level, affected_processes, affected_systems, evidence_documents, supporting_data, screenshots, related_observations, detected_by, assigned_to, detected_at, assigned_at, auto_detection_rules, auto_detection_score, manual_validation_required, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_resolutions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_resolutions (resolution_id, observation_id, resolution_strategy, resolution_description, resolution_steps, success_criteria, validation_requirements, resolution_status, progress_percentage, current_step, planned_start_date, planned_completion_date, actual_start_date, actual_completion_date, assigned_resources, estimated_effort_hours, actual_effort_hours, budget_allocated, budget_spent, implemented_controls, process_changes, system_changes, documentation_updates, training_requirements, validation_tests_planned, validation_tests_completed, validation_results, effectiveness_metrics, resolution_owner, created_by, created_at, validated_by, validated_at, updated_at) FROM stdin;
\.


--
-- Data for Name: observation_versions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observation_versions (observation_version_id, observation_id, cycle_id, report_id, observation_type, severity, title, description, impact_description, affected_attributes, affected_samples, affected_lobs, resolution_status, resolution_description, resolution_date, resolved_by, group_id, is_group_parent, evidence_links, supporting_documents, tracking_metadata, created_at, updated_at, version_number, is_latest_version, version_created_at, version_created_by, version_notes, change_reason, parent_version_id, version_status, approved_version_id, approved_at, approved_by) FROM stdin;
\.


--
-- Data for Name: observations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.observations (observation_id, cycle_id, report_id, attribute_id, observation_type, description, impact_level, samples_impacted, status, tester_comments, report_owner_comments, resolution_rationale, resolved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: permission_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.permission_audit_log (audit_id, action_type, target_type, target_id, permission_id, role_id, performed_by, performed_at, reason, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.permissions (permission_id, resource, action, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: profiling_results; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.profiling_results (result_id, phase_id, rule_id, attribute_id, execution_status, execution_time_ms, executed_at, passed_count, failed_count, total_count, pass_rate, result_summary, failed_records, result_details, quality_impact, severity, has_anomaly, anomaly_description, anomaly_marked_by, anomaly_marked_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: profiling_rules; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.profiling_rules (rule_id, phase_id, attribute_id, rule_name, rule_type, rule_description, rule_code, rule_parameters, llm_provider, llm_rationale, regulatory_reference, status, approved_by, approved_at, approval_notes, is_executable, execution_order, created_at, updated_at, version_number, is_current_version, business_key, version_created_at, version_created_by, effective_from, effective_to, rejected_by, rejected_at, rejection_reason, rejection_notes, revision_notes, cycle_id, report_id, created_by, updated_by, rule_logic, expected_result, severity) FROM stdin;
\.


--
-- Data for Name: regulatory_data_dictionary; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.regulatory_data_dictionary (dict_id, report_name, schedule_name, line_item_number, line_item_name, technical_line_item_name, mdrm, description, static_or_dynamic, mandatory_or_optional, format_specification, num_reports_schedules_used, other_schedule_reference, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: report_attributes; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.report_attributes (attribute_id, cycle_id, report_id, attribute_name, description, data_type, mandatory_flag, cde_flag, historical_issues_flag, is_scoped, llm_generated, llm_rationale, tester_notes, created_at, updated_at, validation_rules, typical_source_documents, keywords_to_look_for, testing_approach, risk_score, llm_risk_rationale, is_primary_key, primary_key_order, approval_status, master_attribute_id, version_number, is_latest_version, is_active, version_notes, change_reason, replaced_attribute_id, version_created_at, version_created_by, approved_at, approved_by, archived_at, archived_by, line_item_number, technical_line_item_name, mdrm) FROM stdin;
\.


--
-- Data for Name: report_owner_assignment_history; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.report_owner_assignment_history (history_id, assignment_id, changed_by, changed_at, field_changed, old_value, new_value, change_reason, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: report_owner_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.report_owner_assignments (assignment_id, cycle_id, report_id, phase_name, assignment_type, title, description, assigned_to, assigned_by, assigned_at, due_date, started_at, completed_at, status, priority, completed_by, completion_notes, completion_attachments, escalated, escalated_at, escalation_reason, assignment_metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: report_owner_executives; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.report_owner_executives (executive_id, report_owner_id) FROM stdin;
\.


--
-- Data for Name: report_owner_scoping_reviews; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.report_owner_scoping_reviews (review_id, submission_id, cycle_id, report_id, approval_status, review_comments, requested_changes, resource_impact_assessment, risk_coverage_assessment, reviewed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: reports; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: request_info_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.request_info_audit_log (audit_id, cycle_id, report_id, phase_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, session_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: request_info_audit_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.request_info_audit_logs (log_id, cycle_id, report_id, phase_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: request_info_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.request_info_phases (phase_id, cycle_id, report_id, phase_status, planned_start_date, planned_end_date, submission_deadline, reminder_schedule, instructions, started_at, started_by, completed_at, completed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: resource_permissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.resource_permissions (resource_permission_id, user_id, resource_type, resource_id, permission_id, granted, granted_by, granted_at, expires_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: resources; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.resources (resource_id, resource_name, display_name, description, resource_type, parent_resource_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: role_hierarchy; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.role_hierarchy (parent_role_id, child_role_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_approval_history; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_approval_history (approval_id, set_id, approval_step, decision, approved_by, approved_at, feedback, requested_changes, conditional_approval, approval_conditions, previous_status, new_status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_audit_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_audit_logs (id, sample_id, submission_id, action, action_details, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: sample_feedback; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_feedback (id, sample_id, submission_id, feedback_type, feedback_text, severity, is_blocking, is_resolved, resolved_at, resolved_by_user_id, resolution_notes, created_by_user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_records; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_records (record_id, set_id, sample_identifier, primary_key_value, sample_data, risk_score, validation_status, validation_score, selection_rationale, data_source_info, created_at, updated_at, approval_status, approved_by, approved_at, rejection_reason, change_requests) FROM stdin;
\.


--
-- Data for Name: sample_selection_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_selection_audit_log (audit_id, cycle_id, report_id, set_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, session_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_selection_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_selection_phases (phase_id, cycle_id, report_id, phase_status, planned_start_date, planned_end_date, actual_start_date, actual_end_date, target_sample_size, sampling_methodology, sampling_criteria, llm_generation_enabled, llm_provider, llm_model, llm_confidence_threshold, manual_upload_enabled, upload_template_url, samples_generated, samples_validated, samples_approved, notes, created_at, updated_at, created_by, updated_by, id) FROM stdin;
\.


--
-- Data for Name: sample_sets; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_sets (set_id, cycle_id, report_id, set_name, description, generation_method, sample_type, status, target_sample_size, actual_sample_size, created_by, created_at, approved_by, approved_at, approval_notes, generation_rationale, selection_criteria, quality_score, sample_metadata, updated_at, master_set_id, version_number, is_latest_version, is_active, version_notes, change_reason, replaced_set_id, version_created_at, version_created_by, archived_at, archived_by) FROM stdin;
\.


--
-- Data for Name: sample_submission_items; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_submission_items (id, submission_id, sample_id, tester_decision, primary_key_value, sample_data_snapshot, created_at) FROM stdin;
\.


--
-- Data for Name: sample_submissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_submissions (id, submission_id, cycle_id, report_id, version_number, submitted_at, submitted_by_user_id, submission_notes, status, reviewed_at, reviewed_by_user_id, review_decision, review_feedback, is_official_version, total_samples, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_upload_history; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_upload_history (upload_id, set_id, upload_method, original_filename, file_size_bytes, total_rows, valid_rows, invalid_rows, primary_key_column, data_mapping, validation_rules_applied, data_quality_score, upload_summary, processing_time_ms, uploaded_by, uploaded_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_validation_issues; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_validation_issues (issue_id, validation_id, record_id, issue_type, severity, field_name, issue_description, suggested_fix, is_resolved, resolved_at, resolved_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sample_validation_results; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sample_validation_results (validation_id, set_id, validation_type, validation_rules, overall_status, total_samples, valid_samples, invalid_samples, warning_samples, overall_quality_score, validation_summary, recommendations, validated_by, validated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: samples; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.samples (sample_id, cycle_id, report_id, primary_key_name, primary_key_value, sample_data, llm_rationale, tester_rationale, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scoping_audit_log; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.scoping_audit_log (audit_id, cycle_id, report_id, action, performed_by, details, previous_values, new_values, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scoping_decision_versions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.scoping_decision_versions (decision_version_id, decision_id, cycle_id, report_id, attribute_id, is_in_scope, scope_reason, testing_approach, sample_size_override, special_instructions, risk_level, risk_factors, assigned_lobs, depends_on_attributes, created_at, updated_at, version_number, is_latest_version, version_created_at, version_created_by, version_notes, change_reason, parent_version_id, version_status, approved_version_id, approved_at, approved_by) FROM stdin;
\.


--
-- Data for Name: scoping_submissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.scoping_submissions (submission_id, cycle_id, report_id, submission_notes, total_attributes, scoped_attributes, skipped_attributes, submitted_by, created_at, updated_at, version, previous_version_id, changes_from_previous, revision_reason) FROM stdin;
\.


--
-- Data for Name: sla_configurations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sla_configurations (sla_config_id, sla_type, sla_hours, warning_hours, escalation_enabled, is_active, business_hours_only, weekend_excluded, auto_escalate_on_breach, escalation_interval_hours, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sla_escalation_rules; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sla_escalation_rules (escalation_rule_id, sla_config_id, escalation_level, escalation_order, escalate_to_role, escalate_to_user_id, hours_after_breach, email_template_subject, email_template_body, include_managers, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sla_violation_tracking; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.sla_violation_tracking (violation_id, sla_config_id, report_id, cycle_id, started_at, due_date, warning_date, completed_at, is_violated, violated_at, violation_hours, current_escalation_level, escalation_count, last_escalated_at, is_resolved, resolved_at, resolution_notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: submission_documents; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.submission_documents (document_id, phase_id, cycle_id, report_id, data_provider_id, document_type, original_filename, stored_filename, file_path, file_size, file_hash, mime_type, sample_records, attributes, description, notes, validation_status, validation_messages, validation_score, uploaded_at, validated_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: submission_reminders; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.submission_reminders (reminder_id, phase_id, data_provider_id, reminder_type, custom_message, days_before_deadline, scheduled_at, sent_at, delivery_status, delivery_attempts, error_message, viewed_at, responded_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: submission_validations; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.submission_validations (validation_id, submission_id, validation_type, status, message, severity, recommendation, rule_applied, validated_at, validated_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_cases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_cases (test_case_id, phase_id, cycle_id, report_id, attribute_id, sample_id, sample_identifier, data_owner_id, assigned_by, assigned_at, attribute_name, primary_key_attributes, expected_evidence_type, special_instructions, status, submission_deadline, submitted_at, acknowledged_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_comparisons; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_comparisons (comparison_id, execution_ids, comparison_criteria, comparison_results, consistency_score, differences_found, recommendations, analysis_method_used, statistical_metrics, compared_at, comparison_duration_ms, compared_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_cycles; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_cycles (cycle_id, cycle_name, description, test_manager_id, created_at, updated_at, start_date, end_date, status, workflow_id) FROM stdin;
\.


--
-- Data for Name: test_execution_audit_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_execution_audit_logs (log_id, cycle_id, report_id, phase_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, execution_time_ms, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_execution_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_execution_phases (phase_id, cycle_id, report_id, phase_status, planned_start_date, planned_end_date, testing_deadline, test_strategy, instructions, started_at, started_by, completed_at, completed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_execution_versions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_execution_versions (execution_version_id, execution_id, cycle_id, report_id, attribute_id, sample_id, test_results, document_results, database_results, overall_result, confidence_score, issues_identified, requires_resubmission, resubmission_reason, evidence_files, screenshots, created_at, updated_at, version_number, is_latest_version, version_created_at, version_created_by, version_notes, change_reason, parent_version_id, version_status, approved_version_id, approved_at, approved_by) FROM stdin;
\.


--
-- Data for Name: test_executions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_executions (execution_id, cycle_id, report_id, sample_id, attribute_id, test_run_number, source_value, expected_value, test_result, discrepancy_details, data_source_type, data_source_id, document_id, table_name, column_name, executed_at, executed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: test_report_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_report_phases (created_at, updated_at, phase_id, cycle_id, report_id, started_at, completed_at, include_executive_summary, include_phase_artifacts, include_detailed_observations, include_metrics_dashboard, report_title, report_period, regulatory_references, final_report_document_id, report_generated_at, report_approved_by, status) FROM stdin;
\.


--
-- Data for Name: test_report_sections; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_report_sections (created_at, updated_at, section_id, phase_id, section_name, section_order, section_type, content_text, content_data, artifacts, metrics_summary) FROM stdin;
\.


--
-- Data for Name: test_result_reviews; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.test_result_reviews (review_id, execution_id, reviewer_id, review_result, reviewer_comments, recommended_action, requires_retest, accuracy_score, completeness_score, consistency_score, overall_score, review_criteria_used, supporting_evidence, reviewed_at, review_duration_ms, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tester_scoping_decisions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.tester_scoping_decisions (decision_id, cycle_id, report_id, attribute_id, recommendation_id, decision, final_scoping, tester_rationale, override_reason, decided_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: testing_execution_audit_logs; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.testing_execution_audit_logs (log_id, cycle_id, report_id, phase_id, action, entity_type, entity_id, performed_by, performed_at, old_values, new_values, notes, ip_address, user_agent, execution_time_ms, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: testing_execution_phases; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.testing_execution_phases (phase_id, cycle_id, report_id, phase_status, planned_start_date, planned_end_date, testing_deadline, test_strategy, instructions, started_at, started_by, completed_at, completed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: testing_test_executions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.testing_test_executions (execution_id, phase_id, cycle_id, report_id, sample_record_id, attribute_id, test_type, analysis_method, priority, custom_instructions, status, result, confidence_score, execution_summary, error_message, document_analysis_id, database_test_id, started_at, completed_at, processing_time_ms, assigned_tester_id, created_at, updated_at, data_source_id, sample_id, executed_by) FROM stdin;
\.


--
-- Data for Name: universal_assignment_history; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.universal_assignment_history (history_id, assignment_id, changed_by_user_id, changed_at, action, field_changed, old_value, new_value, change_reason, change_metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: universal_assignments; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.universal_assignments (assignment_id, assignment_type, from_role, to_role, from_user_id, to_user_id, title, description, task_instructions, context_type, context_data, status, priority, assigned_at, due_date, acknowledged_at, started_at, completed_at, completed_by_user_id, completion_notes, completion_data, completion_attachments, requires_approval, approval_role, approved_by_user_id, approved_at, approval_notes, escalated, escalated_at, escalated_to_user_id, escalation_reason, delegated_to_user_id, delegated_at, delegation_reason, created_at, updated_at, assignment_metadata, workflow_step, parent_assignment_id) FROM stdin;
\.


--
-- Data for Name: user_permissions; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.user_permissions (user_id, permission_id, granted, granted_by, granted_at, expires_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.user_roles (user_id, role_id, assigned_by, assigned_at, expires_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.users (user_id, first_name, last_name, email, phone, role, lob_id, is_active, hashed_password, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: version_history; Type: TABLE DATA; Schema: public; Owner: synapse_user
--

COPY public.version_history (id, entity_type, entity_id, entity_name, version_number, change_type, change_reason, changed_by, changed_at, change_details, cycle_id, report_id, phase_name, created_at, updated_at) FROM stdin;
\.


--
-- Name: attribute_lob_assignments_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.attribute_lob_assignments_assignment_id_seq', 1, false);


--
-- Name: attribute_profiling_scores_score_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.attribute_profiling_scores_score_id_seq', 1, false);


--
-- Name: attribute_scoping_recommendations_recommendation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.attribute_scoping_recommendations_recommendation_id_seq', 1, false);


--
-- Name: attribute_version_change_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.attribute_version_change_logs_log_id_seq', 1, false);


--
-- Name: attribute_version_comparisons_comparison_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.attribute_version_comparisons_comparison_id_seq', 1, false);


--
-- Name: audit_log_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.audit_log_audit_id_seq', 1, false);


--
-- Name: bulk_test_executions_bulk_execution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.bulk_test_executions_bulk_execution_id_seq', 1, false);


--
-- Name: cdo_notifications_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.cdo_notifications_notification_id_seq', 1, false);


--
-- Name: data_owner_assignments_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_owner_assignments_assignment_id_seq', 1, false);


--
-- Name: data_owner_escalation_log_email_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_owner_escalation_log_email_id_seq', 1, false);


--
-- Name: data_owner_phase_audit_log_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_owner_phase_audit_log_audit_id_seq', 1, false);


--
-- Name: data_owner_sla_violations_violation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_owner_sla_violations_violation_id_seq', 1, false);


--
-- Name: data_profiling_files_file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_profiling_files_file_id_seq', 1, false);


--
-- Name: data_profiling_phases_phase_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_profiling_phases_phase_id_seq', 1, false);


--
-- Name: data_provider_assignments_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_provider_assignments_assignment_id_seq', 1, false);


--
-- Name: data_provider_escalation_log_email_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_provider_escalation_log_email_id_seq', 1, false);


--
-- Name: data_provider_phase_audit_log_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_provider_phase_audit_log_audit_id_seq', 1, false);


--
-- Name: data_provider_sla_violations_violation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_provider_sla_violations_violation_id_seq', 1, false);


--
-- Name: data_provider_submissions_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_provider_submissions_submission_id_seq', 1, false);


--
-- Name: data_sources_data_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.data_sources_data_source_id_seq', 1, false);


--
-- Name: database_tests_test_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.database_tests_test_id_seq', 1, false);


--
-- Name: document_access_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.document_access_logs_log_id_seq', 1, false);


--
-- Name: document_analyses_analysis_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.document_analyses_analysis_id_seq', 1, false);


--
-- Name: document_extractions_extraction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.document_extractions_extraction_id_seq', 1, false);


--
-- Name: document_revisions_revision_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.document_revisions_revision_id_seq', 1, false);


--
-- Name: documents_document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.documents_document_id_seq', 1, false);


--
-- Name: escalation_email_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.escalation_email_logs_log_id_seq', 1, false);


--
-- Name: historical_data_owner_assignments_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.historical_data_owner_assignments_history_id_seq', 1, false);


--
-- Name: historical_data_provider_assignments_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.historical_data_provider_assignments_history_id_seq', 1, false);


--
-- Name: individual_samples_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.individual_samples_id_seq', 1, false);


--
-- Name: llm_audit_log_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.llm_audit_log_log_id_seq', 1, false);


--
-- Name: lobs_lob_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.lobs_lob_id_seq', 1, false);


--
-- Name: observation_approvals_approval_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_approvals_approval_id_seq', 1, false);


--
-- Name: observation_clarifications_clarification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_clarifications_clarification_id_seq', 1, false);


--
-- Name: observation_groups_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_groups_group_id_seq', 1, false);


--
-- Name: observation_impact_assessments_assessment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_impact_assessments_assessment_id_seq', 1, false);


--
-- Name: observation_management_audit_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_management_audit_logs_log_id_seq', 1, false);


--
-- Name: observation_records_observation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_records_observation_id_seq', 1, false);


--
-- Name: observation_records_observation_id_seq1; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_records_observation_id_seq1', 1, false);


--
-- Name: observation_resolutions_resolution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observation_resolutions_resolution_id_seq', 1, false);


--
-- Name: observations_observation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.observations_observation_id_seq', 1, false);


--
-- Name: permission_audit_log_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.permission_audit_log_audit_id_seq', 1, false);


--
-- Name: permissions_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.permissions_permission_id_seq', 1, false);


--
-- Name: profiling_results_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.profiling_results_result_id_seq', 1, false);


--
-- Name: profiling_rules_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.profiling_rules_rule_id_seq', 1, false);


--
-- Name: regulatory_data_dictionary_dict_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.regulatory_data_dictionary_dict_id_seq', 1, false);


--
-- Name: report_attributes_attribute_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.report_attributes_attribute_id_seq', 1, false);


--
-- Name: report_owner_assignment_history_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.report_owner_assignment_history_history_id_seq', 1, false);


--
-- Name: report_owner_assignments_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.report_owner_assignments_assignment_id_seq', 1, false);


--
-- Name: report_owner_scoping_reviews_review_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.report_owner_scoping_reviews_review_id_seq', 1, false);


--
-- Name: reports_report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.reports_report_id_seq', 1, false);


--
-- Name: request_info_audit_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.request_info_audit_logs_log_id_seq', 1, false);


--
-- Name: resource_permissions_resource_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.resource_permissions_resource_permission_id_seq', 1, false);


--
-- Name: resources_resource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.resources_resource_id_seq', 1, false);


--
-- Name: roles_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.roles_role_id_seq', 1, false);


--
-- Name: sample_audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sample_audit_logs_id_seq', 1, false);


--
-- Name: sample_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sample_feedback_id_seq', 1, false);


--
-- Name: sample_selection_phases_phase_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sample_selection_phases_phase_id_seq', 1, false);


--
-- Name: sample_submission_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sample_submission_items_id_seq', 1, false);


--
-- Name: sample_submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sample_submissions_id_seq', 1, false);


--
-- Name: samples_sample_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.samples_sample_id_seq', 1, false);


--
-- Name: scoping_audit_log_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.scoping_audit_log_audit_id_seq', 1, false);


--
-- Name: scoping_submissions_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.scoping_submissions_submission_id_seq', 1, false);


--
-- Name: sla_configurations_sla_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sla_configurations_sla_config_id_seq', 1, false);


--
-- Name: sla_escalation_rules_escalation_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sla_escalation_rules_escalation_rule_id_seq', 1, false);


--
-- Name: sla_violation_tracking_violation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.sla_violation_tracking_violation_id_seq', 1, false);


--
-- Name: submission_documents_document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.submission_documents_document_id_seq', 1, false);


--
-- Name: test_comparisons_comparison_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_comparisons_comparison_id_seq', 1, false);


--
-- Name: test_cycles_cycle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_cycles_cycle_id_seq', 1, false);


--
-- Name: test_execution_audit_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_execution_audit_logs_log_id_seq', 1, false);


--
-- Name: test_executions_execution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_executions_execution_id_seq', 1, false);


--
-- Name: test_report_sections_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_report_sections_section_id_seq', 1, false);


--
-- Name: test_result_reviews_review_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.test_result_reviews_review_id_seq', 1, false);


--
-- Name: tester_scoping_decisions_decision_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.tester_scoping_decisions_decision_id_seq', 1, false);


--
-- Name: testing_execution_audit_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.testing_execution_audit_logs_log_id_seq', 1, false);


--
-- Name: testing_test_executions_execution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.testing_test_executions_execution_id_seq', 1, false);


--
-- Name: universal_assignment_history_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.universal_assignment_history_history_id_seq', 1, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: synapse_user
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

