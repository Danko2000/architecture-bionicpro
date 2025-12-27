CREATE TABLE IF NOT EXISTS crm_clients_table (
    client_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255), -- Это поле используется в витрине как client_name
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

-- Вставка данных клиентов
-- full_name совпадает с username из realm-export.json
INSERT INTO crm_clients_table (client_id, full_name, prosthesis_model) VALUES 
(1, 'prothetic1', 'Bionic-Hand-v2'), -- Соответствует пользователю prothetic1
(2, 'prothetic2', 'Bionic-Leg-v1'),  -- Соответствует пользователю prothetic2
(3, 'prothetic3', 'Bionic-Finger-v1');-- Соответствует пользователю prothetic3

-- Вставка тестовой телеметрии
INSERT INTO raw_telemetry_table (client_id, timestamp, response_time_ms, noise_level, duration_sec) VALUES
-- Данные для prothetic1
(1, current_date - interval '1 day' + interval '10 hours', 150, 0.5, 3600),
(1, current_date - interval '1 day' + interval '14 hours', 120, 0.4, 1800),
-- Данные для prothetic2
(2, current_date - interval '1 day' + interval '12 hours', 200, 0.8, 7200),
-- Данные для prothetic3
(3, current_date - interval '1 day' + interval '10 hours', 150, 0.5, 3600),
(3, current_date - interval '1 day' + interval '14 hours', 120, 0.4, 1800),
(3, current_date - interval '1 day' + interval '18 hours', 100, 0.3, 1200);
