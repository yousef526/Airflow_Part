from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from StockMarketScripts.API_Call import apiCall
from StockMarketScripts.Spark_script import process_data


#from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 8, 1),
    #'retries': 1,
}


# Define the DAG
with DAG(
    dag_id='Stock_info_Proj',
    default_args=default_args,
    description='A simple stock prices readings for a specific company to know data of stocks at chosen time',
    schedule_interval=timedelta(minutes=40),  # Run once a day
    catchup=False,  # to prevent the dag from trying to run agian and catch days it didnt run
) as dag:

    # Define the Bash task
    task1 = PythonOperator(
        task_id='Produce_data',
        python_callable=apiCall,
        
    )


    task2 = PythonOperator(
        task_id='Spark_Processing',
        python_callable=process_data,
    )


    
    task1 >> task2 

    

    # You can add more tasks here and set dependencies

# You can add dependencies between tasks like this:
# task1 >> task2
