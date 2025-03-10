"""
Integration tests for the MedConnect API.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from api.handlers.fhir_handler import handler as fhir_handler
from api.handlers.analytics_handler import handler as analytics_handler
from api.handlers.ml_handler import handler as ml_handler


@pytest.fixture
def api_gateway_event():
    """Create a mock API Gateway event."""
    return {
        "resource": "/fhir/Patient",
        "path": "/fhir/Patient",
        "httpMethod": "GET",
        "headers": {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "resourcePath": "/fhir/Patient",
            "httpMethod": "GET",
            "stage": "dev"
        },
        "body": None,
        "isBase64Encoded": False
    }


@pytest.mark.asyncio
async def test_fhir_patient_get(api_gateway_event, patient_table, sample_patient):
    """Test getting a patient through the FHIR API."""
    # Setup
    patient_table.put_item(Item=sample_patient)
    
    # Modify event to get a specific patient
    event = api_gateway_event.copy()
    event["path"] = f"/fhir/Patient/{sample_patient['patient_id']}"
    event["resource"] = "/fhir/Patient/{id}"
    event["pathParameters"] = {"id": sample_patient["patient_id"]}
    
    # Execute
    with patch.dict(os.environ, {"PATIENT_TABLE_NAME": "PatientTable"}):
        response = fhir_handler(event, {})
    
    # Verify
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["patient_id"] == sample_patient["patient_id"]
    assert body["name"][0]["family"] == sample_patient["name"][0]["family"]


@pytest.mark.asyncio
async def test_fhir_patient_create(api_gateway_event, patient_table):
    """Test creating a patient through the FHIR API."""
    # Setup
    new_patient = {
        "resourceType": "Patient",
        "active": True,
        "name": [
            {
                "family": "Doe",
                "given": ["Jane"]
            }
        ],
        "gender": "female",
        "birthDate": "1980-01-01",
        "identifier": [
            {
                "system": "http://example.org/fhir/identifier/mrn",
                "value": "MRN67890"
            }
        ]
    }
    
    # Modify event to create a patient
    event = api_gateway_event.copy()
    event["httpMethod"] = "POST"
    event["body"] = json.dumps(new_patient)
    
    # Execute
    with patch.dict(os.environ, {
        "PATIENT_TABLE_NAME": "PatientTable",
        "FHIR_INGESTION_STREAM": "test-stream",
        "NOTIFICATION_STREAM": "test-stream"
    }):
        with patch("boto3.client") as mock_client:
            mock_kinesis = MagicMock()
            mock_client.return_value = mock_kinesis
            mock_kinesis.put_record.return_value = {"ShardId": "1", "SequenceNumber": "123"}
            
            response = fhir_handler(event, {})
    
    # Verify
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "patient_id" in body
    assert body["name"][0]["family"] == "Doe"
    
    # Verify item was saved to DynamoDB
    response = patient_table.scan()
    items = response["Items"]
    assert len(items) == 1
    assert items[0]["name"][0]["family"] == "Doe"


@pytest.mark.asyncio
async def test_analytics_patient(api_gateway_event, patient_table, observation_table, sample_patient, sample_observation):
    """Test getting patient analytics."""
    # Setup
    patient_table.put_item(Item=sample_patient)
    observation_table.put_item(Item=sample_observation)
    
    # Modify event to get patient analytics
    event = api_gateway_event.copy()
    event["path"] = f"/analytics/patient/{sample_patient['patient_id']}"
    event["resource"] = "/analytics/patient/{id}"
    event["pathParameters"] = {"id": sample_patient["patient_id"]}
    
    # Execute
    with patch.dict(os.environ, {
        "PATIENT_TABLE_NAME": "PatientTable",
        "OBSERVATION_TABLE_NAME": "ObservationTable",
        "ANALYTICS_STREAM": "test-stream"
    }):
        with patch("boto3.client") as mock_client:
            mock_kinesis = MagicMock()
            mock_client.return_value = mock_kinesis
            mock_kinesis.put_record.return_value = {"ShardId": "1", "SequenceNumber": "123"}
            
            response = analytics_handler(event, {})
    
    # Verify
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["patient_id"] == sample_patient["patient_id"]
    assert "demographics" in body
    assert "observation_summary" in body
    assert body["observation_summary"]["total_count"] == 1


@pytest.mark.asyncio
async def test_ml_prediction(api_gateway_event, patient_table, observation_table, prediction_table, sample_patient, sample_observation):
    """Test creating a prediction."""
    # Setup
    patient_table.put_item(Item=sample_patient)
    observation_table.put_item(Item=sample_observation)
    
    # Modify event to create a prediction
    event = api_gateway_event.copy()
    event["path"] = "/ml/predictions"
    event["resource"] = "/ml/predictions"
    event["httpMethod"] = "POST"
    event["body"] = json.dumps({
        "patient_id": sample_patient["patient_id"],
        "model_id": "risk-predictor"
    })
    
    # Execute
    with patch.dict(os.environ, {
        "PATIENT_TABLE_NAME": "PatientTable",
        "OBSERVATION_TABLE_NAME": "ObservationTable",
        "PREDICTION_TABLE_NAME": "PredictionTable",
        "ML_PREDICTION_STREAM": "test-stream",
        "NOTIFICATION_STREAM": "test-stream"
    }):
        with patch("boto3.client") as mock_client:
            mock_kinesis = MagicMock()
            mock_client.return_value = mock_kinesis
            mock_kinesis.put_record.return_value = {"ShardId": "1", "SequenceNumber": "123"}
            
            # Mock the ML model call
            with patch("api.handlers.ml_handler.call_ml_model") as mock_ml:
                mock_ml.return_value = {
                    "prediction": "medium-risk",
                    "probability": 0.65,
                    "scores": {
                        "low-risk": 0.15,
                        "medium-risk": 0.65,
                        "high-risk": 0.20
                    },
                    "explanation": {
                        "factors": [
                            {"name": "age", "importance": 0.3, "direction": "positive"}
                        ]
                    },
                    "thresholds": {
                        "low-risk": 0.3,
                        "medium-risk": 0.6,
                        "high-risk": 0.8
                    }
                }
                
                response = ml_handler(event, {})
    
    # Verify
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "prediction_id" in body
    assert body["patient_id"] == sample_patient["patient_id"]
    assert body["model_id"] == "risk-predictor"
    assert body["prediction"] == "medium-risk"
    
    # Verify item was saved to DynamoDB
    response = prediction_table.scan()
    items = response["Items"]
    assert len(items) == 1
    assert items[0]["patient_id"] == sample_patient["patient_id"]
    assert items[0]["model_id"] == "risk-predictor" 