from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct


class DynamoTablesConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # Patient table
        self.patient_table = dynamodb.Table(
            self,
            "PatientTable",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Add GSI for querying by MRN
        self.patient_table.add_global_secondary_index(
            index_name="MrnIndex",
            partition_key=dynamodb.Attribute(
                name="mrn",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Observation table
        self.observation_table = dynamodb.Table(
            self,
            "ObservationTable",
            partition_key=dynamodb.Attribute(
                name="observation_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Add GSI for querying by patient_id
        self.observation_table.add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by observation type
        self.observation_table.add_global_secondary_index(
            index_name="TypeIndex",
            partition_key=dynamodb.Attribute(
                name="observation_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # ML Prediction table
        self.prediction_table = dynamodb.Table(
            self,
            "PredictionTable",
            partition_key=dynamodb.Attribute(
                name="prediction_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Add GSI for querying by patient_id
        self.prediction_table.add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by model_id
        self.prediction_table.add_global_secondary_index(
            index_name="ModelIndex",
            partition_key=dynamodb.Attribute(
                name="model_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        ) 