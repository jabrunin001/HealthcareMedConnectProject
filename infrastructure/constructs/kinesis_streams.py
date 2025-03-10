from aws_cdk import (
    aws_kinesis as kinesis,
    RemovalPolicy,
)
from constructs import Construct


class KinesisStreamsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # FHIR data ingestion stream
        self.fhir_ingestion_stream = kinesis.Stream(
            self,
            "FhirIngestionStream",
            stream_name="med-connect-fhir-ingestion",
            shard_count=2,
            retention_period=kinesis.Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Analytics data stream
        self.analytics_stream = kinesis.Stream(
            self,
            "AnalyticsStream",
            stream_name="med-connect-analytics",
            shard_count=2,
            retention_period=kinesis.Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ML prediction stream
        self.ml_prediction_stream = kinesis.Stream(
            self,
            "MlPredictionStream",
            stream_name="med-connect-ml-prediction",
            shard_count=2,
            retention_period=kinesis.Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Notification stream
        self.notification_stream = kinesis.Stream(
            self,
            "NotificationStream",
            stream_name="med-connect-notification",
            shard_count=1,
            retention_period=kinesis.Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        ) 