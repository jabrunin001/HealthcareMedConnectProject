#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Stack, Tags
from constructs import Construct

from constructs.api_gateway import ApiGatewayConstruct
from constructs.lambda_funcs import LambdaFunctionsConstruct
from constructs.dynamo_tables import DynamoTablesConstruct
from constructs.kinesis_streams import KinesisStreamsConstruct
from constructs.eks_cluster import EksClusterConstruct

class MedConnectStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        dynamo_tables = DynamoTablesConstruct(self, "DynamoTables")
        
        # Create Kinesis streams
        kinesis_streams = KinesisStreamsConstruct(self, "KinesisStreams")
        
        # Create Lambda functions
        lambda_functions = LambdaFunctionsConstruct(
            self, 
            "LambdaFunctions",
            dynamo_tables=dynamo_tables,
            kinesis_streams=kinesis_streams
        )
        
        # Create API Gateway
        api_gateway = ApiGatewayConstruct(
            self, 
            "ApiGateway",
            lambda_functions=lambda_functions
        )
        
        # Create EKS cluster for ML workloads
        eks_cluster = EksClusterConstruct(self, "EksCluster")
        
        # Export outputs
        self.api_endpoint = api_gateway.api_endpoint
        self.eks_cluster_name = eks_cluster.cluster_name


def main():
    app = App()
    
    env = Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT", ""),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    )
    
    stack = MedConnectStack(app, "MedConnectStack", env=env)
    
    # Add tags to all resources
    Tags.of(stack).add("Project", "MedConnect")
    Tags.of(stack).add("Environment", os.environ.get("ENVIRONMENT", "dev"))
    
    app.synth()


if __name__ == "__main__":
    main() 