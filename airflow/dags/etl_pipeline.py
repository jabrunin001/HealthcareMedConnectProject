"""
MedConnect ETL Pipeline DAG

This DAG extracts data from FHIR sources, transforms it, and loads it into the MedConnect data store.
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.lambda_function import AwsLambdaInvokeFunctionOperator
from airflow.providers.amazon.aws.hooks.lambda_function import AwsLambdaHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator


# Default arguments for the DAG
default_args = {
    'owner': 'medconnect',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email': ['alerts@medconnect.example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = f'medconnect-{ENVIRONMENT}-data'
S3_PREFIX = 'etl/fhir'
REDSHIFT_SCHEMA = 'healthcare'
REDSHIFT_CONN_ID = 'redshift_default'
LAMBDA_EXTRACT_FUNCTION = f'medconnect-{ENVIRONMENT}-fhir-extract'
LAMBDA_TRANSFORM_FUNCTION = f'medconnect-{ENVIRONMENT}-fhir-transform'


# Define functions for the ETL process
def extract_fhir_data(**context):
    """Extract FHIR data from source systems."""
    execution_date = context['execution_date'].strftime('%Y-%m-%d')
    
    # Invoke Lambda function to extract FHIR data
    lambda_hook = AwsLambdaHook(
        function_name=LAMBDA_EXTRACT_FUNCTION,
        region_name=AWS_REGION,
        log_type='None',
        qualifier='$LATEST',
        invocation_type='RequestResponse'
    )
    
    response = lambda_hook.invoke_lambda(
        payload=f'{{"date": "{execution_date}"}}'
    )
    
    # Parse response
    import json
    result = json.loads(response['Payload'].read().decode('utf-8'))
    
    # Pass the S3 path to the next task
    context['ti'].xcom_push(key='s3_extract_path', value=result.get('s3_path'))
    
    return result


def transform_fhir_data(**context):
    """Transform extracted FHIR data."""
    # Get S3 path from previous task
    s3_extract_path = context['ti'].xcom_pull(task_ids='extract_fhir_data', key='s3_extract_path')
    execution_date = context['execution_date'].strftime('%Y-%m-%d')
    
    # Invoke Lambda function to transform FHIR data
    lambda_hook = AwsLambdaHook(
        function_name=LAMBDA_TRANSFORM_FUNCTION,
        region_name=AWS_REGION,
        log_type='None',
        qualifier='$LATEST',
        invocation_type='RequestResponse'
    )
    
    response = lambda_hook.invoke_lambda(
        payload=f'{{"s3_input_path": "{s3_extract_path}", "date": "{execution_date}"}}'
    )
    
    # Parse response
    import json
    result = json.loads(response['Payload'].read().decode('utf-8'))
    
    # Pass the S3 paths to the next tasks
    context['ti'].xcom_push(key='s3_patients_path', value=result.get('s3_patients_path'))
    context['ti'].xcom_push(key='s3_observations_path', value=result.get('s3_observations_path'))
    
    return result


def validate_data(**context):
    """Validate transformed data before loading."""
    # Get S3 paths from previous task
    s3_patients_path = context['ti'].xcom_pull(task_ids='transform_fhir_data', key='s3_patients_path')
    s3_observations_path = context['ti'].xcom_pull(task_ids='transform_fhir_data', key='s3_observations_path')
    
    # Connect to S3
    s3_hook = S3Hook(aws_conn_id='aws_default')
    
    # Validate patients data
    patients_key = s3_patients_path.replace(f's3://{S3_BUCKET}/', '')
    patients_data = s3_hook.read_key(patients_key, S3_BUCKET)
    
    # Validate observations data
    observations_key = s3_observations_path.replace(f's3://{S3_BUCKET}/', '')
    observations_data = s3_hook.read_key(observations_key, S3_BUCKET)
    
    # Perform validation (simplified for example)
    import json
    patients = json.loads(patients_data)
    observations = json.loads(observations_data)
    
    if not patients or not observations:
        raise ValueError("Empty data sets detected")
    
    # Log validation results
    context['ti'].xcom_push(key='patients_count', value=len(patients))
    context['ti'].xcom_push(key='observations_count', value=len(observations))
    
    return {
        'patients_count': len(patients),
        'observations_count': len(observations),
        'validation_passed': True
    }


# Create the DAG
with DAG(
    'medconnect_etl_pipeline',
    default_args=default_args,
    description='Extract, transform, and load FHIR data into MedConnect data store',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['medconnect', 'etl', 'fhir'],
) as dag:
    
    # Task 1: Extract FHIR data
    extract_task = PythonOperator(
        task_id='extract_fhir_data',
        python_callable=extract_fhir_data,
        provide_context=True,
    )
    
    # Task 2: Transform FHIR data
    transform_task = PythonOperator(
        task_id='transform_fhir_data',
        python_callable=transform_fhir_data,
        provide_context=True,
    )
    
    # Task 3: Validate transformed data
    validate_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )
    
    # Task 4: Load patients data to Redshift
    load_patients_task = S3ToRedshiftOperator(
        task_id='load_patients_to_redshift',
        schema=REDSHIFT_SCHEMA,
        table='patients',
        s3_bucket=S3_BUCKET,
        s3_key="{{ ti.xcom_pull(task_ids='transform_fhir_data', key='s3_patients_path').replace('s3://" + S3_BUCKET + "/', '') }}",
        redshift_conn_id=REDSHIFT_CONN_ID,
        copy_options=['JSON \'auto\'', 'COMPUPDATE OFF'],
        method='REPLACE',
    )
    
    # Task 5: Load observations data to Redshift
    load_observations_task = S3ToRedshiftOperator(
        task_id='load_observations_to_redshift',
        schema=REDSHIFT_SCHEMA,
        table='observations',
        s3_bucket=S3_BUCKET,
        s3_key="{{ ti.xcom_pull(task_ids='transform_fhir_data', key='s3_observations_path').replace('s3://" + S3_BUCKET + "/', '') }}",
        redshift_conn_id=REDSHIFT_CONN_ID,
        copy_options=['JSON \'auto\'', 'COMPUPDATE OFF'],
        method='REPLACE',
    )
    
    # Define task dependencies
    extract_task >> transform_task >> validate_task
    validate_task >> load_patients_task
    validate_task >> load_observations_task 