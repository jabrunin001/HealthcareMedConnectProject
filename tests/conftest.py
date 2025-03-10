"""
Test configuration and fixtures for MedConnect.
"""

import os
import pytest
import boto3
import json
from moto import mock_dynamodb, mock_s3, mock_kinesis


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    """DynamoDB mock."""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """S3 mock."""
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture(scope="function")
def kinesis(aws_credentials):
    """Kinesis mock."""
    with mock_kinesis():
        yield boto3.client("kinesis", region_name="us-east-1")


@pytest.fixture(scope="function")
def patient_table(dynamodb):
    """Create a mock patient table."""
    table = dynamodb.create_table(
        TableName="PatientTable",
        KeySchema=[
            {"AttributeName": "patient_id", "KeyType": "HASH"},
            {"AttributeName": "version", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "patient_id", "AttributeType": "S"},
            {"AttributeName": "version", "AttributeType": "S"},
            {"AttributeName": "mrn", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "MrnIndex",
                "KeySchema": [
                    {"AttributeName": "mrn", "KeyType": "HASH"},
                    {"AttributeName": "version", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture(scope="function")
def observation_table(dynamodb):
    """Create a mock observation table."""
    table = dynamodb.create_table(
        TableName="ObservationTable",
        KeySchema=[
            {"AttributeName": "observation_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "observation_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
            {"AttributeName": "patient_id", "AttributeType": "S"},
            {"AttributeName": "observation_type", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "PatientIndex",
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "TypeIndex",
                "KeySchema": [
                    {"AttributeName": "observation_type", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture(scope="function")
def prediction_table(dynamodb):
    """Create a mock prediction table."""
    table = dynamodb.create_table(
        TableName="PredictionTable",
        KeySchema=[
            {"AttributeName": "prediction_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "prediction_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
            {"AttributeName": "patient_id", "AttributeType": "S"},
            {"AttributeName": "model_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "PatientIndex",
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "ModelIndex",
                "KeySchema": [
                    {"AttributeName": "model_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture(scope="function")
def sample_patient():
    """Create a sample patient for testing."""
    from datetime import datetime
    
    return {
        "patient_id": "test-patient-1",
        "version": datetime.utcnow().isoformat(),
        "active": True,
        "identifiers": [
            {
                "system": "http://example.org/fhir/identifier/mrn",
                "value": "MRN12345",
                "type": "MRN"
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John", "Jacob"],
                "use": "official"
            }
        ],
        "gender": "male",
        "birth_date": "1970-01-01",
        "deceased": False,
        "address": [
            {
                "line": ["123 Main St"],
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "USA",
                "use": "home"
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-123-4567",
                "use": "home"
            },
            {
                "system": "email",
                "value": "john.smith@example.com",
                "use": "work"
            }
        ],
        "marital_status": "married",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture(scope="function")
def sample_observation():
    """Create a sample observation for testing."""
    from datetime import datetime
    
    return {
        "observation_id": "test-observation-1",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ],
                "text": "Vital Signs"
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }
            ],
            "text": "Heart rate"
        },
        "subject": {
            "reference": "Patient/test-patient-1"
        },
        "patient_id": "test-patient-1",
        "effective_date_time": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
        "issued": datetime.utcnow().isoformat(),
        "value_quantity": {
            "value": 80,
            "unit": "beats/minute",
            "system": "http://unitsofmeasure.org",
            "code": "/min"
        },
        "observation_type": "heart-rate",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture(scope="function")
def sample_prediction():
    """Create a sample prediction for testing."""
    from datetime import datetime
    
    return {
        "prediction_id": "test-prediction-1",
        "model_id": "risk-predictor",
        "model_version": "1.0.0",
        "patient_id": "test-patient-1",
        "timestamp": datetime.utcnow().isoformat(),
        "prediction_type": "risk",
        "input_data": {
            "patient_id": "test-patient-1",
            "observation_ids": ["test-observation-1"],
            "features": {
                "age": 53,
                "gender": "male",
                "heart_rate": 80
            }
        },
        "output_data": {
            "prediction": "medium-risk",
            "probability": 0.65,
            "scores": {
                "low-risk": 0.15,
                "medium-risk": 0.65,
                "high-risk": 0.20
            }
        },
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    } 