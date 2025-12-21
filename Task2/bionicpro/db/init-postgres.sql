CREATE TABLE IF NOT EXISTS crm_clients_table (
    client_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    prosthesis_model VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS raw_telemetry_table (
    signal_id SERIAL PRIMARY KEY,
    client_id INT REFERENCES crm_clients_table(client_id),
    timestamp TIMESTAMP,
    duration_sec INT DEFAULT 3600,
    response_time_ms INT,
    noise_level FLOAT
);

TRUNCATE TABLE crm_clients_table CASCADE;
TRUNCATE TABLE raw_telemetry_table CASCADE;

INSERT INTO crm_clients_table (client_id, full_name, prosthesis_model) VALUES 
(1, 'Ivan Ivanov', 'Bionic-Hand-v2'),
(2, 'Petr Petrov', 'Bionic-Leg-v1'),
(3, 'sidorov', 'Bionic-Finger-v1');

INSERT INTO raw_telemetry_table (client_id, timestamp, response_time_ms, noise_level, duration_sec) VALUES
(1, current_date - interval '1 day' + interval '10 hours', 150, 0.5, 3600),
(1, current_date - interval '1 day' + interval '14 hours', 120, 0.4, 1800),
(2, current_date - interval '1 day' + interval '12 hours', 200, 0.8, 7200),
(3, current_date - interval '1 day' + interval '10 hours', 150, 0.5, 3600),
(3, current_date - interval '1 day' + interval '14 hours', 120, 0.4, 1800),
(3, current_date - interval '1 day' + interval '18 hours', 100, 0.3, 1200);