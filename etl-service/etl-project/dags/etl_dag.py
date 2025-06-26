from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'you',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'daily_etl',
    default_args=default_args,
    description='Daily ETL from MongoDB to Postgres',
    schedule_interval='0 3 * * *',  # 매일 새벽 3시
    start_date=datetime(2025, 6, 20),
    catchup=False,
) as dag:

    run_etl = BashOperator(
        task_id='run_etl_script',
        bash_command='cd /app && pip install -r requirements.txt && python etl.py',
    )
