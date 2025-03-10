from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
)
from constructs import Construct
import os


class LambdaFunctionsConstruct(Construct):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        dynamo_tables=None, 
        kinesis_streams=None
    ) -> None:
        super().__init__(scope, construct_id)
        
        # Common Lambda configuration
        lambda_runtime = lambda_.Runtime.PYTHON_3_9
        lambda_timeout = Duration.seconds(30)
        lambda_memory_size = 512
        
        # Common environment variables
        environment = {
            "ENVIRONMENT": os.environ.get("ENVIRONMENT", "dev"),
            "LOG_LEVEL": "INFO",
        }
        
        # Add table names to environment if provided
        if dynamo_tables:
            environment.update({
                "PATIENT_TABLE_NAME": dynamo_tables.patient_table.table_name,
                "OBSERVATION_TABLE_NAME": dynamo_tables.observation_table.table_name,
                "PREDICTION_TABLE_NAME": dynamo_tables.prediction_table.table_name,
            })
        
        # Add stream names to environment if provided
        if kinesis_streams:
            environment.update({
                "FHIR_INGESTION_STREAM": kinesis_streams.fhir_ingestion_stream.stream_name,
                "ANALYTICS_STREAM": kinesis_streams.analytics_stream.stream_name,
                "ML_PREDICTION_STREAM": kinesis_streams.ml_prediction_stream.stream_name,
                "NOTIFICATION_STREAM": kinesis_streams.notification_stream.stream_name,
            })
        
        # Common Lambda layers
        common_layer = lambda_.LayerVersion(
            self,
            "CommonLayer",
            code=lambda_.Code.from_asset("../api/layers/common"),
            compatible_runtimes=[lambda_runtime],
            description="Common utilities and dependencies",
        )
        
        # Authentication Lambda
        self.auth_lambda = lambda_.Function(
            self,
            "AuthFunction",
            runtime=lambda_runtime,
            code=lambda_.Code.from_asset("../api/handlers"),
            handler="auth_handler.handler",
            environment=environment,
            timeout=lambda_timeout,
            memory_size=lambda_memory_size,
            layers=[common_layer],
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        # FHIR Handler Lambda
        self.fhir_lambda = lambda_.Function(
            self,
            "FhirFunction",
            runtime=lambda_runtime,
            code=lambda_.Code.from_asset("../api/handlers"),
            handler="fhir_handler.handler",
            environment=environment,
            timeout=lambda_timeout,
            memory_size=lambda_memory_size,
            layers=[common_layer],
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        # Analytics Handler Lambda
        self.analytics_lambda = lambda_.Function(
            self,
            "AnalyticsFunction",
            runtime=lambda_runtime,
            code=lambda_.Code.from_asset("../api/handlers"),
            handler="analytics_handler.handler",
            environment=environment,
            timeout=lambda_timeout,
            memory_size=lambda_memory_size,
            layers=[common_layer],
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        # ML Handler Lambda
        self.ml_lambda = lambda_.Function(
            self,
            "MlFunction",
            runtime=lambda_runtime,
            code=lambda_.Code.from_asset("../api/handlers"),
            handler="ml_handler.handler",
            environment=environment,
            timeout=lambda_timeout,
            memory_size=lambda_memory_size,
            layers=[common_layer],
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        # Grant permissions if resources are provided
        if dynamo_tables:
            dynamo_tables.patient_table.grant_read_write_data(self.fhir_lambda)
            dynamo_tables.patient_table.grant_read_data(self.analytics_lambda)
            dynamo_tables.patient_table.grant_read_data(self.ml_lambda)
            
            dynamo_tables.observation_table.grant_read_write_data(self.fhir_lambda)
            dynamo_tables.observation_table.grant_read_data(self.analytics_lambda)
            dynamo_tables.observation_table.grant_read_data(self.ml_lambda)
            
            dynamo_tables.prediction_table.grant_read_write_data(self.ml_lambda)
            dynamo_tables.prediction_table.grant_read_data(self.analytics_lambda)
        
        if kinesis_streams:
            kinesis_streams.fhir_ingestion_stream.grant_read_write(self.fhir_lambda)
            kinesis_streams.analytics_stream.grant_read_write(self.analytics_lambda)
            kinesis_streams.ml_prediction_stream.grant_read_write(self.ml_lambda)
            kinesis_streams.notification_stream.grant_write(self.fhir_lambda)
            kinesis_streams.notification_stream.grant_write(self.analytics_lambda)
            kinesis_streams.notification_stream.grant_write(self.ml_lambda) 