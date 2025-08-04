-- SynapseDTE Complete Database Schema
-- Generated: 2025-07-29 22:24:28
-- Database: synapse_dt
-- Total Tables: 108 (including workflow/temporal tables)
-- 
-- This file includes:
-- - All table definitions
-- - All ENUM types
-- - All indexes
-- - All constraints
-- - All sequences
-- - All views
-- - All functions/procedures
--
-- Usage: psql -U postgres -f 01_complete_schema.sql

--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

-- Started on 2025-07-29 22:24:27 EDT

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

DROP DATABASE IF EXISTS synapse_dt;
--
-- TOC entry 6164 (class 1262 OID 31255)
-- Name: synapse_dt; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE synapse_dt WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'C';


\connect synapse_dt

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
-- TOC entry 3 (class 3079 OID 116223)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- TOC entry 6165 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- TOC entry 2 (class 3079 OID 116212)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 6166 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 1504 (class 1247 OID 37133)
-- Name: activity_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.activity_status_enum AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'REVISION_REQUESTED',
    'BLOCKED',
    'SKIPPED'
);


--
-- TOC entry 1495 (class 1247 OID 37103)
-- Name: activity_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.activity_type_enum AS ENUM (
    'START',
    'TASK',
    'REVIEW',
    'APPROVAL',
    'COMPLETE',
    'CUSTOM'
);


--
-- TOC entry 1492 (class 1247 OID 37058)
-- Name: activitystatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.activitystatus AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'REVISION_REQUESTED',
    'BLOCKED',
    'SKIPPED'
);


--
-- TOC entry 1489 (class 1247 OID 37044)
-- Name: activitytype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.activitytype AS ENUM (
    'START',
    'TASK',
    'REVIEW',
    'APPROVAL',
    'COMPLETE',
    'CUSTOM'
);


--
-- TOC entry 1096 (class 1247 OID 31386)
-- Name: approval_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status_enum AS ENUM (
    'Pending',
    'Approved',
    'Declined',
    'Needs Revision'
);


--
-- TOC entry 1450 (class 1247 OID 36460)
-- Name: assignment_priority_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assignment_priority_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical'
);


--
-- TOC entry 1114 (class 1247 OID 31446)
-- Name: assignment_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assignment_status_enum AS ENUM (
    'Assigned',
    'In Progress',
    'Completed',
    'Overdue'
);


--
-- TOC entry 1447 (class 1247 OID 36446)
-- Name: assignment_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assignment_type_enum AS ENUM (
    'Data Upload Request',
    'File Review',
    'Documentation Review',
    'Approval Required',
    'Information Request',
    'Phase Review'
);


--
-- TOC entry 1063 (class 1247 OID 31270)
-- Name: cycle_report_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.cycle_report_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


--
-- TOC entry 1594 (class 1247 OID 116270)
-- Name: cycle_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.cycle_status_enum AS ENUM (
    'Draft',
    'Planning',
    'In Progress',
    'Review',
    'Completed',
    'Cancelled'
);


--
-- TOC entry 1145 (class 1247 OID 122769)
-- Name: data_source_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.data_source_type_enum AS ENUM (
    'file_upload',
    'database_direct',
    'api'
);


--
-- TOC entry 1084 (class 1247 OID 31348)
-- Name: data_type_enum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1540 (class 1247 OID 115678)
-- Name: datasourcetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.datasourcetype AS ENUM (
    'POSTGRESQL',
    'MYSQL',
    'ORACLE',
    'SQLSERVER',
    'SNOWFLAKE',
    'BIGQUERY',
    'REDSHIFT',
    'FILE'
);


--
-- TOC entry 1537 (class 1247 OID 123166)
-- Name: decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.decision_enum AS ENUM (
    'approved',
    'rejected',
    'request_changes'
);


--
-- TOC entry 1075 (class 1247 OID 31318)
-- Name: document_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.document_type_enum AS ENUM (
    'Source Document',
    'Supporting Evidence',
    'Data Extract',
    'Query Result',
    'Other'
);


--
-- TOC entry 1099 (class 1247 OID 31396)
-- Name: escalation_level_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.escalation_level_enum AS ENUM (
    'None',
    'Level 1',
    'Level 2',
    'Level 3'
);


--
-- TOC entry 1135 (class 1247 OID 31512)
-- Name: escalationlevel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.escalationlevel AS ENUM (
    'LEVEL_1',
    'LEVEL_2',
    'LEVEL_3',
    'LEVEL_4'
);


--
-- TOC entry 1187 (class 1247 OID 125249)
-- Name: evidence_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.evidence_status_enum AS ENUM (
    'pending',
    'approved',
    'rejected',
    'request_changes'
);


--
-- TOC entry 1126 (class 1247 OID 31476)
-- Name: impact_level_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.impact_level_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical'
);


--
-- TOC entry 1158 (class 1247 OID 31616)
-- Name: impactcategoryenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.impactcategoryenum AS ENUM (
    'FINANCIAL',
    'REGULATORY',
    'OPERATIONAL',
    'REPUTATIONAL',
    'STRATEGIC',
    'CUSTOMER'
);


--
-- TOC entry 1411 (class 1247 OID 119090)
-- Name: information_security_classification_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.information_security_classification_enum AS ENUM (
    'HRCI',
    'Confidential',
    'Proprietary',
    'Public',
    'Internal',
    'Restricted'
);


--
-- TOC entry 1087 (class 1247 OID 31364)
-- Name: mandatory_flag_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.mandatory_flag_enum AS ENUM (
    'Mandatory',
    'Conditional',
    'Optional'
);


--
-- TOC entry 1129 (class 1247 OID 31486)
-- Name: observation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.observation_status_enum AS ENUM (
    'Open',
    'In Review',
    'Approved',
    'Rejected',
    'Resolved'
);


--
-- TOC entry 1123 (class 1247 OID 31470)
-- Name: observation_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.observation_type_enum AS ENUM (
    'Data Quality',
    'Documentation'
);


--
-- TOC entry 1372 (class 1247 OID 35298)
-- Name: observationapprovalstatusenum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1369 (class 1247 OID 35291)
-- Name: observationratingenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.observationratingenum AS ENUM (
    'HIGH',
    'MEDIUM',
    'LOW'
);


--
-- TOC entry 1152 (class 1247 OID 31584)
-- Name: observationseverityenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.observationseverityenum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW',
    'INFORMATIONAL'
);


--
-- TOC entry 1155 (class 1247 OID 31596)
-- Name: observationstatusenum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1149 (class 1247 OID 31566)
-- Name: observationtypeenum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1069 (class 1247 OID 31294)
-- Name: phase_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.phase_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Submitted',
    'Pending Approval',
    'Complete'
);


--
-- TOC entry 1603 (class 1247 OID 119318)
-- Name: profilingmode; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.profilingmode AS ENUM (
    'full_scan',
    'sample_based',
    'incremental',
    'streaming'
);


--
-- TOC entry 1402 (class 1247 OID 35640)
-- Name: profilingrulestatus; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1399 (class 1247 OID 35624)
-- Name: profilingruletype; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1558 (class 1247 OID 119294)
-- Name: profilingsourcetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.profilingsourcetype AS ENUM (
    'file_upload',
    'database_direct',
    'api',
    'streaming'
);


--
-- TOC entry 1600 (class 1247 OID 119304)
-- Name: profilingstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.profilingstatus AS ENUM (
    'pending',
    'queued',
    'running',
    'completed',
    'failed',
    'cancelled'
);


--
-- TOC entry 1546 (class 1247 OID 115706)
-- Name: profilingstrategy; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.profilingstrategy AS ENUM (
    'full_scan',
    'sampling',
    'streaming',
    'partitioned',
    'incremental'
);


--
-- TOC entry 1429 (class 1247 OID 120477)
-- Name: report_owner_decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.report_owner_decision_enum AS ENUM (
    'Approved',
    'Rejected',
    'Pending'
);


--
-- TOC entry 1591 (class 1247 OID 116261)
-- Name: report_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.report_status_enum AS ENUM (
    'Active',
    'Inactive',
    'Under Review',
    'Archived'
);


--
-- TOC entry 1324 (class 1247 OID 34311)
-- Name: request_info_phase_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.request_info_phase_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


--
-- TOC entry 1161 (class 1247 OID 31630)
-- Name: resolutionstatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resolutionstatusenum AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'PENDING_VALIDATION',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);


--
-- TOC entry 1453 (class 1247 OID 119100)
-- Name: review_action_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.review_action_type_enum AS ENUM (
    'submit_for_review',
    'approve',
    'reject',
    'request_revision',
    'revise',
    'auto_approve'
);


--
-- TOC entry 1146 (class 1247 OID 31554)
-- Name: review_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.review_status_enum AS ENUM (
    'Pending',
    'In Review',
    'Approved',
    'Rejected',
    'Requires Revision'
);


--
-- TOC entry 1531 (class 1247 OID 119188)
-- Name: reviewactiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reviewactiontype AS ENUM (
    'submit_for_review',
    'approve',
    'reject',
    'request_revision',
    'revise',
    'auto_approve'
);


--
-- TOC entry 1528 (class 1247 OID 119178)
-- Name: reviewstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reviewstatus AS ENUM (
    'pending',
    'approved',
    'rejected',
    'needs_revision'
);


--
-- TOC entry 1612 (class 1247 OID 122660)
-- Name: rule_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.rule_status_enum AS ENUM (
    'pending',
    'submitted',
    'approved',
    'rejected'
);


--
-- TOC entry 1579 (class 1247 OID 122632)
-- Name: rule_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.rule_type_enum AS ENUM (
    'completeness',
    'validity',
    'accuracy',
    'consistency',
    'uniqueness',
    'format'
);


--
-- TOC entry 1549 (class 1247 OID 115718)
-- Name: rulecategory; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.rulecategory AS ENUM (
    'completeness',
    'validity',
    'accuracy',
    'consistency',
    'uniqueness',
    'timeliness',
    'anomaly',
    'custom'
);


--
-- TOC entry 1321 (class 1247 OID 33987)
-- Name: sample_approval_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_approval_status_enum AS ENUM (
    'Pending',
    'Approved',
    'Rejected',
    'Needs Changes'
);


--
-- TOC entry 1167 (class 1247 OID 124851)
-- Name: sample_category_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_category_enum AS ENUM (
    'clean',
    'anomaly',
    'boundary'
);


--
-- TOC entry 1630 (class 1247 OID 123194)
-- Name: sample_decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_decision_enum AS ENUM (
    'approved',
    'rejected',
    'pending'
);


--
-- TOC entry 1102 (class 1247 OID 31406)
-- Name: sample_generation_method_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_generation_method_enum AS ENUM (
    'LLM Generated',
    'Manual Upload',
    'Hybrid'
);


--
-- TOC entry 1060 (class 1247 OID 124789)
-- Name: sample_selection_version_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_selection_version_status_enum AS ENUM (
    'draft',
    'pending_approval',
    'approved',
    'rejected',
    'superseded'
);


--
-- TOC entry 1170 (class 1247 OID 124858)
-- Name: sample_source_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_source_enum AS ENUM (
    'tester',
    'llm',
    'manual',
    'carried_forward'
);


--
-- TOC entry 1108 (class 1247 OID 31424)
-- Name: sample_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_status_enum AS ENUM (
    'Draft',
    'Pending Approval',
    'Approved',
    'Rejected',
    'Revision Required'
);


--
-- TOC entry 1105 (class 1247 OID 31414)
-- Name: sample_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_type_enum AS ENUM (
    'Population Sample',
    'Targeted Sample',
    'Exception Sample',
    'Control Sample'
);


--
-- TOC entry 1111 (class 1247 OID 31436)
-- Name: sample_validation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sample_validation_status_enum AS ENUM (
    'Valid',
    'Invalid',
    'Warning',
    'Needs Review'
);


--
-- TOC entry 1555 (class 1247 OID 115754)
-- Name: samplecategory; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.samplecategory AS ENUM (
    'normal',
    'anomaly',
    'boundary_high',
    'boundary_low',
    'outlier',
    'edge_case',
    'high_risk'
);


--
-- TOC entry 1552 (class 1247 OID 115736)
-- Name: samplingstrategy; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.samplingstrategy AS ENUM (
    'random',
    'stratified',
    'anomaly_based',
    'boundary',
    'risk_based',
    'systematic',
    'cluster',
    'hybrid'
);


--
-- TOC entry 1354 (class 1247 OID 123042)
-- Name: scoping_attribute_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_attribute_status_enum AS ENUM (
    'pending',
    'submitted',
    'approved',
    'rejected',
    'needs_revision'
);


--
-- TOC entry 1093 (class 1247 OID 31378)
-- Name: scoping_decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_decision_enum AS ENUM (
    'Accept',
    'Decline',
    'Override'
);


--
-- TOC entry 1090 (class 1247 OID 31372)
-- Name: scoping_recommendation_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_recommendation_enum AS ENUM (
    'Test',
    'Skip'
);


--
-- TOC entry 1357 (class 1247 OID 123054)
-- Name: scoping_report_owner_decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_report_owner_decision_enum AS ENUM (
    'approved',
    'rejected',
    'pending',
    'needs_revision'
);


--
-- TOC entry 1351 (class 1247 OID 123034)
-- Name: scoping_tester_decision_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_tester_decision_enum AS ENUM (
    'accept',
    'decline',
    'override'
);


--
-- TOC entry 1312 (class 1247 OID 123001)
-- Name: scoping_version_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoping_version_status_enum AS ENUM (
    'draft',
    'pending_approval',
    'approved',
    'rejected',
    'superseded'
);


--
-- TOC entry 1597 (class 1247 OID 116284)
-- Name: security_classification_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.security_classification_enum AS ENUM (
    'Public',
    'Internal',
    'Confidential',
    'Restricted',
    'HRCI'
);


--
-- TOC entry 1543 (class 1247 OID 115696)
-- Name: securityclassification; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.securityclassification AS ENUM (
    'HRCI',
    'Confidential',
    'Proprietary',
    'Public'
);


--
-- TOC entry 1582 (class 1247 OID 122644)
-- Name: severity_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.severity_enum AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);


--
-- TOC entry 1132 (class 1247 OID 31498)
-- Name: slatype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.slatype AS ENUM (
    'DATA_PROVIDER_IDENTIFICATION',
    'DATA_PROVIDER_RESPONSE',
    'DOCUMENT_SUBMISSION',
    'TESTING_COMPLETION',
    'OBSERVATION_RESPONSE',
    'ISSUE_RESOLUTION'
);


--
-- TOC entry 1381 (class 1247 OID 35476)
-- Name: steptype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.steptype AS ENUM (
    'PHASE',
    'ACTIVITY',
    'TRANSITION',
    'DECISION',
    'PARALLEL_BRANCH',
    'SUB_WORKFLOW'
);


--
-- TOC entry 1072 (class 1247 OID 31304)
-- Name: submission_status_enum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1081 (class 1247 OID 31340)
-- Name: submission_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.submission_type_enum AS ENUM (
    'Document',
    'Database',
    'Mixed'
);


--
-- TOC entry 1327 (class 1247 OID 34318)
-- Name: test_case_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.test_case_status_enum AS ENUM (
    'Pending',
    'Submitted',
    'Overdue'
);


--
-- TOC entry 1465 (class 1247 OID 36638)
-- Name: universal_assignment_priority_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.universal_assignment_priority_enum AS ENUM (
    'Low',
    'Medium',
    'High',
    'Critical',
    'Urgent'
);


--
-- TOC entry 1462 (class 1247 OID 36614)
-- Name: universal_assignment_status_enum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1456 (class 1247 OID 36538)
-- Name: universal_assignment_type_enum; Type: TYPE; Schema: public; Owner: -
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
    'System Configuration',
    'data_owner_identification'
);


--
-- TOC entry 1459 (class 1247 OID 36592)
-- Name: universal_context_type_enum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1510 (class 1247 OID 112975)
-- Name: user_role_enum; Type: TYPE; Schema: public; Owner: -
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


--
-- TOC entry 1078 (class 1247 OID 31330)
-- Name: validation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.validation_status_enum AS ENUM (
    'Pending',
    'Passed',
    'Failed',
    'Warning'
);


--
-- TOC entry 1279 (class 1247 OID 33384)
-- Name: version_change_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.version_change_type_enum AS ENUM (
    'created',
    'updated',
    'approved',
    'rejected',
    'archived',
    'restored'
);


--
-- TOC entry 1573 (class 1247 OID 122620)
-- Name: version_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.version_status_enum AS ENUM (
    'draft',
    'pending_approval',
    'approved',
    'rejected',
    'superseded'
);


--
-- TOC entry 1066 (class 1247 OID 31278)
-- Name: workflow_phase_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.workflow_phase_enum AS ENUM (
    'Planning',
    'Data Profiling',
    'Scoping',
    'Data Provider ID',
    'Data Owner Identification',
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


--
-- TOC entry 1273 (class 1247 OID 33368)
-- Name: workflow_phase_state_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.workflow_phase_state_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Complete'
);


--
-- TOC entry 1276 (class 1247 OID 33376)
-- Name: workflow_phase_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.workflow_phase_status_enum AS ENUM (
    'On Track',
    'At Risk',
    'Past Due'
);


--
-- TOC entry 1378 (class 1247 OID 35462)
-- Name: workflowexecutionstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.workflowexecutionstatus AS ENUM (
    'PENDING',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED',
    'TIMED_OUT'
);


