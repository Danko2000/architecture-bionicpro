CREATE DATABASE IF NOT EXISTS default;

CREATE TABLE IF NOT EXISTS default.report_data_mart (
    report_date Date,
    client_id UInt32,
    client_name String,
    prosthesis_model String,
    telemetry_records_count UInt64,
    total_usage_hours Float64,
    avg_response_time_ms Float64
) ENGINE = ReplacingMergeTree()
ORDER BY (report_date, client_id);
