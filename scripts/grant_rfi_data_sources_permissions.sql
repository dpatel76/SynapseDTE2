-- Grant permissions on cycle_report_rfi_data_sources table to synapse_user

-- Grant all permissions on the table
GRANT ALL ON TABLE cycle_report_rfi_data_sources TO synapse_user;

-- Grant usage on any sequences (for auto-generated IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO synapse_user;

-- Also grant permissions on related tables if needed
GRANT ALL ON TABLE cycle_report_rfi_query_validations TO synapse_user;
GRANT ALL ON TABLE cycle_report_rfi_evidence TO synapse_user;
GRANT ALL ON TABLE cycle_report_rfi_evidence_versions TO synapse_user;