--
-- TOC entry 451 (class 1255 OID 120065)
-- Name: auto_skip_upload_files_activity(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 458 (class 1255 OID 124658)
-- Name: create_evidence_revision(integer, text, timestamp with time zone, integer); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 456 (class 1255 OID 121968)
-- Name: handle_document_versioning(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 453 (class 1255 OID 120092)
-- Name: prevent_duplicate_activities(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 452 (class 1255 OID 120091)
-- Name: reset_phase_activities(integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 438 (class 1255 OID 122273)
-- Name: update_cycle_report_document_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_cycle_report_document_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- TOC entry 437 (class 1255 OID 121966)
-- Name: update_cycle_report_documents_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_cycle_report_documents_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- TOC entry 457 (class 1255 OID 121970)
-- Name: update_document_access_stats(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_document_access_stats() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- This will be called from application code when tracking access
    RETURN NEW;
END;
$$;


--
-- TOC entry 436 (class 1255 OID 121442)
-- Name: update_observation_group_count(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 454 (class 1255 OID 121592)
-- Name: update_observation_group_count_unified(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 450 (class 1255 OID 119176)
-- Name: update_pde_mapping_review_status(); Type: FUNCTION; Schema: public; Owner: -
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


--
-- TOC entry 435 (class 1255 OID 119433)
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- TOC entry 455 (class 1255 OID 121594)
-- Name: update_updated_at_column_unified(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column_unified() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


SET default_table_access_method = heap;

--
-- TOC entry 316 (class 1259 OID 118315)
-- Name: activity_definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_definitions (
    id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    activity_name character varying(100) NOT NULL,
    activity_code character varying(50) NOT NULL,
    description character varying(500),
    activity_type character varying(50) NOT NULL,
    requires_backend_action boolean DEFAULT false,
    backend_endpoint character varying(200),
    sequence_order integer NOT NULL,
    depends_on_activity_codes json DEFAULT '[]'::json,
    button_text character varying(50),
    success_message character varying(200),
    instructions character varying(500),
    can_skip boolean DEFAULT false,
    can_reset boolean DEFAULT true,
    auto_complete_on_condition json,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer,
    auto_complete boolean DEFAULT false,
    conditional_skip_rules json
);


--
-- TOC entry 315 (class 1259 OID 118314)
-- Name: activity_definitions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.activity_definitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6167 (class 0 OID 0)
-- Dependencies: 315
-- Name: activity_definitions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.activity_definitions_id_seq OWNED BY public.activity_definitions.id;


--
-- TOC entry 318 (class 1259 OID 118337)
-- Name: activity_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_states (
    id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    activity_definition_id integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    started_at timestamp without time zone,
    started_by integer,
    completed_at timestamp without time zone,
    completed_by integer,
    is_blocked boolean DEFAULT false,
    blocking_reason character varying(500),
    blocked_by_activities json DEFAULT '[]'::json,
    completion_data json,
    completion_notes character varying(1000),
    reset_count integer DEFAULT 0,
    last_reset_at timestamp without time zone,
    last_reset_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer,
    completion_percentage integer DEFAULT 0,
    metadata jsonb DEFAULT '{}'::jsonb,
    phase_id uuid
);


--
-- TOC entry 317 (class 1259 OID 118336)
-- Name: activity_states_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.activity_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6168 (class 0 OID 0)
-- Dependencies: 317
-- Name: activity_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.activity_states_id_seq OWNED BY public.activity_states.id;


--
-- TOC entry 247 (class 1259 OID 33362)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(255) NOT NULL
);


--
-- TOC entry 295 (class 1259 OID 115796)
-- Name: attribute_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attribute_mappings (
    mapping_id uuid DEFAULT gen_random_uuid() NOT NULL,
    attribute_id integer NOT NULL,
    data_source_id uuid NOT NULL,
    table_name character varying(255) NOT NULL,
    column_name character varying(255) NOT NULL,
    data_type character varying(100),
    security_classification public.securityclassification DEFAULT 'Public'::public.securityclassification NOT NULL,
    is_primary_key boolean DEFAULT false NOT NULL,
    is_nullable boolean DEFAULT true NOT NULL,
    column_description text,
    mapping_confidence integer,
    llm_suggested boolean DEFAULT false NOT NULL,
    manual_override boolean DEFAULT false NOT NULL,
    is_validated boolean DEFAULT false NOT NULL,
    validation_error text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 332 (class 1259 OID 119624)
-- Name: attribute_profile_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attribute_profile_results (
    id integer NOT NULL,
    profiling_job_id integer NOT NULL,
    attribute_id integer NOT NULL,
    total_values bigint,
    null_count bigint,
    null_percentage double precision,
    distinct_count bigint,
    distinct_percentage double precision,
    detected_data_type character varying(50),
    type_consistency double precision,
    min_value double precision,
    max_value double precision,
    mean_value double precision,
    median_value double precision,
    std_deviation double precision,
    percentile_25 double precision,
    percentile_75 double precision,
    min_length integer,
    max_length integer,
    avg_length double precision,
    common_patterns json,
    pattern_coverage double precision,
    top_values json,
    value_distribution json,
    completeness_score double precision,
    validity_score double precision,
    consistency_score double precision,
    uniqueness_score double precision,
    overall_quality_score double precision,
    anomaly_count integer,
    anomaly_examples json,
    anomaly_rules_triggered json,
    outliers_detected integer,
    outlier_examples json,
    profiling_duration_ms integer,
    sampling_applied boolean,
    sample_size_used bigint,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 331 (class 1259 OID 119623)
-- Name: attribute_profile_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attribute_profile_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6169 (class 0 OID 0)
-- Dependencies: 331
-- Name: attribute_profile_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attribute_profile_results_id_seq OWNED BY public.attribute_profile_results.id;


--
-- TOC entry 235 (class 1259 OID 32467)
-- Name: cycle_report_scoping_attribute_recommendations_backup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_attribute_recommendations_backup (
    recommendation_id integer NOT NULL,
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 234 (class 1259 OID 32466)
-- Name: attribute_scoping_recommendations_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attribute_scoping_recommendations_recommendation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6170 (class 0 OID 0)
-- Dependencies: 234
-- Name: attribute_scoping_recommendations_recommendation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attribute_scoping_recommendations_recommendation_id_seq OWNED BY public.cycle_report_scoping_attribute_recommendations_backup.recommendation_id;


--
-- TOC entry 255 (class 1259 OID 33446)
-- Name: attribute_version_change_logs; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 254 (class 1259 OID 33445)
-- Name: attribute_version_change_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attribute_version_change_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6171 (class 0 OID 0)
-- Dependencies: 254
-- Name: attribute_version_change_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attribute_version_change_logs_log_id_seq OWNED BY public.attribute_version_change_logs.log_id;


--
-- TOC entry 257 (class 1259 OID 33468)
-- Name: attribute_version_comparisons; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 256 (class 1259 OID 33467)
-- Name: attribute_version_comparisons_comparison_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attribute_version_comparisons_comparison_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6172 (class 0 OID 0)
-- Dependencies: 256
-- Name: attribute_version_comparisons_comparison_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attribute_version_comparisons_comparison_id_seq OWNED BY public.attribute_version_comparisons.comparison_id;


--
-- TOC entry 220 (class 1259 OID 31754)
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
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


--
-- TOC entry 219 (class 1259 OID 31753)
-- Name: audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6173 (class 0 OID 0)
-- Dependencies: 219
-- Name: audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_audit_id_seq OWNED BY public.audit_logs.audit_id;


--
-- TOC entry 307 (class 1259 OID 116538)
-- Name: cycle_report_planning_attributes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_planning_attributes (
    id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    description text,
    data_type public.data_type_enum NOT NULL,
    is_cde boolean DEFAULT false,
    has_issues boolean DEFAULT false,
    is_primary_key boolean DEFAULT false,
    information_security_classification public.security_classification_enum DEFAULT 'Internal'::public.security_classification_enum,
    data_source_id integer,
    source_table character varying(255),
    source_column character varying(255),
    version integer DEFAULT 1,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    updated_by integer,
    approved_by integer,
    approved_at timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    is_active boolean DEFAULT true NOT NULL,
    is_latest_version boolean DEFAULT true NOT NULL,
    is_scoped boolean DEFAULT false NOT NULL,
    llm_generated boolean DEFAULT false NOT NULL,
    llm_rationale text,
    tester_notes text,
    line_item_number character varying(20),
    technical_line_item_name character varying(255),
    mdrm character varying(50),
    validation_rules text,
    typical_source_documents text,
    keywords_to_look_for text,
    testing_approach text,
    risk_score double precision,
    llm_risk_rationale text,
    primary_key_order integer,
    master_attribute_id integer,
    version_notes text,
    change_reason character varying(100),
    replaced_attribute_id integer,
    version_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version_created_by integer DEFAULT 1 NOT NULL,
    archived_at timestamp without time zone,
    archived_by integer,
    is_mandatory public.mandatory_flag_enum DEFAULT 'Optional'::public.mandatory_flag_enum NOT NULL,
    phase_id integer
);


--
-- TOC entry 6174 (class 0 OID 0)
-- Dependencies: 307
-- Name: COLUMN cycle_report_planning_attributes.information_security_classification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_planning_attributes.information_security_classification IS 'Security classification: HRCI, Confidential, Proprietary, Public';


--
-- TOC entry 306 (class 1259 OID 116537)
-- Name: cycle_report_attributes_planning_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_attributes_planning_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6175 (class 0 OID 0)
-- Dependencies: 306
-- Name: cycle_report_attributes_planning_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_attributes_planning_id_seq OWNED BY public.cycle_report_planning_attributes.id;


--
-- TOC entry 305 (class 1259 OID 116493)
-- Name: cycle_report_planning_attribute_version_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_planning_attribute_version_history (
    id integer NOT NULL,
    planning_attribute_id integer NOT NULL,
    cycle_report_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    description text,
    data_type public.data_type_enum NOT NULL,
    is_mandatory boolean,
    is_cde boolean,
    has_issues boolean,
    is_primary_key boolean,
    information_security_classification public.security_classification_enum,
    data_source_id integer,
    source_table character varying(255),
    source_column character varying(255),
    version integer NOT NULL,
    change_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    phase_id integer
);


--
-- TOC entry 304 (class 1259 OID 116492)
-- Name: cycle_report_attributes_planning_version_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_attributes_planning_version_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6176 (class 0 OID 0)
-- Dependencies: 304
-- Name: cycle_report_attributes_planning_version_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_attributes_planning_version_history_id_seq OWNED BY public.cycle_report_planning_attribute_version_history.id;


--
-- TOC entry 345 (class 1259 OID 120665)
-- Name: cycle_report_data_owner_lob_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_data_owner_lob_mapping (
    mapping_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid,
    phase_id integer NOT NULL,
    sample_id integer,
    attribute_id integer NOT NULL,
    lob_id integer NOT NULL,
    data_owner_id integer,
    data_executive_id integer,
    assigned_by_data_executive_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    assignment_rationale text,
    previous_data_owner_id integer,
    change_reason text,
    assignment_status character varying(50) DEFAULT 'assigned'::character varying NOT NULL,
    data_owner_acknowledged boolean DEFAULT false NOT NULL,
    data_owner_acknowledged_at timestamp with time zone,
    data_owner_response_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by_id integer NOT NULL,
    CONSTRAINT cycle_report_data_owner_lob_attribute_a_assignment_status_check CHECK (((assignment_status)::text = ANY ((ARRAY['assigned'::character varying, 'unassigned'::character varying, 'changed'::character varying, 'confirmed'::character varying])::text[])))
);


--
-- TOC entry 344 (class 1259 OID 120555)
-- Name: cycle_report_data_owner_lob_mapping_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_data_owner_lob_mapping_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer NOT NULL,
    workflow_activity_id integer,
    version_number integer NOT NULL,
    version_status character varying(50) DEFAULT 'draft'::character varying NOT NULL,
    parent_version_id uuid,
    workflow_execution_id character varying(255),
    workflow_run_id character varying(255),
    total_lob_attributes integer DEFAULT 0 NOT NULL,
    assigned_lob_attributes integer DEFAULT 0 NOT NULL,
    unassigned_lob_attributes integer DEFAULT 0 NOT NULL,
    data_executive_id integer NOT NULL,
    assignment_batch_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    assignment_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by_id integer NOT NULL,
    CONSTRAINT cycle_report_data_owner_lob_attribute_vers_version_status_check CHECK (((version_status)::text = ANY ((ARRAY['draft'::character varying, 'active'::character varying, 'superseded'::character varying])::text[])))
);


--
-- TOC entry 379 (class 1259 OID 123265)
-- Name: cycle_report_data_profiling_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_data_profiling_results (
    result_id integer NOT NULL,
    phase_id integer NOT NULL,
    rule_id uuid NOT NULL,
    attribute_id integer,
    execution_status character varying(50) NOT NULL,
    execution_time_ms integer,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    passed_count integer,
    failed_count integer,
    total_count integer,
    pass_rate double precision,
    result_summary json,
    failed_records json,
    result_details text,
    quality_impact double precision,
    severity character varying(50),
    has_anomaly boolean DEFAULT false,
    anomaly_description text,
    anomaly_marked_by integer,
    anomaly_marked_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer
);


--
-- TOC entry 378 (class 1259 OID 123264)
-- Name: cycle_report_data_profiling_results_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_data_profiling_results_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6177 (class 0 OID 0)
-- Dependencies: 378
-- Name: cycle_report_data_profiling_results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_data_profiling_results_result_id_seq OWNED BY public.cycle_report_data_profiling_results.result_id;


--
-- TOC entry 371 (class 1259 OID 122669)
-- Name: cycle_report_data_profiling_rule_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_data_profiling_rule_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer NOT NULL,
    workflow_activity_id integer,
    version_number integer NOT NULL,
    version_status public.version_status_enum DEFAULT 'draft'::public.version_status_enum NOT NULL,
    parent_version_id uuid,
    workflow_execution_id character varying(255),
    workflow_run_id character varying(255),
    total_rules integer DEFAULT 0 NOT NULL,
    approved_rules integer DEFAULT 0 NOT NULL,
    rejected_rules integer DEFAULT 0 NOT NULL,
    planning_data_source_id integer,
    source_table_name character varying(255),
    source_file_path character varying(500),
    total_records_processed integer,
    overall_quality_score numeric(5,2),
    execution_job_id character varying(255),
    generation_job_id character varying(255),
    generation_status character varying(50),
    submitted_by_id integer,
    submitted_at timestamp with time zone,
    approved_by_id integer,
    approved_at timestamp with time zone,
    rejection_reason character varying(500),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer NOT NULL,
    updated_by_id integer NOT NULL,
    data_source_type character varying(50)
);


--
-- TOC entry 6178 (class 0 OID 0)
-- Dependencies: 371
-- Name: TABLE cycle_report_data_profiling_rule_versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_data_profiling_rule_versions IS 'Unified data profiling version management - tracks version sets of rules';


--
-- TOC entry 6179 (class 0 OID 0)
-- Dependencies: 371
-- Name: COLUMN cycle_report_data_profiling_rule_versions.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_data_profiling_rule_versions.version_id IS 'Primary key - UUID for distributed systems';


--
-- TOC entry 6180 (class 0 OID 0)
-- Dependencies: 371
-- Name: COLUMN cycle_report_data_profiling_rule_versions.phase_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_data_profiling_rule_versions.phase_id IS 'Links to workflow_phases - no direct cycle/report reference needed';


--
-- TOC entry 372 (class 1259 OID 122718)
-- Name: cycle_report_data_profiling_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_data_profiling_rules (
    rule_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    attribute_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_type public.rule_type_enum NOT NULL,
    rule_description text,
    rule_code text NOT NULL,
    rule_parameters jsonb,
    llm_provider character varying(50),
    llm_rationale text,
    llm_confidence_score numeric(5,2),
    regulatory_reference text,
    severity public.severity_enum DEFAULT 'medium'::public.severity_enum NOT NULL,
    is_executable boolean DEFAULT true,
    execution_order integer,
    tester_decision public.decision_enum,
    tester_notes text,
    tester_decided_by integer,
    tester_decided_at timestamp with time zone,
    report_owner_decision public.decision_enum,
    report_owner_notes text,
    report_owner_decided_by integer,
    report_owner_decided_at timestamp with time zone,
    status public.rule_status_enum DEFAULT 'pending'::public.rule_status_enum NOT NULL,
    last_execution_job_id character varying(255),
    last_execution_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    phase_id integer,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6181 (class 0 OID 0)
-- Dependencies: 372
-- Name: TABLE cycle_report_data_profiling_rules; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_data_profiling_rules IS 'Individual data profiling rules belonging to a version';


--
-- TOC entry 6182 (class 0 OID 0)
-- Dependencies: 372
-- Name: COLUMN cycle_report_data_profiling_rules.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_data_profiling_rules.version_id IS 'Foreign key to version - all rules belong to a version';


--
-- TOC entry 320 (class 1259 OID 118962)
-- Name: cycle_report_planning_data_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_planning_data_sources (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    source_type public.datasourcetype NOT NULL,
    is_active boolean DEFAULT true,
    connection_config json,
    auth_type character varying(50),
    auth_config json,
    refresh_schedule character varying(100),
    last_sync_at timestamp without time zone,
    last_sync_status character varying(50),
    last_sync_message text,
    validation_rules json,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer,
    schema_summary text
);


--
-- TOC entry 319 (class 1259 OID 118961)
-- Name: cycle_report_data_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_data_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6183 (class 0 OID 0)
-- Dependencies: 319
-- Name: cycle_report_data_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_data_sources_id_seq OWNED BY public.cycle_report_planning_data_sources.id;


--
-- TOC entry 363 (class 1259 OID 122155)
-- Name: cycle_report_document_access_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_document_access_logs (
    log_id integer NOT NULL,
    document_id integer NOT NULL,
    user_id integer NOT NULL,
    access_type character varying(20) NOT NULL,
    accessed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 362 (class 1259 OID 122154)
-- Name: cycle_report_document_access_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_document_access_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6184 (class 0 OID 0)
-- Dependencies: 362
-- Name: cycle_report_document_access_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_document_access_logs_log_id_seq OWNED BY public.cycle_report_document_access_logs.log_id;


--
-- TOC entry 365 (class 1259 OID 122167)
-- Name: cycle_report_document_extractions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_document_extractions (
    extraction_id integer NOT NULL,
    document_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    extracted_value text,
    confidence_score integer,
    extraction_method character varying(50),
    source_location text,
    supporting_context text,
    data_quality_flags jsonb,
    alternative_values jsonb,
    is_validated boolean DEFAULT false NOT NULL,
    validated_by_user_id integer,
    validation_notes text,
    extracted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    llm_provider character varying(50),
    llm_model character varying(100),
    processing_time_ms integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 364 (class 1259 OID 122166)
-- Name: cycle_report_document_extractions_extraction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_document_extractions_extraction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6185 (class 0 OID 0)
-- Dependencies: 364
-- Name: cycle_report_document_extractions_extraction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_document_extractions_extraction_id_seq OWNED BY public.cycle_report_document_extractions.extraction_id;


--
-- TOC entry 361 (class 1259 OID 121857)
-- Name: cycle_report_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_documents (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    document_type character varying(100) NOT NULL,
    document_category character varying(50) DEFAULT 'general'::character varying,
    original_filename character varying(500) NOT NULL,
    stored_filename character varying(500) NOT NULL,
    file_path character varying(1000) NOT NULL,
    file_size bigint NOT NULL,
    file_format character varying(20) NOT NULL,
    mime_type character varying(100) NOT NULL,
    file_hash character varying(64),
    document_title character varying(500) NOT NULL,
    document_description text,
    document_version character varying(20) DEFAULT '1.0'::character varying,
    is_latest_version boolean DEFAULT true,
    parent_document_id integer,
    access_level character varying(50) DEFAULT 'phase_restricted'::character varying,
    allowed_roles jsonb,
    allowed_users jsonb,
    upload_status character varying(50) DEFAULT 'pending'::character varying,
    processing_status character varying(50) DEFAULT 'not_processed'::character varying,
    validation_status character varying(50) DEFAULT 'not_validated'::character varying,
    content_preview text,
    content_summary text,
    extracted_metadata jsonb,
    search_keywords text[],
    validation_errors jsonb,
    validation_warnings jsonb,
    quality_score double precision,
    download_count integer DEFAULT 0,
    last_downloaded_at timestamp with time zone,
    last_downloaded_by integer,
    view_count integer DEFAULT 0,
    last_viewed_at timestamp with time zone,
    last_viewed_by integer,
    workflow_stage character varying(100),
    required_for_completion boolean DEFAULT false,
    approval_required boolean DEFAULT false,
    approved_by integer,
    approved_at timestamp with time zone,
    approval_notes text,
    retention_period_days integer,
    archive_date date,
    delete_date date,
    is_archived boolean DEFAULT false,
    archived_at timestamp with time zone,
    archived_by integer,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    test_case_id character varying(255),
    is_encrypted boolean DEFAULT false NOT NULL,
    encryption_key_id character varying(100),
    is_confidential boolean DEFAULT false NOT NULL,
    document_tags jsonb,
    business_date timestamp with time zone,
    expires_at timestamp with time zone,
    last_integrity_check timestamp with time zone,
    integrity_verified boolean DEFAULT true NOT NULL,
    last_access_session_id character varying(100),
    last_access_ip character varying(45),
    last_access_user_agent text,
    CONSTRAINT cycle_report_documents_access_level_check CHECK (((access_level)::text = ANY ((ARRAY['public'::character varying, 'phase_restricted'::character varying, 'role_restricted'::character varying, 'user_restricted'::character varying])::text[]))),
    CONSTRAINT cycle_report_documents_document_type_check CHECK (((document_type)::text = ANY ((ARRAY['report_sample_data'::character varying, 'report_underlying_transaction_data'::character varying, 'report_source_transaction_data'::character varying, 'report_source_document'::character varying])::text[]))),
    CONSTRAINT cycle_report_documents_file_format_check CHECK (((file_format)::text = ANY ((ARRAY['csv'::character varying, 'pipe'::character varying, 'excel'::character varying, 'xlsx'::character varying, 'xls'::character varying, 'word'::character varying, 'docx'::character varying, 'pdf'::character varying, 'jpeg'::character varying, 'jpg'::character varying, 'png'::character varying])::text[]))),
    CONSTRAINT cycle_report_documents_processing_status_check CHECK (((processing_status)::text = ANY ((ARRAY['not_processed'::character varying, 'processing'::character varying, 'processed'::character varying, 'failed'::character varying, 'skipped'::character varying])::text[]))),
    CONSTRAINT cycle_report_documents_quality_score_check CHECK (((quality_score IS NULL) OR ((quality_score >= (0.0)::double precision) AND (quality_score <= (1.0)::double precision)))),
    CONSTRAINT cycle_report_documents_upload_status_check CHECK (((upload_status)::text = ANY ((ARRAY['pending'::character varying, 'uploading'::character varying, 'uploaded'::character varying, 'processing'::character varying, 'processed'::character varying, 'failed'::character varying, 'quarantined'::character varying])::text[]))),
    CONSTRAINT cycle_report_documents_validation_status_check CHECK (((validation_status)::text = ANY ((ARRAY['not_validated'::character varying, 'validating'::character varying, 'valid'::character varying, 'invalid'::character varying, 'warning'::character varying])::text[])))
);


--
-- TOC entry 6186 (class 0 OID 0)
-- Dependencies: 361
-- Name: TABLE cycle_report_documents; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_documents IS 'Generic document management system for cycle report testing phases';


--
-- TOC entry 6187 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.document_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.document_type IS 'Type of document: report_sample_data, report_underlying_transaction_data, report_source_transaction_data, report_source_document';


--
-- TOC entry 6188 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.file_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.file_format IS 'Supported formats: csv, pipe, excel, xlsx, xls, word, docx, pdf, jpeg, jpg, png';


--
-- TOC entry 6189 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.file_hash; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.file_hash IS 'SHA-256 hash for file integrity verification and duplicate detection';


--
-- TOC entry 6190 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.is_latest_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.is_latest_version IS 'Whether this is the latest version of the document';


--
-- TOC entry 6191 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.parent_document_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.parent_document_id IS 'Reference to previous version for document versioning';


--
-- TOC entry 6192 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.access_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.access_level IS 'Access control level: public, phase_restricted, role_restricted, user_restricted';


--
-- TOC entry 6193 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.upload_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.upload_status IS 'Upload progress: pending, uploading, uploaded, processing, processed, failed, quarantined';


--
-- TOC entry 6194 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.processing_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.processing_status IS 'Document processing status for content extraction and analysis';


--
-- TOC entry 6195 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.validation_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.validation_status IS 'Document validation status for format and content validation';


--
-- TOC entry 6196 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.extracted_metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.extracted_metadata IS 'Metadata extracted from the document (headers, properties, etc.)';


--
-- TOC entry 6197 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.search_keywords; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.search_keywords IS 'Keywords extracted for search functionality';


--
-- TOC entry 6198 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.quality_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.quality_score IS 'Quality score from 0.0 to 1.0 based on validation and analysis';


--
-- TOC entry 6199 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.required_for_completion; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.required_for_completion IS 'Whether this document is required for phase completion';


--
-- TOC entry 6200 (class 0 OID 0)
-- Dependencies: 361
-- Name: COLUMN cycle_report_documents.test_case_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_documents.test_case_id IS 'Optional test case ID for granular document tracking within phases';


--
-- TOC entry 367 (class 1259 OID 122320)
-- Name: cycle_report_documents_by_test_case; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.cycle_report_documents_by_test_case AS
 SELECT cycle_report_documents.phase_id,
    cycle_report_documents.test_case_id,
    cycle_report_documents.document_type,
    count(*) AS document_count,
    sum(cycle_report_documents.file_size) AS total_size_bytes,
    count(
        CASE
            WHEN ((cycle_report_documents.upload_status)::text = ANY ((ARRAY['uploaded'::character varying, 'processed'::character varying])::text[])) THEN 1
            ELSE NULL::integer
        END) AS uploaded_count,
    count(
        CASE
            WHEN (cycle_report_documents.is_latest_version = true) THEN 1
            ELSE NULL::integer
        END) AS latest_version_count
   FROM public.cycle_report_documents
  WHERE ((cycle_report_documents.test_case_id IS NOT NULL) AND (cycle_report_documents.is_archived = false))
  GROUP BY cycle_report_documents.phase_id, cycle_report_documents.test_case_id, cycle_report_documents.document_type;


--
-- TOC entry 360 (class 1259 OID 121856)
-- Name: cycle_report_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6201 (class 0 OID 0)
-- Dependencies: 360
-- Name: cycle_report_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_documents_id_seq OWNED BY public.cycle_report_documents.id;


--
-- TOC entry 366 (class 1259 OID 122315)
-- Name: cycle_report_documents_latest; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.cycle_report_documents_latest AS
 SELECT cycle_report_documents.id,
    cycle_report_documents.phase_id,
    cycle_report_documents.document_type,
    cycle_report_documents.document_category,
    cycle_report_documents.original_filename,
    cycle_report_documents.stored_filename,
    cycle_report_documents.file_path,
    cycle_report_documents.file_size,
    cycle_report_documents.file_format,
    cycle_report_documents.mime_type,
    cycle_report_documents.file_hash,
    cycle_report_documents.document_title,
    cycle_report_documents.document_description,
    cycle_report_documents.document_version,
    cycle_report_documents.is_latest_version,
    cycle_report_documents.parent_document_id,
    cycle_report_documents.access_level,
    cycle_report_documents.allowed_roles,
    cycle_report_documents.allowed_users,
    cycle_report_documents.upload_status,
    cycle_report_documents.processing_status,
    cycle_report_documents.validation_status,
    cycle_report_documents.content_preview,
    cycle_report_documents.content_summary,
    cycle_report_documents.extracted_metadata,
    cycle_report_documents.search_keywords,
    cycle_report_documents.validation_errors,
    cycle_report_documents.validation_warnings,
    cycle_report_documents.quality_score,
    cycle_report_documents.download_count,
    cycle_report_documents.last_downloaded_at,
    cycle_report_documents.last_downloaded_by,
    cycle_report_documents.view_count,
    cycle_report_documents.last_viewed_at,
    cycle_report_documents.last_viewed_by,
    cycle_report_documents.workflow_stage,
    cycle_report_documents.required_for_completion,
    cycle_report_documents.approval_required,
    cycle_report_documents.approved_by,
    cycle_report_documents.approved_at,
    cycle_report_documents.approval_notes,
    cycle_report_documents.retention_period_days,
    cycle_report_documents.archive_date,
    cycle_report_documents.delete_date,
    cycle_report_documents.is_archived,
    cycle_report_documents.archived_at,
    cycle_report_documents.archived_by,
    cycle_report_documents.uploaded_by,
    cycle_report_documents.uploaded_at,
    cycle_report_documents.created_at,
    cycle_report_documents.updated_at,
    cycle_report_documents.created_by,
    cycle_report_documents.updated_by
   FROM public.cycle_report_documents
  WHERE ((cycle_report_documents.is_latest_version = true) AND (cycle_report_documents.is_archived = false));


--
-- TOC entry 357 (class 1259 OID 121445)
-- Name: cycle_report_observation_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_groups (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    group_name character varying(255) NOT NULL,
    group_description text,
    attribute_id integer NOT NULL,
    lob_id integer NOT NULL,
    observation_count integer DEFAULT 0,
    severity_level character varying(50) DEFAULT 'medium'::character varying,
    issue_type character varying(100) NOT NULL,
    issue_summary text NOT NULL,
    impact_description text,
    proposed_resolution text,
    status character varying(50) DEFAULT 'draft'::character varying,
    tester_review_status character varying(50),
    tester_review_notes text,
    tester_review_score integer,
    tester_reviewed_by integer,
    tester_reviewed_at timestamp with time zone,
    report_owner_approval_status character varying(50),
    report_owner_approval_notes text,
    report_owner_approved_by integer,
    report_owner_approved_at timestamp with time zone,
    clarification_requested boolean DEFAULT false,
    clarification_request_text text,
    clarification_response text,
    clarification_due_date timestamp with time zone,
    resolution_status character varying(50) DEFAULT 'pending'::character varying,
    resolution_approach text,
    resolution_timeline text,
    resolution_owner integer,
    resolution_notes text,
    resolved_by integer,
    resolved_at timestamp with time zone,
    detection_method character varying(50) NOT NULL,
    detected_by integer NOT NULL,
    detected_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    CONSTRAINT cycle_report_observation_gro_report_owner_approval_status_check CHECK (((report_owner_approval_status)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying, 'needs_clarification'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_detection_method_check CHECK (((detection_method)::text = ANY ((ARRAY['auto_detected'::character varying, 'manual_review'::character varying, 'escalation'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_issue_type_check CHECK (((issue_type)::text = ANY ((ARRAY['data_quality'::character varying, 'process_failure'::character varying, 'system_error'::character varying, 'compliance_gap'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_resolution_status_check CHECK (((resolution_status)::text = ANY ((ARRAY['pending'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'deferred'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_severity_level_check CHECK (((severity_level)::text = ANY ((ARRAY['high'::character varying, 'medium'::character varying, 'low'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_status_check CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'pending_tester_review'::character varying, 'tester_approved'::character varying, 'pending_report_owner_approval'::character varying, 'report_owner_approved'::character varying, 'rejected'::character varying, 'resolved'::character varying, 'closed'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_groups_tester_review_score_check CHECK (((tester_review_score >= 1) AND (tester_review_score <= 100))),
    CONSTRAINT cycle_report_observation_groups_tester_review_status_check CHECK (((tester_review_status)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying, 'needs_clarification'::character varying])::text[])))
);


--
-- TOC entry 6202 (class 0 OID 0)
-- Dependencies: 357
-- Name: TABLE cycle_report_observation_groups; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_observation_groups IS 'Observation groups with built-in approval workflow, grouped by attribute and LOB';


--
-- TOC entry 6203 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.observation_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.observation_count IS 'Automatically maintained count of observations in this group';


--
-- TOC entry 6204 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.status IS 'Main workflow status for the group';


--
-- TOC entry 6205 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.tester_review_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.tester_review_status IS 'Tester review decision (built-in approval)';


--
-- TOC entry 6206 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.report_owner_approval_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.report_owner_approval_status IS 'Report owner approval decision (built-in approval)';


--
-- TOC entry 6207 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.clarification_requested; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.clarification_requested IS 'Whether clarification has been requested';


--
-- TOC entry 6208 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN cycle_report_observation_groups.resolution_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observation_groups.resolution_status IS 'Resolution tracking status';


--
-- TOC entry 356 (class 1259 OID 121444)
-- Name: cycle_report_observation_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_observation_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6209 (class 0 OID 0)
-- Dependencies: 356
-- Name: cycle_report_observation_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_observation_groups_id_seq OWNED BY public.cycle_report_observation_groups.id;


--
-- TOC entry 242 (class 1259 OID 33232)
-- Name: cycle_report_observation_mgmt_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_approvals (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 246 (class 1259 OID 33288)
-- Name: cycle_report_observation_mgmt_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_audit_logs (
    log_id integer NOT NULL,
    phase_id integer,
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


--
-- TOC entry 240 (class 1259 OID 33206)
-- Name: cycle_report_observation_mgmt_impact_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_impact_assessments (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 294 (class 1259 OID 98899)
-- Name: cycle_report_observation_mgmt_observation_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_observation_records (
    observation_id integer NOT NULL,
    phase_id integer NOT NULL,
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 336 (class 1259 OID 119697)
-- Name: cycle_report_observation_mgmt_preliminary_findings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_preliminary_findings (
    id integer NOT NULL,
    finding_title character varying(500) NOT NULL,
    finding_description text NOT NULL,
    finding_type character varying(50),
    source_type character varying(50),
    source_reference character varying(255),
    category character varying(100),
    severity_estimate character varying(20),
    evidence_summary text,
    supporting_data jsonb,
    status character varying(50) DEFAULT 'draft'::character varying,
    review_notes text,
    conversion_date timestamp with time zone,
    dismissed_reason text,
    dismissed_date timestamp with time zone,
    assigned_to_id integer,
    tags text[],
    created_by_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    phase_id integer,
    CONSTRAINT cycle_report_observation_mgmt_prelimina_severity_estimate_check CHECK (((severity_estimate)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying, 'unknown'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_mgmt_preliminary_fi_finding_type_check CHECK (((finding_type)::text = ANY ((ARRAY['potential_issue'::character varying, 'anomaly'::character varying, 'clarification_needed'::character varying, 'noteworthy'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_mgmt_preliminary_fin_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['test_execution'::character varying, 'data_analysis'::character varying, 'document_review'::character varying, 'llm_analysis'::character varying])::text[]))),
    CONSTRAINT cycle_report_observation_mgmt_preliminary_findings_status_check CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'under_review'::character varying, 'converted_to_observation'::character varying, 'dismissed'::character varying, 'merged'::character varying])::text[])))
);


--
-- TOC entry 335 (class 1259 OID 119696)
-- Name: cycle_report_observation_mgmt_preliminary_findings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_observation_mgmt_preliminary_findings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6210 (class 0 OID 0)
-- Dependencies: 335
-- Name: cycle_report_observation_mgmt_preliminary_findings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_observation_mgmt_preliminary_findings_id_seq OWNED BY public.cycle_report_observation_mgmt_preliminary_findings.id;


--
-- TOC entry 244 (class 1259 OID 33258)
-- Name: cycle_report_observation_mgmt_resolutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observation_mgmt_resolutions (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 359 (class 1259 OID 121532)
-- Name: cycle_report_observations_unified; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_observations_unified (
    id integer NOT NULL,
    group_id integer NOT NULL,
    test_execution_id integer NOT NULL,
    test_case_id character varying(255) NOT NULL,
    attribute_id integer NOT NULL,
    sample_id character varying(255) NOT NULL,
    lob_id integer NOT NULL,
    observation_title character varying(255) NOT NULL,
    observation_description text NOT NULL,
    expected_value text,
    actual_value text,
    variance_details jsonb,
    test_result character varying(50),
    evidence_files jsonb,
    supporting_documentation text,
    confidence_level double precision,
    reproducible boolean DEFAULT false,
    frequency_estimate character varying(50),
    business_impact text,
    technical_impact text,
    regulatory_impact text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    CONSTRAINT cycle_report_observations_unified_confidence_level_check CHECK (((confidence_level >= (0.0)::double precision) AND (confidence_level <= (1.0)::double precision))),
    CONSTRAINT cycle_report_observations_unified_frequency_estimate_check CHECK (((frequency_estimate)::text = ANY ((ARRAY['isolated'::character varying, 'occasional'::character varying, 'frequent'::character varying, 'systematic'::character varying])::text[]))),
    CONSTRAINT cycle_report_observations_unified_test_result_check CHECK (((test_result)::text = ANY ((ARRAY['fail'::character varying, 'inconclusive'::character varying])::text[])))
);


--
-- TOC entry 6211 (class 0 OID 0)
-- Dependencies: 359
-- Name: TABLE cycle_report_observations_unified; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_observations_unified IS 'Individual observations, one per test case failure, linked to test execution results';


--
-- TOC entry 6212 (class 0 OID 0)
-- Dependencies: 359
-- Name: COLUMN cycle_report_observations_unified.test_execution_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observations_unified.test_execution_id IS 'Links to the test execution that generated this observation';


--
-- TOC entry 6213 (class 0 OID 0)
-- Dependencies: 359
-- Name: COLUMN cycle_report_observations_unified.variance_details; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observations_unified.variance_details IS 'JSON object with detailed variance information';


--
-- TOC entry 6214 (class 0 OID 0)
-- Dependencies: 359
-- Name: COLUMN cycle_report_observations_unified.evidence_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observations_unified.evidence_files IS 'JSON array of evidence file paths and metadata';


--
-- TOC entry 6215 (class 0 OID 0)
-- Dependencies: 359
-- Name: COLUMN cycle_report_observations_unified.confidence_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_observations_unified.confidence_level IS 'Confidence level (0.0-1.0) that this is a real issue';


--
-- TOC entry 358 (class 1259 OID 121531)
-- Name: cycle_report_observations_unified_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_observations_unified_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6216 (class 0 OID 0)
-- Dependencies: 358
-- Name: cycle_report_observations_unified_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_observations_unified_id_seq OWNED BY public.cycle_report_observations_unified.id;


--
-- TOC entry 322 (class 1259 OID 118994)
-- Name: cycle_report_planning_pde_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_planning_pde_mappings (
    id integer NOT NULL,
    attribute_id integer NOT NULL,
    data_source_id integer,
    pde_name character varying(255) NOT NULL,
    pde_code character varying(100) NOT NULL,
    pde_description text,
    source_field character varying(255),
    transformation_rule json,
    mapping_type character varying(50),
    llm_suggested_mapping json,
    llm_confidence_score integer,
    llm_mapping_rationale text,
    llm_alternative_mappings json,
    mapping_confirmed_by_user boolean DEFAULT false,
    business_process character varying(255),
    business_owner character varying(255),
    data_steward character varying(255),
    criticality character varying(50),
    risk_level character varying(50),
    regulatory_flag boolean DEFAULT false,
    pii_flag boolean DEFAULT false,
    llm_suggested_criticality character varying(50),
    llm_suggested_risk_level character varying(50),
    llm_classification_rationale text,
    llm_regulatory_references json,
    is_validated boolean DEFAULT false,
    validation_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    latest_review_status public.reviewstatus,
    latest_review_id integer,
    information_security_classification character varying(50),
    profiling_criteria json,
    phase_id integer
);


--
-- TOC entry 321 (class 1259 OID 118993)
-- Name: cycle_report_pde_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_pde_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6217 (class 0 OID 0)
-- Dependencies: 321
-- Name: cycle_report_pde_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_pde_mappings_id_seq OWNED BY public.cycle_report_planning_pde_mappings.id;


--
-- TOC entry 233 (class 1259 OID 32435)
-- Name: cycle_report_request_info_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_audit_logs (
    log_id integer NOT NULL,
    phase_id integer,
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    audit_id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    cycle_id integer,
    report_id integer,
    session_id character varying(100),
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 334 (class 1259 OID 119664)
-- Name: cycle_report_request_info_document_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_document_versions (
    id integer NOT NULL,
    document_submission_id integer NOT NULL,
    version_number integer DEFAULT 1 NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path character varying(500),
    file_size integer,
    mime_type character varying(100),
    checksum character varying(64),
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id integer,
    change_reason text,
    is_current boolean DEFAULT true,
    created_by_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    phase_id integer
);


--
-- TOC entry 333 (class 1259 OID 119663)
-- Name: cycle_report_request_info_document_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_request_info_document_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6218 (class 0 OID 0)
-- Dependencies: 333
-- Name: cycle_report_request_info_document_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_request_info_document_versions_id_seq OWNED BY public.cycle_report_request_info_document_versions.id;


--
-- TOC entry 388 (class 1259 OID 125310)
-- Name: cycle_report_request_info_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_evidence (
    evidence_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    phase_id integer NOT NULL,
    test_case_id integer NOT NULL,
    sample_id character varying(255) NOT NULL,
    attribute_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    evidence_type character varying(20) NOT NULL,
    evidence_status public.evidence_status_enum DEFAULT 'pending'::public.evidence_status_enum NOT NULL,
    document_name character varying(255),
    document_path text,
    document_size_bytes bigint,
    document_mime_type character varying(100),
    data_source_name character varying(255),
    data_source_type character varying(50),
    query_text text,
    query_result jsonb,
    query_row_count integer,
    submitted_by_id integer,
    submitted_at timestamp with time zone,
    submission_notes text,
    tester_decision character varying(50),
    tester_notes text,
    tester_decided_by_id integer,
    tester_decided_at timestamp with time zone,
    report_owner_decision character varying(50),
    report_owner_notes text,
    report_owner_decided_by_id integer,
    report_owner_decided_at timestamp with time zone,
    rejection_reason text,
    requires_resubmission boolean DEFAULT false,
    resubmission_deadline timestamp with time zone,
    is_resubmission boolean DEFAULT false,
    parent_evidence_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer,
    CONSTRAINT cycle_report_request_info_evidence_versione_evidence_type_check CHECK (((evidence_type)::text = ANY ((ARRAY['document'::character varying, 'data_source'::character varying])::text[])))
);


--
-- TOC entry 6219 (class 0 OID 0)
-- Dependencies: 388
-- Name: TABLE cycle_report_request_info_evidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_request_info_evidence IS 'Individual evidence submissions for test cases in Request Info phase';


--
-- TOC entry 6220 (class 0 OID 0)
-- Dependencies: 388
-- Name: COLUMN cycle_report_request_info_evidence.evidence_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence.evidence_id IS 'Unique identifier for this evidence';


--
-- TOC entry 6221 (class 0 OID 0)
-- Dependencies: 388
-- Name: COLUMN cycle_report_request_info_evidence.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence.version_id IS 'Reference to the version this evidence belongs to';


--
-- TOC entry 6222 (class 0 OID 0)
-- Dependencies: 388
-- Name: COLUMN cycle_report_request_info_evidence.test_case_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence.test_case_id IS 'Reference to the test case this evidence supports';


--
-- TOC entry 349 (class 1259 OID 120876)
-- Name: cycle_report_request_info_evidence_validation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_evidence_validation (
    id integer NOT NULL,
    evidence_id integer NOT NULL,
    validation_rule character varying(255) NOT NULL,
    validation_result character varying(50) NOT NULL,
    validation_message text,
    validated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    validated_by integer NOT NULL
);


--
-- TOC entry 348 (class 1259 OID 120875)
-- Name: cycle_report_request_info_evidence_validation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_request_info_evidence_validation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6223 (class 0 OID 0)
-- Dependencies: 348
-- Name: cycle_report_request_info_evidence_validation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_request_info_evidence_validation_id_seq OWNED BY public.cycle_report_request_info_evidence_validation.id;


--
-- TOC entry 387 (class 1259 OID 125257)
-- Name: cycle_report_request_info_evidence_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_evidence_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer NOT NULL,
    version_number integer NOT NULL,
    version_status public.version_status_enum DEFAULT 'draft'::public.version_status_enum NOT NULL,
    parent_version_id uuid,
    total_test_cases integer DEFAULT 0 NOT NULL,
    submitted_count integer DEFAULT 0 NOT NULL,
    approved_count integer DEFAULT 0 NOT NULL,
    rejected_count integer DEFAULT 0 NOT NULL,
    pending_count integer DEFAULT 0 NOT NULL,
    document_evidence_count integer DEFAULT 0 NOT NULL,
    data_source_evidence_count integer DEFAULT 0 NOT NULL,
    submission_deadline timestamp with time zone,
    reminder_schedule jsonb,
    instructions text,
    submitted_by_id integer,
    submitted_at timestamp with time zone,
    approved_by_id integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    report_owner_review_requested_at timestamp with time zone,
    report_owner_review_completed_at timestamp with time zone,
    report_owner_feedback_summary jsonb,
    workflow_execution_id character varying(255),
    workflow_run_id character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6224 (class 0 OID 0)
-- Dependencies: 387
-- Name: TABLE cycle_report_request_info_evidence_versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_request_info_evidence_versions IS 'Version management for Request Info evidence submissions';


--
-- TOC entry 6225 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN cycle_report_request_info_evidence_versions.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence_versions.version_id IS 'Unique identifier for this version';


--
-- TOC entry 6226 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN cycle_report_request_info_evidence_versions.phase_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence_versions.phase_id IS 'Reference to the workflow phase';


--
-- TOC entry 6227 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN cycle_report_request_info_evidence_versions.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence_versions.version_number IS 'Sequential version number within the phase';


--
-- TOC entry 6228 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN cycle_report_request_info_evidence_versions.version_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_request_info_evidence_versions.version_status IS 'Current status of this version';


--
-- TOC entry 347 (class 1259 OID 120803)
-- Name: cycle_report_request_info_testcase_source_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_request_info_testcase_source_evidence (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    test_case_id integer NOT NULL,
    sample_id character varying(255) NOT NULL,
    attribute_id integer NOT NULL,
    evidence_type character varying(50) NOT NULL,
    document_name character varying(255),
    document_path character varying(500),
    document_size integer,
    mime_type character varying(100),
    document_hash character varying(128),
    data_source_id integer,
    query_text text,
    query_parameters jsonb,
    query_result_sample jsonb,
    submitted_by integer NOT NULL,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    submission_notes text,
    validation_status character varying(50) DEFAULT 'pending'::character varying,
    validation_notes text,
    validated_by integer,
    validated_at timestamp with time zone,
    version_number integer DEFAULT 1,
    is_current boolean DEFAULT true,
    replaced_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    query_validation_id uuid,
    CONSTRAINT check_evidence_type CHECK (((((evidence_type)::text = 'document'::text) AND (document_name IS NOT NULL)) OR (((evidence_type)::text = 'data_source'::text) AND (data_source_id IS NOT NULL) AND (query_text IS NOT NULL))))
);


--
-- TOC entry 346 (class 1259 OID 120802)
-- Name: cycle_report_request_info_testcase_source_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_request_info_testcase_source_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6229 (class 0 OID 0)
-- Dependencies: 346
-- Name: cycle_report_request_info_testcase_source_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_request_info_testcase_source_evidence_id_seq OWNED BY public.cycle_report_request_info_testcase_source_evidence.id;


--
-- TOC entry 368 (class 1259 OID 122325)
-- Name: cycle_report_required_documents; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.cycle_report_required_documents AS
 SELECT cycle_report_documents.phase_id,
    cycle_report_documents.document_type,
    count(*) AS document_count,
    count(
        CASE
            WHEN ((cycle_report_documents.upload_status)::text = ANY ((ARRAY['uploaded'::character varying, 'processed'::character varying])::text[])) THEN 1
            ELSE NULL::integer
        END) AS uploaded_count,
    count(
        CASE
            WHEN ((cycle_report_documents.validation_status)::text = 'valid'::text) THEN 1
            ELSE NULL::integer
        END) AS valid_count,
        CASE
            WHEN (count(*) = count(
            CASE
                WHEN ((cycle_report_documents.upload_status)::text = ANY ((ARRAY['uploaded'::character varying, 'processed'::character varying])::text[])) THEN 1
                ELSE NULL::integer
            END)) THEN 'complete'::text
            ELSE 'incomplete'::text
        END AS completion_status
   FROM public.cycle_report_documents
  WHERE ((cycle_report_documents.required_for_completion = true) AND (cycle_report_documents.is_latest_version = true) AND (cycle_report_documents.is_archived = false))
  GROUP BY cycle_report_documents.phase_id, cycle_report_documents.document_type;


--
-- TOC entry 380 (class 1259 OID 124265)
-- Name: cycle_report_rfi_data_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_rfi_data_sources (
    data_source_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer,
    data_owner_id integer NOT NULL,
    source_name character varying(255) NOT NULL,
    connection_type character varying(50) NOT NULL,
    connection_details jsonb NOT NULL,
    is_active boolean DEFAULT true,
    test_query text,
    last_validated_at timestamp with time zone,
    validation_status character varying(50),
    validation_error text,
    usage_count integer DEFAULT 0,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by integer,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cycle_report_rfi_data_sources_connection_type_check CHECK (((connection_type)::text = ANY ((ARRAY['postgresql'::character varying, 'mysql'::character varying, 'oracle'::character varying, 'csv'::character varying, 'api'::character varying])::text[]))),
    CONSTRAINT cycle_report_rfi_data_sources_validation_status_check CHECK (((validation_status)::text = ANY ((ARRAY['valid'::character varying, 'invalid'::character varying, 'pending'::character varying])::text[])))
);


--
-- TOC entry 6230 (class 0 OID 0)
-- Dependencies: 380
-- Name: TABLE cycle_report_rfi_data_sources; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_rfi_data_sources IS 'Reusable data source configurations for query-based evidence in RFI phase';


--
-- TOC entry 383 (class 1259 OID 124563)
-- Name: cycle_report_rfi_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_rfi_evidence (
    id integer NOT NULL,
    test_case_id integer NOT NULL,
    phase_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    sample_id character varying(255) NOT NULL,
    evidence_type character varying(20) NOT NULL,
    version_number integer DEFAULT 1 NOT NULL,
    is_current boolean DEFAULT true NOT NULL,
    parent_evidence_id integer,
    submitted_by integer NOT NULL,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    submission_notes text,
    validation_status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    validation_notes text,
    validated_by integer,
    validated_at timestamp with time zone,
    tester_decision character varying(50),
    tester_notes text,
    decided_by integer,
    decided_at timestamp with time zone,
    requires_resubmission boolean DEFAULT false,
    resubmission_deadline timestamp with time zone,
    original_filename character varying(255),
    stored_filename character varying(255),
    file_path character varying(500),
    file_size_bytes integer,
    file_hash character varying(64),
    mime_type character varying(100),
    rfi_data_source_id uuid,
    planning_data_source_id integer,
    query_text text,
    query_parameters jsonb,
    query_validation_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    CONSTRAINT check_evidence_type_fields CHECK (((((evidence_type)::text = 'document'::text) AND (original_filename IS NOT NULL) AND (file_path IS NOT NULL)) OR (((evidence_type)::text = 'data_source'::text) AND (query_text IS NOT NULL)))),
    CONSTRAINT cycle_report_rfi_evidence_evidence_type_check CHECK (((evidence_type)::text = ANY ((ARRAY['document'::character varying, 'data_source'::character varying])::text[]))),
    CONSTRAINT cycle_report_rfi_evidence_tester_decision_check CHECK (((tester_decision)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying, 'requires_revision'::character varying])::text[])))
);


--
-- TOC entry 382 (class 1259 OID 124562)
-- Name: cycle_report_rfi_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_rfi_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6231 (class 0 OID 0)
-- Dependencies: 382
-- Name: cycle_report_rfi_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_rfi_evidence_id_seq OWNED BY public.cycle_report_rfi_evidence.id;


--
-- TOC entry 381 (class 1259 OID 124304)
-- Name: cycle_report_rfi_query_validations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_rfi_query_validations (
    validation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_case_id integer NOT NULL,
    data_source_id uuid NOT NULL,
    query_text text NOT NULL,
    query_parameters jsonb,
    validation_status character varying(50) NOT NULL,
    validation_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms integer,
    row_count integer,
    column_names jsonb,
    sample_rows jsonb,
    error_message text,
    has_primary_keys boolean,
    has_target_attribute boolean,
    missing_columns jsonb,
    validated_by integer NOT NULL,
    validation_warnings jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cycle_report_rfi_query_validations_validation_status_check CHECK (((validation_status)::text = ANY ((ARRAY['success'::character varying, 'failed'::character varying, 'timeout'::character varying])::text[])))
);


--
-- TOC entry 6232 (class 0 OID 0)
-- Dependencies: 381
-- Name: TABLE cycle_report_rfi_query_validations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_rfi_query_validations IS 'Query validation results before evidence submission';


--
-- TOC entry 6233 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN cycle_report_rfi_query_validations.validation_warnings; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cycle_report_rfi_query_validations.validation_warnings IS 'Array of validation warnings to help users improve their queries (e.g., column alias suggestions)';


--
-- TOC entry 236 (class 1259 OID 32676)
-- Name: cycle_report_sample_selection_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_sample_selection_audit_logs (
    audit_id character varying(36) NOT NULL,
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    phase_id integer
);


--
-- TOC entry 386 (class 1259 OID 124867)
-- Name: cycle_report_sample_selection_samples; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_sample_selection_samples (
    sample_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    phase_id integer NOT NULL,
    lob_id integer,
    sample_identifier character varying(255) NOT NULL,
    sample_data jsonb NOT NULL,
    sample_category public.sample_category_enum NOT NULL,
    sample_source public.sample_source_enum NOT NULL,
    tester_decision public.sample_decision_enum DEFAULT 'pending'::public.sample_decision_enum NOT NULL,
    tester_decision_notes text,
    tester_decision_at timestamp with time zone,
    tester_decision_by_id integer,
    report_owner_decision public.sample_decision_enum DEFAULT 'pending'::public.sample_decision_enum NOT NULL,
    report_owner_decision_notes text,
    report_owner_decision_at timestamp with time zone,
    report_owner_decision_by_id integer,
    risk_score double precision,
    confidence_score double precision,
    generation_metadata jsonb,
    validation_results jsonb,
    carried_from_version_id uuid,
    carried_from_sample_id uuid,
    carry_forward_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 385 (class 1259 OID 124799)
-- Name: cycle_report_sample_selection_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_sample_selection_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer NOT NULL,
    workflow_activity_id integer,
    version_number integer NOT NULL,
    version_status public.sample_selection_version_status_enum NOT NULL,
    parent_version_id uuid,
    workflow_execution_id character varying(255) NOT NULL,
    workflow_run_id character varying(255) NOT NULL,
    activity_name character varying(100) NOT NULL,
    selection_criteria jsonb NOT NULL,
    target_sample_size integer NOT NULL,
    actual_sample_size integer DEFAULT 0 NOT NULL,
    intelligent_sampling_config jsonb,
    distribution_metrics jsonb,
    data_source_config jsonb,
    submission_notes text,
    submitted_by_id integer,
    submitted_at timestamp with time zone,
    approval_notes text,
    approved_by_id integer,
    approved_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    report_owner_decision character varying(20),
    report_owner_feedback text,
    report_owner_reviewed_at timestamp with time zone,
    report_owner_reviewed_by_id integer,
    CONSTRAINT cycle_report_sample_selection_versi_report_owner_decision_check CHECK (((report_owner_decision)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying, 'revision_required'::character varying])::text[])))
);


--
-- TOC entry 375 (class 1259 OID 122909)
-- Name: cycle_report_scoping_attributes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_attributes (
    attribute_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    phase_id integer NOT NULL,
    planning_attribute_id integer NOT NULL,
    llm_recommendation jsonb,
    llm_provider character varying(50),
    llm_confidence_score numeric(3,2),
    llm_rationale text,
    llm_processing_time_ms integer,
    tester_decision public.scoping_tester_decision_enum,
    tester_rationale text,
    tester_decided_by_id integer,
    tester_decided_at timestamp with time zone,
    report_owner_decision public.scoping_report_owner_decision_enum,
    report_owner_notes text,
    report_owner_decided_by_id integer,
    report_owner_decided_at timestamp with time zone,
    final_status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    override_reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    llm_request_payload jsonb,
    llm_response_payload jsonb,
    final_scoping boolean,
    is_override boolean DEFAULT false,
    is_cde boolean DEFAULT false,
    has_historical_issues boolean DEFAULT false,
    is_primary_key boolean DEFAULT false,
    data_quality_score double precision,
    data_quality_issues jsonb,
    expected_source_documents jsonb,
    search_keywords jsonb,
    risk_factors jsonb,
    status public.scoping_attribute_status_enum,
    CONSTRAINT cycle_report_scoping_attributes_final_status_check CHECK (((final_status)::text = ANY ((ARRAY['pending'::character varying, 'included'::character varying, 'excluded'::character varying])::text[]))),
    CONSTRAINT cycle_report_scoping_attributes_llm_recommendation_check CHECK (((llm_recommendation)::text = ANY (ARRAY[('include'::character varying)::text, ('exclude'::character varying)::text, ('review'::character varying)::text, (NULL::character varying)::text]))),
    CONSTRAINT cycle_report_scoping_attributes_report_owner_decision_check CHECK (((report_owner_decision)::text = ANY (ARRAY[('approve'::character varying)::text, ('override'::character varying)::text, (NULL::character varying)::text]))),
    CONSTRAINT cycle_report_scoping_attributes_tester_decision_check CHECK (((tester_decision)::text = ANY (ARRAY[('include'::character varying)::text, ('exclude'::character varying)::text, (NULL::character varying)::text])))
);


--
-- TOC entry 6234 (class 0 OID 0)
-- Dependencies: 375
-- Name: TABLE cycle_report_scoping_attributes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_scoping_attributes IS 'Attribute-level scoping decisions within a version';


--
-- TOC entry 281 (class 1259 OID 36379)
-- Name: cycle_report_scoping_decision_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_decision_versions (
    decision_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    decision_id uuid NOT NULL,
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
    approved_by character varying(255),
    phase_id integer,
    approval_status character varying(50),
    approval_notes text,
    rejected_by integer,
    rejected_at timestamp without time zone,
    rejection_reason text
);


--
-- TOC entry 343 (class 1259 OID 120484)
-- Name: cycle_report_scoping_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_decisions (
    decision_id integer NOT NULL,
    attribute_id integer NOT NULL,
    phase_id integer,
    tester_decision public.scoping_decision_enum,
    final_scoping boolean,
    tester_rationale text,
    tester_decided_by integer,
    tester_decided_at timestamp with time zone,
    report_owner_decision public.report_owner_decision_enum,
    report_owner_notes text,
    report_owner_decided_by integer,
    report_owner_decided_at timestamp with time zone,
    override_reason text,
    override_by_user_id integer,
    override_timestamp timestamp with time zone,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by integer,
    updated_at timestamp with time zone,
    updated_by integer
);


--
-- TOC entry 342 (class 1259 OID 120483)
-- Name: cycle_report_scoping_decisions_decision_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_scoping_decisions_decision_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6235 (class 0 OID 0)
-- Dependencies: 342
-- Name: cycle_report_scoping_decisions_decision_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_scoping_decisions_decision_id_seq OWNED BY public.cycle_report_scoping_decisions.decision_id;


--
-- TOC entry 227 (class 1259 OID 31939)
-- Name: cycle_report_scoping_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_submissions (
    submission_id integer NOT NULL,
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
    revision_reason text,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 374 (class 1259 OID 122854)
-- Name: cycle_report_scoping_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_scoping_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phase_id integer NOT NULL,
    workflow_activity_id integer,
    version_number integer DEFAULT 1 NOT NULL,
    version_status character varying(50) DEFAULT 'draft'::character varying NOT NULL,
    parent_version_id uuid,
    workflow_execution_id character varying(255),
    workflow_run_id character varying(255),
    activity_name character varying(255),
    total_attributes integer DEFAULT 0,
    scoped_attributes integer DEFAULT 0,
    declined_attributes integer DEFAULT 0,
    override_count integer DEFAULT 0,
    cde_count integer DEFAULT 0,
    recommendation_accuracy numeric(5,2),
    submission_notes text,
    submitted_by_id integer,
    submitted_at timestamp with time zone,
    approval_notes text,
    approved_by_id integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    requested_changes text,
    resource_impact_assessment text,
    risk_coverage_assessment text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    CONSTRAINT cycle_report_scoping_versions_version_status_check CHECK (((version_status)::text = ANY (ARRAY[('draft'::character varying)::text, ('pending_approval'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text, ('superseded'::character varying)::text])))
);


--
-- TOC entry 6236 (class 0 OID 0)
-- Dependencies: 374
-- Name: TABLE cycle_report_scoping_versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_scoping_versions IS 'Version management for scoping decisions';


--
-- TOC entry 309 (class 1259 OID 116583)
-- Name: cycle_report_test_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_cases (
    id integer NOT NULL,
    test_case_number character varying(50) NOT NULL,
    test_case_name character varying(255) NOT NULL,
    description text,
    expected_outcome text,
    test_type character varying(50),
    query_text text,
    version integer DEFAULT 1,
    status public.phase_status_enum DEFAULT 'Not Started'::public.phase_status_enum,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    updated_by integer,
    phase_id integer,
    sample_id character varying(255) DEFAULT 'TEMP'::character varying NOT NULL,
    attribute_id integer,
    attribute_name character varying(255) DEFAULT 'TEMP'::character varying NOT NULL,
    lob_id integer,
    data_owner_id integer,
    assigned_by integer,
    assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    submission_deadline timestamp with time zone,
    submitted_at timestamp with time zone,
    acknowledged_at timestamp with time zone,
    special_instructions text
);


--
-- TOC entry 311 (class 1259 OID 116613)
-- Name: cycle_report_test_cases_document_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_cases_document_submissions (
    id integer NOT NULL,
    data_owner_id integer,
    file_path text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    updated_by integer,
    phase_id integer,
    submission_id character varying(36) NOT NULL,
    test_case_id integer,
    original_filename character varying(255),
    stored_filename character varying(255),
    file_size_bytes integer,
    mime_type character varying(100),
    submission_notes text,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    parent_submission_id character varying(36),
    is_current boolean DEFAULT true,
    is_valid boolean DEFAULT true,
    validation_notes text,
    validated_by integer,
    validated_at timestamp with time zone,
    submission_number integer DEFAULT 1,
    is_revision boolean DEFAULT false,
    revision_requested_by integer,
    revision_requested_at timestamp with time zone,
    revision_reason text,
    revision_deadline timestamp with time zone,
    file_hash character varying(64),
    validation_status character varying(50) DEFAULT 'pending'::character varying
);


--
-- TOC entry 310 (class 1259 OID 116612)
-- Name: cycle_report_test_cases_document_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_cases_document_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6237 (class 0 OID 0)
-- Dependencies: 310
-- Name: cycle_report_test_cases_document_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_cases_document_submissions_id_seq OWNED BY public.cycle_report_test_cases_document_submissions.id;


--
-- TOC entry 308 (class 1259 OID 116582)
-- Name: cycle_report_test_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6238 (class 0 OID 0)
-- Dependencies: 308
-- Name: cycle_report_test_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_cases_id_seq OWNED BY public.cycle_report_test_cases.id;


--
-- TOC entry 355 (class 1259 OID 121252)
-- Name: cycle_report_test_execution_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_execution_audit (
    id integer NOT NULL,
    execution_id integer NOT NULL,
    action character varying(100) NOT NULL,
    previous_status character varying(50),
    new_status character varying(50),
    change_reason text,
    action_details jsonb,
    system_info jsonb,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 354 (class 1259 OID 121251)
-- Name: cycle_report_test_execution_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_execution_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6239 (class 0 OID 0)
-- Dependencies: 354
-- Name: cycle_report_test_execution_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_execution_audit_id_seq OWNED BY public.cycle_report_test_execution_audit.id;


--
-- TOC entry 351 (class 1259 OID 121164)
-- Name: cycle_report_test_execution_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_execution_results (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    test_case_id character varying(100) NOT NULL,
    evidence_id integer NOT NULL,
    execution_number integer NOT NULL,
    is_latest_execution boolean DEFAULT false,
    execution_reason character varying(100),
    test_type character varying(50) NOT NULL,
    analysis_method character varying(50) NOT NULL,
    sample_value text,
    extracted_value text,
    expected_value text,
    test_result character varying(50),
    comparison_result boolean,
    variance_details jsonb,
    llm_confidence_score double precision,
    llm_analysis_rationale text,
    llm_model_used character varying(100),
    llm_tokens_used integer,
    llm_response_raw jsonb,
    llm_processing_time_ms integer,
    database_query_executed text,
    database_result_count integer,
    database_execution_time_ms integer,
    database_result_sample jsonb,
    execution_status character varying(50) DEFAULT 'pending'::character varying,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_time_ms integer,
    error_message text,
    error_details jsonb,
    retry_count integer DEFAULT 0,
    analysis_results jsonb NOT NULL,
    evidence_validation_status character varying(50),
    evidence_version_number integer,
    execution_summary text,
    processing_notes text,
    executed_by integer NOT NULL,
    execution_method character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL,
    CONSTRAINT ck_test_execution_evidence_approved CHECK (((evidence_validation_status)::text = ANY ((ARRAY['valid'::character varying, 'approved'::character varying])::text[])))
);


--
-- TOC entry 350 (class 1259 OID 121163)
-- Name: cycle_report_test_execution_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_execution_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6240 (class 0 OID 0)
-- Dependencies: 350
-- Name: cycle_report_test_execution_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_execution_results_id_seq OWNED BY public.cycle_report_test_execution_results.id;


--
-- TOC entry 353 (class 1259 OID 121213)
-- Name: cycle_report_test_execution_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_execution_reviews (
    id integer NOT NULL,
    execution_id integer NOT NULL,
    phase_id integer NOT NULL,
    review_status character varying(50) NOT NULL,
    review_notes text,
    reviewer_comments text,
    recommended_action character varying(100),
    accuracy_score double precision,
    completeness_score double precision,
    consistency_score double precision,
    overall_score double precision,
    review_criteria_used jsonb,
    supporting_evidence text,
    requires_retest boolean DEFAULT false,
    escalation_required boolean DEFAULT false,
    escalation_reason text,
    escalation_level character varying(50),
    reviewed_by integer NOT NULL,
    reviewed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    review_duration_ms integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL,
    updated_by integer NOT NULL
);


--
-- TOC entry 352 (class 1259 OID 121212)
-- Name: cycle_report_test_execution_reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_execution_reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6241 (class 0 OID 0)
-- Dependencies: 352
-- Name: cycle_report_test_execution_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_execution_reviews_id_seq OWNED BY public.cycle_report_test_execution_reviews.id;


--
-- TOC entry 370 (class 1259 OID 122560)
-- Name: cycle_report_test_report_generation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_report_generation (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    generation_started_at timestamp with time zone,
    generation_completed_at timestamp with time zone,
    generation_duration_ms integer,
    phase_data_collected jsonb,
    status character varying(50) DEFAULT 'not_started'::character varying NOT NULL,
    error_message text,
    total_sections integer DEFAULT 0 NOT NULL,
    sections_completed integer DEFAULT 0 NOT NULL,
    output_formats_generated text[],
    all_approvals_received boolean DEFAULT false NOT NULL,
    phase_completion_ready boolean DEFAULT false NOT NULL,
    phase_completed_at timestamp with time zone,
    phase_completed_by integer,
    generated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    CONSTRAINT cycle_report_test_report_generation_status_check CHECK (((status)::text = ANY ((ARRAY['not_started'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- TOC entry 369 (class 1259 OID 122559)
-- Name: cycle_report_test_report_generation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_report_generation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6242 (class 0 OID 0)
-- Dependencies: 369
-- Name: cycle_report_test_report_generation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_report_generation_id_seq OWNED BY public.cycle_report_test_report_generation.id;


--
-- TOC entry 270 (class 1259 OID 35203)
-- Name: cycle_report_test_report_sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cycle_report_test_report_sections (
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    section_id integer NOT NULL,
    phase_id integer NOT NULL,
    section_name character varying NOT NULL,
    section_order integer NOT NULL,
    section_type character varying NOT NULL,
    content_text text,
    content_data json,
    artifacts json,
    metrics_summary json,
    created_by_id integer,
    updated_by_id integer,
    id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    section_title character varying(255) NOT NULL,
    section_content jsonb,
    data_sources jsonb,
    last_generated_at timestamp with time zone,
    requires_refresh boolean DEFAULT false,
    status character varying(50) DEFAULT 'draft'::character varying,
    tester_approved boolean DEFAULT false,
    tester_approved_by integer,
    tester_approved_at timestamp with time zone,
    tester_notes text,
    report_owner_approved boolean DEFAULT false,
    report_owner_approved_by integer,
    report_owner_approved_at timestamp with time zone,
    report_owner_notes text,
    executive_approved boolean DEFAULT false,
    executive_approved_by integer,
    executive_approved_at timestamp with time zone,
    executive_notes text,
    markdown_content text,
    html_content text,
    pdf_path character varying(500)
);


--
-- TOC entry 6243 (class 0 OID 0)
-- Dependencies: 270
-- Name: TABLE cycle_report_test_report_sections; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_report_test_report_sections IS 'Test report sections with built-in approval workflow';


--
-- TOC entry 373 (class 1259 OID 122796)
-- Name: cycle_report_test_report_sections_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cycle_report_test_report_sections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6244 (class 0 OID 0)
-- Dependencies: 373
-- Name: cycle_report_test_report_sections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cycle_report_test_report_sections_id_seq OWNED BY public.cycle_report_test_report_sections.id;


--
-- TOC entry 223 (class 1259 OID 31810)
-- Name: cycle_reports; Type: TABLE; Schema: public; Owner: -
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
    workflow_id character varying(255),
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6245 (class 0 OID 0)
-- Dependencies: 223
-- Name: TABLE cycle_reports; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cycle_reports IS 'Instances of reports being tested in specific test cycles';


--
-- TOC entry 268 (class 1259 OID 34612)
-- Name: data_owner_phase_audit_logs_legacy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_owner_phase_audit_logs_legacy (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    phase_id uuid
);


--
-- TOC entry 267 (class 1259 OID 34611)
-- Name: data_owner_phase_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_owner_phase_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6246 (class 0 OID 0)
-- Dependencies: 267
-- Name: data_owner_phase_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_owner_phase_audit_log_audit_id_seq OWNED BY public.data_owner_phase_audit_logs_legacy.audit_id;


--
-- TOC entry 328 (class 1259 OID 119544)
-- Name: data_profiling_configurations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_profiling_configurations (
    id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    source_type public.profilingsourcetype NOT NULL,
    profiling_mode public.profilingmode DEFAULT 'sample_based'::public.profilingmode,
    data_source_id integer,
    file_upload_id integer,
    use_timeframe boolean DEFAULT false,
    timeframe_start timestamp without time zone,
    timeframe_end timestamp without time zone,
    timeframe_column character varying(255),
    sample_size bigint,
    sample_percentage double precision,
    sample_method character varying(50),
    partition_column character varying(255),
    partition_count integer DEFAULT 10,
    max_memory_mb integer DEFAULT 1024,
    custom_query text,
    table_name character varying(255),
    schema_name character varying(255),
    where_clause text,
    exclude_columns json,
    include_columns json,
    profile_relationships boolean DEFAULT true,
    profile_distributions boolean DEFAULT true,
    profile_patterns boolean DEFAULT true,
    detect_anomalies boolean DEFAULT true,
    is_scheduled boolean DEFAULT false,
    schedule_cron character varying(100),
    last_run_at timestamp without time zone,
    next_run_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 327 (class 1259 OID 119543)
-- Name: data_profiling_configurations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_profiling_configurations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6247 (class 0 OID 0)
-- Dependencies: 327
-- Name: data_profiling_configurations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_profiling_configurations_id_seq OWNED BY public.data_profiling_configurations.id;


--
-- TOC entry 330 (class 1259 OID 119594)
-- Name: data_profiling_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_profiling_jobs (
    id integer NOT NULL,
    configuration_id integer NOT NULL,
    job_id character varying(255) NOT NULL,
    status public.profilingstatus DEFAULT 'pending'::public.profilingstatus NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    duration_seconds integer,
    total_records bigint,
    records_processed bigint,
    records_failed bigint,
    processing_rate double precision,
    memory_peak_mb integer,
    cpu_peak_percent double precision,
    profile_results json,
    anomalies_detected integer,
    data_quality_score double precision,
    error_message text,
    error_details json,
    retry_count integer DEFAULT 0,
    checkpoint_data json,
    last_checkpoint_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 329 (class 1259 OID 119593)
-- Name: data_profiling_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_profiling_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6248 (class 0 OID 0)
-- Dependencies: 329
-- Name: data_profiling_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_profiling_jobs_id_seq OWNED BY public.data_profiling_jobs.id;


--
-- TOC entry 324 (class 1259 OID 119389)
-- Name: data_profiling_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_profiling_rules (
    id integer NOT NULL,
    cycle_id integer,
    report_id integer,
    attribute_id integer,
    rule_name character varying(255) NOT NULL,
    rule_description text,
    rule_type character varying(50),
    is_active boolean DEFAULT true,
    rule_config json NOT NULL,
    severity character varying(20) DEFAULT 'warning'::character varying,
    auto_flag boolean DEFAULT true,
    notification_required boolean DEFAULT false,
    is_expensive boolean DEFAULT false,
    max_sample_size integer,
    last_execution_at timestamp without time zone,
    total_executions integer DEFAULT 0,
    total_violations integer DEFAULT 0,
    avg_execution_time_ms double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 323 (class 1259 OID 119388)
-- Name: data_profiling_rules_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_profiling_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6249 (class 0 OID 0)
-- Dependencies: 323
-- Name: data_profiling_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_profiling_rules_id_seq OWNED BY public.data_profiling_rules.id;


--
-- TOC entry 326 (class 1259 OID 119519)
-- Name: data_profiling_uploads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_profiling_uploads (
    id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    file_path text NOT NULL,
    file_size bigint,
    file_type character varying(50),
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id integer
);


--
-- TOC entry 325 (class 1259 OID 119518)
-- Name: data_profiling_uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_profiling_uploads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6250 (class 0 OID 0)
-- Dependencies: 325
-- Name: data_profiling_uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_profiling_uploads_id_seq OWNED BY public.data_profiling_uploads.id;


--
-- TOC entry 296 (class 1259 OID 115832)
-- Name: data_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_queries (
    query_id uuid DEFAULT gen_random_uuid() NOT NULL,
    data_source_id uuid NOT NULL,
    query_name character varying(255) NOT NULL,
    query_type character varying(50) NOT NULL,
    query_template text NOT NULL,
    parameters jsonb,
    estimated_rows integer,
    execution_timeout_seconds integer DEFAULT 300 NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 238 (class 1259 OID 32826)
-- Name: escalation_email_logs; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 237 (class 1259 OID 32825)
-- Name: escalation_email_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.escalation_email_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6251 (class 0 OID 0)
-- Dependencies: 237
-- Name: escalation_email_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.escalation_email_logs_log_id_seq OWNED BY public.escalation_email_logs.log_id;


--
-- TOC entry 338 (class 1259 OID 119953)
-- Name: fry14m_scheduled1_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fry14m_scheduled1_data (
    id integer NOT NULL,
    reference_number character varying(50),
    customer_id character varying(50),
    bank_id character varying(20),
    period_id character varying(20),
    corporate_id character varying(50),
    state character varying(2),
    zip_code character varying(20),
    credit_card_type integer,
    product_type integer,
    lending_type integer,
    revolve_feature integer,
    network_id integer,
    secured_credit_type integer,
    loan_source_channel integer,
    purchased_credit_deteriorated_status integer,
    cycle_ending_balance numeric(20,2),
    promotional_balance_mix numeric(20,2),
    cash_balance_mix numeric(20,2),
    penalty_balance_mix numeric(20,2),
    other_balance_mix numeric(20,2),
    average_daily_balance numeric(20,2),
    month_ending_balance numeric(20,2),
    total_reward_cash numeric(20,2),
    reward_type integer,
    account_cycle_date date,
    account_origination_date date,
    acquisition_date date,
    credit_bureau_score_refresh_date date,
    next_payment_due_date date,
    collection_re_age_date date,
    customer_service_re_age_date date,
    date_co_borrower_added date,
    multiple_banking_relationships integer,
    multiple_credit_card_relationships integer,
    joint_account integer,
    authorized_users integer,
    flagged_as_securitized integer,
    borrower_income_at_origination numeric(20,2),
    income_source_at_origination integer,
    origination_credit_bureau_score_primary integer,
    origination_credit_bureau_score_co_borrower integer,
    refreshed_credit_bureau_score integer,
    behavioral_score numeric(10,6),
    original_credit_limit numeric(20,2),
    current_credit_limit numeric(20,2),
    current_cash_advance_limit numeric(20,2),
    line_frozen_flag integer,
    line_increase_decrease_flag integer,
    minimum_payment_due numeric(20,2),
    total_payment_due numeric(20,2),
    actual_payment_amount numeric(20,2),
    total_past_due numeric(20,2),
    days_past_due integer,
    apr_at_cycle_end numeric(10,3),
    variable_rate_index numeric(10,3),
    variable_rate_margin numeric(10,3),
    maximum_apr numeric(10,3),
    rate_reset_frequency integer,
    promotional_apr numeric(10,3),
    cash_apr numeric(10,3),
    account_60_plus_dpd_last_three_years_flag integer,
    fee_type integer,
    month_end_account_status_active_closed integer,
    account_sold_flag integer,
    bankruptcy_flag integer,
    loss_sharing integer,
    purchase_amount numeric(20,2),
    cash_advance_amount numeric(20,2),
    balance_transfer_amount numeric(20,2),
    convenience_check_amount numeric(20,2),
    charge_off_reason integer,
    gross_charge_off_amount numeric(20,2),
    recovery_amount numeric(20,2),
    principal_charge_off_amount numeric(20,2),
    probability_of_default numeric(10,5),
    loss_given_default numeric(10,5),
    expected_loss_given_default numeric(10,5),
    exposure_at_default numeric(20,2),
    ead_id_segment character varying(50),
    loss_share_id character varying(50),
    loss_share_rate numeric(10,5),
    other_credits numeric(20,2),
    late_fee numeric(20,2),
    over_limit_fee numeric(20,2),
    nsf_fee numeric(20,2),
    cash_advance_fee numeric(20,2),
    monthly_annual_fee numeric(20,2),
    debt_suspension_fee numeric(20,2),
    balance_transfer_fee numeric(20,2),
    other_fee numeric(20,2),
    cycles_past_due_at_cycle_date integer,
    cycles_past_due_at_month_end integer,
    hardship_program_flag integer,
    payment_assistance_program_flag integer,
    workout_program_flag integer,
    debt_management_program_flag integer,
    forbearance_program_flag integer,
    trial_modification_program_flag integer,
    permanent_modification_program_flag integer,
    short_sale_program_flag integer,
    original_credit_bureau_score_name character varying(100),
    refreshed_credit_bureau_score_name character varying(100),
    behavioral_score_name character varying(100),
    behavioral_score_version character varying(100),
    credit_limit_change_type integer,
    line_change_type integer,
    internal_credit_score_flag integer,
    internal_credit_score_value numeric(10,3),
    entity_type integer,
    national_bank_rssd_id character varying(20),
    utilization_rate numeric(10,3),
    account_age_months integer,
    last_statement_balance numeric(20,2),
    interest_charged numeric(20,2),
    available_credit numeric(20,2),
    payment_channel integer,
    cycle_days integer,
    stmt_closing_balance numeric(20,2),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by character varying(100),
    updated_by character varying(100)
);


--
-- TOC entry 337 (class 1259 OID 119952)
-- Name: fry14m_scheduled1_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fry14m_scheduled1_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6252 (class 0 OID 0)
-- Dependencies: 337
-- Name: fry14m_scheduled1_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fry14m_scheduled1_data_id_seq OWNED BY public.fry14m_scheduled1_data.id;


--
-- TOC entry 229 (class 1259 OID 32164)
-- Name: llm_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_audit_logs (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    phase_id uuid
);


--
-- TOC entry 228 (class 1259 OID 32163)
-- Name: llm_audit_log_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.llm_audit_log_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6253 (class 0 OID 0)
-- Dependencies: 228
-- Name: llm_audit_log_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.llm_audit_log_log_id_seq OWNED BY public.llm_audit_logs.log_id;


--
-- TOC entry 212 (class 1259 OID 31644)
-- Name: lobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lobs (
    lob_id integer NOT NULL,
    lob_name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6254 (class 0 OID 0)
-- Dependencies: 212
-- Name: COLUMN lobs.created_by_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lobs.created_by_id IS 'ID of user who created this record';


--
-- TOC entry 6255 (class 0 OID 0)
-- Dependencies: 212
-- Name: COLUMN lobs.updated_by_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lobs.updated_by_id IS 'ID of user who last updated this record';


--
-- TOC entry 211 (class 1259 OID 31643)
-- Name: lobs_lob_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lobs_lob_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6256 (class 0 OID 0)
-- Dependencies: 211
-- Name: lobs_lob_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lobs_lob_id_seq OWNED BY public.lobs.lob_id;


--
-- TOC entry 279 (class 1259 OID 36251)
-- Name: metrics_execution; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id uuid
);


--
-- TOC entry 278 (class 1259 OID 36234)
-- Name: metrics_phases; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    phase_id uuid
);


--
-- TOC entry 241 (class 1259 OID 33231)
-- Name: observation_approvals_approval_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.observation_approvals_approval_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6257 (class 0 OID 0)
-- Dependencies: 241
-- Name: observation_approvals_approval_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.observation_approvals_approval_id_seq OWNED BY public.cycle_report_observation_mgmt_approvals.approval_id;


--
-- TOC entry 239 (class 1259 OID 33205)
-- Name: observation_impact_assessments_assessment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.observation_impact_assessments_assessment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6258 (class 0 OID 0)
-- Dependencies: 239
-- Name: observation_impact_assessments_assessment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.observation_impact_assessments_assessment_id_seq OWNED BY public.cycle_report_observation_mgmt_impact_assessments.assessment_id;


--
-- TOC entry 245 (class 1259 OID 33287)
-- Name: observation_management_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.observation_management_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6259 (class 0 OID 0)
-- Dependencies: 245
-- Name: observation_management_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.observation_management_audit_logs_log_id_seq OWNED BY public.cycle_report_observation_mgmt_audit_logs.log_id;


--
-- TOC entry 293 (class 1259 OID 98898)
-- Name: observation_records_observation_id_seq1; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.observation_records_observation_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6260 (class 0 OID 0)
-- Dependencies: 293
-- Name: observation_records_observation_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.observation_records_observation_id_seq1 OWNED BY public.cycle_report_observation_mgmt_observation_records.observation_id;


--
-- TOC entry 243 (class 1259 OID 33257)
-- Name: observation_resolutions_resolution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.observation_resolutions_resolution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6261 (class 0 OID 0)
-- Dependencies: 243
-- Name: observation_resolutions_resolution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.observation_resolutions_resolution_id_seq OWNED BY public.cycle_report_observation_mgmt_resolutions.resolution_id;


--
-- TOC entry 314 (class 1259 OID 118234)
-- Name: permission_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permission_audit_log (
    audit_id integer NOT NULL,
    action_type character varying(50) NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id integer NOT NULL,
    permission_id integer,
    role_id integer,
    performed_by integer,
    performed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 264 (class 1259 OID 33616)
-- Name: rbac_permission_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_permission_audit_logs (
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


--
-- TOC entry 263 (class 1259 OID 33615)
-- Name: permission_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permission_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6262 (class 0 OID 0)
-- Dependencies: 263
-- Name: permission_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permission_audit_log_audit_id_seq OWNED BY public.rbac_permission_audit_logs.audit_id;


--
-- TOC entry 313 (class 1259 OID 118233)
-- Name: permission_audit_log_audit_id_seq1; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permission_audit_log_audit_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6263 (class 0 OID 0)
-- Dependencies: 313
-- Name: permission_audit_log_audit_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permission_audit_log_audit_id_seq1 OWNED BY public.permission_audit_log.audit_id;


--
-- TOC entry 249 (class 1259 OID 33398)
-- Name: rbac_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_permissions (
    permission_id integer NOT NULL,
    resource character varying(100) NOT NULL,
    action character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 248 (class 1259 OID 33397)
-- Name: permissions_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permissions_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6264 (class 0 OID 0)
-- Dependencies: 248
-- Name: permissions_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_permission_id_seq OWNED BY public.rbac_permissions.permission_id;


--
-- TOC entry 299 (class 1259 OID 115985)
-- Name: profiling_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profiling_cache (
    cache_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cache_key character varying(500) NOT NULL,
    cache_type character varying(50) NOT NULL,
    cache_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    is_valid boolean DEFAULT true NOT NULL,
    source_identifier character varying(255),
    source_version character varying(50)
);


--
-- TOC entry 300 (class 1259 OID 116122)
-- Name: profiling_executions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profiling_executions (
    execution_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_source_id uuid,
    execution_type character varying(50) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    status character varying(50) NOT NULL,
    profiling_criteria jsonb NOT NULL,
    total_records_profiled integer,
    total_rules_executed integer,
    execution_time_seconds integer,
    records_per_second integer,
    peak_memory_mb integer,
    rules_passed integer,
    rules_failed integer,
    anomalies_detected integer,
    error_message text,
    error_details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer,
    created_by_id integer,
    updated_by_id integer,
    phase_id uuid
);


--
-- TOC entry 297 (class 1259 OID 115858)
-- Name: profiling_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profiling_jobs (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    job_name character varying(255) NOT NULL,
    strategy public.profilingstrategy NOT NULL,
    priority integer DEFAULT 5 NOT NULL,
    source_type character varying(50) NOT NULL,
    source_config jsonb NOT NULL,
    total_records integer,
    total_rules integer,
    estimated_runtime_minutes integer,
    partition_strategy character varying(50),
    partition_count integer DEFAULT 1 NOT NULL,
    max_memory_gb integer DEFAULT 8 NOT NULL,
    max_cpu_cores integer DEFAULT 4 NOT NULL,
    status character varying(50) NOT NULL,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    progress_percent integer DEFAULT 0 NOT NULL,
    records_processed integer DEFAULT 0 NOT NULL,
    rules_executed integer DEFAULT 0 NOT NULL,
    anomalies_found integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer,
    created_by_id integer,
    updated_by_id integer,
    phase_id uuid
);


--
-- TOC entry 298 (class 1259 OID 115896)
-- Name: profiling_partitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profiling_partitions (
    partition_id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    partition_index integer NOT NULL,
    partition_key character varying(255),
    start_value character varying(255),
    end_value character varying(255),
    estimated_records integer,
    status character varying(50) NOT NULL,
    assigned_worker character varying(255),
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    records_processed integer DEFAULT 0 NOT NULL,
    last_checkpoint character varying(255),
    execution_time_seconds integer,
    anomalies_found integer DEFAULT 0 NOT NULL,
    error_message text
);


--
-- TOC entry 262 (class 1259 OID 33568)
-- Name: rbac_resource_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_resource_permissions (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 253 (class 1259 OID 33427)
-- Name: rbac_resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_resources (
    resource_id integer NOT NULL,
    resource_name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    resource_type character varying(50) NOT NULL,
    parent_resource_id integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 312 (class 1259 OID 118201)
-- Name: rbac_role_hierarchy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_role_hierarchy (
    parent_role_id integer NOT NULL,
    child_role_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer,
    CONSTRAINT role_hierarchy_check CHECK ((parent_role_id <> child_role_id))
);


--
-- TOC entry 258 (class 1259 OID 33494)
-- Name: rbac_role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_role_permissions (
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 251 (class 1259 OID 33414)
-- Name: rbac_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_roles (
    role_id integer NOT NULL,
    role_name character varying(100) NOT NULL,
    description text,
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    can_classify_pdes boolean DEFAULT true
);


--
-- TOC entry 260 (class 1259 OID 33542)
-- Name: rbac_user_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_user_permissions (
    user_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted boolean NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 259 (class 1259 OID 33517)
-- Name: rbac_user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 266 (class 1259 OID 33715)
-- Name: regulatory_data_dictionaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regulatory_data_dictionaries (
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
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 265 (class 1259 OID 33714)
-- Name: regulatory_data_dictionary_dict_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regulatory_data_dictionary_dict_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6265 (class 0 OID 0)
-- Dependencies: 265
-- Name: regulatory_data_dictionary_dict_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regulatory_data_dictionary_dict_id_seq OWNED BY public.regulatory_data_dictionaries.dict_id;


--
-- TOC entry 303 (class 1259 OID 116448)
-- Name: reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reports (
    id integer NOT NULL,
    report_number character varying(50) NOT NULL,
    report_name character varying(255) NOT NULL,
    description text,
    frequency character varying(50),
    business_unit character varying(100),
    regulatory_requirement boolean DEFAULT false,
    status public.report_status_enum DEFAULT 'Active'::public.report_status_enum,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    updated_by integer,
    report_owner_id integer,
    lob_id integer,
    is_active boolean DEFAULT true NOT NULL,
    regulation character varying(255),
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 302 (class 1259 OID 116447)
-- Name: report_inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.report_inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6266 (class 0 OID 0)
-- Dependencies: 302
-- Name: report_inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.report_inventory_id_seq OWNED BY public.reports.id;


--
-- TOC entry 232 (class 1259 OID 32434)
-- Name: request_info_audit_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.request_info_audit_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6267 (class 0 OID 0)
-- Dependencies: 232
-- Name: request_info_audit_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.request_info_audit_logs_log_id_seq OWNED BY public.cycle_report_request_info_audit_logs.log_id;


--
-- TOC entry 261 (class 1259 OID 33567)
-- Name: resource_permissions_resource_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resource_permissions_resource_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6268 (class 0 OID 0)
-- Dependencies: 261
-- Name: resource_permissions_resource_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resource_permissions_resource_permission_id_seq OWNED BY public.rbac_resource_permissions.resource_permission_id;


--
-- TOC entry 252 (class 1259 OID 33426)
-- Name: resources_resource_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resources_resource_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6269 (class 0 OID 0)
-- Dependencies: 252
-- Name: resources_resource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resources_resource_id_seq OWNED BY public.rbac_resources.resource_id;


--
-- TOC entry 250 (class 1259 OID 33413)
-- Name: roles_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6270 (class 0 OID 0)
-- Dependencies: 250
-- Name: roles_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_role_id_seq OWNED BY public.rbac_roles.role_id;


--
-- TOC entry 377 (class 1259 OID 122969)
-- Name: scoping_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scoping_audit_log (
    audit_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id integer NOT NULL,
    action character varying(100) NOT NULL,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    details jsonb
);


--
-- TOC entry 6271 (class 0 OID 0)
-- Dependencies: 377
-- Name: TABLE scoping_audit_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.scoping_audit_log IS 'Audit trail for scoping phase activities';


--
-- TOC entry 376 (class 1259 OID 122968)
-- Name: scoping_audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scoping_audit_log_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6272 (class 0 OID 0)
-- Dependencies: 376
-- Name: scoping_audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scoping_audit_log_audit_id_seq OWNED BY public.scoping_audit_log.audit_id;


--
-- TOC entry 226 (class 1259 OID 31938)
-- Name: scoping_submissions_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scoping_submissions_submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6273 (class 0 OID 0)
-- Dependencies: 226
-- Name: scoping_submissions_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scoping_submissions_submission_id_seq OWNED BY public.cycle_report_scoping_submissions.submission_id;


--
-- TOC entry 301 (class 1259 OID 116157)
-- Name: secure_data_access_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.secure_data_access_logs (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id integer NOT NULL,
    table_name character varying(255) NOT NULL,
    column_name character varying(255) NOT NULL,
    record_identifier character varying(255),
    security_classification public.securityclassification NOT NULL,
    access_type character varying(50) NOT NULL,
    access_reason text,
    ip_address character varying(45),
    user_agent character varying(500),
    accessed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 214 (class 1259 OID 31668)
-- Name: universal_sla_configurations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_sla_configurations (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 213 (class 1259 OID 31667)
-- Name: sla_configurations_sla_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sla_configurations_sla_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6274 (class 0 OID 0)
-- Dependencies: 213
-- Name: sla_configurations_sla_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sla_configurations_sla_config_id_seq OWNED BY public.universal_sla_configurations.sla_config_id;


--
-- TOC entry 222 (class 1259 OID 31772)
-- Name: universal_sla_escalation_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_sla_escalation_rules (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 221 (class 1259 OID 31771)
-- Name: sla_escalation_rules_escalation_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sla_escalation_rules_escalation_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6275 (class 0 OID 0)
-- Dependencies: 221
-- Name: sla_escalation_rules_escalation_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sla_escalation_rules_escalation_rule_id_seq OWNED BY public.universal_sla_escalation_rules.escalation_rule_id;


--
-- TOC entry 231 (class 1259 OID 32192)
-- Name: universal_sla_violation_trackings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_sla_violation_trackings (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    phase_id uuid
);


--
-- TOC entry 230 (class 1259 OID 32191)
-- Name: sla_violation_tracking_violation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sla_violation_tracking_violation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6276 (class 0 OID 0)
-- Dependencies: 230
-- Name: sla_violation_tracking_violation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sla_violation_tracking_violation_id_seq OWNED BY public.universal_sla_violation_trackings.violation_id;


--
-- TOC entry 218 (class 1259 OID 31736)
-- Name: test_cycles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.test_cycles (
    cycle_id integer NOT NULL,
    cycle_name character varying(255) NOT NULL,
    description text,
    test_executive_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    start_date date NOT NULL,
    end_date date,
    status character varying(50) NOT NULL,
    workflow_id character varying(255),
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6277 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN test_cycles.workflow_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.test_cycles.workflow_id IS 'Temporal workflow ID for tracking workflow execution';


--
-- TOC entry 217 (class 1259 OID 31735)
-- Name: test_cycles_cycle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.test_cycles_cycle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6278 (class 0 OID 0)
-- Dependencies: 217
-- Name: test_cycles_cycle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.test_cycles_cycle_id_seq OWNED BY public.test_cycles.cycle_id;


--
-- TOC entry 269 (class 1259 OID 35202)
-- Name: test_report_sections_section_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.test_report_sections_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6279 (class 0 OID 0)
-- Dependencies: 269
-- Name: test_report_sections_section_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.test_report_sections_section_id_seq OWNED BY public.cycle_report_test_report_sections.section_id;


--
-- TOC entry 284 (class 1259 OID 36707)
-- Name: universal_assignment_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_assignment_histories (
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


--
-- TOC entry 340 (class 1259 OID 120189)
-- Name: universal_assignment_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_assignment_history (
    history_id integer NOT NULL,
    assignment_id character varying(36) NOT NULL,
    changed_by_user_id integer NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    action character varying(50) NOT NULL,
    field_changed character varying(100),
    old_value text,
    new_value text,
    change_reason text,
    change_metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6280 (class 0 OID 0)
-- Dependencies: 340
-- Name: TABLE universal_assignment_history; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.universal_assignment_history IS 'Tracks all changes to universal assignments for audit trail and metrics. Essential for tracking rule approval iterations between Tester and Report Owner.';


--
-- TOC entry 6281 (class 0 OID 0)
-- Dependencies: 340
-- Name: COLUMN universal_assignment_history.change_metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.universal_assignment_history.change_metadata IS 'JSONB field containing structured data about the change, including old and new values in their original format';


--
-- TOC entry 283 (class 1259 OID 36706)
-- Name: universal_assignment_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.universal_assignment_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6282 (class 0 OID 0)
-- Dependencies: 283
-- Name: universal_assignment_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.universal_assignment_history_history_id_seq OWNED BY public.universal_assignment_histories.history_id;


--
-- TOC entry 339 (class 1259 OID 120188)
-- Name: universal_assignment_history_history_id_seq1; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.universal_assignment_history_history_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6283 (class 0 OID 0)
-- Dependencies: 339
-- Name: universal_assignment_history_history_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.universal_assignment_history_history_id_seq1 OWNED BY public.universal_assignment_history.history_id;


--
-- TOC entry 282 (class 1259 OID 36649)
-- Name: universal_assignments; Type: TABLE; Schema: public; Owner: -
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
    parent_assignment_id character varying(36),
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 6284 (class 0 OID 0)
-- Dependencies: 282
-- Name: TABLE universal_assignments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.universal_assignments IS 'Flexible assignment system for any entity to any user';


--
-- TOC entry 280 (class 1259 OID 36294)
-- Name: universal_version_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_version_histories (
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    phase_id uuid
);


--
-- TOC entry 216 (class 1259 OID 31679)
-- Name: users; Type: TABLE; Schema: public; Owner: -
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_cdo boolean DEFAULT false
);


--
-- TOC entry 215 (class 1259 OID 31678)
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6285 (class 0 OID 0)
-- Dependencies: 215
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- TOC entry 341 (class 1259 OID 120224)
-- Name: v_rule_approval_iterations; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_rule_approval_iterations AS
 SELECT ua.assignment_id,
    (ua.context_data ->> 'cycle_id'::text) AS cycle_id,
    (ua.context_data ->> 'report_id'::text) AS report_id,
    (ua.context_data ->> 'report_name'::text) AS report_name,
    count(DISTINCT uah.history_id) FILTER (WHERE (((uah.action)::text = 'completed'::text) AND (uah.new_value ~~ '%rejected%'::text))) AS rejection_count,
    count(DISTINCT uah.history_id) FILTER (WHERE (((uah.action)::text = 'completed'::text) AND (uah.new_value ~~ '%approved%'::text))) AS approval_count,
    count(DISTINCT uah.history_id) FILTER (WHERE ((uah.action)::text = ANY ((ARRAY['created'::character varying, 'assigned'::character varying, 'started'::character varying, 'completed'::character varying])::text[]))) AS total_state_changes,
    min(uah.changed_at) FILTER (WHERE ((uah.action)::text = 'created'::text)) AS first_created_at,
    max(uah.changed_at) FILTER (WHERE ((uah.action)::text = 'completed'::text)) AS final_completed_at,
    ua.status AS current_status
   FROM (public.universal_assignments ua
     LEFT JOIN public.universal_assignment_history uah ON (((ua.assignment_id)::text = (uah.assignment_id)::text)))
  WHERE (ua.assignment_type = 'Rule Approval'::public.universal_assignment_type_enum)
  GROUP BY ua.assignment_id, ua.context_data, ua.status;


--
-- TOC entry 384 (class 1259 OID 124653)
-- Name: vw_rfi_current_evidence; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_rfi_current_evidence AS
 SELECT e.id,
    e.test_case_id,
    e.phase_id,
    e.cycle_id,
    e.report_id,
    e.sample_id,
    e.evidence_type,
    e.version_number,
    e.is_current,
    e.parent_evidence_id,
    e.submitted_by,
    e.submitted_at,
    e.submission_notes,
    e.validation_status,
    e.validation_notes,
    e.validated_by,
    e.validated_at,
    e.tester_decision,
    e.tester_notes,
    e.decided_by,
    e.decided_at,
    e.requires_resubmission,
    e.resubmission_deadline,
    e.original_filename,
    e.stored_filename,
    e.file_path,
    e.file_size_bytes,
    e.file_hash,
    e.mime_type,
    e.rfi_data_source_id,
    e.planning_data_source_id,
    e.query_text,
    e.query_parameters,
    e.query_validation_id,
    e.created_at,
    e.updated_at,
    e.created_by,
    e.updated_by,
    tc.test_case_name,
    tc.attribute_name,
    tc.data_owner_id,
    (((u.first_name)::text || ' '::text) || (u.last_name)::text) AS data_owner_name,
    ds.source_name AS data_source_name
   FROM (((public.cycle_report_rfi_evidence e
     JOIN public.cycle_report_test_cases tc ON ((e.test_case_id = tc.id)))
     JOIN public.users u ON ((tc.data_owner_id = u.user_id)))
     LEFT JOIN public.cycle_report_rfi_data_sources ds ON ((e.rfi_data_source_id = ds.data_source_id)))
  WHERE (e.is_current = true);


--
-- TOC entry 286 (class 1259 OID 36958)
-- Name: workflow_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_activities (
    activity_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    activity_type public.activity_type_enum NOT NULL,
    activity_order integer NOT NULL,
    status public.activity_status_enum DEFAULT 'NOT_STARTED'::public.activity_status_enum NOT NULL,
    can_start boolean DEFAULT false NOT NULL,
    can_complete boolean DEFAULT false NOT NULL,
    is_manual boolean DEFAULT true NOT NULL,
    is_optional boolean DEFAULT false NOT NULL,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    revision_requested_at timestamp with time zone,
    revision_requested_by integer,
    revision_reason text,
    blocked_at timestamp with time zone,
    blocked_reason text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    instance_id character varying(255),
    parent_activity_id integer,
    execution_mode character varying(50),
    retry_count integer DEFAULT 0,
    last_error text,
    created_by_id integer,
    updated_by_id integer,
    phase_id integer
);


--
-- TOC entry 285 (class 1259 OID 36957)
-- Name: workflow_activities_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_activities_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6286 (class 0 OID 0)
-- Dependencies: 285
-- Name: workflow_activities_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_activities_activity_id_seq OWNED BY public.workflow_activities.activity_id;


--
-- TOC entry 290 (class 1259 OID 37014)
-- Name: workflow_activity_dependencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_activity_dependencies (
    dependency_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    depends_on_activity character varying(255) NOT NULL,
    dependency_type character varying(50) DEFAULT 'completion'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 289 (class 1259 OID 37013)
-- Name: workflow_activity_dependencies_dependency_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_activity_dependencies_dependency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6287 (class 0 OID 0)
-- Dependencies: 289
-- Name: workflow_activity_dependencies_dependency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_activity_dependencies_dependency_id_seq OWNED BY public.workflow_activity_dependencies.dependency_id;


--
-- TOC entry 288 (class 1259 OID 36994)
-- Name: workflow_activity_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_activity_histories (
    history_id integer NOT NULL,
    activity_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    from_status character varying(50),
    to_status character varying(50) NOT NULL,
    changed_by integer NOT NULL,
    changed_at timestamp with time zone DEFAULT now() NOT NULL,
    change_reason text,
    metadata jsonb,
    phase_id uuid
);


--
-- TOC entry 287 (class 1259 OID 36993)
-- Name: workflow_activity_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_activity_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6288 (class 0 OID 0)
-- Dependencies: 287
-- Name: workflow_activity_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_activity_history_history_id_seq OWNED BY public.workflow_activity_histories.history_id;


--
-- TOC entry 292 (class 1259 OID 37028)
-- Name: workflow_activity_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_activity_templates (
    template_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    activity_type public.activity_type_enum NOT NULL,
    activity_order integer NOT NULL,
    description text,
    is_manual boolean DEFAULT true NOT NULL,
    is_optional boolean DEFAULT false NOT NULL,
    required_role character varying(100),
    auto_complete_on_event character varying(100),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    handler_name character varying(255),
    timeout_seconds integer DEFAULT 300,
    retry_policy json,
    conditional_expression text,
    execution_mode character varying(50) DEFAULT 'sequential'::character varying,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 291 (class 1259 OID 37027)
-- Name: workflow_activity_templates_template_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_activity_templates_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6289 (class 0 OID 0)
-- Dependencies: 291
-- Name: workflow_activity_templates_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_activity_templates_template_id_seq OWNED BY public.workflow_activity_templates.template_id;


--
-- TOC entry 276 (class 1259 OID 35552)
-- Name: workflow_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_alerts (
    alert_id integer NOT NULL,
    execution_id character varying(36),
    workflow_type character varying(100),
    phase_name character varying(50),
    alert_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    threshold_value double precision,
    actual_value double precision,
    alert_message text,
    created_at timestamp with time zone,
    acknowledged boolean,
    acknowledged_by integer,
    acknowledged_at timestamp with time zone,
    resolved boolean,
    resolved_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 275 (class 1259 OID 35551)
-- Name: workflow_alerts_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_alerts_alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6290 (class 0 OID 0)
-- Dependencies: 275
-- Name: workflow_alerts_alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_alerts_alert_id_seq OWNED BY public.workflow_alerts.alert_id;


--
-- TOC entry 271 (class 1259 OID 35489)
-- Name: workflow_executions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_executions (
    execution_id character varying(36) NOT NULL,
    workflow_id character varying(100) NOT NULL,
    workflow_run_id character varying(100) NOT NULL,
    workflow_type character varying(100) NOT NULL,
    workflow_version character varying(20),
    cycle_id integer NOT NULL,
    report_id integer,
    initiated_by integer NOT NULL,
    status public.workflowexecutionstatus,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    input_data json,
    output_data json,
    error_details json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer,
    phase_id uuid
);


--
-- TOC entry 273 (class 1259 OID 35517)
-- Name: workflow_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_metrics (
    metric_id integer NOT NULL,
    workflow_type character varying(100) NOT NULL,
    phase_name character varying(50),
    activity_name character varying(100),
    step_type public.steptype,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    execution_count integer,
    success_count integer,
    failure_count integer,
    avg_duration double precision,
    min_duration double precision,
    max_duration double precision,
    p50_duration double precision,
    p90_duration double precision,
    p95_duration double precision,
    p99_duration double precision,
    avg_retry_count double precision,
    timeout_count integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 272 (class 1259 OID 35516)
-- Name: workflow_metrics_metric_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_metrics_metric_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6291 (class 0 OID 0)
-- Dependencies: 272
-- Name: workflow_metrics_metric_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_metrics_metric_id_seq OWNED BY public.workflow_metrics.metric_id;


--
-- TOC entry 225 (class 1259 OID 31833)
-- Name: workflow_phases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_phases (
    phase_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name public.workflow_phase_enum NOT NULL,
    status public.phase_status_enum NOT NULL,
    planned_start_date date,
    planned_end_date date,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    state public.workflow_phase_state_enum DEFAULT 'Not Started'::public.workflow_phase_state_enum NOT NULL,
    schedule_status public.workflow_phase_status_enum DEFAULT 'On Track'::public.workflow_phase_status_enum NOT NULL,
    state_override public.workflow_phase_state_enum,
    status_override public.workflow_phase_status_enum,
    override_reason text,
    override_by integer,
    override_at timestamp with time zone,
    started_by integer,
    completed_by integer,
    notes text,
    metadata jsonb,
    phase_data jsonb,
    created_by_id integer,
    updated_by_id integer,
    phase_order integer,
    data_requested_at timestamp with time zone,
    data_requested_by integer,
    data_received_at timestamp with time zone,
    rules_generated_at timestamp with time zone,
    profiling_executed_at timestamp with time zone,
    risk_level character varying(20),
    progress_percentage integer DEFAULT 0,
    estimated_completion_date date,
    sla_deadline timestamp with time zone,
    is_sla_breached boolean DEFAULT false,
    CONSTRAINT workflow_phases_phase_order_check CHECK (((phase_order >= 1) AND (phase_order <= 9))),
    CONSTRAINT workflow_phases_risk_level_check CHECK ((((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])) OR (risk_level IS NULL)))
);


--
-- TOC entry 224 (class 1259 OID 31832)
-- Name: workflow_phases_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_phases_phase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 6292 (class 0 OID 0)
-- Dependencies: 224
-- Name: workflow_phases_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_phases_phase_id_seq OWNED BY public.workflow_phases.phase_id;


--
-- TOC entry 274 (class 1259 OID 35529)
-- Name: workflow_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_steps (
    step_id character varying(36) NOT NULL,
    execution_id character varying(36) NOT NULL,
    parent_step_id character varying(36),
    step_name character varying(100) NOT NULL,
    step_type public.steptype NOT NULL,
    phase_name character varying(50),
    activity_name character varying(100),
    status public.workflowexecutionstatus,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    attempt_number integer,
    max_attempts integer,
    retry_delay_seconds integer,
    input_data json,
    output_data json,
    error_details json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 277 (class 1259 OID 35573)
-- Name: workflow_transitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_transitions (
    transition_id character varying(36) NOT NULL,
    execution_id character varying(36) NOT NULL,
    from_step_id character varying(36),
    to_step_id character varying(36),
    transition_type character varying(50),
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    condition_evaluated character varying(200),
    condition_result boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    updated_by_id integer
);


--
-- TOC entry 4583 (class 2604 OID 118318)
-- Name: activity_definitions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_definitions ALTER COLUMN id SET DEFAULT nextval('public.activity_definitions_id_seq'::regclass);


--
-- TOC entry 4593 (class 2604 OID 118340)
-- Name: activity_states id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states ALTER COLUMN id SET DEFAULT nextval('public.activity_states_id_seq'::regclass);


--
-- TOC entry 4641 (class 2604 OID 119627)
-- Name: attribute_profile_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results ALTER COLUMN id SET DEFAULT nextval('public.attribute_profile_results_id_seq'::regclass);


--
-- TOC entry 4411 (class 2604 OID 33449)
-- Name: attribute_version_change_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_change_logs ALTER COLUMN log_id SET DEFAULT nextval('public.attribute_version_change_logs_log_id_seq'::regclass);


--
-- TOC entry 4414 (class 2604 OID 33471)
-- Name: attribute_version_comparisons comparison_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_comparisons ALTER COLUMN comparison_id SET DEFAULT nextval('public.attribute_version_comparisons_comparison_id_seq'::regclass);


--
-- TOC entry 4351 (class 2604 OID 31757)
-- Name: audit_logs audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN audit_id SET DEFAULT nextval('public.audit_log_audit_id_seq'::regclass);


--
-- TOC entry 4816 (class 2604 OID 123268)
-- Name: cycle_report_data_profiling_results result_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results ALTER COLUMN result_id SET DEFAULT nextval('public.cycle_report_data_profiling_results_result_id_seq'::regclass);


--
-- TOC entry 4760 (class 2604 OID 122158)
-- Name: cycle_report_document_access_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs ALTER COLUMN log_id SET DEFAULT nextval('public.cycle_report_document_access_logs_log_id_seq'::regclass);


--
-- TOC entry 4764 (class 2604 OID 122170)
-- Name: cycle_report_document_extractions extraction_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions ALTER COLUMN extraction_id SET DEFAULT nextval('public.cycle_report_document_extractions_extraction_id_seq'::regclass);


--
-- TOC entry 4734 (class 2604 OID 121860)
-- Name: cycle_report_documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_documents_id_seq'::regclass);


--
-- TOC entry 4710 (class 2604 OID 121448)
-- Name: cycle_report_observation_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_observation_groups_id_seq'::regclass);


--
-- TOC entry 4393 (class 2604 OID 33235)
-- Name: cycle_report_observation_mgmt_approvals approval_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals ALTER COLUMN approval_id SET DEFAULT nextval('public.observation_approvals_approval_id_seq'::regclass);


--
-- TOC entry 4398 (class 2604 OID 33291)
-- Name: cycle_report_observation_mgmt_audit_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_audit_logs ALTER COLUMN log_id SET DEFAULT nextval('public.observation_management_audit_logs_log_id_seq'::regclass);


--
-- TOC entry 4390 (class 2604 OID 33209)
-- Name: cycle_report_observation_mgmt_impact_assessments assessment_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments ALTER COLUMN assessment_id SET DEFAULT nextval('public.observation_impact_assessments_assessment_id_seq'::regclass);


--
-- TOC entry 4495 (class 2604 OID 98902)
-- Name: cycle_report_observation_mgmt_observation_records observation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records ALTER COLUMN observation_id SET DEFAULT nextval('public.observation_records_observation_id_seq1'::regclass);


--
-- TOC entry 4650 (class 2604 OID 119700)
-- Name: cycle_report_observation_mgmt_preliminary_findings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_observation_mgmt_preliminary_findings_id_seq'::regclass);


--
-- TOC entry 4396 (class 2604 OID 33261)
-- Name: cycle_report_observation_mgmt_resolutions resolution_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions ALTER COLUMN resolution_id SET DEFAULT nextval('public.observation_resolutions_resolution_id_seq'::regclass);


--
-- TOC entry 4727 (class 2604 OID 121535)
-- Name: cycle_report_observations_unified id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_observations_unified_id_seq'::regclass);


--
-- TOC entry 4541 (class 2604 OID 116496)
-- Name: cycle_report_planning_attribute_version_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attribute_version_history ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_attributes_planning_version_history_id_seq'::regclass);


--
-- TOC entry 4545 (class 2604 OID 116541)
-- Name: cycle_report_planning_attributes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_attributes_planning_id_seq'::regclass);


--
-- TOC entry 4601 (class 2604 OID 118965)
-- Name: cycle_report_planning_data_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_data_sources ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_data_sources_id_seq'::regclass);


--
-- TOC entry 4605 (class 2604 OID 118997)
-- Name: cycle_report_planning_pde_mappings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_pde_mappings_id_seq'::regclass);


--
-- TOC entry 4378 (class 2604 OID 32438)
-- Name: cycle_report_request_info_audit_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs ALTER COLUMN log_id SET DEFAULT nextval('public.request_info_audit_logs_log_id_seq'::regclass);


--
-- TOC entry 4644 (class 2604 OID 119667)
-- Name: cycle_report_request_info_document_versions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_request_info_document_versions_id_seq'::regclass);


--
-- TOC entry 4692 (class 2604 OID 120879)
-- Name: cycle_report_request_info_evidence_validation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_validation ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_request_info_evidence_validation_id_seq'::regclass);


--
-- TOC entry 4684 (class 2604 OID 120806)
-- Name: cycle_report_request_info_testcase_source_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_request_info_testcase_source_evidence_id_seq'::regclass);


--
-- TOC entry 4833 (class 2604 OID 124566)
-- Name: cycle_report_rfi_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_rfi_evidence_id_seq'::regclass);


--
-- TOC entry 4382 (class 2604 OID 32470)
-- Name: cycle_report_scoping_attribute_recommendations_backup recommendation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attribute_recommendations_backup ALTER COLUMN recommendation_id SET DEFAULT nextval('public.attribute_scoping_recommendations_recommendation_id_seq'::regclass);


--
-- TOC entry 4665 (class 2604 OID 120487)
-- Name: cycle_report_scoping_decisions decision_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions ALTER COLUMN decision_id SET DEFAULT nextval('public.cycle_report_scoping_decisions_decision_id_seq'::regclass);


--
-- TOC entry 4368 (class 2604 OID 31942)
-- Name: cycle_report_scoping_submissions submission_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions ALTER COLUMN submission_id SET DEFAULT nextval('public.scoping_submissions_submission_id_seq'::regclass);


--
-- TOC entry 4562 (class 2604 OID 116586)
-- Name: cycle_report_test_cases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_cases_id_seq'::regclass);


--
-- TOC entry 4573 (class 2604 OID 116616)
-- Name: cycle_report_test_cases_document_submissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_cases_document_submissions_id_seq'::regclass);


--
-- TOC entry 4707 (class 2604 OID 121255)
-- Name: cycle_report_test_execution_audit id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_audit ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_execution_audit_id_seq'::regclass);


--
-- TOC entry 4694 (class 2604 OID 121167)
-- Name: cycle_report_test_execution_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_execution_results_id_seq'::regclass);


--
-- TOC entry 4701 (class 2604 OID 121216)
-- Name: cycle_report_test_execution_reviews id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_execution_reviews_id_seq'::regclass);


--
-- TOC entry 4769 (class 2604 OID 122563)
-- Name: cycle_report_test_report_generation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_report_generation_id_seq'::regclass);


--
-- TOC entry 4440 (class 2604 OID 35206)
-- Name: cycle_report_test_report_sections section_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections ALTER COLUMN section_id SET DEFAULT nextval('public.test_report_sections_section_id_seq'::regclass);


--
-- TOC entry 4441 (class 2604 OID 122797)
-- Name: cycle_report_test_report_sections id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections ALTER COLUMN id SET DEFAULT nextval('public.cycle_report_test_report_sections_id_seq'::regclass);


--
-- TOC entry 4437 (class 2604 OID 34615)
-- Name: data_owner_phase_audit_logs_legacy audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_owner_phase_audit_logs_legacy ALTER COLUMN audit_id SET DEFAULT nextval('public.data_owner_phase_audit_log_audit_id_seq'::regclass);


--
-- TOC entry 4630 (class 2604 OID 119547)
-- Name: data_profiling_configurations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations ALTER COLUMN id SET DEFAULT nextval('public.data_profiling_configurations_id_seq'::regclass);


--
-- TOC entry 4636 (class 2604 OID 119597)
-- Name: data_profiling_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs ALTER COLUMN id SET DEFAULT nextval('public.data_profiling_jobs_id_seq'::regclass);


--
-- TOC entry 4612 (class 2604 OID 119392)
-- Name: data_profiling_rules id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules ALTER COLUMN id SET DEFAULT nextval('public.data_profiling_rules_id_seq'::regclass);


--
-- TOC entry 4622 (class 2604 OID 119522)
-- Name: data_profiling_uploads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_uploads ALTER COLUMN id SET DEFAULT nextval('public.data_profiling_uploads_id_seq'::regclass);


--
-- TOC entry 4387 (class 2604 OID 32829)
-- Name: escalation_email_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs ALTER COLUMN log_id SET DEFAULT nextval('public.escalation_email_logs_log_id_seq'::regclass);


--
-- TOC entry 4658 (class 2604 OID 119956)
-- Name: fry14m_scheduled1_data id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fry14m_scheduled1_data ALTER COLUMN id SET DEFAULT nextval('public.fry14m_scheduled1_data_id_seq'::regclass);


--
-- TOC entry 4372 (class 2604 OID 32167)
-- Name: llm_audit_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_audit_logs ALTER COLUMN log_id SET DEFAULT nextval('public.llm_audit_log_log_id_seq'::regclass);


--
-- TOC entry 4338 (class 2604 OID 31647)
-- Name: lobs lob_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lobs ALTER COLUMN lob_id SET DEFAULT nextval('public.lobs_lob_id_seq'::regclass);


--
-- TOC entry 4579 (class 2604 OID 118237)
-- Name: permission_audit_log audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log ALTER COLUMN audit_id SET DEFAULT nextval('public.permission_audit_log_audit_id_seq1'::regclass);


--
-- TOC entry 4430 (class 2604 OID 33619)
-- Name: rbac_permission_audit_logs audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permission_audit_logs ALTER COLUMN audit_id SET DEFAULT nextval('public.permission_audit_log_audit_id_seq'::regclass);


--
-- TOC entry 4401 (class 2604 OID 33401)
-- Name: rbac_permissions permission_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permissions ALTER COLUMN permission_id SET DEFAULT nextval('public.permissions_permission_id_seq'::regclass);


--
-- TOC entry 4426 (class 2604 OID 33571)
-- Name: rbac_resource_permissions resource_permission_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions ALTER COLUMN resource_permission_id SET DEFAULT nextval('public.resource_permissions_resource_permission_id_seq'::regclass);


--
-- TOC entry 4408 (class 2604 OID 33430)
-- Name: rbac_resources resource_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resources ALTER COLUMN resource_id SET DEFAULT nextval('public.resources_resource_id_seq'::regclass);


--
-- TOC entry 4404 (class 2604 OID 33417)
-- Name: rbac_roles role_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles ALTER COLUMN role_id SET DEFAULT nextval('public.roles_role_id_seq'::regclass);


--
-- TOC entry 4434 (class 2604 OID 33718)
-- Name: regulatory_data_dictionaries dict_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulatory_data_dictionaries ALTER COLUMN dict_id SET DEFAULT nextval('public.regulatory_data_dictionary_dict_id_seq'::regclass);


--
-- TOC entry 4536 (class 2604 OID 116451)
-- Name: reports id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports ALTER COLUMN id SET DEFAULT nextval('public.report_inventory_id_seq'::regclass);


--
-- TOC entry 4814 (class 2604 OID 122972)
-- Name: scoping_audit_log audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log ALTER COLUMN audit_id SET DEFAULT nextval('public.scoping_audit_log_audit_id_seq'::regclass);


--
-- TOC entry 4348 (class 2604 OID 31739)
-- Name: test_cycles cycle_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_cycles ALTER COLUMN cycle_id SET DEFAULT nextval('public.test_cycles_cycle_id_seq'::regclass);


--
-- TOC entry 4469 (class 2604 OID 36710)
-- Name: universal_assignment_histories history_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_histories ALTER COLUMN history_id SET DEFAULT nextval('public.universal_assignment_history_history_id_seq'::regclass);


--
-- TOC entry 4661 (class 2604 OID 120192)
-- Name: universal_assignment_history history_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history ALTER COLUMN history_id SET DEFAULT nextval('public.universal_assignment_history_history_id_seq1'::regclass);


--
-- TOC entry 4341 (class 2604 OID 31671)
-- Name: universal_sla_configurations sla_config_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_configurations ALTER COLUMN sla_config_id SET DEFAULT nextval('public.sla_configurations_sla_config_id_seq'::regclass);


--
-- TOC entry 4354 (class 2604 OID 31775)
-- Name: universal_sla_escalation_rules escalation_rule_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules ALTER COLUMN escalation_rule_id SET DEFAULT nextval('public.sla_escalation_rules_escalation_rule_id_seq'::regclass);


--
-- TOC entry 4375 (class 2604 OID 32195)
-- Name: universal_sla_violation_trackings violation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_violation_trackings ALTER COLUMN violation_id SET DEFAULT nextval('public.sla_violation_tracking_violation_id_seq'::regclass);


--
-- TOC entry 4344 (class 2604 OID 31682)
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- TOC entry 4472 (class 2604 OID 36961)
-- Name: workflow_activities activity_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities ALTER COLUMN activity_id SET DEFAULT nextval('public.workflow_activities_activity_id_seq'::regclass);


--
-- TOC entry 4483 (class 2604 OID 37017)
-- Name: workflow_activity_dependencies dependency_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_dependencies ALTER COLUMN dependency_id SET DEFAULT nextval('public.workflow_activity_dependencies_dependency_id_seq'::regclass);


--
-- TOC entry 4481 (class 2604 OID 36997)
-- Name: workflow_activity_histories history_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_histories ALTER COLUMN history_id SET DEFAULT nextval('public.workflow_activity_history_history_id_seq'::regclass);


--
-- TOC entry 4487 (class 2604 OID 37031)
-- Name: workflow_activity_templates template_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_templates ALTER COLUMN template_id SET DEFAULT nextval('public.workflow_activity_templates_template_id_seq'::regclass);


--
-- TOC entry 4454 (class 2604 OID 35555)
-- Name: workflow_alerts alert_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts ALTER COLUMN alert_id SET DEFAULT nextval('public.workflow_alerts_alert_id_seq'::regclass);


--
-- TOC entry 4449 (class 2604 OID 35520)
-- Name: workflow_metrics metric_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_metrics ALTER COLUMN metric_id SET DEFAULT nextval('public.workflow_metrics_metric_id_seq'::regclass);


--
-- TOC entry 4359 (class 2604 OID 31836)
-- Name: workflow_phases phase_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases ALTER COLUMN phase_id SET DEFAULT nextval('public.workflow_phases_phase_id_seq'::regclass);


--
-- TOC entry 5257 (class 2606 OID 118329)
-- Name: activity_definitions activity_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_definitions
    ADD CONSTRAINT activity_definitions_pkey PRIMARY KEY (id);


--
-- TOC entry 5265 (class 2606 OID 118350)
-- Name: activity_states activity_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT activity_states_pkey PRIMARY KEY (id);


--
-- TOC entry 4981 (class 2606 OID 34731)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 5169 (class 2606 OID 115811)
-- Name: attribute_mappings attribute_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_mappings
    ADD CONSTRAINT attribute_mappings_pkey PRIMARY KEY (mapping_id);


--
-- TOC entry 5291 (class 2606 OID 119633)
-- Name: attribute_profile_results attribute_profile_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results
    ADD CONSTRAINT attribute_profile_results_pkey PRIMARY KEY (id);


--
-- TOC entry 4943 (class 2606 OID 32476)
-- Name: cycle_report_scoping_attribute_recommendations_backup attribute_scoping_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attribute_recommendations_backup
    ADD CONSTRAINT attribute_scoping_recommendations_pkey PRIMARY KEY (recommendation_id);


--
-- TOC entry 5003 (class 2606 OID 33455)
-- Name: attribute_version_change_logs attribute_version_change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_change_logs
    ADD CONSTRAINT attribute_version_change_logs_pkey PRIMARY KEY (log_id);


--
-- TOC entry 5008 (class 2606 OID 33477)
-- Name: attribute_version_comparisons attribute_version_comparisons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_comparisons
    ADD CONSTRAINT attribute_version_comparisons_pkey PRIMARY KEY (comparison_id);


--
-- TOC entry 4900 (class 2606 OID 31763)
-- Name: audit_logs audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (audit_id);


--
-- TOC entry 5219 (class 2606 OID 116554)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_pkey PRIMARY KEY (id);


--
-- TOC entry 5216 (class 2606 OID 116501)
-- Name: cycle_report_planning_attribute_version_history cycle_report_attributes_planning_version_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attribute_version_history
    ADD CONSTRAINT cycle_report_attributes_planning_version_history_pkey PRIMARY KEY (id);


--
-- TOC entry 5333 (class 2606 OID 120680)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_a_version_id_phase_id_sample_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_a_version_id_phase_id_sample_id_key UNIQUE (version_id, phase_id, sample_id, attribute_id, lob_id);


--
-- TOC entry 5325 (class 2606 OID 120572)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribu_phase_id_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribu_phase_id_version_number_key UNIQUE (phase_id, version_number);


--
-- TOC entry 5327 (class 2606 OID 120570)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_versions_pkey PRIMARY KEY (version_id);


--
-- TOC entry 5335 (class 2606 OID 120678)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_mapping_pkey PRIMARY KEY (mapping_id);


--
-- TOC entry 5475 (class 2606 OID 123276)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_pkey PRIMARY KEY (result_id);


--
-- TOC entry 5444 (class 2606 OID 122682)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_pkey PRIMARY KEY (version_id);


--
-- TOC entry 5451 (class 2606 OID 122730)
-- Name: cycle_report_data_profiling_rules cycle_report_data_profiling_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rules
    ADD CONSTRAINT cycle_report_data_profiling_rules_pkey PRIMARY KEY (rule_id);


--
-- TOC entry 5271 (class 2606 OID 118972)
-- Name: cycle_report_planning_data_sources cycle_report_data_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_data_sources
    ADD CONSTRAINT cycle_report_data_sources_pkey PRIMARY KEY (id);


--
-- TOC entry 5427 (class 2606 OID 122165)
-- Name: cycle_report_document_access_logs cycle_report_document_access_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs
    ADD CONSTRAINT cycle_report_document_access_logs_pkey PRIMARY KEY (log_id);


--
-- TOC entry 5432 (class 2606 OID 122178)
-- Name: cycle_report_document_extractions cycle_report_document_extractions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions
    ADD CONSTRAINT cycle_report_document_extractions_pkey PRIMARY KEY (extraction_id);


--
-- TOC entry 5400 (class 2606 OID 121886)
-- Name: cycle_report_documents cycle_report_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5402 (class 2606 OID 121888)
-- Name: cycle_report_documents cycle_report_documents_stored_filename_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_stored_filename_key UNIQUE (stored_filename);


--
-- TOC entry 5380 (class 2606 OID 121470)
-- Name: cycle_report_observation_groups cycle_report_observation_group_attribute_id_lob_id_phase_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_group_attribute_id_lob_id_phase_id_key UNIQUE (attribute_id, lob_id, phase_id);


--
-- TOC entry 5382 (class 2606 OID 121468)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_pkey PRIMARY KEY (id);


--
-- TOC entry 5302 (class 2606 OID 119711)
-- Name: cycle_report_observation_mgmt_preliminary_findings cycle_report_observation_mgmt_preliminary_findings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings
    ADD CONSTRAINT cycle_report_observation_mgmt_preliminary_findings_pkey PRIMARY KEY (id);


--
-- TOC entry 5388 (class 2606 OID 121549)
-- Name: cycle_report_observations_unified cycle_report_observations_uni_test_case_id_sample_id_attrib_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_uni_test_case_id_sample_id_attrib_key UNIQUE (test_case_id, sample_id, attribute_id);


--
-- TOC entry 5390 (class 2606 OID 121545)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_pkey PRIMARY KEY (id);


--
-- TOC entry 5392 (class 2606 OID 121547)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_test_execution_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_test_execution_id_key UNIQUE (test_execution_id);


--
-- TOC entry 5273 (class 2606 OID 119007)
-- Name: cycle_report_planning_pde_mappings cycle_report_pde_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT cycle_report_pde_mappings_pkey PRIMARY KEY (id);


--
-- TOC entry 5295 (class 2606 OID 119676)
-- Name: cycle_report_request_info_document_versions cycle_report_request_info_document_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT cycle_report_request_info_document_versions_pkey PRIMARY KEY (id);


--
-- TOC entry 5358 (class 2606 OID 120884)
-- Name: cycle_report_request_info_evidence_validation cycle_report_request_info_evidence_validation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_validation
    ADD CONSTRAINT cycle_report_request_info_evidence_validation_pkey PRIMARY KEY (id);


--
-- TOC entry 5525 (class 2606 OID 125323)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_pkey PRIMARY KEY (evidence_id);


--
-- TOC entry 5518 (class 2606 OID 125274)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versions_pkey PRIMARY KEY (version_id);


--
-- TOC entry 5349 (class 2606 OID 120819)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testc_test_case_id_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testc_test_case_id_version_number_key UNIQUE (test_case_id, version_number);


--
-- TOC entry 5351 (class 2606 OID 120817)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evidence_pkey PRIMARY KEY (id);


--
-- TOC entry 5481 (class 2606 OID 124278)
-- Name: cycle_report_rfi_data_sources cycle_report_rfi_data_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT cycle_report_rfi_data_sources_pkey PRIMARY KEY (data_source_id);


--
-- TOC entry 5494 (class 2606 OID 124580)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_pkey PRIMARY KEY (id);


--
-- TOC entry 5488 (class 2606 OID 124313)
-- Name: cycle_report_rfi_query_validations cycle_report_rfi_query_validations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_query_validations
    ADD CONSTRAINT cycle_report_rfi_query_validations_pkey PRIMARY KEY (validation_id);


--
-- TOC entry 5509 (class 2606 OID 124878)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_pkey PRIMARY KEY (sample_id);


--
-- TOC entry 5503 (class 2606 OID 124810)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_pkey PRIMARY KEY (version_id);


--
-- TOC entry 5464 (class 2606 OID 122925)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attribut_version_id_planning_attribute_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attribut_version_id_planning_attribute_key UNIQUE (version_id, planning_attribute_id);


--
-- TOC entry 5466 (class 2606 OID 122923)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_pkey PRIMARY KEY (attribute_id);


--
-- TOC entry 5321 (class 2606 OID 120493)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_pkey PRIMARY KEY (decision_id);


--
-- TOC entry 5457 (class 2606 OID 122873)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_phase_id_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_phase_id_version_number_key UNIQUE (phase_id, version_number);


--
-- TOC entry 5459 (class 2606 OID 122871)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_pkey PRIMARY KEY (version_id);


--
-- TOC entry 5234 (class 2606 OID 122516)
-- Name: cycle_report_test_cases_document_submissions cycle_report_test_case_document_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT cycle_report_test_case_document_submissions_pkey PRIMARY KEY (submission_id);


--
-- TOC entry 5227 (class 2606 OID 116594)
-- Name: cycle_report_test_cases cycle_report_test_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases
    ADD CONSTRAINT cycle_report_test_cases_pkey PRIMARY KEY (id);


--
-- TOC entry 5375 (class 2606 OID 121261)
-- Name: cycle_report_test_execution_audit cycle_report_test_execution_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_audit
    ADD CONSTRAINT cycle_report_test_execution_audit_pkey PRIMARY KEY (id);


--
-- TOC entry 5361 (class 2606 OID 121176)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_pkey PRIMARY KEY (id);


--
-- TOC entry 5370 (class 2606 OID 121225)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_pkey PRIMARY KEY (id);


--
-- TOC entry 5437 (class 2606 OID 122577)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_phase_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_phase_id_key UNIQUE (phase_id);


--
-- TOC entry 5439 (class 2606 OID 122575)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_pkey PRIMARY KEY (id);


--
-- TOC entry 4909 (class 2606 OID 31816)
-- Name: cycle_reports cycle_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_reports
    ADD CONSTRAINT cycle_reports_pkey PRIMARY KEY (cycle_id, report_id);


--
-- TOC entry 5046 (class 2606 OID 34621)
-- Name: data_owner_phase_audit_logs_legacy data_owner_phase_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_owner_phase_audit_logs_legacy
    ADD CONSTRAINT data_owner_phase_audit_log_pkey PRIMARY KEY (audit_id);


--
-- TOC entry 5282 (class 2606 OID 119562)
-- Name: data_profiling_configurations data_profiling_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_pkey PRIMARY KEY (id);


--
-- TOC entry 5285 (class 2606 OID 119607)
-- Name: data_profiling_jobs data_profiling_jobs_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs
    ADD CONSTRAINT data_profiling_jobs_job_id_key UNIQUE (job_id);


--
-- TOC entry 5287 (class 2606 OID 119605)
-- Name: data_profiling_jobs data_profiling_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs
    ADD CONSTRAINT data_profiling_jobs_pkey PRIMARY KEY (id);


--
-- TOC entry 5276 (class 2606 OID 119405)
-- Name: data_profiling_rules data_profiling_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_pkey PRIMARY KEY (id);


--
-- TOC entry 5280 (class 2606 OID 119527)
-- Name: data_profiling_uploads data_profiling_uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_uploads
    ADD CONSTRAINT data_profiling_uploads_pkey PRIMARY KEY (id);


--
-- TOC entry 5176 (class 2606 OID 115842)
-- Name: data_queries data_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_queries
    ADD CONSTRAINT data_queries_pkey PRIMARY KEY (query_id);


--
-- TOC entry 4958 (class 2606 OID 32835)
-- Name: escalation_email_logs escalation_email_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_pkey PRIMARY KEY (log_id);


--
-- TOC entry 5107 (class 2606 OID 36258)
-- Name: metrics_execution execution_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_execution
    ADD CONSTRAINT execution_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 5308 (class 2606 OID 119962)
-- Name: fry14m_scheduled1_data fry14m_scheduled1_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fry14m_scheduled1_data
    ADD CONSTRAINT fry14m_scheduled1_data_pkey PRIMARY KEY (id);


--
-- TOC entry 4933 (class 2606 OID 32173)
-- Name: llm_audit_logs llm_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_audit_logs
    ADD CONSTRAINT llm_audit_log_pkey PRIMARY KEY (log_id);


--
-- TOC entry 4876 (class 2606 OID 31651)
-- Name: lobs lobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lobs
    ADD CONSTRAINT lobs_pkey PRIMARY KEY (lob_id);


--
-- TOC entry 4971 (class 2606 OID 33241)
-- Name: cycle_report_observation_mgmt_approvals observation_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT observation_approvals_pkey PRIMARY KEY (approval_id);


--
-- TOC entry 4966 (class 2606 OID 33215)
-- Name: cycle_report_observation_mgmt_impact_assessments observation_impact_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT observation_impact_assessments_pkey PRIMARY KEY (assessment_id);


--
-- TOC entry 4979 (class 2606 OID 33297)
-- Name: cycle_report_observation_mgmt_audit_logs observation_management_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_audit_logs
    ADD CONSTRAINT observation_management_audit_logs_pkey PRIMARY KEY (log_id);


--
-- TOC entry 5167 (class 2606 OID 98908)
-- Name: cycle_report_observation_mgmt_observation_records observation_records_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT observation_records_pkey1 PRIMARY KEY (observation_id);


--
-- TOC entry 4976 (class 2606 OID 33266)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_pkey PRIMARY KEY (resolution_id);


--
-- TOC entry 5035 (class 2606 OID 33626)
-- Name: rbac_permission_audit_logs permission_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permission_audit_logs
    ADD CONSTRAINT permission_audit_log_pkey PRIMARY KEY (audit_id);


--
-- TOC entry 5255 (class 2606 OID 118244)
-- Name: permission_audit_log permission_audit_log_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_pkey1 PRIMARY KEY (audit_id);


--
-- TOC entry 4988 (class 2606 OID 33407)
-- Name: rbac_permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (permission_id);


--
-- TOC entry 5105 (class 2606 OID 36240)
-- Name: metrics_phases phase_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_phases
    ADD CONSTRAINT phase_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 5193 (class 2606 OID 115996)
-- Name: profiling_cache profiling_cache_cache_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_cache
    ADD CONSTRAINT profiling_cache_cache_key_key UNIQUE (cache_key);


--
-- TOC entry 5195 (class 2606 OID 115994)
-- Name: profiling_cache profiling_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_cache
    ADD CONSTRAINT profiling_cache_pkey PRIMARY KEY (cache_id);


--
-- TOC entry 5201 (class 2606 OID 116131)
-- Name: profiling_executions profiling_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_pkey PRIMARY KEY (execution_id);


--
-- TOC entry 5185 (class 2606 OID 115875)
-- Name: profiling_jobs profiling_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_pkey PRIMARY KEY (job_id);


--
-- TOC entry 5189 (class 2606 OID 115905)
-- Name: profiling_partitions profiling_partitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_partitions
    ADD CONSTRAINT profiling_partitions_pkey PRIMARY KEY (partition_id);


--
-- TOC entry 5044 (class 2606 OID 33724)
-- Name: regulatory_data_dictionaries regulatory_data_dictionary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulatory_data_dictionaries
    ADD CONSTRAINT regulatory_data_dictionary_pkey PRIMARY KEY (dict_id);


--
-- TOC entry 5212 (class 2606 OID 116459)
-- Name: reports report_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 5214 (class 2606 OID 116461)
-- Name: reports report_inventory_report_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_report_number_key UNIQUE (report_number);


--
-- TOC entry 4941 (class 2606 OID 32444)
-- Name: cycle_report_request_info_audit_logs request_info_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT request_info_audit_logs_pkey PRIMARY KEY (log_id);


--
-- TOC entry 5027 (class 2606 OID 33576)
-- Name: rbac_resource_permissions resource_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT resource_permissions_pkey PRIMARY KEY (resource_permission_id);


--
-- TOC entry 5001 (class 2606 OID 33436)
-- Name: rbac_resources resources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (resource_id);


--
-- TOC entry 5250 (class 2606 OID 118208)
-- Name: rbac_role_hierarchy role_hierarchy_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_hierarchy
    ADD CONSTRAINT role_hierarchy_pkey1 PRIMARY KEY (parent_role_id, child_role_id);


--
-- TOC entry 5013 (class 2606 OID 33501)
-- Name: rbac_role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- TOC entry 4996 (class 2606 OID 33423)
-- Name: rbac_roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (role_id);


--
-- TOC entry 4956 (class 2606 OID 32684)
-- Name: cycle_report_sample_selection_audit_logs sample_selection_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_audit_logs
    ADD CONSTRAINT sample_selection_audit_log_pkey PRIMARY KEY (audit_id);


--
-- TOC entry 5473 (class 2606 OID 122977)
-- Name: scoping_audit_log scoping_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log
    ADD CONSTRAINT scoping_audit_log_pkey PRIMARY KEY (audit_id);


--
-- TOC entry 5116 (class 2606 OID 36388)
-- Name: cycle_report_scoping_decision_versions scoping_decision_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decision_versions
    ADD CONSTRAINT scoping_decision_versions_pkey PRIMARY KEY (decision_version_id);


--
-- TOC entry 4929 (class 2606 OID 31948)
-- Name: cycle_report_scoping_submissions scoping_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT scoping_submissions_pkey PRIMARY KEY (submission_id);


--
-- TOC entry 5207 (class 2606 OID 116167)
-- Name: secure_data_access_logs secure_data_access_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_pkey PRIMARY KEY (access_id);


--
-- TOC entry 4882 (class 2606 OID 31675)
-- Name: universal_sla_configurations sla_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_configurations
    ADD CONSTRAINT sla_configurations_pkey PRIMARY KEY (sla_config_id);


--
-- TOC entry 4907 (class 2606 OID 31781)
-- Name: universal_sla_escalation_rules sla_escalation_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules
    ADD CONSTRAINT sla_escalation_rules_pkey PRIMARY KEY (escalation_rule_id);


--
-- TOC entry 4936 (class 2606 OID 32201)
-- Name: universal_sla_violation_trackings sla_violation_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_violation_trackings
    ADD CONSTRAINT sla_violation_tracking_pkey PRIMARY KEY (violation_id);


--
-- TOC entry 4898 (class 2606 OID 31745)
-- Name: test_cycles test_cycles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_cycles
    ADD CONSTRAINT test_cycles_pkey PRIMARY KEY (cycle_id);


--
-- TOC entry 5060 (class 2606 OID 35210)
-- Name: cycle_report_test_report_sections test_report_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT test_report_sections_pkey PRIMARY KEY (section_id);


--
-- TOC entry 5449 (class 2606 OID 122754)
-- Name: cycle_report_data_profiling_rule_versions uk_profiling_version_number_per_phase; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT uk_profiling_version_number_per_phase UNIQUE (phase_id, version_number);


--
-- TOC entry 5131 (class 2606 OID 36716)
-- Name: universal_assignment_histories universal_assignment_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_histories
    ADD CONSTRAINT universal_assignment_history_pkey PRIMARY KEY (history_id);


--
-- TOC entry 5319 (class 2606 OID 120199)
-- Name: universal_assignment_history universal_assignment_history_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history
    ADD CONSTRAINT universal_assignment_history_pkey1 PRIMARY KEY (history_id);


--
-- TOC entry 5128 (class 2606 OID 36655)
-- Name: universal_assignments universal_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_pkey PRIMARY KEY (assignment_id);


--
-- TOC entry 5261 (class 2606 OID 118331)
-- Name: activity_definitions uq_activity_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_definitions
    ADD CONSTRAINT uq_activity_code UNIQUE (activity_code);


--
-- TOC entry 5151 (class 2606 OID 37026)
-- Name: workflow_activity_dependencies uq_activity_dependencies_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_dependencies
    ADD CONSTRAINT uq_activity_dependencies_unique UNIQUE (phase_name, activity_name, depends_on_activity);


--
-- TOC entry 5269 (class 2606 OID 118352)
-- Name: activity_states uq_activity_state; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT uq_activity_state UNIQUE (cycle_id, report_id, activity_definition_id);


--
-- TOC entry 5159 (class 2606 OID 37042)
-- Name: workflow_activity_templates uq_activity_templates_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_templates
    ADD CONSTRAINT uq_activity_templates_unique UNIQUE (phase_name, activity_name);


--
-- TOC entry 5486 (class 2606 OID 124280)
-- Name: cycle_report_rfi_data_sources uq_data_source_name_owner; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT uq_data_source_name_owner UNIQUE (data_owner_id, source_name);


--
-- TOC entry 5263 (class 2606 OID 118333)
-- Name: activity_definitions uq_phase_activity; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_definitions
    ADD CONSTRAINT uq_phase_activity UNIQUE (phase_name, activity_name);


--
-- TOC entry 5523 (class 2606 OID 125276)
-- Name: cycle_report_request_info_evidence_versions uq_request_info_version_phase_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT uq_request_info_version_phase_number UNIQUE (phase_id, version_number);


--
-- TOC entry 4990 (class 2606 OID 33409)
-- Name: rbac_permissions uq_resource_action; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permissions
    ADD CONSTRAINT uq_resource_action UNIQUE (resource, action);


--
-- TOC entry 5242 (class 2606 OID 122555)
-- Name: cycle_report_test_cases_document_submissions uq_stored_filename; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT uq_stored_filename UNIQUE (stored_filename);


--
-- TOC entry 5300 (class 2606 OID 119678)
-- Name: cycle_report_request_info_document_versions uq_submission_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT uq_submission_version UNIQUE (document_submission_id, version_number);


--
-- TOC entry 5244 (class 2606 OID 122558)
-- Name: cycle_report_test_cases_document_submissions uq_test_case_submission_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT uq_test_case_submission_number UNIQUE (test_case_id, submission_number);


--
-- TOC entry 5501 (class 2606 OID 124582)
-- Name: cycle_report_rfi_evidence uq_test_case_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT uq_test_case_version UNIQUE (test_case_id, version_number);


--
-- TOC entry 5368 (class 2606 OID 121273)
-- Name: cycle_report_test_execution_results uq_test_execution_results_test_case_execution; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT uq_test_execution_results_test_case_execution UNIQUE (test_case_id, execution_number);


--
-- TOC entry 5062 (class 2606 OID 122847)
-- Name: cycle_report_test_report_sections uq_test_report_section_phase; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT uq_test_report_section_phase UNIQUE (phase_id, section_name);


--
-- TOC entry 5064 (class 2606 OID 122849)
-- Name: cycle_report_test_report_sections uq_test_report_section_report; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT uq_test_report_section_report UNIQUE (cycle_id, report_id, section_name);


--
-- TOC entry 5029 (class 2606 OID 33578)
-- Name: rbac_resource_permissions uq_user_resource_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT uq_user_resource_permission UNIQUE (user_id, resource_type, resource_id, permission_id);


--
-- TOC entry 5143 (class 2606 OID 119912)
-- Name: workflow_activities uq_workflow_activities_unique_activity; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT uq_workflow_activities_unique_activity UNIQUE (cycle_id, report_id, phase_id, activity_name);


--
-- TOC entry 5021 (class 2606 OID 33549)
-- Name: rbac_user_permissions user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT user_permissions_pkey PRIMARY KEY (user_id, permission_id);


--
-- TOC entry 5017 (class 2606 OID 33524)
-- Name: rbac_user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- TOC entry 4889 (class 2606 OID 31688)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- TOC entry 5113 (class 2606 OID 36303)
-- Name: universal_version_histories version_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_version_histories
    ADD CONSTRAINT version_history_pkey PRIMARY KEY (id);


--
-- TOC entry 5145 (class 2606 OID 36972)
-- Name: workflow_activities workflow_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_pkey PRIMARY KEY (activity_id);


--
-- TOC entry 5153 (class 2606 OID 37024)
-- Name: workflow_activity_dependencies workflow_activity_dependencies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_dependencies
    ADD CONSTRAINT workflow_activity_dependencies_pkey PRIMARY KEY (dependency_id);


--
-- TOC entry 5147 (class 2606 OID 37002)
-- Name: workflow_activity_histories workflow_activity_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_histories
    ADD CONSTRAINT workflow_activity_history_pkey PRIMARY KEY (history_id);


--
-- TOC entry 5161 (class 2606 OID 37040)
-- Name: workflow_activity_templates workflow_activity_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_templates
    ADD CONSTRAINT workflow_activity_templates_pkey PRIMARY KEY (template_id);


--
-- TOC entry 5092 (class 2606 OID 35560)
-- Name: workflow_alerts workflow_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts
    ADD CONSTRAINT workflow_alerts_pkey PRIMARY KEY (alert_id);


--
-- TOC entry 5071 (class 2606 OID 35497)
-- Name: workflow_executions workflow_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_pkey PRIMARY KEY (execution_id);


--
-- TOC entry 5077 (class 2606 OID 35524)
-- Name: workflow_metrics workflow_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_metrics
    ADD CONSTRAINT workflow_metrics_pkey PRIMARY KEY (metric_id);


--
-- TOC entry 5079 (class 2606 OID 35526)
-- Name: workflow_metrics workflow_metrics_workflow_type_phase_name_activity_name_ste_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_metrics
    ADD CONSTRAINT workflow_metrics_workflow_type_phase_name_activity_name_ste_key UNIQUE (workflow_type, phase_name, activity_name, step_type, period_start, period_end);


--
-- TOC entry 4921 (class 2606 OID 31840)
-- Name: workflow_phases workflow_phases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_pkey PRIMARY KEY (phase_id);


--
-- TOC entry 4923 (class 2606 OID 119915)
-- Name: workflow_phases workflow_phases_unique_phase_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_unique_phase_name UNIQUE (cycle_id, report_id, phase_name);


--
-- TOC entry 5086 (class 2606 OID 35537)
-- Name: workflow_steps workflow_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_pkey PRIMARY KEY (step_id);


--
-- TOC entry 5098 (class 2606 OID 35579)
-- Name: workflow_transitions workflow_transitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_pkey PRIMARY KEY (transition_id);


--
-- TOC entry 5258 (class 1259 OID 118335)
-- Name: idx_activity_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_code ON public.activity_definitions USING btree (activity_code);


--
-- TOC entry 5259 (class 1259 OID 118334)
-- Name: idx_activity_phase_sequence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_phase_sequence ON public.activity_definitions USING btree (phase_name, sequence_order);


--
-- TOC entry 5266 (class 1259 OID 118373)
-- Name: idx_activity_state_context; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_state_context ON public.activity_states USING btree (cycle_id, report_id, phase_name);


--
-- TOC entry 5267 (class 1259 OID 118374)
-- Name: idx_activity_state_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_state_status ON public.activity_states USING btree (status);


--
-- TOC entry 5314 (class 1259 OID 120223)
-- Name: idx_assignment_history_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_history_action ON public.universal_assignment_history USING btree (action);


--
-- TOC entry 5315 (class 1259 OID 120220)
-- Name: idx_assignment_history_assignment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_history_assignment_id ON public.universal_assignment_history USING btree (assignment_id);


--
-- TOC entry 5316 (class 1259 OID 120222)
-- Name: idx_assignment_history_changed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_history_changed_at ON public.universal_assignment_history USING btree (changed_at);


--
-- TOC entry 5317 (class 1259 OID 120221)
-- Name: idx_assignment_history_changed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_history_changed_by ON public.universal_assignment_history USING btree (changed_by_user_id);


--
-- TOC entry 5170 (class 1259 OID 117848)
-- Name: idx_attribute_mappings_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_mappings_created_by ON public.attribute_mappings USING btree (created_by_id);


--
-- TOC entry 5171 (class 1259 OID 117854)
-- Name: idx_attribute_mappings_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_mappings_updated_by ON public.attribute_mappings USING btree (updated_by_id);


--
-- TOC entry 5292 (class 1259 OID 119658)
-- Name: idx_attribute_profiles_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_profiles_attribute ON public.attribute_profile_results USING btree (attribute_id);


--
-- TOC entry 5293 (class 1259 OID 119657)
-- Name: idx_attribute_profiles_job; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_profiles_job ON public.attribute_profile_results USING btree (profiling_job_id);


--
-- TOC entry 4944 (class 1259 OID 117968)
-- Name: idx_attribute_scoping_recommendations_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_scoping_recommendations_created_by ON public.cycle_report_scoping_attribute_recommendations_backup USING btree (created_by_id);


--
-- TOC entry 4945 (class 1259 OID 117974)
-- Name: idx_attribute_scoping_recommendations_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_scoping_recommendations_updated_by ON public.cycle_report_scoping_attribute_recommendations_backup USING btree (updated_by_id);


--
-- TOC entry 5004 (class 1259 OID 117992)
-- Name: idx_attribute_version_change_logs_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_version_change_logs_created_by ON public.attribute_version_change_logs USING btree (created_by_id);


--
-- TOC entry 5005 (class 1259 OID 117998)
-- Name: idx_attribute_version_change_logs_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_version_change_logs_updated_by ON public.attribute_version_change_logs USING btree (updated_by_id);


--
-- TOC entry 5009 (class 1259 OID 118004)
-- Name: idx_attribute_version_comparisons_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_version_comparisons_created_by ON public.attribute_version_comparisons USING btree (created_by_id);


--
-- TOC entry 5010 (class 1259 OID 118010)
-- Name: idx_attribute_version_comparisons_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribute_version_comparisons_updated_by ON public.attribute_version_comparisons USING btree (updated_by_id);


--
-- TOC entry 4937 (class 1259 OID 125401)
-- Name: idx_audit_logs_audit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_audit_logs_audit_id ON public.cycle_report_request_info_audit_logs USING btree (audit_id);


--
-- TOC entry 5190 (class 1259 OID 116196)
-- Name: idx_cache_key_valid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cache_key_valid ON public.profiling_cache USING btree (cache_key, is_valid, expires_at);


--
-- TOC entry 5191 (class 1259 OID 116197)
-- Name: idx_cache_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cache_source ON public.profiling_cache USING btree (source_identifier, cache_type);


--
-- TOC entry 5220 (class 1259 OID 117980)
-- Name: idx_cycle_report_attributes_planning_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_attributes_planning_created_by ON public.cycle_report_planning_attributes USING btree (created_by_id);


--
-- TOC entry 5221 (class 1259 OID 117986)
-- Name: idx_cycle_report_attributes_planning_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_attributes_planning_updated_by ON public.cycle_report_planning_attributes USING btree (updated_by_id);


--
-- TOC entry 5328 (class 1259 OID 120733)
-- Name: idx_cycle_report_data_owner_lob_attribute_versions_data_executi; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_data_executi ON public.cycle_report_data_owner_lob_mapping_versions USING btree (data_executive_id);


--
-- TOC entry 5329 (class 1259 OID 120731)
-- Name: idx_cycle_report_data_owner_lob_attribute_versions_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_phase ON public.cycle_report_data_owner_lob_mapping_versions USING btree (phase_id);


--
-- TOC entry 5330 (class 1259 OID 120732)
-- Name: idx_cycle_report_data_owner_lob_attribute_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_status ON public.cycle_report_data_owner_lob_mapping_versions USING btree (version_status);


--
-- TOC entry 5331 (class 1259 OID 120734)
-- Name: idx_cycle_report_data_owner_lob_attribute_versions_workflow_act; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_workflow_act ON public.cycle_report_data_owner_lob_mapping_versions USING btree (workflow_activity_id);


--
-- TOC entry 5428 (class 1259 OID 122269)
-- Name: idx_cycle_report_document_access_logs_accessed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_access_logs_accessed_at ON public.cycle_report_document_access_logs USING btree (accessed_at);


--
-- TOC entry 5429 (class 1259 OID 122190)
-- Name: idx_cycle_report_document_access_logs_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_access_logs_document_id ON public.cycle_report_document_access_logs USING btree (document_id);


--
-- TOC entry 5430 (class 1259 OID 122268)
-- Name: idx_cycle_report_document_access_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_access_logs_user_id ON public.cycle_report_document_access_logs USING btree (user_id);


--
-- TOC entry 5433 (class 1259 OID 122270)
-- Name: idx_cycle_report_document_extractions_attribute_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_extractions_attribute_name ON public.cycle_report_document_extractions USING btree (attribute_name);


--
-- TOC entry 5434 (class 1259 OID 122191)
-- Name: idx_cycle_report_document_extractions_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_extractions_document_id ON public.cycle_report_document_extractions USING btree (document_id);


--
-- TOC entry 5435 (class 1259 OID 122271)
-- Name: idx_cycle_report_document_extractions_validated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_document_extractions_validated ON public.cycle_report_document_extractions USING btree (is_validated);


--
-- TOC entry 5403 (class 1259 OID 121957)
-- Name: idx_cycle_report_documents_access_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_access_level ON public.cycle_report_documents USING btree (access_level);


--
-- TOC entry 5404 (class 1259 OID 121960)
-- Name: idx_cycle_report_documents_allowed_roles_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_allowed_roles_gin ON public.cycle_report_documents USING gin (allowed_roles);


--
-- TOC entry 5405 (class 1259 OID 121961)
-- Name: idx_cycle_report_documents_allowed_users_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_allowed_users_gin ON public.cycle_report_documents USING gin (allowed_users);


--
-- TOC entry 5406 (class 1259 OID 122152)
-- Name: idx_cycle_report_documents_business_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_business_date ON public.cycle_report_documents USING btree (business_date);


--
-- TOC entry 5407 (class 1259 OID 121965)
-- Name: idx_cycle_report_documents_content_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_content_search ON public.cycle_report_documents USING gin (to_tsvector('english'::regconfig, (((((((COALESCE(document_title, ''::character varying))::text || ' '::text) || COALESCE(document_description, ''::text)) || ' '::text) || COALESCE(content_preview, ''::text)) || ' '::text) || COALESCE(content_summary, ''::text))));


--
-- TOC entry 5408 (class 1259 OID 121949)
-- Name: idx_cycle_report_documents_document_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_document_type ON public.cycle_report_documents USING btree (document_type);


--
-- TOC entry 5409 (class 1259 OID 122153)
-- Name: idx_cycle_report_documents_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_expires_at ON public.cycle_report_documents USING btree (expires_at);


--
-- TOC entry 5410 (class 1259 OID 121962)
-- Name: idx_cycle_report_documents_extracted_metadata_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_extracted_metadata_gin ON public.cycle_report_documents USING gin (extracted_metadata);


--
-- TOC entry 5411 (class 1259 OID 121950)
-- Name: idx_cycle_report_documents_file_format; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_file_format ON public.cycle_report_documents USING btree (file_format);


--
-- TOC entry 5412 (class 1259 OID 121959)
-- Name: idx_cycle_report_documents_file_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_file_hash ON public.cycle_report_documents USING btree (file_hash);


--
-- TOC entry 5413 (class 1259 OID 122151)
-- Name: idx_cycle_report_documents_is_confidential; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_is_confidential ON public.cycle_report_documents USING btree (is_confidential);


--
-- TOC entry 5414 (class 1259 OID 122150)
-- Name: idx_cycle_report_documents_is_encrypted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_is_encrypted ON public.cycle_report_documents USING btree (is_encrypted);


--
-- TOC entry 5415 (class 1259 OID 121956)
-- Name: idx_cycle_report_documents_is_latest_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_is_latest_version ON public.cycle_report_documents USING btree (is_latest_version);


--
-- TOC entry 5416 (class 1259 OID 121948)
-- Name: idx_cycle_report_documents_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_phase_id ON public.cycle_report_documents USING btree (phase_id);


--
-- TOC entry 5417 (class 1259 OID 121952)
-- Name: idx_cycle_report_documents_processing_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_processing_status ON public.cycle_report_documents USING btree (processing_status);


--
-- TOC entry 5418 (class 1259 OID 121958)
-- Name: idx_cycle_report_documents_required_for_completion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_required_for_completion ON public.cycle_report_documents USING btree (required_for_completion);


--
-- TOC entry 5419 (class 1259 OID 121964)
-- Name: idx_cycle_report_documents_search_keywords_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_search_keywords_gin ON public.cycle_report_documents USING gin (search_keywords);


--
-- TOC entry 5420 (class 1259 OID 121981)
-- Name: idx_cycle_report_documents_test_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_test_case_id ON public.cycle_report_documents USING btree (test_case_id);


--
-- TOC entry 5421 (class 1259 OID 121951)
-- Name: idx_cycle_report_documents_upload_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_upload_status ON public.cycle_report_documents USING btree (upload_status);


--
-- TOC entry 5422 (class 1259 OID 121955)
-- Name: idx_cycle_report_documents_uploaded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_uploaded_at ON public.cycle_report_documents USING btree (uploaded_at);


--
-- TOC entry 5423 (class 1259 OID 121954)
-- Name: idx_cycle_report_documents_uploaded_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_uploaded_by ON public.cycle_report_documents USING btree (uploaded_by);


--
-- TOC entry 5424 (class 1259 OID 121963)
-- Name: idx_cycle_report_documents_validation_errors_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_validation_errors_gin ON public.cycle_report_documents USING gin (validation_errors);


--
-- TOC entry 5425 (class 1259 OID 121953)
-- Name: idx_cycle_report_documents_validation_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_documents_validation_status ON public.cycle_report_documents USING btree (validation_status);


--
-- TOC entry 4967 (class 1259 OID 119930)
-- Name: idx_cycle_report_observation_mgmt_approvals_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_approvals_phase_id ON public.cycle_report_observation_mgmt_approvals USING btree (phase_id);


--
-- TOC entry 4977 (class 1259 OID 122388)
-- Name: idx_cycle_report_observation_mgmt_audit_logs_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_audit_logs_phase_id ON public.cycle_report_observation_mgmt_audit_logs USING btree (phase_id);


--
-- TOC entry 4962 (class 1259 OID 119929)
-- Name: idx_cycle_report_observation_mgmt_impact_assessments_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_impact_assessments_phase_id ON public.cycle_report_observation_mgmt_impact_assessments USING btree (phase_id);


--
-- TOC entry 5162 (class 1259 OID 122362)
-- Name: idx_cycle_report_observation_mgmt_observation_records_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_observation_records_phase_id ON public.cycle_report_observation_mgmt_observation_records USING btree (phase_id);


--
-- TOC entry 5303 (class 1259 OID 119942)
-- Name: idx_cycle_report_observation_mgmt_preliminary_findings_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_preliminary_findings_phase_id ON public.cycle_report_observation_mgmt_preliminary_findings USING btree (phase_id);


--
-- TOC entry 4972 (class 1259 OID 119931)
-- Name: idx_cycle_report_observation_mgmt_resolutions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_observation_mgmt_resolutions_phase_id ON public.cycle_report_observation_mgmt_resolutions USING btree (phase_id);


--
-- TOC entry 5217 (class 1259 OID 119919)
-- Name: idx_cycle_report_planning_attribute_version_history_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_planning_attribute_version_history_phase_id ON public.cycle_report_planning_attribute_version_history USING btree (phase_id);


--
-- TOC entry 5222 (class 1259 OID 119937)
-- Name: idx_cycle_report_planning_attributes_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_planning_attributes_phase_id ON public.cycle_report_planning_attributes USING btree (phase_id);


--
-- TOC entry 4938 (class 1259 OID 122396)
-- Name: idx_cycle_report_request_info_audit_logs_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_request_info_audit_logs_phase_id ON public.cycle_report_request_info_audit_logs USING btree (phase_id);


--
-- TOC entry 5296 (class 1259 OID 119941)
-- Name: idx_cycle_report_request_info_document_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_request_info_document_versions_phase_id ON public.cycle_report_request_info_document_versions USING btree (phase_id);


--
-- TOC entry 4949 (class 1259 OID 119920)
-- Name: idx_cycle_report_sample_selection_audit_logs_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_sample_selection_audit_logs_phase_id ON public.cycle_report_sample_selection_audit_logs USING btree (phase_id);


--
-- TOC entry 4946 (class 1259 OID 119936)
-- Name: idx_cycle_report_scoping_attribute_recommendations_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_scoping_attribute_recommendations_phase_id ON public.cycle_report_scoping_attribute_recommendations_backup USING btree (phase_id);


--
-- TOC entry 5114 (class 1259 OID 119924)
-- Name: idx_cycle_report_scoping_decision_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_scoping_decision_versions_phase_id ON public.cycle_report_scoping_decision_versions USING btree (phase_id);


--
-- TOC entry 4924 (class 1259 OID 119933)
-- Name: idx_cycle_report_scoping_submissions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_scoping_submissions_phase_id ON public.cycle_report_scoping_submissions USING btree (phase_id);


--
-- TOC entry 5049 (class 1259 OID 122374)
-- Name: idx_cycle_report_test_report_sections_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_report_test_report_sections_phase_id ON public.cycle_report_test_report_sections USING btree (phase_id);


--
-- TOC entry 4910 (class 1259 OID 116325)
-- Name: idx_cycle_reports_cycle; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_reports_cycle ON public.cycle_reports USING btree (cycle_id);


--
-- TOC entry 4911 (class 1259 OID 116326)
-- Name: idx_cycle_reports_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_reports_report ON public.cycle_reports USING btree (report_id);


--
-- TOC entry 4912 (class 1259 OID 116327)
-- Name: idx_cycle_reports_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_reports_status ON public.cycle_reports USING btree (status);


--
-- TOC entry 4913 (class 1259 OID 35598)
-- Name: idx_cycle_reports_workflow_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cycle_reports_workflow_id ON public.cycle_reports USING btree (workflow_id);


--
-- TOC entry 5336 (class 1259 OID 120738)
-- Name: idx_data_owner_assignments_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_attribute ON public.cycle_report_data_owner_lob_mapping USING btree (attribute_id);


--
-- TOC entry 5337 (class 1259 OID 120741)
-- Name: idx_data_owner_assignments_data_executive; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_data_executive ON public.cycle_report_data_owner_lob_mapping USING btree (data_executive_id);


--
-- TOC entry 5338 (class 1259 OID 120740)
-- Name: idx_data_owner_assignments_data_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_data_owner ON public.cycle_report_data_owner_lob_mapping USING btree (data_owner_id);


--
-- TOC entry 5339 (class 1259 OID 120739)
-- Name: idx_data_owner_assignments_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_lob ON public.cycle_report_data_owner_lob_mapping USING btree (lob_id);


--
-- TOC entry 5340 (class 1259 OID 120743)
-- Name: idx_data_owner_assignments_lob_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_lob_attribute ON public.cycle_report_data_owner_lob_mapping USING btree (lob_id, attribute_id);


--
-- TOC entry 5341 (class 1259 OID 120745)
-- Name: idx_data_owner_assignments_owner_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_owner_status ON public.cycle_report_data_owner_lob_mapping USING btree (data_owner_id, assignment_status);


--
-- TOC entry 5342 (class 1259 OID 120736)
-- Name: idx_data_owner_assignments_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_phase ON public.cycle_report_data_owner_lob_mapping USING btree (phase_id);


--
-- TOC entry 5343 (class 1259 OID 120744)
-- Name: idx_data_owner_assignments_phase_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_phase_lob ON public.cycle_report_data_owner_lob_mapping USING btree (phase_id, lob_id);


--
-- TOC entry 5344 (class 1259 OID 120737)
-- Name: idx_data_owner_assignments_sample; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_sample ON public.cycle_report_data_owner_lob_mapping USING btree (sample_id);


--
-- TOC entry 5345 (class 1259 OID 120742)
-- Name: idx_data_owner_assignments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_status ON public.cycle_report_data_owner_lob_mapping USING btree (assignment_status);


--
-- TOC entry 5346 (class 1259 OID 120735)
-- Name: idx_data_owner_assignments_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_owner_assignments_version ON public.cycle_report_data_owner_lob_mapping USING btree (version_id);


--
-- TOC entry 5177 (class 1259 OID 117824)
-- Name: idx_data_queries_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_queries_created_by ON public.data_queries USING btree (created_by_id);


--
-- TOC entry 5178 (class 1259 OID 117830)
-- Name: idx_data_queries_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_queries_updated_by ON public.data_queries USING btree (updated_by_id);


--
-- TOC entry 5297 (class 1259 OID 119694)
-- Name: idx_doc_versions_is_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_versions_is_current ON public.cycle_report_request_info_document_versions USING btree (is_current) WHERE (is_current = true);


--
-- TOC entry 5298 (class 1259 OID 119695)
-- Name: idx_doc_versions_submission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_versions_submission_id ON public.cycle_report_request_info_document_versions USING btree (document_submission_id);


--
-- TOC entry 4959 (class 1259 OID 118172)
-- Name: idx_escalation_email_logs_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_escalation_email_logs_created_by ON public.escalation_email_logs USING btree (created_by_id);


--
-- TOC entry 4960 (class 1259 OID 118178)
-- Name: idx_escalation_email_logs_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_escalation_email_logs_updated_by ON public.escalation_email_logs USING btree (updated_by_id);


--
-- TOC entry 5352 (class 1259 OID 120933)
-- Name: idx_evidence_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_current ON public.cycle_report_request_info_testcase_source_evidence USING btree (test_case_id, is_current);


--
-- TOC entry 5353 (class 1259 OID 120932)
-- Name: idx_evidence_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_phase ON public.cycle_report_request_info_testcase_source_evidence USING btree (phase_id);


--
-- TOC entry 5354 (class 1259 OID 120934)
-- Name: idx_evidence_submitted_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_submitted_by ON public.cycle_report_request_info_testcase_source_evidence USING btree (submitted_by);


--
-- TOC entry 5355 (class 1259 OID 120931)
-- Name: idx_evidence_test_case; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_test_case ON public.cycle_report_request_info_testcase_source_evidence USING btree (test_case_id);


--
-- TOC entry 5359 (class 1259 OID 120936)
-- Name: idx_evidence_validation_evidence_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_validation_evidence_id ON public.cycle_report_request_info_evidence_validation USING btree (evidence_id);


--
-- TOC entry 5356 (class 1259 OID 120935)
-- Name: idx_evidence_validation_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evidence_validation_status ON public.cycle_report_request_info_testcase_source_evidence USING btree (validation_status);


--
-- TOC entry 5108 (class 1259 OID 118088)
-- Name: idx_execution_metrics_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_execution_metrics_created_by ON public.metrics_execution USING btree (created_by_id);


--
-- TOC entry 5109 (class 1259 OID 36272)
-- Name: idx_execution_metrics_cycle_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_execution_metrics_cycle_id ON public.metrics_execution USING btree (cycle_id);


--
-- TOC entry 5110 (class 1259 OID 36273)
-- Name: idx_execution_metrics_report_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_execution_metrics_report_id ON public.metrics_execution USING btree (report_id);


--
-- TOC entry 5111 (class 1259 OID 118094)
-- Name: idx_execution_metrics_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_execution_metrics_updated_by ON public.metrics_execution USING btree (updated_by_id);


--
-- TOC entry 5309 (class 1259 OID 119963)
-- Name: idx_fry14m_account_origination_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fry14m_account_origination_date ON public.fry14m_scheduled1_data USING btree (account_origination_date);


--
-- TOC entry 5310 (class 1259 OID 119964)
-- Name: idx_fry14m_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fry14m_customer_id ON public.fry14m_scheduled1_data USING btree (customer_id);


--
-- TOC entry 5311 (class 1259 OID 119992)
-- Name: idx_fry14m_period_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fry14m_period_id ON public.fry14m_scheduled1_data USING btree (period_id);


--
-- TOC entry 5312 (class 1259 OID 119966)
-- Name: idx_fry14m_reference_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fry14m_reference_number ON public.fry14m_scheduled1_data USING btree (reference_number);


--
-- TOC entry 5313 (class 1259 OID 119967)
-- Name: idx_fry14m_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fry14m_state ON public.fry14m_scheduled1_data USING btree (state);


--
-- TOC entry 5172 (class 1259 OID 116184)
-- Name: idx_mapping_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_attribute ON public.attribute_mappings USING btree (attribute_id);


--
-- TOC entry 5173 (class 1259 OID 116186)
-- Name: idx_mapping_security; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_security ON public.attribute_mappings USING btree (security_classification);


--
-- TOC entry 5174 (class 1259 OID 116185)
-- Name: idx_mapping_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mapping_source ON public.attribute_mappings USING btree (data_source_id);


--
-- TOC entry 5223 (class 1259 OID 118282)
-- Name: idx_master_attribute_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_master_attribute_id ON public.cycle_report_planning_attributes USING btree (master_attribute_id);


--
-- TOC entry 4968 (class 1259 OID 117692)
-- Name: idx_observation_approvals_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_approvals_created_by ON public.cycle_report_observation_mgmt_approvals USING btree (created_by_id);


--
-- TOC entry 4969 (class 1259 OID 117698)
-- Name: idx_observation_approvals_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_approvals_updated_by ON public.cycle_report_observation_mgmt_approvals USING btree (updated_by_id);


--
-- TOC entry 5383 (class 1259 OID 121583)
-- Name: idx_observation_groups_attribute_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_groups_attribute_lob ON public.cycle_report_observation_groups USING btree (attribute_id, lob_id);


--
-- TOC entry 5384 (class 1259 OID 121585)
-- Name: idx_observation_groups_detected_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_groups_detected_by ON public.cycle_report_observation_groups USING btree (detected_by);


--
-- TOC entry 5385 (class 1259 OID 121580)
-- Name: idx_observation_groups_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_groups_phase_id ON public.cycle_report_observation_groups USING btree (phase_id);


--
-- TOC entry 5386 (class 1259 OID 121584)
-- Name: idx_observation_groups_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_groups_status ON public.cycle_report_observation_groups USING btree (status);


--
-- TOC entry 4963 (class 1259 OID 117716)
-- Name: idx_observation_impact_assessments_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_impact_assessments_created_by ON public.cycle_report_observation_mgmt_impact_assessments USING btree (created_by_id);


--
-- TOC entry 4964 (class 1259 OID 117722)
-- Name: idx_observation_impact_assessments_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_impact_assessments_updated_by ON public.cycle_report_observation_mgmt_impact_assessments USING btree (updated_by_id);


--
-- TOC entry 5163 (class 1259 OID 117668)
-- Name: idx_observation_records_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_records_created_by ON public.cycle_report_observation_mgmt_observation_records USING btree (created_by_id);


--
-- TOC entry 5164 (class 1259 OID 117674)
-- Name: idx_observation_records_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_records_updated_by ON public.cycle_report_observation_mgmt_observation_records USING btree (updated_by_id);


--
-- TOC entry 4973 (class 1259 OID 117704)
-- Name: idx_observation_resolutions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_resolutions_created_by ON public.cycle_report_observation_mgmt_resolutions USING btree (created_by_id);


--
-- TOC entry 4974 (class 1259 OID 117710)
-- Name: idx_observation_resolutions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observation_resolutions_updated_by ON public.cycle_report_observation_mgmt_resolutions USING btree (updated_by_id);


--
-- TOC entry 5165 (class 1259 OID 122361)
-- Name: idx_observations_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_phase ON public.cycle_report_observation_mgmt_observation_records USING btree (phase_id);


--
-- TOC entry 5393 (class 1259 OID 121589)
-- Name: idx_observations_unified_attribute_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_attribute_id ON public.cycle_report_observations_unified USING btree (attribute_id);


--
-- TOC entry 5394 (class 1259 OID 121586)
-- Name: idx_observations_unified_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_group_id ON public.cycle_report_observations_unified USING btree (group_id);


--
-- TOC entry 5395 (class 1259 OID 121590)
-- Name: idx_observations_unified_lob_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_lob_id ON public.cycle_report_observations_unified USING btree (lob_id);


--
-- TOC entry 5396 (class 1259 OID 121591)
-- Name: idx_observations_unified_sample_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_sample_id ON public.cycle_report_observations_unified USING btree (sample_id);


--
-- TOC entry 5397 (class 1259 OID 121588)
-- Name: idx_observations_unified_test_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_test_case_id ON public.cycle_report_observations_unified USING btree (test_case_id);


--
-- TOC entry 5398 (class 1259 OID 121587)
-- Name: idx_observations_unified_test_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observations_unified_test_execution_id ON public.cycle_report_observations_unified USING btree (test_execution_id);


--
-- TOC entry 5186 (class 1259 OID 116190)
-- Name: idx_partition_job_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_partition_job_status ON public.profiling_partitions USING btree (job_id, status);


--
-- TOC entry 5187 (class 1259 OID 116191)
-- Name: idx_partition_worker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_partition_worker ON public.profiling_partitions USING btree (assigned_worker, status);


--
-- TOC entry 5274 (class 1259 OID 119083)
-- Name: idx_pde_mappings_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pde_mappings_attribute ON public.cycle_report_planning_pde_mappings USING btree (attribute_id);


--
-- TOC entry 5251 (class 1259 OID 118271)
-- Name: idx_permission_audit_log_performed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_audit_log_performed_at ON public.permission_audit_log USING btree (performed_at);


--
-- TOC entry 5252 (class 1259 OID 118272)
-- Name: idx_permission_audit_log_performed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_audit_log_performed_by ON public.permission_audit_log USING btree (performed_by);


--
-- TOC entry 5253 (class 1259 OID 118270)
-- Name: idx_permission_audit_log_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_audit_log_target ON public.permission_audit_log USING btree (target_type, target_id);


--
-- TOC entry 4982 (class 1259 OID 117170)
-- Name: idx_permissions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permissions_created_by ON public.rbac_permissions USING btree (created_by_id);


--
-- TOC entry 4983 (class 1259 OID 117171)
-- Name: idx_permissions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permissions_updated_by ON public.rbac_permissions USING btree (updated_by_id);


--
-- TOC entry 5099 (class 1259 OID 118076)
-- Name: idx_phase_metrics_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phase_metrics_created_by ON public.metrics_phases USING btree (created_by_id);


--
-- TOC entry 5100 (class 1259 OID 36269)
-- Name: idx_phase_metrics_cycle_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phase_metrics_cycle_id ON public.metrics_phases USING btree (cycle_id);


--
-- TOC entry 5101 (class 1259 OID 36271)
-- Name: idx_phase_metrics_phase_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phase_metrics_phase_name ON public.metrics_phases USING btree (phase_name);


--
-- TOC entry 5102 (class 1259 OID 36270)
-- Name: idx_phase_metrics_report_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phase_metrics_report_id ON public.metrics_phases USING btree (report_id);


--
-- TOC entry 5103 (class 1259 OID 118082)
-- Name: idx_phase_metrics_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phase_metrics_updated_by ON public.metrics_phases USING btree (updated_by_id);


--
-- TOC entry 5224 (class 1259 OID 119881)
-- Name: idx_planning_attributes_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_planning_attributes_phase ON public.cycle_report_planning_attributes USING btree (phase_id);


--
-- TOC entry 5225 (class 1259 OID 118313)
-- Name: idx_planning_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_planning_status ON public.cycle_report_planning_attributes USING btree (status);


--
-- TOC entry 5304 (class 1259 OID 119739)
-- Name: idx_prelim_findings_assigned; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prelim_findings_assigned ON public.cycle_report_observation_mgmt_preliminary_findings USING btree (assigned_to_id);


--
-- TOC entry 5305 (class 1259 OID 119738)
-- Name: idx_prelim_findings_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prelim_findings_status ON public.cycle_report_observation_mgmt_preliminary_findings USING btree (status);


--
-- TOC entry 5306 (class 1259 OID 119740)
-- Name: idx_prelim_findings_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prelim_findings_tags ON public.cycle_report_observation_mgmt_preliminary_findings USING gin (tags);


--
-- TOC entry 5283 (class 1259 OID 119654)
-- Name: idx_profiling_configs_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_configs_cycle_report ON public.data_profiling_configurations USING btree (cycle_id, report_id);


--
-- TOC entry 5196 (class 1259 OID 116208)
-- Name: idx_profiling_exec_cycle; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_exec_cycle ON public.profiling_executions USING btree (cycle_id, report_id);


--
-- TOC entry 5197 (class 1259 OID 116209)
-- Name: idx_profiling_exec_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_exec_status ON public.profiling_executions USING btree (status, start_time);


--
-- TOC entry 5198 (class 1259 OID 117788)
-- Name: idx_profiling_executions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_executions_created_by ON public.profiling_executions USING btree (created_by_id);


--
-- TOC entry 5199 (class 1259 OID 117794)
-- Name: idx_profiling_executions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_executions_updated_by ON public.profiling_executions USING btree (updated_by_id);


--
-- TOC entry 5180 (class 1259 OID 116189)
-- Name: idx_profiling_job_cycle; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_job_cycle ON public.profiling_jobs USING btree (cycle_id, report_id);


--
-- TOC entry 5181 (class 1259 OID 116188)
-- Name: idx_profiling_job_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_job_status ON public.profiling_jobs USING btree (status, priority);


--
-- TOC entry 5288 (class 1259 OID 119655)
-- Name: idx_profiling_jobs_configuration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_jobs_configuration ON public.data_profiling_jobs USING btree (configuration_id);


--
-- TOC entry 5182 (class 1259 OID 117776)
-- Name: idx_profiling_jobs_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_jobs_created_by ON public.profiling_jobs USING btree (created_by_id);


--
-- TOC entry 5289 (class 1259 OID 119656)
-- Name: idx_profiling_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_jobs_status ON public.data_profiling_jobs USING btree (status);


--
-- TOC entry 5183 (class 1259 OID 117782)
-- Name: idx_profiling_jobs_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_jobs_updated_by ON public.profiling_jobs USING btree (updated_by_id);


--
-- TOC entry 5476 (class 1259 OID 123304)
-- Name: idx_profiling_results_attribute_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_results_attribute_id ON public.cycle_report_data_profiling_results USING btree (attribute_id);


--
-- TOC entry 5477 (class 1259 OID 123305)
-- Name: idx_profiling_results_executed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_results_executed_at ON public.cycle_report_data_profiling_results USING btree (executed_at);


--
-- TOC entry 5478 (class 1259 OID 123302)
-- Name: idx_profiling_results_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_results_phase_id ON public.cycle_report_data_profiling_results USING btree (phase_id);


--
-- TOC entry 5479 (class 1259 OID 123303)
-- Name: idx_profiling_results_rule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_results_rule_id ON public.cycle_report_data_profiling_results USING btree (rule_id);


--
-- TOC entry 5277 (class 1259 OID 119432)
-- Name: idx_profiling_rules_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_attribute ON public.data_profiling_rules USING btree (attribute_id);


--
-- TOC entry 5452 (class 1259 OID 122750)
-- Name: idx_profiling_rules_attribute_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_attribute_id ON public.cycle_report_data_profiling_rules USING btree (attribute_id);


--
-- TOC entry 5278 (class 1259 OID 119431)
-- Name: idx_profiling_rules_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_cycle_report ON public.data_profiling_rules USING btree (cycle_id, report_id);


--
-- TOC entry 5453 (class 1259 OID 122752)
-- Name: idx_profiling_rules_rule_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_rule_type ON public.cycle_report_data_profiling_rules USING btree (rule_type);


--
-- TOC entry 5454 (class 1259 OID 122751)
-- Name: idx_profiling_rules_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_status ON public.cycle_report_data_profiling_rules USING btree (status);


--
-- TOC entry 5455 (class 1259 OID 122749)
-- Name: idx_profiling_rules_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_rules_version_id ON public.cycle_report_data_profiling_rules USING btree (version_id);


--
-- TOC entry 5445 (class 1259 OID 122748)
-- Name: idx_profiling_versions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_versions_created_at ON public.cycle_report_data_profiling_rule_versions USING btree (created_at DESC);


--
-- TOC entry 5446 (class 1259 OID 122746)
-- Name: idx_profiling_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_versions_phase_id ON public.cycle_report_data_profiling_rule_versions USING btree (phase_id);


--
-- TOC entry 5447 (class 1259 OID 122747)
-- Name: idx_profiling_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_profiling_versions_status ON public.cycle_report_data_profiling_rule_versions USING btree (version_status);


--
-- TOC entry 5179 (class 1259 OID 116187)
-- Name: idx_query_source_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_source_type ON public.data_queries USING btree (data_source_id, query_type);


--
-- TOC entry 5208 (class 1259 OID 116727)
-- Name: idx_report_inventory_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_inventory_lob ON public.reports USING btree (lob_id);


--
-- TOC entry 5209 (class 1259 OID 116535)
-- Name: idx_report_inventory_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_inventory_number ON public.reports USING btree (report_number);


--
-- TOC entry 5210 (class 1259 OID 116726)
-- Name: idx_report_inventory_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_inventory_owner ON public.reports USING btree (report_owner_id);


--
-- TOC entry 5526 (class 1259 OID 125376)
-- Name: idx_request_info_evidence_sample; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_evidence_sample ON public.cycle_report_request_info_evidence USING btree (sample_id);


--
-- TOC entry 5527 (class 1259 OID 125377)
-- Name: idx_request_info_evidence_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_evidence_status ON public.cycle_report_request_info_evidence USING btree (evidence_status);


--
-- TOC entry 5528 (class 1259 OID 125375)
-- Name: idx_request_info_evidence_test_case; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_evidence_test_case ON public.cycle_report_request_info_evidence USING btree (test_case_id);


--
-- TOC entry 5529 (class 1259 OID 125374)
-- Name: idx_request_info_evidence_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_evidence_version_id ON public.cycle_report_request_info_evidence USING btree (version_id);


--
-- TOC entry 5519 (class 1259 OID 125309)
-- Name: idx_request_info_versions_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_versions_parent ON public.cycle_report_request_info_evidence_versions USING btree (parent_version_id);


--
-- TOC entry 5520 (class 1259 OID 125307)
-- Name: idx_request_info_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_versions_phase_id ON public.cycle_report_request_info_evidence_versions USING btree (phase_id);


--
-- TOC entry 5521 (class 1259 OID 125308)
-- Name: idx_request_info_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_info_versions_status ON public.cycle_report_request_info_evidence_versions USING btree (version_status);


--
-- TOC entry 5482 (class 1259 OID 124303)
-- Name: idx_rfi_data_sources_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_data_sources_active ON public.cycle_report_rfi_data_sources USING btree (is_active);


--
-- TOC entry 5483 (class 1259 OID 124301)
-- Name: idx_rfi_data_sources_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_data_sources_owner ON public.cycle_report_rfi_data_sources USING btree (data_owner_id);


--
-- TOC entry 5484 (class 1259 OID 124302)
-- Name: idx_rfi_data_sources_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_data_sources_phase ON public.cycle_report_rfi_data_sources USING btree (phase_id);


--
-- TOC entry 5495 (class 1259 OID 124650)
-- Name: idx_rfi_evidence_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_evidence_current ON public.cycle_report_rfi_evidence USING btree (is_current) WHERE (is_current = true);


--
-- TOC entry 5496 (class 1259 OID 124649)
-- Name: idx_rfi_evidence_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_evidence_phase ON public.cycle_report_rfi_evidence USING btree (phase_id);


--
-- TOC entry 5497 (class 1259 OID 124652)
-- Name: idx_rfi_evidence_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_evidence_status ON public.cycle_report_rfi_evidence USING btree (validation_status);


--
-- TOC entry 5498 (class 1259 OID 124648)
-- Name: idx_rfi_evidence_test_case; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_evidence_test_case ON public.cycle_report_rfi_evidence USING btree (test_case_id);


--
-- TOC entry 5499 (class 1259 OID 124651)
-- Name: idx_rfi_evidence_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_evidence_type ON public.cycle_report_rfi_evidence USING btree (evidence_type);


--
-- TOC entry 5489 (class 1259 OID 124335)
-- Name: idx_rfi_query_validations_data_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_query_validations_data_source ON public.cycle_report_rfi_query_validations USING btree (data_source_id);


--
-- TOC entry 5490 (class 1259 OID 124337)
-- Name: idx_rfi_query_validations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_query_validations_status ON public.cycle_report_rfi_query_validations USING btree (validation_status);


--
-- TOC entry 5491 (class 1259 OID 124334)
-- Name: idx_rfi_query_validations_test_case; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_query_validations_test_case ON public.cycle_report_rfi_query_validations USING btree (test_case_id);


--
-- TOC entry 5492 (class 1259 OID 124336)
-- Name: idx_rfi_query_validations_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rfi_query_validations_timestamp ON public.cycle_report_rfi_query_validations USING btree (validation_timestamp);


--
-- TOC entry 5245 (class 1259 OID 118230)
-- Name: idx_role_hierarchy_child; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_hierarchy_child ON public.rbac_role_hierarchy USING btree (child_role_id);


--
-- TOC entry 5246 (class 1259 OID 118231)
-- Name: idx_role_hierarchy_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_hierarchy_created_by ON public.rbac_role_hierarchy USING btree (created_by_id);


--
-- TOC entry 5247 (class 1259 OID 118229)
-- Name: idx_role_hierarchy_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_hierarchy_parent ON public.rbac_role_hierarchy USING btree (parent_role_id);


--
-- TOC entry 5248 (class 1259 OID 118232)
-- Name: idx_role_hierarchy_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_hierarchy_updated_by ON public.rbac_role_hierarchy USING btree (updated_by_id);


--
-- TOC entry 4991 (class 1259 OID 117182)
-- Name: idx_roles_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_created_by ON public.rbac_roles USING btree (created_by_id);


--
-- TOC entry 4992 (class 1259 OID 117183)
-- Name: idx_roles_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_updated_by ON public.rbac_roles USING btree (updated_by_id);


--
-- TOC entry 4950 (class 1259 OID 32709)
-- Name: idx_sample_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_audit_action ON public.cycle_report_sample_selection_audit_logs USING btree (action);


--
-- TOC entry 4951 (class 1259 OID 32706)
-- Name: idx_sample_audit_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_audit_entity ON public.cycle_report_sample_selection_audit_logs USING btree (entity_type, entity_id);


--
-- TOC entry 4952 (class 1259 OID 32710)
-- Name: idx_sample_audit_performed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_audit_performed_at ON public.cycle_report_sample_selection_audit_logs USING btree (performed_at);


--
-- TOC entry 5510 (class 1259 OID 124928)
-- Name: idx_sample_selection_samples_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_category ON public.cycle_report_sample_selection_samples USING btree (sample_category);


--
-- TOC entry 5511 (class 1259 OID 124927)
-- Name: idx_sample_selection_samples_identifier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_identifier ON public.cycle_report_sample_selection_samples USING btree (sample_identifier);


--
-- TOC entry 5512 (class 1259 OID 124926)
-- Name: idx_sample_selection_samples_lob_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_lob_id ON public.cycle_report_sample_selection_samples USING btree (lob_id);


--
-- TOC entry 5513 (class 1259 OID 124925)
-- Name: idx_sample_selection_samples_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_phase_id ON public.cycle_report_sample_selection_samples USING btree (phase_id);


--
-- TOC entry 5514 (class 1259 OID 124930)
-- Name: idx_sample_selection_samples_report_owner_decision; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_report_owner_decision ON public.cycle_report_sample_selection_samples USING btree (report_owner_decision);


--
-- TOC entry 5515 (class 1259 OID 124929)
-- Name: idx_sample_selection_samples_tester_decision; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_tester_decision ON public.cycle_report_sample_selection_samples USING btree (tester_decision);


--
-- TOC entry 5516 (class 1259 OID 124924)
-- Name: idx_sample_selection_samples_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_samples_version_id ON public.cycle_report_sample_selection_samples USING btree (version_id);


--
-- TOC entry 5504 (class 1259 OID 124846)
-- Name: idx_sample_selection_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_versions_phase_id ON public.cycle_report_sample_selection_versions USING btree (phase_id);


--
-- TOC entry 5505 (class 1259 OID 124847)
-- Name: idx_sample_selection_versions_phase_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_sample_selection_versions_phase_version ON public.cycle_report_sample_selection_versions USING btree (phase_id, version_number);


--
-- TOC entry 5506 (class 1259 OID 125245)
-- Name: idx_sample_selection_versions_ro_decision; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_versions_ro_decision ON public.cycle_report_sample_selection_versions USING btree (report_owner_decision);


--
-- TOC entry 5507 (class 1259 OID 124848)
-- Name: idx_sample_selection_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sample_selection_versions_status ON public.cycle_report_sample_selection_versions USING btree (version_status);


--
-- TOC entry 5467 (class 1259 OID 122966)
-- Name: idx_scoping_attributes_final_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_attributes_final_status ON public.cycle_report_scoping_attributes USING btree (final_status);


--
-- TOC entry 5468 (class 1259 OID 122965)
-- Name: idx_scoping_attributes_planning_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_attributes_planning_id ON public.cycle_report_scoping_attributes USING btree (planning_attribute_id);


--
-- TOC entry 5469 (class 1259 OID 122964)
-- Name: idx_scoping_attributes_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_attributes_version_id ON public.cycle_report_scoping_attributes USING btree (version_id);


--
-- TOC entry 5470 (class 1259 OID 122999)
-- Name: idx_scoping_audit_performed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_audit_performed_at ON public.scoping_audit_log USING btree (performed_at DESC);


--
-- TOC entry 5471 (class 1259 OID 122998)
-- Name: idx_scoping_audit_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_audit_phase_id ON public.scoping_audit_log USING btree (phase_id);


--
-- TOC entry 5322 (class 1259 OID 120542)
-- Name: idx_scoping_decisions_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_decisions_attribute ON public.cycle_report_scoping_decisions USING btree (attribute_id);


--
-- TOC entry 5323 (class 1259 OID 120543)
-- Name: idx_scoping_decisions_decision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_decisions_decision_id ON public.cycle_report_scoping_decisions USING btree (decision_id);


--
-- TOC entry 4947 (class 1259 OID 119882)
-- Name: idx_scoping_recommendations_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_recommendations_phase ON public.cycle_report_scoping_attribute_recommendations_backup USING btree (phase_id);


--
-- TOC entry 4925 (class 1259 OID 117932)
-- Name: idx_scoping_submissions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_submissions_created_by ON public.cycle_report_scoping_submissions USING btree (created_by_id);


--
-- TOC entry 4926 (class 1259 OID 117938)
-- Name: idx_scoping_submissions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_submissions_updated_by ON public.cycle_report_scoping_submissions USING btree (updated_by_id);


--
-- TOC entry 5460 (class 1259 OID 122963)
-- Name: idx_scoping_versions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_versions_created_at ON public.cycle_report_scoping_versions USING btree (created_at DESC);


--
-- TOC entry 5461 (class 1259 OID 122961)
-- Name: idx_scoping_versions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_versions_phase_id ON public.cycle_report_scoping_versions USING btree (phase_id);


--
-- TOC entry 5462 (class 1259 OID 122962)
-- Name: idx_scoping_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scoping_versions_status ON public.cycle_report_scoping_versions USING btree (version_status);


--
-- TOC entry 5202 (class 1259 OID 116211)
-- Name: idx_secure_access_classification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_secure_access_classification ON public.secure_data_access_logs USING btree (security_classification, accessed_at);


--
-- TOC entry 5203 (class 1259 OID 116210)
-- Name: idx_secure_access_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_secure_access_user ON public.secure_data_access_logs USING btree (user_id, accessed_at);


--
-- TOC entry 5204 (class 1259 OID 117860)
-- Name: idx_secure_data_access_logs_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_secure_data_access_logs_created_by ON public.secure_data_access_logs USING btree (created_by_id);


--
-- TOC entry 5205 (class 1259 OID 117866)
-- Name: idx_secure_data_access_logs_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_secure_data_access_logs_updated_by ON public.secure_data_access_logs USING btree (updated_by_id);


--
-- TOC entry 4877 (class 1259 OID 118040)
-- Name: idx_sla_configurations_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sla_configurations_created_by ON public.universal_sla_configurations USING btree (created_by_id);


--
-- TOC entry 4878 (class 1259 OID 118046)
-- Name: idx_sla_configurations_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sla_configurations_updated_by ON public.universal_sla_configurations USING btree (updated_by_id);


--
-- TOC entry 4903 (class 1259 OID 118052)
-- Name: idx_sla_escalation_rules_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sla_escalation_rules_created_by ON public.universal_sla_escalation_rules USING btree (created_by_id);


--
-- TOC entry 4904 (class 1259 OID 118058)
-- Name: idx_sla_escalation_rules_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sla_escalation_rules_updated_by ON public.universal_sla_escalation_rules USING btree (updated_by_id);


--
-- TOC entry 5235 (class 1259 OID 122514)
-- Name: idx_submission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_submission_id ON public.cycle_report_test_cases_document_submissions USING btree (submission_id);


--
-- TOC entry 5228 (class 1259 OID 122501)
-- Name: idx_test_case_attribute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_attribute ON public.cycle_report_test_cases USING btree (attribute_id);


--
-- TOC entry 5229 (class 1259 OID 122500)
-- Name: idx_test_case_data_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_data_owner ON public.cycle_report_test_cases USING btree (data_owner_id);


--
-- TOC entry 5230 (class 1259 OID 122502)
-- Name: idx_test_case_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_lob ON public.cycle_report_test_cases USING btree (lob_id);


--
-- TOC entry 5231 (class 1259 OID 122503)
-- Name: idx_test_case_phase_data_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_phase_data_owner ON public.cycle_report_test_cases USING btree (phase_id, data_owner_id);


--
-- TOC entry 5232 (class 1259 OID 122509)
-- Name: idx_test_case_sample; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_sample ON public.cycle_report_test_cases USING btree (sample_id);


--
-- TOC entry 5236 (class 1259 OID 122552)
-- Name: idx_test_case_submissions_data_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_submissions_data_owner_id ON public.cycle_report_test_cases_document_submissions USING btree (data_owner_id);


--
-- TOC entry 5237 (class 1259 OID 122553)
-- Name: idx_test_case_submissions_is_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_submissions_is_current ON public.cycle_report_test_cases_document_submissions USING btree (is_current);


--
-- TOC entry 5238 (class 1259 OID 122550)
-- Name: idx_test_case_submissions_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_submissions_phase_id ON public.cycle_report_test_cases_document_submissions USING btree (phase_id);


--
-- TOC entry 5239 (class 1259 OID 122551)
-- Name: idx_test_case_submissions_test_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_case_submissions_test_case_id ON public.cycle_report_test_cases_document_submissions USING btree (test_case_id);


--
-- TOC entry 4890 (class 1259 OID 117194)
-- Name: idx_test_cycles_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_cycles_created_by ON public.test_cycles USING btree (created_by_id);


--
-- TOC entry 4891 (class 1259 OID 116324)
-- Name: idx_test_cycles_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_cycles_dates ON public.test_cycles USING btree (start_date, end_date);


--
-- TOC entry 4892 (class 1259 OID 117195)
-- Name: idx_test_cycles_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_cycles_updated_by ON public.test_cycles USING btree (updated_by_id);


--
-- TOC entry 5376 (class 1259 OID 121286)
-- Name: idx_test_execution_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_audit_action ON public.cycle_report_test_execution_audit USING btree (action);


--
-- TOC entry 5377 (class 1259 OID 121284)
-- Name: idx_test_execution_audit_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_audit_execution_id ON public.cycle_report_test_execution_audit USING btree (execution_id);


--
-- TOC entry 5378 (class 1259 OID 121285)
-- Name: idx_test_execution_audit_performed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_audit_performed_at ON public.cycle_report_test_execution_audit USING btree (performed_at);


--
-- TOC entry 5362 (class 1259 OID 121279)
-- Name: idx_test_execution_results_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_results_created_at ON public.cycle_report_test_execution_results USING btree (created_at);


--
-- TOC entry 5363 (class 1259 OID 121277)
-- Name: idx_test_execution_results_evidence_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_results_evidence_id ON public.cycle_report_test_execution_results USING btree (evidence_id);


--
-- TOC entry 5364 (class 1259 OID 121278)
-- Name: idx_test_execution_results_execution_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_results_execution_status ON public.cycle_report_test_execution_results USING btree (execution_status);


--
-- TOC entry 5365 (class 1259 OID 121280)
-- Name: idx_test_execution_results_test_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_results_test_case_id ON public.cycle_report_test_execution_results USING btree (test_case_id);


--
-- TOC entry 5371 (class 1259 OID 121281)
-- Name: idx_test_execution_reviews_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_reviews_execution_id ON public.cycle_report_test_execution_reviews USING btree (execution_id);


--
-- TOC entry 5372 (class 1259 OID 121283)
-- Name: idx_test_execution_reviews_reviewed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_reviews_reviewed_by ON public.cycle_report_test_execution_reviews USING btree (reviewed_by);


--
-- TOC entry 5373 (class 1259 OID 121282)
-- Name: idx_test_execution_reviews_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_execution_reviews_status ON public.cycle_report_test_execution_reviews USING btree (review_status);


--
-- TOC entry 5440 (class 1259 OID 122615)
-- Name: idx_test_report_generation_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_generation_cycle_report ON public.cycle_report_test_report_generation USING btree (cycle_id, report_id);


--
-- TOC entry 5441 (class 1259 OID 122614)
-- Name: idx_test_report_generation_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_generation_phase_id ON public.cycle_report_test_report_generation USING btree (phase_id);


--
-- TOC entry 5442 (class 1259 OID 122616)
-- Name: idx_test_report_generation_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_generation_status ON public.cycle_report_test_report_generation USING btree (status);


--
-- TOC entry 5050 (class 1259 OID 122845)
-- Name: idx_test_report_sections_approvals; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_approvals ON public.cycle_report_test_report_sections USING btree (tester_approved, report_owner_approved, executive_approved);


--
-- TOC entry 5051 (class 1259 OID 117524)
-- Name: idx_test_report_sections_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_created_by ON public.cycle_report_test_report_sections USING btree (created_by_id);


--
-- TOC entry 5052 (class 1259 OID 122843)
-- Name: idx_test_report_sections_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_cycle_report ON public.cycle_report_test_report_sections USING btree (cycle_id, report_id);


--
-- TOC entry 5053 (class 1259 OID 122373)
-- Name: idx_test_report_sections_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_phase ON public.cycle_report_test_report_sections USING btree (phase_id);


--
-- TOC entry 5054 (class 1259 OID 122613)
-- Name: idx_test_report_sections_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_phase_id ON public.cycle_report_test_report_sections USING btree (phase_id);


--
-- TOC entry 5055 (class 1259 OID 122842)
-- Name: idx_test_report_sections_section_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_test_report_sections_section_id ON public.cycle_report_test_report_sections USING btree (section_id);


--
-- TOC entry 5056 (class 1259 OID 122844)
-- Name: idx_test_report_sections_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_status ON public.cycle_report_test_report_sections USING btree (status);


--
-- TOC entry 5057 (class 1259 OID 117530)
-- Name: idx_test_report_sections_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_test_report_sections_updated_by ON public.cycle_report_test_report_sections USING btree (updated_by_id);


--
-- TOC entry 5240 (class 1259 OID 122556)
-- Name: idx_unique_current_submission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_unique_current_submission ON public.cycle_report_test_cases_document_submissions USING btree (test_case_id, is_current) WHERE (is_current = true);


--
-- TOC entry 5347 (class 1259 OID 125246)
-- Name: idx_unique_phase_attribute_lob; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_unique_phase_attribute_lob ON public.cycle_report_data_owner_lob_mapping USING btree (phase_id, attribute_id, lob_id);


--
-- TOC entry 5117 (class 1259 OID 118028)
-- Name: idx_universal_assignments_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_universal_assignments_created_by ON public.universal_assignments USING btree (created_by_id);


--
-- TOC entry 5118 (class 1259 OID 116373)
-- Name: idx_universal_assignments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_universal_assignments_status ON public.universal_assignments USING btree (status);


--
-- TOC entry 5119 (class 1259 OID 118034)
-- Name: idx_universal_assignments_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_universal_assignments_updated_by ON public.universal_assignments USING btree (updated_by_id);


--
-- TOC entry 4883 (class 1259 OID 116322)
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- TOC entry 4884 (class 1259 OID 116323)
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- TOC entry 5132 (class 1259 OID 117392)
-- Name: idx_workflow_activities_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activities_created_by ON public.workflow_activities USING btree (created_by_id);


--
-- TOC entry 5133 (class 1259 OID 119913)
-- Name: idx_workflow_activities_cycle_report_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activities_cycle_report_phase ON public.workflow_activities USING btree (cycle_id, report_id, phase_id);


--
-- TOC entry 5134 (class 1259 OID 120094)
-- Name: idx_workflow_activities_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activities_lookup ON public.workflow_activities USING btree (cycle_id, report_id, phase_name, activity_name);


--
-- TOC entry 5135 (class 1259 OID 119775)
-- Name: idx_workflow_activities_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activities_phase_id ON public.workflow_activities USING btree (phase_id);


--
-- TOC entry 5136 (class 1259 OID 117398)
-- Name: idx_workflow_activities_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activities_updated_by ON public.workflow_activities USING btree (updated_by_id);


--
-- TOC entry 5148 (class 1259 OID 117404)
-- Name: idx_workflow_activity_dependencies_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activity_dependencies_created_by ON public.workflow_activity_dependencies USING btree (created_by_id);


--
-- TOC entry 5149 (class 1259 OID 117410)
-- Name: idx_workflow_activity_dependencies_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activity_dependencies_updated_by ON public.workflow_activity_dependencies USING btree (updated_by_id);


--
-- TOC entry 5154 (class 1259 OID 117476)
-- Name: idx_workflow_activity_templates_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activity_templates_created_by ON public.workflow_activity_templates USING btree (created_by_id);


--
-- TOC entry 5155 (class 1259 OID 117482)
-- Name: idx_workflow_activity_templates_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_activity_templates_updated_by ON public.workflow_activity_templates USING btree (updated_by_id);


--
-- TOC entry 5087 (class 1259 OID 117452)
-- Name: idx_workflow_alerts_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_alerts_created_by ON public.workflow_alerts USING btree (created_by_id);


--
-- TOC entry 5088 (class 1259 OID 35572)
-- Name: idx_workflow_alerts_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_alerts_severity ON public.workflow_alerts USING btree (severity, created_at);


--
-- TOC entry 5089 (class 1259 OID 35571)
-- Name: idx_workflow_alerts_unresolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_alerts_unresolved ON public.workflow_alerts USING btree (resolved, created_at);


--
-- TOC entry 5090 (class 1259 OID 117458)
-- Name: idx_workflow_alerts_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_alerts_updated_by ON public.workflow_alerts USING btree (updated_by_id);


--
-- TOC entry 5065 (class 1259 OID 117428)
-- Name: idx_workflow_executions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_executions_created_by ON public.workflow_executions USING btree (created_by_id);


--
-- TOC entry 5066 (class 1259 OID 35513)
-- Name: idx_workflow_executions_cycle; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_executions_cycle ON public.workflow_executions USING btree (cycle_id);


--
-- TOC entry 5067 (class 1259 OID 35515)
-- Name: idx_workflow_executions_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_executions_started ON public.workflow_executions USING btree (started_at);


--
-- TOC entry 5068 (class 1259 OID 35514)
-- Name: idx_workflow_executions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_executions_status ON public.workflow_executions USING btree (status);


--
-- TOC entry 5069 (class 1259 OID 117434)
-- Name: idx_workflow_executions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_executions_updated_by ON public.workflow_executions USING btree (updated_by_id);


--
-- TOC entry 5072 (class 1259 OID 117440)
-- Name: idx_workflow_metrics_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_metrics_created_by ON public.workflow_metrics USING btree (created_by_id);


--
-- TOC entry 5073 (class 1259 OID 35528)
-- Name: idx_workflow_metrics_phase_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_metrics_phase_period ON public.workflow_metrics USING btree (phase_name, period_start);


--
-- TOC entry 5074 (class 1259 OID 35527)
-- Name: idx_workflow_metrics_type_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_metrics_type_period ON public.workflow_metrics USING btree (workflow_type, period_start);


--
-- TOC entry 5075 (class 1259 OID 117446)
-- Name: idx_workflow_metrics_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_metrics_updated_by ON public.workflow_metrics USING btree (updated_by_id);


--
-- TOC entry 4914 (class 1259 OID 117380)
-- Name: idx_workflow_phases_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_phases_created_by ON public.workflow_phases USING btree (created_by_id);


--
-- TOC entry 4915 (class 1259 OID 119767)
-- Name: idx_workflow_phases_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_phases_cycle_report ON public.workflow_phases USING btree (cycle_id, report_id);


--
-- TOC entry 4916 (class 1259 OID 119769)
-- Name: idx_workflow_phases_phase_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_phases_phase_name ON public.workflow_phases USING btree (phase_name);


--
-- TOC entry 4917 (class 1259 OID 119768)
-- Name: idx_workflow_phases_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_phases_status ON public.workflow_phases USING btree (status);


--
-- TOC entry 4918 (class 1259 OID 117386)
-- Name: idx_workflow_phases_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_phases_updated_by ON public.workflow_phases USING btree (updated_by_id);


--
-- TOC entry 5080 (class 1259 OID 117464)
-- Name: idx_workflow_steps_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_steps_created_by ON public.workflow_steps USING btree (created_by_id);


--
-- TOC entry 5081 (class 1259 OID 35548)
-- Name: idx_workflow_steps_execution; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_steps_execution ON public.workflow_steps USING btree (execution_id);


--
-- TOC entry 5082 (class 1259 OID 35550)
-- Name: idx_workflow_steps_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_steps_phase ON public.workflow_steps USING btree (phase_name);


--
-- TOC entry 5083 (class 1259 OID 35549)
-- Name: idx_workflow_steps_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_steps_status ON public.workflow_steps USING btree (status);


--
-- TOC entry 5084 (class 1259 OID 117470)
-- Name: idx_workflow_steps_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_steps_updated_by ON public.workflow_steps USING btree (updated_by_id);


--
-- TOC entry 5093 (class 1259 OID 117416)
-- Name: idx_workflow_transitions_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_transitions_created_by ON public.workflow_transitions USING btree (created_by_id);


--
-- TOC entry 5094 (class 1259 OID 35595)
-- Name: idx_workflow_transitions_execution; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_transitions_execution ON public.workflow_transitions USING btree (execution_id);


--
-- TOC entry 5095 (class 1259 OID 35596)
-- Name: idx_workflow_transitions_timing; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_transitions_timing ON public.workflow_transitions USING btree (started_at, completed_at);


--
-- TOC entry 5096 (class 1259 OID 117422)
-- Name: idx_workflow_transitions_updated_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_transitions_updated_by ON public.workflow_transitions USING btree (updated_by_id);


--
-- TOC entry 4948 (class 1259 OID 32492)
-- Name: ix_attribute_scoping_recommendations_recommendation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attribute_scoping_recommendations_recommendation_id ON public.cycle_report_scoping_attribute_recommendations_backup USING btree (recommendation_id);


--
-- TOC entry 5006 (class 1259 OID 33466)
-- Name: ix_attribute_version_change_logs_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attribute_version_change_logs_log_id ON public.attribute_version_change_logs USING btree (log_id);


--
-- TOC entry 5011 (class 1259 OID 33493)
-- Name: ix_attribute_version_comparisons_comparison_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attribute_version_comparisons_comparison_id ON public.attribute_version_comparisons USING btree (comparison_id);


--
-- TOC entry 4901 (class 1259 OID 31769)
-- Name: ix_audit_log_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_action ON public.audit_logs USING btree (action);


--
-- TOC entry 4902 (class 1259 OID 31770)
-- Name: ix_audit_log_audit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_audit_id ON public.audit_logs USING btree (audit_id);


--
-- TOC entry 5047 (class 1259 OID 34637)
-- Name: ix_data_owner_phase_audit_log_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_owner_phase_audit_log_action ON public.data_owner_phase_audit_logs_legacy USING btree (action);


--
-- TOC entry 5048 (class 1259 OID 34638)
-- Name: ix_data_owner_phase_audit_log_audit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_owner_phase_audit_log_audit_id ON public.data_owner_phase_audit_logs_legacy USING btree (audit_id);


--
-- TOC entry 4961 (class 1259 OID 32851)
-- Name: ix_escalation_email_logs_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_escalation_email_logs_log_id ON public.escalation_email_logs USING btree (log_id);


--
-- TOC entry 4930 (class 1259 OID 32189)
-- Name: ix_llm_audit_log_llm_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_llm_audit_log_llm_provider ON public.llm_audit_logs USING btree (llm_provider);


--
-- TOC entry 4931 (class 1259 OID 32190)
-- Name: ix_llm_audit_log_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_llm_audit_log_log_id ON public.llm_audit_logs USING btree (log_id);


--
-- TOC entry 4873 (class 1259 OID 31653)
-- Name: ix_lobs_lob_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_lobs_lob_id ON public.lobs USING btree (lob_id);


--
-- TOC entry 4874 (class 1259 OID 31652)
-- Name: ix_lobs_lob_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_lobs_lob_name ON public.lobs USING btree (lob_name);


--
-- TOC entry 5030 (class 1259 OID 33645)
-- Name: ix_permission_audit_log_audit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permission_audit_log_audit_id ON public.rbac_permission_audit_logs USING btree (audit_id);


--
-- TOC entry 5031 (class 1259 OID 33642)
-- Name: ix_permission_audit_log_performed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permission_audit_log_performed_at ON public.rbac_permission_audit_logs USING btree (performed_at);


--
-- TOC entry 5032 (class 1259 OID 33644)
-- Name: ix_permission_audit_log_target_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permission_audit_log_target_id ON public.rbac_permission_audit_logs USING btree (target_id);


--
-- TOC entry 5033 (class 1259 OID 33643)
-- Name: ix_permission_audit_log_target_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permission_audit_log_target_type ON public.rbac_permission_audit_logs USING btree (target_type);


--
-- TOC entry 4984 (class 1259 OID 33410)
-- Name: ix_permissions_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_action ON public.rbac_permissions USING btree (action);


--
-- TOC entry 4985 (class 1259 OID 33411)
-- Name: ix_permissions_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_permission_id ON public.rbac_permissions USING btree (permission_id);


--
-- TOC entry 4986 (class 1259 OID 33412)
-- Name: ix_permissions_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_resource ON public.rbac_permissions USING btree (resource);


--
-- TOC entry 5036 (class 1259 OID 33725)
-- Name: ix_rdd_item_name_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rdd_item_name_search ON public.regulatory_data_dictionaries USING btree (line_item_name);


--
-- TOC entry 5037 (class 1259 OID 33729)
-- Name: ix_rdd_mandatory_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rdd_mandatory_search ON public.regulatory_data_dictionaries USING btree (mandatory_or_optional);


--
-- TOC entry 5038 (class 1259 OID 33727)
-- Name: ix_rdd_report_schedule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rdd_report_schedule ON public.regulatory_data_dictionaries USING btree (report_name, schedule_name);


--
-- TOC entry 5039 (class 1259 OID 33730)
-- Name: ix_regulatory_data_dictionary_line_item_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regulatory_data_dictionary_line_item_name ON public.regulatory_data_dictionaries USING btree (line_item_name);


--
-- TOC entry 5040 (class 1259 OID 33728)
-- Name: ix_regulatory_data_dictionary_mandatory_or_optional; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regulatory_data_dictionary_mandatory_or_optional ON public.regulatory_data_dictionaries USING btree (mandatory_or_optional);


--
-- TOC entry 5041 (class 1259 OID 33731)
-- Name: ix_regulatory_data_dictionary_report_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regulatory_data_dictionary_report_name ON public.regulatory_data_dictionaries USING btree (report_name);


--
-- TOC entry 5042 (class 1259 OID 33726)
-- Name: ix_regulatory_data_dictionary_schedule_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regulatory_data_dictionary_schedule_name ON public.regulatory_data_dictionaries USING btree (schedule_name);


--
-- TOC entry 4939 (class 1259 OID 32465)
-- Name: ix_request_info_audit_logs_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_request_info_audit_logs_log_id ON public.cycle_report_request_info_audit_logs USING btree (log_id);


--
-- TOC entry 5022 (class 1259 OID 33594)
-- Name: ix_resource_permissions_resource_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_permissions_resource_id ON public.rbac_resource_permissions USING btree (resource_id);


--
-- TOC entry 5023 (class 1259 OID 33597)
-- Name: ix_resource_permissions_resource_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_permissions_resource_permission_id ON public.rbac_resource_permissions USING btree (resource_permission_id);


--
-- TOC entry 5024 (class 1259 OID 33596)
-- Name: ix_resource_permissions_resource_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_permissions_resource_type ON public.rbac_resource_permissions USING btree (resource_type);


--
-- TOC entry 5025 (class 1259 OID 33595)
-- Name: ix_resource_permissions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_permissions_user_id ON public.rbac_resource_permissions USING btree (user_id);


--
-- TOC entry 4997 (class 1259 OID 33443)
-- Name: ix_resources_resource_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resources_resource_id ON public.rbac_resources USING btree (resource_id);


--
-- TOC entry 4998 (class 1259 OID 33442)
-- Name: ix_resources_resource_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_resources_resource_name ON public.rbac_resources USING btree (resource_name);


--
-- TOC entry 4999 (class 1259 OID 33444)
-- Name: ix_resources_resource_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resources_resource_type ON public.rbac_resources USING btree (resource_type);


--
-- TOC entry 4993 (class 1259 OID 33425)
-- Name: ix_roles_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_role_id ON public.rbac_roles USING btree (role_id);


--
-- TOC entry 4994 (class 1259 OID 33424)
-- Name: ix_roles_role_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_roles_role_name ON public.rbac_roles USING btree (role_name);


--
-- TOC entry 4953 (class 1259 OID 32708)
-- Name: ix_sample_selection_audit_log_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sample_selection_audit_log_action ON public.cycle_report_sample_selection_audit_logs USING btree (action);


--
-- TOC entry 4954 (class 1259 OID 32705)
-- Name: ix_sample_selection_audit_log_audit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sample_selection_audit_log_audit_id ON public.cycle_report_sample_selection_audit_logs USING btree (audit_id);


--
-- TOC entry 4927 (class 1259 OID 31964)
-- Name: ix_scoping_submissions_submission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scoping_submissions_submission_id ON public.cycle_report_scoping_submissions USING btree (submission_id);


--
-- TOC entry 4879 (class 1259 OID 31676)
-- Name: ix_sla_configurations_sla_config_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sla_configurations_sla_config_id ON public.universal_sla_configurations USING btree (sla_config_id);


--
-- TOC entry 4880 (class 1259 OID 31677)
-- Name: ix_sla_configurations_sla_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sla_configurations_sla_type ON public.universal_sla_configurations USING btree (sla_type);


--
-- TOC entry 4905 (class 1259 OID 31792)
-- Name: ix_sla_escalation_rules_escalation_rule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sla_escalation_rules_escalation_rule_id ON public.universal_sla_escalation_rules USING btree (escalation_rule_id);


--
-- TOC entry 4934 (class 1259 OID 32217)
-- Name: ix_sla_violation_tracking_violation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sla_violation_tracking_violation_id ON public.universal_sla_violation_trackings USING btree (violation_id);


--
-- TOC entry 4893 (class 1259 OID 31752)
-- Name: ix_test_cycles_cycle_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_cycles_cycle_id ON public.test_cycles USING btree (cycle_id);


--
-- TOC entry 4894 (class 1259 OID 31751)
-- Name: ix_test_cycles_cycle_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_cycles_cycle_name ON public.test_cycles USING btree (cycle_name);


--
-- TOC entry 4895 (class 1259 OID 35460)
-- Name: ix_test_cycles_cycle_workflow; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_cycles_cycle_workflow ON public.test_cycles USING btree (cycle_id, workflow_id);


--
-- TOC entry 4896 (class 1259 OID 35459)
-- Name: ix_test_cycles_workflow_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_cycles_workflow_id ON public.test_cycles USING btree (workflow_id);


--
-- TOC entry 5058 (class 1259 OID 35216)
-- Name: ix_test_report_sections_section_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_test_report_sections_section_id ON public.cycle_report_test_report_sections USING btree (section_id);


--
-- TOC entry 5129 (class 1259 OID 36727)
-- Name: ix_universal_assignment_history_history_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignment_history_history_id ON public.universal_assignment_histories USING btree (history_id);


--
-- TOC entry 5120 (class 1259 OID 36694)
-- Name: ix_universal_assignments_assignment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_assignment_id ON public.universal_assignments USING btree (assignment_id);


--
-- TOC entry 5121 (class 1259 OID 36696)
-- Name: ix_universal_assignments_assignment_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_assignment_type ON public.universal_assignments USING btree (assignment_type);


--
-- TOC entry 5122 (class 1259 OID 36697)
-- Name: ix_universal_assignments_context_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_context_type ON public.universal_assignments USING btree (context_type);


--
-- TOC entry 5123 (class 1259 OID 36691)
-- Name: ix_universal_assignments_due_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_due_date ON public.universal_assignments USING btree (due_date);


--
-- TOC entry 5124 (class 1259 OID 36693)
-- Name: ix_universal_assignments_from_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_from_role ON public.universal_assignments USING btree (from_role);


--
-- TOC entry 5125 (class 1259 OID 36692)
-- Name: ix_universal_assignments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_status ON public.universal_assignments USING btree (status);


--
-- TOC entry 5126 (class 1259 OID 36695)
-- Name: ix_universal_assignments_to_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universal_assignments_to_role ON public.universal_assignments USING btree (to_role);


--
-- TOC entry 5018 (class 1259 OID 33565)
-- Name: ix_user_permissions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_permissions_expires_at ON public.rbac_user_permissions USING btree (expires_at);


--
-- TOC entry 5019 (class 1259 OID 33566)
-- Name: ix_user_permissions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_permissions_user_id ON public.rbac_user_permissions USING btree (user_id);


--
-- TOC entry 5014 (class 1259 OID 33541)
-- Name: ix_user_roles_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_expires_at ON public.rbac_user_roles USING btree (expires_at);


--
-- TOC entry 5015 (class 1259 OID 33540)
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_user_id ON public.rbac_user_roles USING btree (user_id);


--
-- TOC entry 4885 (class 1259 OID 31696)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 4886 (class 1259 OID 112989)
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- TOC entry 4887 (class 1259 OID 31694)
-- Name: ix_users_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_user_id ON public.users USING btree (user_id);


--
-- TOC entry 5137 (class 1259 OID 36990)
-- Name: ix_workflow_activities_cycle_report; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activities_cycle_report ON public.workflow_activities USING btree (cycle_id, report_id);


--
-- TOC entry 5138 (class 1259 OID 115324)
-- Name: ix_workflow_activities_instance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activities_instance_id ON public.workflow_activities USING btree (cycle_id, report_id, instance_id);


--
-- TOC entry 5139 (class 1259 OID 115325)
-- Name: ix_workflow_activities_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activities_parent ON public.workflow_activities USING btree (parent_activity_id);


--
-- TOC entry 5140 (class 1259 OID 36991)
-- Name: ix_workflow_activities_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activities_phase ON public.workflow_activities USING btree (cycle_id, report_id, phase_name);


--
-- TOC entry 5141 (class 1259 OID 37145)
-- Name: ix_workflow_activities_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activities_status ON public.workflow_activities USING btree (status);


--
-- TOC entry 5156 (class 1259 OID 115326)
-- Name: ix_workflow_activity_templates_handler; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activity_templates_handler ON public.workflow_activity_templates USING btree (handler_name);


--
-- TOC entry 5157 (class 1259 OID 115327)
-- Name: ix_workflow_activity_templates_phase_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_activity_templates_phase_order ON public.workflow_activity_templates USING btree (phase_name, activity_order);


--
-- TOC entry 4919 (class 1259 OID 31851)
-- Name: ix_workflow_phases_phase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_phases_phase_id ON public.workflow_phases USING btree (phase_id);


--
-- TOC entry 5366 (class 1259 OID 121274)
-- Name: uq_test_execution_results_latest_execution; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_test_execution_results_latest_execution ON public.cycle_report_test_execution_results USING btree (test_case_id, is_latest_execution) WHERE (is_latest_execution = true);


--
-- TOC entry 5997 (class 2620 OID 120089)
-- Name: workflow_activities trg_auto_skip_upload_files; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_auto_skip_upload_files BEFORE INSERT OR UPDATE ON public.workflow_activities FOR EACH ROW EXECUTE FUNCTION public.auto_skip_upload_files_activity();


--
-- TOC entry 6008 (class 2620 OID 121967)
-- Name: cycle_report_documents trg_cycle_report_documents_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cycle_report_documents_updated_at BEFORE UPDATE ON public.cycle_report_documents FOR EACH ROW EXECUTE FUNCTION public.update_cycle_report_documents_updated_at();


--
-- TOC entry 6009 (class 2620 OID 121969)
-- Name: cycle_report_documents trg_handle_document_versioning; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_handle_document_versioning BEFORE INSERT OR UPDATE ON public.cycle_report_documents FOR EACH ROW EXECUTE FUNCTION public.handle_document_versioning();


--
-- TOC entry 6005 (class 2620 OID 121595)
-- Name: cycle_report_observation_groups trg_observation_groups_updated_at_unified; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_observation_groups_updated_at_unified BEFORE UPDATE ON public.cycle_report_observation_groups FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column_unified();


--
-- TOC entry 6007 (class 2620 OID 121596)
-- Name: cycle_report_observations_unified trg_observations_unified_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_observations_unified_updated_at BEFORE UPDATE ON public.cycle_report_observations_unified FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column_unified();


--
-- TOC entry 5998 (class 2620 OID 120095)
-- Name: workflow_activities trg_prevent_duplicate_activities; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_prevent_duplicate_activities BEFORE INSERT OR UPDATE ON public.workflow_activities FOR EACH ROW EXECUTE FUNCTION public.prevent_duplicate_activities();


--
-- TOC entry 6006 (class 2620 OID 121593)
-- Name: cycle_report_observations_unified trg_update_observation_count_unified; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_update_observation_count_unified AFTER INSERT OR DELETE ON public.cycle_report_observations_unified FOR EACH ROW EXECUTE FUNCTION public.update_observation_group_count_unified();


--
-- TOC entry 6010 (class 2620 OID 122274)
-- Name: cycle_report_document_access_logs trigger_cycle_report_document_access_logs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_cycle_report_document_access_logs_updated_at BEFORE UPDATE ON public.cycle_report_document_access_logs FOR EACH ROW EXECUTE FUNCTION public.update_cycle_report_document_updated_at();


--
-- TOC entry 6011 (class 2620 OID 122275)
-- Name: cycle_report_document_extractions trigger_cycle_report_document_extractions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_cycle_report_document_extractions_updated_at BEFORE UPDATE ON public.cycle_report_document_extractions FOR EACH ROW EXECUTE FUNCTION public.update_cycle_report_document_updated_at();


--
-- TOC entry 6002 (class 2620 OID 119661)
-- Name: attribute_profile_results update_attribute_profile_results_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_attribute_profile_results_updated_at BEFORE UPDATE ON public.attribute_profile_results FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6012 (class 2620 OID 125380)
-- Name: cycle_report_rfi_query_validations update_cycle_report_rfi_query_validations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_cycle_report_rfi_query_validations_updated_at BEFORE UPDATE ON public.cycle_report_rfi_query_validations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6014 (class 2620 OID 124931)
-- Name: cycle_report_sample_selection_samples update_cycle_report_sample_selection_samples_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_cycle_report_sample_selection_samples_updated_at BEFORE UPDATE ON public.cycle_report_sample_selection_samples FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6013 (class 2620 OID 124849)
-- Name: cycle_report_sample_selection_versions update_cycle_report_sample_selection_versions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_cycle_report_sample_selection_versions_updated_at BEFORE UPDATE ON public.cycle_report_sample_selection_versions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6000 (class 2620 OID 119659)
-- Name: data_profiling_configurations update_data_profiling_configurations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_data_profiling_configurations_updated_at BEFORE UPDATE ON public.data_profiling_configurations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6001 (class 2620 OID 119660)
-- Name: data_profiling_jobs update_data_profiling_jobs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_data_profiling_jobs_updated_at BEFORE UPDATE ON public.data_profiling_jobs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 5999 (class 2620 OID 119434)
-- Name: data_profiling_rules update_data_profiling_rules_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_data_profiling_rules_updated_at BEFORE UPDATE ON public.data_profiling_rules FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6003 (class 2620 OID 121287)
-- Name: cycle_report_test_execution_results update_test_execution_results_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_test_execution_results_updated_at BEFORE UPDATE ON public.cycle_report_test_execution_results FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 6004 (class 2620 OID 121288)
-- Name: cycle_report_test_execution_reviews update_test_execution_reviews_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_test_execution_reviews_updated_at BEFORE UPDATE ON public.cycle_report_test_execution_reviews FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 5713 (class 2606 OID 115822)
-- Name: attribute_mappings attribute_mappings_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_mappings
    ADD CONSTRAINT attribute_mappings_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5711 (class 2606 OID 117843)
-- Name: attribute_mappings attribute_mappings_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_mappings
    ADD CONSTRAINT attribute_mappings_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5714 (class 2606 OID 115827)
-- Name: attribute_mappings attribute_mappings_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_mappings
    ADD CONSTRAINT attribute_mappings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5712 (class 2606 OID 117849)
-- Name: attribute_mappings attribute_mappings_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_mappings
    ADD CONSTRAINT attribute_mappings_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5806 (class 2606 OID 119639)
-- Name: attribute_profile_results attribute_profile_results_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results
    ADD CONSTRAINT attribute_profile_results_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id) ON DELETE CASCADE;


--
-- TOC entry 5807 (class 2606 OID 119644)
-- Name: attribute_profile_results attribute_profile_results_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results
    ADD CONSTRAINT attribute_profile_results_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5805 (class 2606 OID 119634)
-- Name: attribute_profile_results attribute_profile_results_profiling_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results
    ADD CONSTRAINT attribute_profile_results_profiling_job_id_fkey FOREIGN KEY (profiling_job_id) REFERENCES public.data_profiling_jobs(id) ON DELETE CASCADE;


--
-- TOC entry 5808 (class 2606 OID 119649)
-- Name: attribute_profile_results attribute_profile_results_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_profile_results
    ADD CONSTRAINT attribute_profile_results_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5572 (class 2606 OID 117963)
-- Name: cycle_report_scoping_attribute_recommendations_backup attribute_scoping_recommendations_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attribute_recommendations_backup
    ADD CONSTRAINT attribute_scoping_recommendations_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5573 (class 2606 OID 117969)
-- Name: cycle_report_scoping_attribute_recommendations_backup attribute_scoping_recommendations_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attribute_recommendations_backup
    ADD CONSTRAINT attribute_scoping_recommendations_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5607 (class 2606 OID 33461)
-- Name: attribute_version_change_logs attribute_version_change_logs_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_change_logs
    ADD CONSTRAINT attribute_version_change_logs_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5608 (class 2606 OID 117987)
-- Name: attribute_version_change_logs attribute_version_change_logs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_change_logs
    ADD CONSTRAINT attribute_version_change_logs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5609 (class 2606 OID 117993)
-- Name: attribute_version_change_logs attribute_version_change_logs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_change_logs
    ADD CONSTRAINT attribute_version_change_logs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5610 (class 2606 OID 33488)
-- Name: attribute_version_comparisons attribute_version_comparisons_compared_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_comparisons
    ADD CONSTRAINT attribute_version_comparisons_compared_by_fkey FOREIGN KEY (compared_by) REFERENCES public.users(user_id);


--
-- TOC entry 5611 (class 2606 OID 117999)
-- Name: attribute_version_comparisons attribute_version_comparisons_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_comparisons
    ADD CONSTRAINT attribute_version_comparisons_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5612 (class 2606 OID 118005)
-- Name: attribute_version_comparisons attribute_version_comparisons_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribute_version_comparisons
    ADD CONSTRAINT attribute_version_comparisons_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5538 (class 2606 OID 31764)
-- Name: audit_logs audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5751 (class 2606 OID 116572)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5749 (class 2606 OID 116562)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5745 (class 2606 OID 117975)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5750 (class 2606 OID 116567)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5746 (class 2606 OID 117981)
-- Name: cycle_report_planning_attributes cycle_report_attributes_planning_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_attributes_planning_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5743 (class 2606 OID 116502)
-- Name: cycle_report_planning_attribute_version_history cycle_report_attributes_planning_version_histor_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attribute_version_history
    ADD CONSTRAINT cycle_report_attributes_planning_version_histor_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5840 (class 2606 OID 120716)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribu_previous_data_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribu_previous_data_owner_id_fkey FOREIGN KEY (previous_data_owner_id) REFERENCES public.users(user_id);


--
-- TOC entry 5839 (class 2606 OID 120711)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_as_data_executive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_as_data_executive_id_fkey FOREIGN KEY (data_executive_id) REFERENCES public.users(user_id);


--
-- TOC entry 5841 (class 2606 OID 120721)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assign_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assign_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5838 (class 2606 OID 120706)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assign_data_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assign_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES public.users(user_id);


--
-- TOC entry 5842 (class 2606 OID 120726)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assign_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assign_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5836 (class 2606 OID 120696)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assignm_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assignm_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5834 (class 2606 OID 120681)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assignmen_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assignmen_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.cycle_report_data_owner_lob_mapping_versions(version_id) ON DELETE CASCADE;


--
-- TOC entry 5837 (class 2606 OID 120701)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assignments_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assignments_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5835 (class 2606 OID 120686)
-- Name: cycle_report_data_owner_lob_mapping cycle_report_data_owner_lob_attribute_assignments_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_assignments_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5831 (class 2606 OID 120588)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_ve_data_executive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_ve_data_executive_id_fkey FOREIGN KEY (data_executive_id) REFERENCES public.users(user_id);


--
-- TOC entry 5830 (class 2606 OID 120583)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_ve_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_ve_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.cycle_report_data_owner_lob_mapping_versions(version_id);


--
-- TOC entry 5832 (class 2606 OID 120593)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_versio_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_versio_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5833 (class 2606 OID 120598)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_versio_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_versio_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5828 (class 2606 OID 120573)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5829 (class 2606 OID 120578)
-- Name: cycle_report_data_owner_lob_mapping_versions cycle_report_data_owner_lob_attribute_workflow_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_owner_lob_mapping_versions
    ADD CONSTRAINT cycle_report_data_owner_lob_attribute_workflow_activity_id_fkey FOREIGN KEY (workflow_activity_id) REFERENCES public.workflow_activities(activity_id);


--
-- TOC entry 5938 (class 2606 OID 123287)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_anomaly_marked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_anomaly_marked_by_fkey FOREIGN KEY (anomaly_marked_by) REFERENCES public.users(user_id);


--
-- TOC entry 5939 (class 2606 OID 123292)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5936 (class 2606 OID 123277)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5937 (class 2606 OID 123282)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES public.cycle_report_data_profiling_rules(rule_id);


--
-- TOC entry 5940 (class 2606 OID 123297)
-- Name: cycle_report_data_profiling_results cycle_report_data_profiling_results_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_results
    ADD CONSTRAINT cycle_report_data_profiling_results_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5908 (class 2606 OID 122688)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_vers_workflow_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_vers_workflow_activity_id_fkey FOREIGN KEY (workflow_activity_id) REFERENCES public.workflow_activities(activity_id);


--
-- TOC entry 5909 (class 2606 OID 122693)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_version_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_version_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.cycle_report_data_profiling_rule_versions(version_id);


--
-- TOC entry 5911 (class 2606 OID 122703)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5912 (class 2606 OID 122708)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5907 (class 2606 OID 122683)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5910 (class 2606 OID 122698)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_submitted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_submitted_by_id_fkey FOREIGN KEY (submitted_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5913 (class 2606 OID 122713)
-- Name: cycle_report_data_profiling_rule_versions cycle_report_data_profiling_rule_versions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rule_versions
    ADD CONSTRAINT cycle_report_data_profiling_rule_versions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5916 (class 2606 OID 122741)
-- Name: cycle_report_data_profiling_rules cycle_report_data_profiling_rules_report_owner_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rules
    ADD CONSTRAINT cycle_report_data_profiling_rules_report_owner_decided_by_fkey FOREIGN KEY (report_owner_decided_by) REFERENCES public.users(user_id);


--
-- TOC entry 5915 (class 2606 OID 122736)
-- Name: cycle_report_data_profiling_rules cycle_report_data_profiling_rules_tester_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rules
    ADD CONSTRAINT cycle_report_data_profiling_rules_tester_decided_by_fkey FOREIGN KEY (tester_decided_by) REFERENCES public.users(user_id);


--
-- TOC entry 5914 (class 2606 OID 122731)
-- Name: cycle_report_data_profiling_rules cycle_report_data_profiling_rules_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rules
    ADD CONSTRAINT cycle_report_data_profiling_rules_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.cycle_report_data_profiling_rule_versions(version_id) ON DELETE CASCADE;


--
-- TOC entry 5781 (class 2606 OID 118983)
-- Name: cycle_report_planning_data_sources cycle_report_data_sources_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_data_sources
    ADD CONSTRAINT cycle_report_data_sources_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5782 (class 2606 OID 118988)
-- Name: cycle_report_planning_data_sources cycle_report_data_sources_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_data_sources
    ADD CONSTRAINT cycle_report_data_sources_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5765 (class 2606 OID 116630)
-- Name: cycle_report_test_cases_document_submissions cycle_report_document_submissions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT cycle_report_document_submissions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5764 (class 2606 OID 116625)
-- Name: cycle_report_test_cases_document_submissions cycle_report_document_submissions_data_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT cycle_report_document_submissions_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES public.users(user_id);


--
-- TOC entry 5766 (class 2606 OID 116635)
-- Name: cycle_report_test_cases_document_submissions cycle_report_document_submissions_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT cycle_report_document_submissions_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5887 (class 2606 OID 121921)
-- Name: cycle_report_documents cycle_report_documents_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5888 (class 2606 OID 121926)
-- Name: cycle_report_documents cycle_report_documents_archived_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_archived_by_fkey FOREIGN KEY (archived_by) REFERENCES public.users(user_id);


--
-- TOC entry 5890 (class 2606 OID 121936)
-- Name: cycle_report_documents cycle_report_documents_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5885 (class 2606 OID 121911)
-- Name: cycle_report_documents cycle_report_documents_last_downloaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_last_downloaded_by_fkey FOREIGN KEY (last_downloaded_by) REFERENCES public.users(user_id);


--
-- TOC entry 5886 (class 2606 OID 121916)
-- Name: cycle_report_documents cycle_report_documents_last_viewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_last_viewed_by_fkey FOREIGN KEY (last_viewed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5884 (class 2606 OID 121906)
-- Name: cycle_report_documents cycle_report_documents_parent_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_parent_document_id_fkey FOREIGN KEY (parent_document_id) REFERENCES public.cycle_report_documents(id);


--
-- TOC entry 5883 (class 2606 OID 121901)
-- Name: cycle_report_documents cycle_report_documents_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5891 (class 2606 OID 121941)
-- Name: cycle_report_documents cycle_report_documents_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5889 (class 2606 OID 121931)
-- Name: cycle_report_documents cycle_report_documents_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_documents
    ADD CONSTRAINT cycle_report_documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(user_id);


--
-- TOC entry 5868 (class 2606 OID 121486)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5875 (class 2606 OID 121521)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5874 (class 2606 OID 121516)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_detected_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_detected_by_fkey FOREIGN KEY (detected_by) REFERENCES public.users(user_id);


--
-- TOC entry 5869 (class 2606 OID 121491)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5867 (class 2606 OID 121471)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5871 (class 2606 OID 121501)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_report_owner_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_report_owner_approved_by_fkey FOREIGN KEY (report_owner_approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5872 (class 2606 OID 121506)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_resolution_owner_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_resolution_owner_fkey FOREIGN KEY (resolution_owner) REFERENCES public.users(user_id);


--
-- TOC entry 5873 (class 2606 OID 121511)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5870 (class 2606 OID 121496)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_tester_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_tester_reviewed_by_fkey FOREIGN KEY (tester_reviewed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5876 (class 2606 OID 121526)
-- Name: cycle_report_observation_groups cycle_report_observation_groups_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_groups
    ADD CONSTRAINT cycle_report_observation_groups_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5591 (class 2606 OID 119866)
-- Name: cycle_report_observation_mgmt_approvals cycle_report_observation_mgmt_approvals_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT cycle_report_observation_mgmt_approvals_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5586 (class 2606 OID 119861)
-- Name: cycle_report_observation_mgmt_impact_assessments cycle_report_observation_mgmt_impact_assessments_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT cycle_report_observation_mgmt_impact_assessments_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5813 (class 2606 OID 119722)
-- Name: cycle_report_observation_mgmt_preliminary_findings cycle_report_observation_mgmt_preliminary_f_assigned_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings
    ADD CONSTRAINT cycle_report_observation_mgmt_preliminary_f_assigned_to_id_fkey FOREIGN KEY (assigned_to_id) REFERENCES public.users(user_id);


--
-- TOC entry 5814 (class 2606 OID 119727)
-- Name: cycle_report_observation_mgmt_preliminary_findings cycle_report_observation_mgmt_preliminary_fi_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings
    ADD CONSTRAINT cycle_report_observation_mgmt_preliminary_fi_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5815 (class 2606 OID 119732)
-- Name: cycle_report_observation_mgmt_preliminary_findings cycle_report_observation_mgmt_preliminary_fi_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings
    ADD CONSTRAINT cycle_report_observation_mgmt_preliminary_fi_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5816 (class 2606 OID 119876)
-- Name: cycle_report_observation_mgmt_preliminary_findings cycle_report_observation_mgmt_preliminary_finding_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_preliminary_findings
    ADD CONSTRAINT cycle_report_observation_mgmt_preliminary_finding_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5597 (class 2606 OID 119871)
-- Name: cycle_report_observation_mgmt_resolutions cycle_report_observation_mgmt_resolutions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT cycle_report_observation_mgmt_resolutions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5879 (class 2606 OID 121560)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5881 (class 2606 OID 121570)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5877 (class 2606 OID 121550)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.cycle_report_observation_groups(id) ON DELETE CASCADE;


--
-- TOC entry 5880 (class 2606 OID 121565)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5878 (class 2606 OID 121555)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_test_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_test_execution_id_fkey FOREIGN KEY (test_execution_id) REFERENCES public.cycle_report_test_execution_results(id);


--
-- TOC entry 5882 (class 2606 OID 121575)
-- Name: cycle_report_observations_unified cycle_report_observations_unified_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observations_unified
    ADD CONSTRAINT cycle_report_observations_unified_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5784 (class 2606 OID 119020)
-- Name: cycle_report_planning_pde_mappings cycle_report_pde_mappings_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT cycle_report_pde_mappings_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5786 (class 2606 OID 119030)
-- Name: cycle_report_planning_pde_mappings cycle_report_pde_mappings_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT cycle_report_pde_mappings_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5785 (class 2606 OID 119025)
-- Name: cycle_report_planning_pde_mappings cycle_report_pde_mappings_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT cycle_report_pde_mappings_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.cycle_report_planning_data_sources(id);


--
-- TOC entry 5787 (class 2606 OID 119035)
-- Name: cycle_report_planning_pde_mappings cycle_report_pde_mappings_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT cycle_report_pde_mappings_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5744 (class 2606 OID 119781)
-- Name: cycle_report_planning_attribute_version_history cycle_report_planning_attribute_version_history_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attribute_version_history
    ADD CONSTRAINT cycle_report_planning_attribute_version_history_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5754 (class 2606 OID 119776)
-- Name: cycle_report_planning_attributes cycle_report_planning_attributes_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT cycle_report_planning_attributes_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5569 (class 2606 OID 125412)
-- Name: cycle_report_request_info_audit_logs cycle_report_request_info_audit_logs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT cycle_report_request_info_audit_logs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5567 (class 2606 OID 125402)
-- Name: cycle_report_request_info_audit_logs cycle_report_request_info_audit_logs_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT cycle_report_request_info_audit_logs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5568 (class 2606 OID 125407)
-- Name: cycle_report_request_info_audit_logs cycle_report_request_info_audit_logs_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT cycle_report_request_info_audit_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5570 (class 2606 OID 125417)
-- Name: cycle_report_request_info_audit_logs cycle_report_request_info_audit_logs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT cycle_report_request_info_audit_logs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5810 (class 2606 OID 119684)
-- Name: cycle_report_request_info_document_versions cycle_report_request_info_document_versions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT cycle_report_request_info_document_versions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5812 (class 2606 OID 119836)
-- Name: cycle_report_request_info_document_versions cycle_report_request_info_document_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT cycle_report_request_info_document_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5811 (class 2606 OID 119689)
-- Name: cycle_report_request_info_document_versions cycle_report_request_info_document_versions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT cycle_report_request_info_document_versions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5809 (class 2606 OID 119679)
-- Name: cycle_report_request_info_document_versions cycle_report_request_info_document_versions_uploaded_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_document_versions
    ADD CONSTRAINT cycle_report_request_info_document_versions_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5993 (class 2606 OID 125354)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evide_report_owner_decided_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evide_report_owner_decided_by_id_fkey FOREIGN KEY (report_owner_decided_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5853 (class 2606 OID 120885)
-- Name: cycle_report_request_info_evidence_validation cycle_report_request_info_evidence_validation_evidence_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_validation
    ADD CONSTRAINT cycle_report_request_info_evidence_validation_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES public.cycle_report_request_info_testcase_source_evidence(id);


--
-- TOC entry 5854 (class 2606 OID 120890)
-- Name: cycle_report_request_info_evidence_validation cycle_report_request_info_evidence_validation_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_validation
    ADD CONSTRAINT cycle_report_request_info_evidence_validation_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5992 (class 2606 OID 125349)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_ve_tester_decided_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_ve_tester_decided_by_id_fkey FOREIGN KEY (tester_decided_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5994 (class 2606 OID 125359)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_vers_parent_evidence_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_vers_parent_evidence_id_fkey FOREIGN KEY (parent_evidence_id) REFERENCES public.cycle_report_request_info_evidence(evidence_id);


--
-- TOC entry 5982 (class 2606 OID 125282)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versi_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versi_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.cycle_report_request_info_evidence_versions(version_id);


--
-- TOC entry 5991 (class 2606 OID 125344)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versio_submitted_by_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versio_submitted_by_id_fkey1 FOREIGN KEY (submitted_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5983 (class 2606 OID 125287)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_version_submitted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_version_submitted_by_id_fkey FOREIGN KEY (submitted_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5990 (class 2606 OID 125339)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5995 (class 2606 OID 125364)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5988 (class 2606 OID 125329)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5989 (class 2606 OID 125334)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_test_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id);


--
-- TOC entry 5996 (class 2606 OID 125369)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5987 (class 2606 OID 125324)
-- Name: cycle_report_request_info_evidence cycle_report_request_info_evidence_versioned_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence
    ADD CONSTRAINT cycle_report_request_info_evidence_versioned_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.cycle_report_request_info_evidence_versions(version_id) ON DELETE CASCADE;


--
-- TOC entry 5984 (class 2606 OID 125292)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versions_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versions_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5985 (class 2606 OID 125297)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5981 (class 2606 OID 125277)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5986 (class 2606 OID 125302)
-- Name: cycle_report_request_info_evidence_versions cycle_report_request_info_evidence_versions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_evidence_versions
    ADD CONSTRAINT cycle_report_request_info_evidence_versions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5852 (class 2606 OID 124338)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_sou_query_validation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_sou_query_validation_id_fkey FOREIGN KEY (query_validation_id) REFERENCES public.cycle_report_rfi_query_validations(validation_id);


--
-- TOC entry 5846 (class 2606 OID 120845)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_e_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_e_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.cycle_report_planning_data_sources(id);


--
-- TOC entry 5845 (class 2606 OID 120840)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evi_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evi_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5847 (class 2606 OID 120850)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evi_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evi_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5844 (class 2606 OID 120835)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evi_test_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evi_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id);


--
-- TOC entry 5848 (class 2606 OID 120855)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evi_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evi_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5849 (class 2606 OID 120860)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evid_replaced_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evid_replaced_by_fkey FOREIGN KEY (replaced_by) REFERENCES public.cycle_report_request_info_testcase_source_evidence(id);


--
-- TOC entry 5850 (class 2606 OID 120865)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evide_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evide_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5851 (class 2606 OID 120870)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evide_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evide_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5843 (class 2606 OID 120820)
-- Name: cycle_report_request_info_testcase_source_evidence cycle_report_request_info_testcase_source_evidenc_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_testcase_source_evidence
    ADD CONSTRAINT cycle_report_request_info_testcase_source_evidenc_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5943 (class 2606 OID 124291)
-- Name: cycle_report_rfi_data_sources cycle_report_rfi_data_sources_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT cycle_report_rfi_data_sources_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5942 (class 2606 OID 124286)
-- Name: cycle_report_rfi_data_sources cycle_report_rfi_data_sources_data_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT cycle_report_rfi_data_sources_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES public.users(user_id);


--
-- TOC entry 5941 (class 2606 OID 124281)
-- Name: cycle_report_rfi_data_sources cycle_report_rfi_data_sources_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT cycle_report_rfi_data_sources_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5944 (class 2606 OID 124296)
-- Name: cycle_report_rfi_data_sources cycle_report_rfi_data_sources_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_data_sources
    ADD CONSTRAINT cycle_report_rfi_data_sources_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5960 (class 2606 OID 124638)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5962 (class 2606 OID 125382)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5951 (class 2606 OID 124593)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5956 (class 2606 OID 124618)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.users(user_id);


--
-- TOC entry 5953 (class 2606 OID 124603)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_parent_evidence_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_parent_evidence_id_fkey FOREIGN KEY (parent_evidence_id) REFERENCES public.cycle_report_rfi_evidence(id);


--
-- TOC entry 5950 (class 2606 OID 124588)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5958 (class 2606 OID 124628)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_planning_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_planning_data_source_id_fkey FOREIGN KEY (planning_data_source_id) REFERENCES public.cycle_report_planning_data_sources(id);


--
-- TOC entry 5959 (class 2606 OID 124633)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_query_validation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_query_validation_id_fkey FOREIGN KEY (query_validation_id) REFERENCES public.cycle_report_rfi_query_validations(validation_id);


--
-- TOC entry 5952 (class 2606 OID 124598)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5957 (class 2606 OID 124623)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_rfi_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_rfi_data_source_id_fkey FOREIGN KEY (rfi_data_source_id) REFERENCES public.cycle_report_rfi_data_sources(data_source_id);


--
-- TOC entry 5954 (class 2606 OID 124608)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5949 (class 2606 OID 124583)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_test_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id);


--
-- TOC entry 5961 (class 2606 OID 124643)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5963 (class 2606 OID 125387)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5955 (class 2606 OID 124613)
-- Name: cycle_report_rfi_evidence cycle_report_rfi_evidence_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_evidence
    ADD CONSTRAINT cycle_report_rfi_evidence_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5946 (class 2606 OID 124319)
-- Name: cycle_report_rfi_query_validations cycle_report_rfi_query_validations_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_query_validations
    ADD CONSTRAINT cycle_report_rfi_query_validations_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.cycle_report_rfi_data_sources(data_source_id);


--
-- TOC entry 5945 (class 2606 OID 124314)
-- Name: cycle_report_rfi_query_validations cycle_report_rfi_query_validations_test_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_query_validations
    ADD CONSTRAINT cycle_report_rfi_query_validations_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id);


--
-- TOC entry 5947 (class 2606 OID 124324)
-- Name: cycle_report_rfi_query_validations cycle_report_rfi_query_validations_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_query_validations
    ADD CONSTRAINT cycle_report_rfi_query_validations_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5976 (class 2606 OID 124899)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection__report_owner_decision_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection__report_owner_decision_by_id_fkey FOREIGN KEY (report_owner_decision_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5971 (class 2606 OID 125240)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection__report_owner_reviewed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection__report_owner_reviewed_by_id_fkey FOREIGN KEY (report_owner_reviewed_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5576 (class 2606 OID 119846)
-- Name: cycle_report_sample_selection_audit_logs cycle_report_sample_selection_audit_logs_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_audit_logs
    ADD CONSTRAINT cycle_report_sample_selection_audit_logs_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5977 (class 2606 OID 124904)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samp_carried_from_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samp_carried_from_version_id_fkey FOREIGN KEY (carried_from_version_id) REFERENCES public.cycle_report_sample_selection_versions(version_id);


--
-- TOC entry 5978 (class 2606 OID 124909)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_sampl_carried_from_sample_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_sampl_carried_from_sample_id_fkey FOREIGN KEY (carried_from_sample_id) REFERENCES public.cycle_report_sample_selection_samples(sample_id);


--
-- TOC entry 5975 (class 2606 OID 124894)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_sample_tester_decision_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_sample_tester_decision_by_id_fkey FOREIGN KEY (tester_decision_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5979 (class 2606 OID 124914)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5974 (class 2606 OID 124889)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5973 (class 2606 OID 124884)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5980 (class 2606 OID 124919)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5972 (class 2606 OID 124879)
-- Name: cycle_report_sample_selection_samples cycle_report_sample_selection_samples_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_samples
    ADD CONSTRAINT cycle_report_sample_selection_samples_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.cycle_report_sample_selection_versions(version_id) ON DELETE CASCADE;


--
-- TOC entry 5965 (class 2606 OID 124816)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_version_workflow_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_version_workflow_activity_id_fkey FOREIGN KEY (workflow_activity_id) REFERENCES public.workflow_activities(activity_id);


--
-- TOC entry 5968 (class 2606 OID 124831)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5969 (class 2606 OID 124836)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5966 (class 2606 OID 124821)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.cycle_report_sample_selection_versions(version_id);


--
-- TOC entry 5964 (class 2606 OID 124811)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5967 (class 2606 OID 124826)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_submitted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_submitted_by_id_fkey FOREIGN KEY (submitted_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5970 (class 2606 OID 124841)
-- Name: cycle_report_sample_selection_versions cycle_report_sample_selection_versions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_versions
    ADD CONSTRAINT cycle_report_sample_selection_versions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5574 (class 2606 OID 119801)
-- Name: cycle_report_scoping_attribute_recommendations_backup cycle_report_scoping_attribute_recommendations_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attribute_recommendations_backup
    ADD CONSTRAINT cycle_report_scoping_attribute_recommendations_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5930 (class 2606 OID 122951)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5926 (class 2606 OID 122931)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5927 (class 2606 OID 122936)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_planning_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_planning_attribute_id_fkey FOREIGN KEY (planning_attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5929 (class 2606 OID 122946)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_report_owner_decided_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_report_owner_decided_by_id_fkey FOREIGN KEY (report_owner_decided_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5928 (class 2606 OID 122941)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_tester_decided_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_tester_decided_by_id_fkey FOREIGN KEY (tester_decided_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5931 (class 2606 OID 122956)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5925 (class 2606 OID 122926)
-- Name: cycle_report_scoping_attributes cycle_report_scoping_attributes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_attributes
    ADD CONSTRAINT cycle_report_scoping_attributes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.cycle_report_scoping_versions(version_id) ON DELETE CASCADE;


--
-- TOC entry 5678 (class 2606 OID 119831)
-- Name: cycle_report_scoping_decision_versions cycle_report_scoping_decision_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decision_versions
    ADD CONSTRAINT cycle_report_scoping_decision_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5677 (class 2606 OID 120250)
-- Name: cycle_report_scoping_decision_versions cycle_report_scoping_decision_versions_rejected_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decision_versions
    ADD CONSTRAINT cycle_report_scoping_decision_versions_rejected_by_fkey FOREIGN KEY (rejected_by) REFERENCES public.users(user_id);


--
-- TOC entry 5821 (class 2606 OID 120506)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5826 (class 2606 OID 120531)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5825 (class 2606 OID 120526)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_override_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_override_by_user_id_fkey FOREIGN KEY (override_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5822 (class 2606 OID 120511)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5824 (class 2606 OID 120521)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_report_owner_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_report_owner_decided_by_fkey FOREIGN KEY (report_owner_decided_by) REFERENCES public.users(user_id);


--
-- TOC entry 5823 (class 2606 OID 120516)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_tester_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_tester_decided_by_fkey FOREIGN KEY (tester_decided_by) REFERENCES public.users(user_id);


--
-- TOC entry 5827 (class 2606 OID 120536)
-- Name: cycle_report_scoping_decisions cycle_report_scoping_decisions_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_decisions
    ADD CONSTRAINT cycle_report_scoping_decisions_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5559 (class 2606 OID 119816)
-- Name: cycle_report_scoping_submissions cycle_report_scoping_submissions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT cycle_report_scoping_submissions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5922 (class 2606 OID 122894)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5923 (class 2606 OID 122899)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5920 (class 2606 OID 122884)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.cycle_report_scoping_versions(version_id);


--
-- TOC entry 5918 (class 2606 OID 122874)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5921 (class 2606 OID 122889)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_submitted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_submitted_by_id_fkey FOREIGN KEY (submitted_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5924 (class 2606 OID 122904)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5919 (class 2606 OID 122879)
-- Name: cycle_report_scoping_versions cycle_report_scoping_versions_workflow_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_versions
    ADD CONSTRAINT cycle_report_scoping_versions_workflow_activity_id_fkey FOREIGN KEY (workflow_activity_id) REFERENCES public.workflow_activities(activity_id);


--
-- TOC entry 5756 (class 2606 OID 116597)
-- Name: cycle_report_test_cases cycle_report_test_cases_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases
    ADD CONSTRAINT cycle_report_test_cases_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5762 (class 2606 OID 122540)
-- Name: cycle_report_test_cases_document_submissions cycle_report_test_cases_document_sub_revision_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT cycle_report_test_cases_document_sub_revision_requested_by_fkey FOREIGN KEY (revision_requested_by) REFERENCES public.users(user_id);


--
-- TOC entry 5757 (class 2606 OID 116602)
-- Name: cycle_report_test_cases cycle_report_test_cases_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases
    ADD CONSTRAINT cycle_report_test_cases_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5865 (class 2606 OID 121262)
-- Name: cycle_report_test_execution_audit cycle_report_test_execution_audit_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_audit
    ADD CONSTRAINT cycle_report_test_execution_audit_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES public.cycle_report_test_execution_results(id);


--
-- TOC entry 5866 (class 2606 OID 121267)
-- Name: cycle_report_test_execution_audit cycle_report_test_execution_audit_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_audit
    ADD CONSTRAINT cycle_report_test_execution_audit_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5858 (class 2606 OID 121202)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5856 (class 2606 OID 121192)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_evidence_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES public.cycle_report_request_info_testcase_source_evidence(id);


--
-- TOC entry 5857 (class 2606 OID 121197)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_executed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_executed_by_fkey FOREIGN KEY (executed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5855 (class 2606 OID 121177)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5859 (class 2606 OID 121207)
-- Name: cycle_report_test_execution_results cycle_report_test_execution_results_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_results
    ADD CONSTRAINT cycle_report_test_execution_results_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5863 (class 2606 OID 121241)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5860 (class 2606 OID 121226)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES public.cycle_report_test_execution_results(id);


--
-- TOC entry 5861 (class 2606 OID 121231)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5862 (class 2606 OID 121236)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5864 (class 2606 OID 121246)
-- Name: cycle_report_test_execution_reviews cycle_report_test_execution_reviews_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_execution_reviews
    ADD CONSTRAINT cycle_report_test_execution_reviews_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5905 (class 2606 OID 122603)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5901 (class 2606 OID 122583)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5904 (class 2606 OID 122598)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_generated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5903 (class 2606 OID 122593)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_phase_completed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_phase_completed_by_fkey FOREIGN KEY (phase_completed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5900 (class 2606 OID 122578)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5902 (class 2606 OID 122588)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5906 (class 2606 OID 122608)
-- Name: cycle_report_test_report_generation cycle_report_test_report_generation_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_generation
    ADD CONSTRAINT cycle_report_test_report_generation_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5644 (class 2606 OID 122803)
-- Name: cycle_report_test_report_sections cycle_report_test_report_sections_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT cycle_report_test_report_sections_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5648 (class 2606 OID 122823)
-- Name: cycle_report_test_report_sections cycle_report_test_report_sections_executive_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT cycle_report_test_report_sections_executive_approved_by_fkey FOREIGN KEY (executive_approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5645 (class 2606 OID 122808)
-- Name: cycle_report_test_report_sections cycle_report_test_report_sections_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT cycle_report_test_report_sections_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5647 (class 2606 OID 122818)
-- Name: cycle_report_test_report_sections cycle_report_test_report_sections_report_owner_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT cycle_report_test_report_sections_report_owner_approved_by_fkey FOREIGN KEY (report_owner_approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5646 (class 2606 OID 122813)
-- Name: cycle_report_test_report_sections cycle_report_test_report_sections_tester_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT cycle_report_test_report_sections_tester_approved_by_fkey FOREIGN KEY (tester_approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5545 (class 2606 OID 117313)
-- Name: cycle_reports cycle_reports_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_reports
    ADD CONSTRAINT cycle_reports_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5543 (class 2606 OID 31817)
-- Name: cycle_reports cycle_reports_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_reports
    ADD CONSTRAINT cycle_reports_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5544 (class 2606 OID 31827)
-- Name: cycle_reports cycle_reports_tester_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_reports
    ADD CONSTRAINT cycle_reports_tester_id_fkey FOREIGN KEY (tester_id) REFERENCES public.users(user_id);


--
-- TOC entry 5546 (class 2606 OID 117318)
-- Name: cycle_reports cycle_reports_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_reports
    ADD CONSTRAINT cycle_reports_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5639 (class 2606 OID 34622)
-- Name: data_owner_phase_audit_logs_legacy data_owner_phase_audit_log_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_owner_phase_audit_logs_legacy
    ADD CONSTRAINT data_owner_phase_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5640 (class 2606 OID 34632)
-- Name: data_owner_phase_audit_logs_legacy data_owner_phase_audit_log_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_owner_phase_audit_logs_legacy
    ADD CONSTRAINT data_owner_phase_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5638 (class 2606 OID 116808)
-- Name: data_owner_phase_audit_logs_legacy data_owner_phase_audit_log_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_owner_phase_audit_logs_legacy
    ADD CONSTRAINT data_owner_phase_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5800 (class 2606 OID 119583)
-- Name: data_profiling_configurations data_profiling_configurations_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5796 (class 2606 OID 119563)
-- Name: data_profiling_configurations data_profiling_configurations_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id) ON DELETE CASCADE;


--
-- TOC entry 5798 (class 2606 OID 119573)
-- Name: data_profiling_configurations data_profiling_configurations_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.cycle_report_planning_data_sources(id) ON DELETE SET NULL;


--
-- TOC entry 5799 (class 2606 OID 119578)
-- Name: data_profiling_configurations data_profiling_configurations_file_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_file_upload_id_fkey FOREIGN KEY (file_upload_id) REFERENCES public.data_profiling_uploads(id) ON DELETE SET NULL;


--
-- TOC entry 5797 (class 2606 OID 119568)
-- Name: data_profiling_configurations data_profiling_configurations_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE CASCADE;


--
-- TOC entry 5801 (class 2606 OID 119588)
-- Name: data_profiling_configurations data_profiling_configurations_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_configurations
    ADD CONSTRAINT data_profiling_configurations_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5802 (class 2606 OID 119608)
-- Name: data_profiling_jobs data_profiling_jobs_configuration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs
    ADD CONSTRAINT data_profiling_jobs_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES public.data_profiling_configurations(id) ON DELETE CASCADE;


--
-- TOC entry 5803 (class 2606 OID 119613)
-- Name: data_profiling_jobs data_profiling_jobs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs
    ADD CONSTRAINT data_profiling_jobs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5804 (class 2606 OID 119618)
-- Name: data_profiling_jobs data_profiling_jobs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_jobs
    ADD CONSTRAINT data_profiling_jobs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5790 (class 2606 OID 119416)
-- Name: data_profiling_rules data_profiling_rules_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES public.cycle_report_planning_attributes(id) ON DELETE CASCADE;


--
-- TOC entry 5791 (class 2606 OID 119421)
-- Name: data_profiling_rules data_profiling_rules_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5788 (class 2606 OID 119406)
-- Name: data_profiling_rules data_profiling_rules_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id) ON DELETE CASCADE;


--
-- TOC entry 5789 (class 2606 OID 119411)
-- Name: data_profiling_rules data_profiling_rules_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE CASCADE;


--
-- TOC entry 5792 (class 2606 OID 119426)
-- Name: data_profiling_rules data_profiling_rules_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_rules
    ADD CONSTRAINT data_profiling_rules_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5793 (class 2606 OID 119528)
-- Name: data_profiling_uploads data_profiling_uploads_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_uploads
    ADD CONSTRAINT data_profiling_uploads_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id) ON DELETE CASCADE;


--
-- TOC entry 5794 (class 2606 OID 119533)
-- Name: data_profiling_uploads data_profiling_uploads_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_uploads
    ADD CONSTRAINT data_profiling_uploads_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE CASCADE;


--
-- TOC entry 5795 (class 2606 OID 119538)
-- Name: data_profiling_uploads data_profiling_uploads_uploaded_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_profiling_uploads
    ADD CONSTRAINT data_profiling_uploads_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5717 (class 2606 OID 115848)
-- Name: data_queries data_queries_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_queries
    ADD CONSTRAINT data_queries_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5715 (class 2606 OID 117819)
-- Name: data_queries data_queries_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_queries
    ADD CONSTRAINT data_queries_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5718 (class 2606 OID 115853)
-- Name: data_queries data_queries_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_queries
    ADD CONSTRAINT data_queries_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5716 (class 2606 OID 117825)
-- Name: data_queries data_queries_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_queries
    ADD CONSTRAINT data_queries_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5580 (class 2606 OID 118167)
-- Name: escalation_email_logs escalation_email_logs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5578 (class 2606 OID 32841)
-- Name: escalation_email_logs escalation_email_logs_escalation_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_escalation_rule_id_fkey FOREIGN KEY (escalation_rule_id) REFERENCES public.universal_sla_escalation_rules(escalation_rule_id);


--
-- TOC entry 5579 (class 2606 OID 116863)
-- Name: escalation_email_logs escalation_email_logs_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5577 (class 2606 OID 32836)
-- Name: escalation_email_logs escalation_email_logs_sla_violation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_sla_violation_id_fkey FOREIGN KEY (sla_violation_id) REFERENCES public.universal_sla_violation_trackings(violation_id);


--
-- TOC entry 5581 (class 2606 OID 118173)
-- Name: escalation_email_logs escalation_email_logs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalation_email_logs
    ADD CONSTRAINT escalation_email_logs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5776 (class 2606 OID 118353)
-- Name: activity_states fk_activity_definition; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT fk_activity_definition FOREIGN KEY (activity_definition_id) REFERENCES public.activity_definitions(id);


--
-- TOC entry 5753 (class 2606 OID 118295)
-- Name: cycle_report_planning_attributes fk_archived_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT fk_archived_by FOREIGN KEY (archived_by) REFERENCES public.users(user_id);


--
-- TOC entry 5778 (class 2606 OID 118363)
-- Name: activity_states fk_completed_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT fk_completed_by FOREIGN KEY (completed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5758 (class 2606 OID 122410)
-- Name: cycle_report_test_cases_document_submissions fk_cycle_report_document_submissions_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT fk_cycle_report_document_submissions_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5599 (class 2606 OID 122430)
-- Name: cycle_report_observation_mgmt_audit_logs fk_cycle_report_observation_mgmt_audit_logs_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_audit_logs
    ADD CONSTRAINT fk_cycle_report_observation_mgmt_audit_logs_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5710 (class 2606 OID 122435)
-- Name: cycle_report_observation_mgmt_observation_records fk_cycle_report_observation_mgmt_observation_records_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT fk_cycle_report_observation_mgmt_observation_records_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5780 (class 2606 OID 122415)
-- Name: cycle_report_planning_data_sources fk_cycle_report_planning_data_sources_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_data_sources
    ADD CONSTRAINT fk_cycle_report_planning_data_sources_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5783 (class 2606 OID 122420)
-- Name: cycle_report_planning_pde_mappings fk_cycle_report_planning_pde_mappings_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_pde_mappings
    ADD CONSTRAINT fk_cycle_report_planning_pde_mappings_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5571 (class 2606 OID 122440)
-- Name: cycle_report_request_info_audit_logs fk_cycle_report_request_info_audit_logs_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT fk_cycle_report_request_info_audit_logs_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5755 (class 2606 OID 122425)
-- Name: cycle_report_test_cases fk_cycle_report_test_cases_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases
    ADD CONSTRAINT fk_cycle_report_test_cases_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5643 (class 2606 OID 122451)
-- Name: cycle_report_test_report_sections fk_cycle_report_test_report_sections_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT fk_cycle_report_test_report_sections_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5917 (class 2606 OID 122763)
-- Name: cycle_report_data_profiling_rules fk_data_profiling_rules_phase_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_data_profiling_rules
    ADD CONSTRAINT fk_data_profiling_rules_phase_id FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5894 (class 2606 OID 122203)
-- Name: cycle_report_document_access_logs fk_document_access_logs_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs
    ADD CONSTRAINT fk_document_access_logs_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5892 (class 2606 OID 122193)
-- Name: cycle_report_document_access_logs fk_document_access_logs_document_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs
    ADD CONSTRAINT fk_document_access_logs_document_id FOREIGN KEY (document_id) REFERENCES public.cycle_report_documents(id) ON DELETE CASCADE;


--
-- TOC entry 5895 (class 2606 OID 122208)
-- Name: cycle_report_document_access_logs fk_document_access_logs_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs
    ADD CONSTRAINT fk_document_access_logs_updated_by FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5893 (class 2606 OID 122198)
-- Name: cycle_report_document_access_logs fk_document_access_logs_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_access_logs
    ADD CONSTRAINT fk_document_access_logs_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5898 (class 2606 OID 122223)
-- Name: cycle_report_document_extractions fk_document_extractions_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions
    ADD CONSTRAINT fk_document_extractions_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5896 (class 2606 OID 122213)
-- Name: cycle_report_document_extractions fk_document_extractions_document_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions
    ADD CONSTRAINT fk_document_extractions_document_id FOREIGN KEY (document_id) REFERENCES public.cycle_report_documents(id) ON DELETE CASCADE;


--
-- TOC entry 5899 (class 2606 OID 122228)
-- Name: cycle_report_document_extractions fk_document_extractions_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions
    ADD CONSTRAINT fk_document_extractions_updated_by FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5897 (class 2606 OID 122218)
-- Name: cycle_report_document_extractions fk_document_extractions_validated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_document_extractions
    ADD CONSTRAINT fk_document_extractions_validated_by FOREIGN KEY (validated_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5817 (class 2606 OID 120200)
-- Name: universal_assignment_history fk_history_assignment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history
    ADD CONSTRAINT fk_history_assignment FOREIGN KEY (assignment_id) REFERENCES public.universal_assignments(assignment_id) ON DELETE CASCADE;


--
-- TOC entry 5818 (class 2606 OID 120205)
-- Name: universal_assignment_history fk_history_changed_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history
    ADD CONSTRAINT fk_history_changed_by FOREIGN KEY (changed_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5819 (class 2606 OID 120210)
-- Name: universal_assignment_history fk_history_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history
    ADD CONSTRAINT fk_history_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5820 (class 2606 OID 120215)
-- Name: universal_assignment_history fk_history_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_history
    ADD CONSTRAINT fk_history_updated_by FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5779 (class 2606 OID 118368)
-- Name: activity_states fk_last_reset_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT fk_last_reset_by FOREIGN KEY (last_reset_by) REFERENCES public.users(user_id);


--
-- TOC entry 5747 (class 2606 OID 118277)
-- Name: cycle_report_planning_attributes fk_master_attribute; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT fk_master_attribute FOREIGN KEY (master_attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5760 (class 2606 OID 122527)
-- Name: cycle_report_test_cases_document_submissions fk_parent_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT fk_parent_submission_id FOREIGN KEY (parent_submission_id) REFERENCES public.cycle_report_test_cases_document_submissions(submission_id);


--
-- TOC entry 5636 (class 2606 OID 118377)
-- Name: regulatory_data_dictionaries fk_regulatory_data_dictionaries_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulatory_data_dictionaries
    ADD CONSTRAINT fk_regulatory_data_dictionaries_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5637 (class 2606 OID 118382)
-- Name: regulatory_data_dictionaries fk_regulatory_data_dictionaries_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulatory_data_dictionaries
    ADD CONSTRAINT fk_regulatory_data_dictionaries_updated_by FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5748 (class 2606 OID 118283)
-- Name: cycle_report_planning_attributes fk_replaced_attribute; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT fk_replaced_attribute FOREIGN KEY (replaced_attribute_id) REFERENCES public.cycle_report_planning_attributes(id);


--
-- TOC entry 5763 (class 2606 OID 122545)
-- Name: cycle_report_test_cases_document_submissions fk_revision_requested_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT fk_revision_requested_by FOREIGN KEY (revision_requested_by) REFERENCES public.users(user_id);


--
-- TOC entry 5556 (class 2606 OID 33757)
-- Name: cycle_report_scoping_submissions fk_scoping_submissions_previous_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT fk_scoping_submissions_previous_version FOREIGN KEY (previous_version_id) REFERENCES public.cycle_report_scoping_submissions(submission_id);


--
-- TOC entry 5777 (class 2606 OID 118358)
-- Name: activity_states fk_started_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_states
    ADD CONSTRAINT fk_started_by FOREIGN KEY (started_by) REFERENCES public.users(user_id);


--
-- TOC entry 5759 (class 2606 OID 122517)
-- Name: cycle_report_test_cases_document_submissions fk_test_case_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT fk_test_case_id FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id);


--
-- TOC entry 5761 (class 2606 OID 122532)
-- Name: cycle_report_test_cases_document_submissions fk_validated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_cases_document_submissions
    ADD CONSTRAINT fk_validated_by FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5948 (class 2606 OID 124329)
-- Name: cycle_report_rfi_query_validations fk_validation_test_case; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_rfi_query_validations
    ADD CONSTRAINT fk_validation_test_case FOREIGN KEY (test_case_id) REFERENCES public.cycle_report_test_cases(id) ON DELETE CASCADE;


--
-- TOC entry 5752 (class 2606 OID 118290)
-- Name: cycle_report_planning_attributes fk_version_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_planning_attributes
    ADD CONSTRAINT fk_version_created_by FOREIGN KEY (version_created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5697 (class 2606 OID 119896)
-- Name: workflow_activities fk_workflow_activities_cycle; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT fk_workflow_activities_cycle FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5693 (class 2606 OID 115319)
-- Name: workflow_activities fk_workflow_activities_parent; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT fk_workflow_activities_parent FOREIGN KEY (parent_activity_id) REFERENCES public.workflow_activities(activity_id) ON DELETE SET NULL;


--
-- TOC entry 5699 (class 2606 OID 119906)
-- Name: workflow_activities fk_workflow_activities_phase; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT fk_workflow_activities_phase FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5698 (class 2606 OID 119901)
-- Name: workflow_activities fk_workflow_activities_report; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT fk_workflow_activities_report FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5550 (class 2606 OID 33661)
-- Name: workflow_phases fk_workflow_phases_completed_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT fk_workflow_phases_completed_by FOREIGN KEY (completed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5548 (class 2606 OID 33651)
-- Name: workflow_phases fk_workflow_phases_override_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT fk_workflow_phases_override_by FOREIGN KEY (override_by) REFERENCES public.users(user_id);


--
-- TOC entry 5549 (class 2606 OID 33656)
-- Name: workflow_phases fk_workflow_phases_started_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT fk_workflow_phases_started_by FOREIGN KEY (started_by) REFERENCES public.users(user_id);


--
-- TOC entry 5560 (class 2606 OID 32174)
-- Name: llm_audit_logs llm_audit_log_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_audit_logs
    ADD CONSTRAINT llm_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5561 (class 2606 OID 32184)
-- Name: llm_audit_logs llm_audit_log_executed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_audit_logs
    ADD CONSTRAINT llm_audit_log_executed_by_fkey FOREIGN KEY (executed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5562 (class 2606 OID 116883)
-- Name: llm_audit_logs llm_audit_log_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_audit_logs
    ADD CONSTRAINT llm_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5530 (class 2606 OID 117148)
-- Name: lobs lobs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lobs
    ADD CONSTRAINT lobs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5531 (class 2606 OID 117153)
-- Name: lobs lobs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lobs
    ADD CONSTRAINT lobs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5673 (class 2606 OID 121815)
-- Name: metrics_execution metrics_execution_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_execution
    ADD CONSTRAINT metrics_execution_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5674 (class 2606 OID 121820)
-- Name: metrics_execution metrics_execution_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_execution
    ADD CONSTRAINT metrics_execution_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5675 (class 2606 OID 121825)
-- Name: metrics_execution metrics_execution_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_execution
    ADD CONSTRAINT metrics_execution_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5676 (class 2606 OID 121830)
-- Name: metrics_execution metrics_execution_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_execution
    ADD CONSTRAINT metrics_execution_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5669 (class 2606 OID 121835)
-- Name: metrics_phases metrics_phases_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_phases
    ADD CONSTRAINT metrics_phases_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5670 (class 2606 OID 121840)
-- Name: metrics_phases metrics_phases_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_phases
    ADD CONSTRAINT metrics_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5671 (class 2606 OID 121845)
-- Name: metrics_phases metrics_phases_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_phases
    ADD CONSTRAINT metrics_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5672 (class 2606 OID 121850)
-- Name: metrics_phases metrics_phases_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metrics_phases
    ADD CONSTRAINT metrics_phases_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5587 (class 2606 OID 33247)
-- Name: cycle_report_observation_mgmt_approvals observation_approvals_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT observation_approvals_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(user_id);


--
-- TOC entry 5589 (class 2606 OID 117687)
-- Name: cycle_report_observation_mgmt_approvals observation_approvals_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT observation_approvals_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5588 (class 2606 OID 33252)
-- Name: cycle_report_observation_mgmt_approvals observation_approvals_escalated_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT observation_approvals_escalated_to_fkey FOREIGN KEY (escalated_to) REFERENCES public.users(user_id);


--
-- TOC entry 5590 (class 2606 OID 117693)
-- Name: cycle_report_observation_mgmt_approvals observation_approvals_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_approvals
    ADD CONSTRAINT observation_approvals_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5582 (class 2606 OID 33221)
-- Name: cycle_report_observation_mgmt_impact_assessments observation_impact_assessments_assessed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT observation_impact_assessments_assessed_by_fkey FOREIGN KEY (assessed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5584 (class 2606 OID 117711)
-- Name: cycle_report_observation_mgmt_impact_assessments observation_impact_assessments_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT observation_impact_assessments_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5583 (class 2606 OID 33226)
-- Name: cycle_report_observation_mgmt_impact_assessments observation_impact_assessments_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT observation_impact_assessments_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5585 (class 2606 OID 117717)
-- Name: cycle_report_observation_mgmt_impact_assessments observation_impact_assessments_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_impact_assessments
    ADD CONSTRAINT observation_impact_assessments_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5598 (class 2606 OID 33318)
-- Name: cycle_report_observation_mgmt_audit_logs observation_management_audit_logs_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_audit_logs
    ADD CONSTRAINT observation_management_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5709 (class 2606 OID 98939)
-- Name: cycle_report_observation_mgmt_observation_records observation_records_assigned_to_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT observation_records_assigned_to_fkey1 FOREIGN KEY (assigned_to) REFERENCES public.users(user_id);


--
-- TOC entry 5706 (class 2606 OID 117663)
-- Name: cycle_report_observation_mgmt_observation_records observation_records_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT observation_records_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5708 (class 2606 OID 98934)
-- Name: cycle_report_observation_mgmt_observation_records observation_records_detected_by_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT observation_records_detected_by_fkey1 FOREIGN KEY (detected_by) REFERENCES public.users(user_id);


--
-- TOC entry 5707 (class 2606 OID 117669)
-- Name: cycle_report_observation_mgmt_observation_records observation_records_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_observation_records
    ADD CONSTRAINT observation_records_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5593 (class 2606 OID 33277)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5595 (class 2606 OID 117699)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5592 (class 2606 OID 33272)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_resolution_owner_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_resolution_owner_fkey FOREIGN KEY (resolution_owner) REFERENCES public.users(user_id);


--
-- TOC entry 5596 (class 2606 OID 117705)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5594 (class 2606 OID 33282)
-- Name: cycle_report_observation_mgmt_resolutions observation_resolutions_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_observation_mgmt_resolutions
    ADD CONSTRAINT observation_resolutions_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5774 (class 2606 OID 118260)
-- Name: permission_audit_log permission_audit_log_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5773 (class 2606 OID 118255)
-- Name: permission_audit_log permission_audit_log_performed_by_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_performed_by_fkey1 FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5771 (class 2606 OID 118245)
-- Name: permission_audit_log permission_audit_log_permission_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_permission_id_fkey1 FOREIGN KEY (permission_id) REFERENCES public.rbac_permissions(permission_id);


--
-- TOC entry 5772 (class 2606 OID 118250)
-- Name: permission_audit_log permission_audit_log_role_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_role_id_fkey1 FOREIGN KEY (role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5775 (class 2606 OID 118265)
-- Name: permission_audit_log permission_audit_log_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_audit_log
    ADD CONSTRAINT permission_audit_log_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5730 (class 2606 OID 116147)
-- Name: profiling_executions profiling_executions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5727 (class 2606 OID 117783)
-- Name: profiling_executions profiling_executions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5729 (class 2606 OID 116132)
-- Name: profiling_executions profiling_executions_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5726 (class 2606 OID 116933)
-- Name: profiling_executions profiling_executions_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5731 (class 2606 OID 116152)
-- Name: profiling_executions profiling_executions_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5728 (class 2606 OID 117789)
-- Name: profiling_executions profiling_executions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_executions
    ADD CONSTRAINT profiling_executions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5723 (class 2606 OID 115886)
-- Name: profiling_jobs profiling_jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5720 (class 2606 OID 117771)
-- Name: profiling_jobs profiling_jobs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5722 (class 2606 OID 115876)
-- Name: profiling_jobs profiling_jobs_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5719 (class 2606 OID 116938)
-- Name: profiling_jobs profiling_jobs_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5724 (class 2606 OID 115891)
-- Name: profiling_jobs profiling_jobs_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5721 (class 2606 OID 117777)
-- Name: profiling_jobs profiling_jobs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_jobs
    ADD CONSTRAINT profiling_jobs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5725 (class 2606 OID 115906)
-- Name: profiling_partitions profiling_partitions_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiling_partitions
    ADD CONSTRAINT profiling_partitions_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.profiling_jobs(job_id);


--
-- TOC entry 5633 (class 2606 OID 121755)
-- Name: rbac_permission_audit_logs rbac_permission_audit_logs_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permission_audit_logs
    ADD CONSTRAINT rbac_permission_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5634 (class 2606 OID 121760)
-- Name: rbac_permission_audit_logs rbac_permission_audit_logs_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permission_audit_logs
    ADD CONSTRAINT rbac_permission_audit_logs_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.rbac_permissions(permission_id);


--
-- TOC entry 5635 (class 2606 OID 121765)
-- Name: rbac_permission_audit_logs rbac_permission_audit_logs_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permission_audit_logs
    ADD CONSTRAINT rbac_permission_audit_logs_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5600 (class 2606 OID 121600)
-- Name: rbac_permissions rbac_permissions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permissions
    ADD CONSTRAINT rbac_permissions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5601 (class 2606 OID 121605)
-- Name: rbac_permissions rbac_permissions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permissions
    ADD CONSTRAINT rbac_permissions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5630 (class 2606 OID 121720)
-- Name: rbac_resource_permissions rbac_resource_permissions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT rbac_resource_permissions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5632 (class 2606 OID 121730)
-- Name: rbac_resource_permissions rbac_resource_permissions_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT rbac_resource_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5629 (class 2606 OID 121715)
-- Name: rbac_resource_permissions rbac_resource_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT rbac_resource_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.rbac_permissions(permission_id);


--
-- TOC entry 5631 (class 2606 OID 121725)
-- Name: rbac_resource_permissions rbac_resource_permissions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT rbac_resource_permissions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5628 (class 2606 OID 121710)
-- Name: rbac_resource_permissions rbac_resource_permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resource_permissions
    ADD CONSTRAINT rbac_resource_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5604 (class 2606 OID 121620)
-- Name: rbac_resources rbac_resources_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resources
    ADD CONSTRAINT rbac_resources_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5606 (class 2606 OID 121630)
-- Name: rbac_resources rbac_resources_parent_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resources
    ADD CONSTRAINT rbac_resources_parent_resource_id_fkey FOREIGN KEY (parent_resource_id) REFERENCES public.rbac_resources(resource_id);


--
-- TOC entry 5605 (class 2606 OID 121625)
-- Name: rbac_resources rbac_resources_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_resources
    ADD CONSTRAINT rbac_resources_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5768 (class 2606 OID 121740)
-- Name: rbac_role_hierarchy rbac_role_hierarchy_child_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_hierarchy
    ADD CONSTRAINT rbac_role_hierarchy_child_role_id_fkey FOREIGN KEY (child_role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5769 (class 2606 OID 121745)
-- Name: rbac_role_hierarchy rbac_role_hierarchy_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_hierarchy
    ADD CONSTRAINT rbac_role_hierarchy_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5767 (class 2606 OID 121735)
-- Name: rbac_role_hierarchy rbac_role_hierarchy_parent_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_hierarchy
    ADD CONSTRAINT rbac_role_hierarchy_parent_role_id_fkey FOREIGN KEY (parent_role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5770 (class 2606 OID 121750)
-- Name: rbac_role_hierarchy rbac_role_hierarchy_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_hierarchy
    ADD CONSTRAINT rbac_role_hierarchy_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5615 (class 2606 OID 121645)
-- Name: rbac_role_permissions rbac_role_permissions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT rbac_role_permissions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5617 (class 2606 OID 121655)
-- Name: rbac_role_permissions rbac_role_permissions_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT rbac_role_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5614 (class 2606 OID 121640)
-- Name: rbac_role_permissions rbac_role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT rbac_role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.rbac_permissions(permission_id);


--
-- TOC entry 5613 (class 2606 OID 121635)
-- Name: rbac_role_permissions rbac_role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT rbac_role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5616 (class 2606 OID 121650)
-- Name: rbac_role_permissions rbac_role_permissions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permissions
    ADD CONSTRAINT rbac_role_permissions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5602 (class 2606 OID 121610)
-- Name: rbac_roles rbac_roles_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles
    ADD CONSTRAINT rbac_roles_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5603 (class 2606 OID 121615)
-- Name: rbac_roles rbac_roles_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles
    ADD CONSTRAINT rbac_roles_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5625 (class 2606 OID 121670)
-- Name: rbac_user_permissions rbac_user_permissions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT rbac_user_permissions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5627 (class 2606 OID 121680)
-- Name: rbac_user_permissions rbac_user_permissions_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT rbac_user_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5624 (class 2606 OID 121665)
-- Name: rbac_user_permissions rbac_user_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT rbac_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.rbac_permissions(permission_id);


--
-- TOC entry 5626 (class 2606 OID 121675)
-- Name: rbac_user_permissions rbac_user_permissions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT rbac_user_permissions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5623 (class 2606 OID 121660)
-- Name: rbac_user_permissions rbac_user_permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_permissions
    ADD CONSTRAINT rbac_user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5620 (class 2606 OID 121695)
-- Name: rbac_user_roles rbac_user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT rbac_user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(user_id);


--
-- TOC entry 5621 (class 2606 OID 121700)
-- Name: rbac_user_roles rbac_user_roles_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT rbac_user_roles_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5619 (class 2606 OID 121690)
-- Name: rbac_user_roles rbac_user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT rbac_user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.rbac_roles(role_id);


--
-- TOC entry 5622 (class 2606 OID 121705)
-- Name: rbac_user_roles rbac_user_roles_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT rbac_user_roles_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5618 (class 2606 OID 121685)
-- Name: rbac_user_roles rbac_user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_user_roles
    ADD CONSTRAINT rbac_user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5741 (class 2606 OID 116462)
-- Name: reports report_inventory_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5738 (class 2606 OID 116699)
-- Name: reports report_inventory_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5737 (class 2606 OID 116694)
-- Name: reports report_inventory_report_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_report_owner_id_fkey FOREIGN KEY (report_owner_id) REFERENCES public.users(user_id);


--
-- TOC entry 5742 (class 2606 OID 116467)
-- Name: reports report_inventory_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT report_inventory_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5739 (class 2606 OID 118191)
-- Name: reports reports_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5740 (class 2606 OID 118196)
-- Name: reports reports_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5566 (class 2606 OID 32460)
-- Name: cycle_report_request_info_audit_logs request_info_audit_logs_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_request_info_audit_logs
    ADD CONSTRAINT request_info_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5575 (class 2606 OID 32700)
-- Name: cycle_report_sample_selection_audit_logs sample_selection_audit_log_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_sample_selection_audit_logs
    ADD CONSTRAINT sample_selection_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5932 (class 2606 OID 122978)
-- Name: scoping_audit_log scoping_audit_log_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log
    ADD CONSTRAINT scoping_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5935 (class 2606 OID 122993)
-- Name: scoping_audit_log scoping_audit_log_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log
    ADD CONSTRAINT scoping_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5934 (class 2606 OID 122988)
-- Name: scoping_audit_log scoping_audit_log_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log
    ADD CONSTRAINT scoping_audit_log_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5933 (class 2606 OID 122983)
-- Name: scoping_audit_log scoping_audit_log_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoping_audit_log
    ADD CONSTRAINT scoping_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5557 (class 2606 OID 117927)
-- Name: cycle_report_scoping_submissions scoping_submissions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT scoping_submissions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5555 (class 2606 OID 31959)
-- Name: cycle_report_scoping_submissions scoping_submissions_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT scoping_submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id);


--
-- TOC entry 5558 (class 2606 OID 117933)
-- Name: cycle_report_scoping_submissions scoping_submissions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_scoping_submissions
    ADD CONSTRAINT scoping_submissions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5735 (class 2606 OID 116173)
-- Name: secure_data_access_logs secure_data_access_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- TOC entry 5732 (class 2606 OID 117855)
-- Name: secure_data_access_logs secure_data_access_logs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5736 (class 2606 OID 116178)
-- Name: secure_data_access_logs secure_data_access_logs_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5733 (class 2606 OID 117861)
-- Name: secure_data_access_logs secure_data_access_logs_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5734 (class 2606 OID 116168)
-- Name: secure_data_access_logs secure_data_access_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.secure_data_access_logs
    ADD CONSTRAINT secure_data_access_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5536 (class 2606 OID 117184)
-- Name: test_cycles test_cycles_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_cycles
    ADD CONSTRAINT test_cycles_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5535 (class 2606 OID 31746)
-- Name: test_cycles test_cycles_test_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_cycles
    ADD CONSTRAINT test_cycles_test_manager_id_fkey FOREIGN KEY (test_executive_id) REFERENCES public.users(user_id);


--
-- TOC entry 5537 (class 2606 OID 117189)
-- Name: test_cycles test_cycles_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.test_cycles
    ADD CONSTRAINT test_cycles_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5641 (class 2606 OID 117519)
-- Name: cycle_report_test_report_sections test_report_sections_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT test_report_sections_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5642 (class 2606 OID 117525)
-- Name: cycle_report_test_report_sections test_report_sections_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cycle_report_test_report_sections
    ADD CONSTRAINT test_report_sections_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5688 (class 2606 OID 36717)
-- Name: universal_assignment_histories universal_assignment_history_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_histories
    ADD CONSTRAINT universal_assignment_history_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.universal_assignments(assignment_id);


--
-- TOC entry 5689 (class 2606 OID 36722)
-- Name: universal_assignment_histories universal_assignment_history_changed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignment_histories
    ADD CONSTRAINT universal_assignment_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5682 (class 2606 OID 36671)
-- Name: universal_assignments universal_assignments_approved_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_approved_by_user_id_fkey FOREIGN KEY (approved_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5681 (class 2606 OID 36666)
-- Name: universal_assignments universal_assignments_completed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_completed_by_user_id_fkey FOREIGN KEY (completed_by_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5686 (class 2606 OID 118023)
-- Name: universal_assignments universal_assignments_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5684 (class 2606 OID 36681)
-- Name: universal_assignments universal_assignments_delegated_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_delegated_to_user_id_fkey FOREIGN KEY (delegated_to_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5683 (class 2606 OID 36676)
-- Name: universal_assignments universal_assignments_escalated_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_escalated_to_user_id_fkey FOREIGN KEY (escalated_to_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5679 (class 2606 OID 36656)
-- Name: universal_assignments universal_assignments_from_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_from_user_id_fkey FOREIGN KEY (from_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5685 (class 2606 OID 36686)
-- Name: universal_assignments universal_assignments_parent_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_parent_assignment_id_fkey FOREIGN KEY (parent_assignment_id) REFERENCES public.universal_assignments(assignment_id);


--
-- TOC entry 5680 (class 2606 OID 36661)
-- Name: universal_assignments universal_assignments_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_to_user_id_fkey FOREIGN KEY (to_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5687 (class 2606 OID 118029)
-- Name: universal_assignments universal_assignments_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_assignments
    ADD CONSTRAINT universal_assignments_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5532 (class 2606 OID 121770)
-- Name: universal_sla_configurations universal_sla_configurations_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_configurations
    ADD CONSTRAINT universal_sla_configurations_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5533 (class 2606 OID 121775)
-- Name: universal_sla_configurations universal_sla_configurations_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_configurations
    ADD CONSTRAINT universal_sla_configurations_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5539 (class 2606 OID 121780)
-- Name: universal_sla_escalation_rules universal_sla_escalation_rules_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules
    ADD CONSTRAINT universal_sla_escalation_rules_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5541 (class 2606 OID 121790)
-- Name: universal_sla_escalation_rules universal_sla_escalation_rules_escalate_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules
    ADD CONSTRAINT universal_sla_escalation_rules_escalate_to_user_id_fkey FOREIGN KEY (escalate_to_user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5542 (class 2606 OID 121795)
-- Name: universal_sla_escalation_rules universal_sla_escalation_rules_sla_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules
    ADD CONSTRAINT universal_sla_escalation_rules_sla_config_id_fkey FOREIGN KEY (sla_config_id) REFERENCES public.universal_sla_configurations(sla_config_id);


--
-- TOC entry 5540 (class 2606 OID 121785)
-- Name: universal_sla_escalation_rules universal_sla_escalation_rules_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_escalation_rules
    ADD CONSTRAINT universal_sla_escalation_rules_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id);


--
-- TOC entry 5563 (class 2606 OID 121800)
-- Name: universal_sla_violation_trackings universal_sla_violation_trackings_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_violation_trackings
    ADD CONSTRAINT universal_sla_violation_trackings_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5564 (class 2606 OID 121805)
-- Name: universal_sla_violation_trackings universal_sla_violation_trackings_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_violation_trackings
    ADD CONSTRAINT universal_sla_violation_trackings_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5565 (class 2606 OID 121810)
-- Name: universal_sla_violation_trackings universal_sla_violation_trackings_sla_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_sla_violation_trackings
    ADD CONSTRAINT universal_sla_violation_trackings_sla_config_id_fkey FOREIGN KEY (sla_config_id) REFERENCES public.universal_sla_configurations(sla_config_id);


--
-- TOC entry 5534 (class 2606 OID 31689)
-- Name: users users_lob_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES public.lobs(lob_id);


--
-- TOC entry 5691 (class 2606 OID 36980)
-- Name: workflow_activities workflow_activities_completed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5694 (class 2606 OID 117387)
-- Name: workflow_activities workflow_activities_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5696 (class 2606 OID 119770)
-- Name: workflow_activities workflow_activities_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.workflow_phases(phase_id);


--
-- TOC entry 5692 (class 2606 OID 36985)
-- Name: workflow_activities workflow_activities_revision_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_revision_requested_by_fkey FOREIGN KEY (revision_requested_by) REFERENCES public.users(user_id);


--
-- TOC entry 5690 (class 2606 OID 36975)
-- Name: workflow_activities workflow_activities_started_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_started_by_fkey FOREIGN KEY (started_by) REFERENCES public.users(user_id);


--
-- TOC entry 5695 (class 2606 OID 117393)
-- Name: workflow_activities workflow_activities_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activities
    ADD CONSTRAINT workflow_activities_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5702 (class 2606 OID 117399)
-- Name: workflow_activity_dependencies workflow_activity_dependencies_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_dependencies
    ADD CONSTRAINT workflow_activity_dependencies_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5703 (class 2606 OID 117405)
-- Name: workflow_activity_dependencies workflow_activity_dependencies_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_dependencies
    ADD CONSTRAINT workflow_activity_dependencies_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5700 (class 2606 OID 37003)
-- Name: workflow_activity_histories workflow_activity_history_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_histories
    ADD CONSTRAINT workflow_activity_history_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.workflow_activities(activity_id);


--
-- TOC entry 5701 (class 2606 OID 37008)
-- Name: workflow_activity_histories workflow_activity_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_histories
    ADD CONSTRAINT workflow_activity_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- TOC entry 5704 (class 2606 OID 117471)
-- Name: workflow_activity_templates workflow_activity_templates_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_templates
    ADD CONSTRAINT workflow_activity_templates_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5705 (class 2606 OID 117477)
-- Name: workflow_activity_templates workflow_activity_templates_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_activity_templates
    ADD CONSTRAINT workflow_activity_templates_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5661 (class 2606 OID 35566)
-- Name: workflow_alerts workflow_alerts_acknowledged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts
    ADD CONSTRAINT workflow_alerts_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES public.users(user_id);


--
-- TOC entry 5662 (class 2606 OID 117447)
-- Name: workflow_alerts workflow_alerts_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts
    ADD CONSTRAINT workflow_alerts_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5660 (class 2606 OID 35561)
-- Name: workflow_alerts workflow_alerts_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts
    ADD CONSTRAINT workflow_alerts_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES public.workflow_executions(execution_id);


--
-- TOC entry 5663 (class 2606 OID 117453)
-- Name: workflow_alerts workflow_alerts_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_alerts
    ADD CONSTRAINT workflow_alerts_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5652 (class 2606 OID 117423)
-- Name: workflow_executions workflow_executions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5650 (class 2606 OID 35498)
-- Name: workflow_executions workflow_executions_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5651 (class 2606 OID 35508)
-- Name: workflow_executions workflow_executions_initiated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES public.users(user_id);


--
-- TOC entry 5649 (class 2606 OID 117053)
-- Name: workflow_executions workflow_executions_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5653 (class 2606 OID 117429)
-- Name: workflow_executions workflow_executions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_executions
    ADD CONSTRAINT workflow_executions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5654 (class 2606 OID 117435)
-- Name: workflow_metrics workflow_metrics_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_metrics
    ADD CONSTRAINT workflow_metrics_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5655 (class 2606 OID 117441)
-- Name: workflow_metrics workflow_metrics_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_metrics
    ADD CONSTRAINT workflow_metrics_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5552 (class 2606 OID 117375)
-- Name: workflow_phases workflow_phases_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5547 (class 2606 OID 31841)
-- Name: workflow_phases workflow_phases_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.test_cycles(cycle_id);


--
-- TOC entry 5554 (class 2606 OID 119889)
-- Name: workflow_phases workflow_phases_data_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_data_requested_by_fkey FOREIGN KEY (data_requested_by) REFERENCES public.users(user_id);


--
-- TOC entry 5551 (class 2606 OID 117058)
-- Name: workflow_phases workflow_phases_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);


--
-- TOC entry 5553 (class 2606 OID 117381)
-- Name: workflow_phases workflow_phases_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_phases
    ADD CONSTRAINT workflow_phases_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5659 (class 2606 OID 117459)
-- Name: workflow_steps workflow_steps_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5657 (class 2606 OID 35538)
-- Name: workflow_steps workflow_steps_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES public.workflow_executions(execution_id);


--
-- TOC entry 5658 (class 2606 OID 35543)
-- Name: workflow_steps workflow_steps_parent_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_parent_step_id_fkey FOREIGN KEY (parent_step_id) REFERENCES public.workflow_steps(step_id);


--
-- TOC entry 5656 (class 2606 OID 117465)
-- Name: workflow_steps workflow_steps_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5667 (class 2606 OID 117411)
-- Name: workflow_transitions workflow_transitions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- TOC entry 5664 (class 2606 OID 35580)
-- Name: workflow_transitions workflow_transitions_execution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES public.workflow_executions(execution_id);


--
-- TOC entry 5665 (class 2606 OID 35585)
-- Name: workflow_transitions workflow_transitions_from_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_from_step_id_fkey FOREIGN KEY (from_step_id) REFERENCES public.workflow_steps(step_id);


--
-- TOC entry 5666 (class 2606 OID 35590)
-- Name: workflow_transitions workflow_transitions_to_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_to_step_id_fkey FOREIGN KEY (to_step_id) REFERENCES public.workflow_steps(step_id);


--
-- TOC entry 5668 (class 2606 OID 117417)
-- Name: workflow_transitions workflow_transitions_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_transitions
    ADD CONSTRAINT workflow_transitions_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


-- Completed on 2025-07-29 22:24:28 EDT

--
-- PostgreSQL database dump complete
--

