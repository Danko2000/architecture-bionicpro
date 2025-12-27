from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from clickhouse_driver import Client
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def transfer_data_to_clickhouse(**kwargs):
    ds = kwargs['ds']
    
    # 1. Забираем данные из Postgres
    pg_hook = PostgresHook(postgres_conn_id='crm_db_conn')
    sql_query = f"""
        SELECT 
            '{ds}'::date, 
            c.client_id, c.full_name, c.prosthesis_model, 
            COALESCE(t.telemetry_records_count, 0), 
            COALESCE(t.total_usage_hours, 0),
            COALESCE(t.avg_response_time_ms, 0)
        FROM staging_crm c
        LEFT JOIN staging_telemetry t ON c.client_id = t.client_id
    """
    records = pg_hook.get_records(sql_query)
    
    # 2. Подключаемся к ClickHouse с ПАРОЛЕМ
    client = Client(
        host='clickhouse', 
        port=9000, 
        user='airflow_user', 
        password='airflow_pass', 
        database='default'
    )
    
    # 3. Вставка данных
    if records:
        client.execute(f"ALTER TABLE report_data_mart DELETE WHERE report_date = '{ds}'")
        client.execute(
            'INSERT INTO report_data_mart (report_date, client_id, client_name, prosthesis_model, telemetry_records_count, total_usage_hours, avg_response_time_ms) VALUES',
            records
        )
        print(f"Inserted {len(records)} rows into ClickHouse.")
    else:
        print("No records found.")

with DAG(
    'bionicpro_etl_reporting_v2',
    default_args=default_args,
    schedule_interval='0 2 * * *', 
    catchup=False,
    tags=['bionicpro'],
) as dag:

    start = EmptyOperator(task_id='start')

    extract_crm = PostgresOperator(
        task_id='extract_crm_data',
        postgres_conn_id='crm_db_conn',
        sql="""
        DROP TABLE IF EXISTS staging_crm;
        CREATE TABLE staging_crm AS
        SELECT client_id, full_name, prosthesis_model 
        FROM crm_clients_table 
        WHERE is_active = TRUE;
        """
    )

    aggregate_telemetry = PostgresOperator(
        task_id='aggregate_telemetry_data',
        postgres_conn_id='telemetry_db_conn',
        sql="""
            DROP TABLE IF EXISTS staging_telemetry;
            CREATE TABLE staging_telemetry AS
            SELECT 
                client_id, 
                COUNT(*) as telemetry_records_count, 
                SUM(duration_sec)/3600.0 as total_usage_hours,
                AVG(response_time_ms) as avg_response_time_ms
            FROM raw_telemetry_table
            WHERE timestamp::date = '{{ ds }}'::date - interval '1 day'
            GROUP BY client_id;
        """
    )

    load_to_clickhouse = PythonOperator(
        task_id='load_to_olap_vitrine',
        python_callable=transfer_data_to_clickhouse,
        provide_context=True
    )

    end = EmptyOperator(task_id='end')

    start >> [extract_crm, aggregate_telemetry] >> load_to_clickhouse >> end
