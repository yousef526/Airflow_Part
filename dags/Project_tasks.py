from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.email import send_email

from StockMarketScripts.API_Call import apiCall
from StockMarketScripts.Spark_script import process_data

# Logger instance for use in tasks
log = LoggingMixin().log

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email': ['yousefalaa14761@gmail.com'],
    'execution_timeout': timedelta(minutes=15),
}

# DAG definition
with DAG(
    dag_id='Stock_info_Proj22',
    default_args=default_args,
    description='Stock data pipeline: API fetch → Spark processing → validation',
    schedule_interval=timedelta(minutes=40),
    catchup=False,
    tags=['stock', 'spark', 'learning']
) as dag:

    def wrapped_api_call(**kwargs):
        company = Variable.get("stock_company", default_var="IBM")
        log.info(f"Calling API for company: {company}")
        apiCall(company)
        # Save metadata to XCom
        kwargs['ti'].xcom_push(key='company_name', value=company)

    
    def wrapped_process_data(**kwargs):
        log.info("Starting Spark job for stock data")
        time_now = datetime.now()
        kwargs['ti'].xcom_push(key='time_now', value=time_now)
        company = kwargs['ti'].xcom_pull(key='company_name')
        process_data(time_now, company)

    def validate_output(**kwargs):
        import os
        company = kwargs['ti'].xcom_pull(key='company_name')
        time_written = kwargs['ti'].xcom_pull(key='time_now')
        expected_file = f"/opt/airflow/dags/StockMarketScripts/GeneratedData/{company}/{time_written}"
        log.info(f"Validating output at {expected_file}")
        if not os.path.exists(expected_file):
            raise FileNotFoundError(f"{expected_file} not found!")
        log.info("Validation passed!")

    def final_notification(**kwargs):
        subject = "Stock_info_Proj DAG Finished"
        body = "The DAG has finished running — check logs for more details."
        send_email(to="yousefalaa14761@gmail.com", subject=subject, html_content=body)

    # Task 1: Fetch data via API
    fetch_task = PythonOperator(
        task_id='Produce_data',
        python_callable=wrapped_api_call,
        provide_context=True
    )
    fetch_task.doc_md = """
    #### Task: Produce Data
    This task fetches stock data for a company (default: AAPL) from an external API.
    """

    # Task 2: Process the data with Spark only if prevoius tasks success
    spark_task = PythonOperator(
        task_id='Spark_Processing',
        python_callable=wrapped_process_data,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )
    spark_task.doc_md = """
    #### Task: Spark Processing
    This task runs a PySpark job to clean, transform, and process the stock data.
    """

    # Task 3: Validate output file only if one task at least success
    validate_task = PythonOperator(
        task_id='Validate_Output',
        python_callable=validate_output,
        provide_context=True,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )
    validate_task.doc_md = """
    #### Task: Validate Output
    Checks if the processed file exists and is ready for downstream use.
    """

    
    notify_task = PythonOperator(
    task_id='final_notification',
    python_callable=final_notification,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE  # Ensures it runs no matter what
    )
    notify_task.doc_md = """
    #### Task: Final Notification
    This runs at the end of the DAG regardless of upstream task success or failure.
    Good for logging, alerts, or cleanups.
    """

    # Task dependencies
    fetch_task >> spark_task >> validate_task >> notify_task
