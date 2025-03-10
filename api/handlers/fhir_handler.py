import json
import os
import uuid
from typing import Dict, Any, List, Optional
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.parser import parse_json_body

# Import models
import sys
sys.path.append('/opt/python')  # Lambda layer path
from api.models.patient import Patient
from api.models.observation import Observation

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = Logger(service="fhir-service", level=log_level)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kinesis = boto3.client('kinesis')

# Get table names from environment variables
PATIENT_TABLE_NAME = os.environ.get("PATIENT_TABLE_NAME", "PatientTable")
OBSERVATION_TABLE_NAME = os.environ.get("OBSERVATION_TABLE_NAME", "ObservationTable")
FHIR_INGESTION_STREAM = os.environ.get("FHIR_INGESTION_STREAM", "med-connect-fhir-ingestion")
NOTIFICATION_STREAM = os.environ.get("NOTIFICATION_STREAM", "med-connect-notification")

# Initialize DynamoDB tables
patient_table = dynamodb.Table(PATIENT_TABLE_NAME)
observation_table = dynamodb.Table(OBSERVATION_TABLE_NAME)


def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Get patient by ID.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Patient data or None if not found
    """
    try:
        response = patient_table.query(
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": patient_id
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error getting patient {patient_id}: {str(e)}")
        return None


def create_patient(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new patient.
    
    Args:
        patient_data: Patient data
        
    Returns:
        Created patient data
    """
    try:
        # Convert to Patient model
        patient = Patient.from_fhir(patient_data)
        
        # Save to DynamoDB
        patient_dict = patient.dict()
        patient_table.put_item(Item=patient_dict)
        
        # Publish to Kinesis
        kinesis.put_record(
            StreamName=FHIR_INGESTION_STREAM,
            Data=json.dumps({
                "resource_type": "Patient",
                "operation": "create",
                "data": patient_dict
            }),
            PartitionKey=patient.patient_id
        )
        
        # Publish notification
        kinesis.put_record(
            StreamName=NOTIFICATION_STREAM,
            Data=json.dumps({
                "type": "patient_created",
                "patient_id": patient.patient_id,
                "timestamp": patient.created_at
            }),
            PartitionKey=patient.patient_id
        )
        
        return patient_dict
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise


def update_patient(patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing patient.
    
    Args:
        patient_id: Patient ID
        patient_data: Patient data
        
    Returns:
        Updated patient data
    """
    try:
        # Ensure patient exists
        existing_patient = get_patient(patient_id)
        if not existing_patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Convert to Patient model
        patient_data["id"] = patient_id
        patient = Patient.from_fhir(patient_data)
        
        # Save to DynamoDB
        patient_dict = patient.dict()
        patient_table.put_item(Item=patient_dict)
        
        # Publish to Kinesis
        kinesis.put_record(
            StreamName=FHIR_INGESTION_STREAM,
            Data=json.dumps({
                "resource_type": "Patient",
                "operation": "update",
                "data": patient_dict
            }),
            PartitionKey=patient.patient_id
        )
        
        # Publish notification
        kinesis.put_record(
            StreamName=NOTIFICATION_STREAM,
            Data=json.dumps({
                "type": "patient_updated",
                "patient_id": patient.patient_id,
                "timestamp": patient.updated_at
            }),
            PartitionKey=patient.patient_id
        )
        
        return patient_dict
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        raise


def get_observation(observation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get observation by ID.
    
    Args:
        observation_id: Observation ID
        
    Returns:
        Observation data or None if not found
    """
    try:
        response = observation_table.query(
            KeyConditionExpression="observation_id = :oid",
            ExpressionAttributeValues={
                ":oid": observation_id
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error getting observation {observation_id}: {str(e)}")
        return None


def create_observation(observation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new observation.
    
    Args:
        observation_data: Observation data
        
    Returns:
        Created observation data
    """
    try:
        # Convert to Observation model
        observation = Observation.from_fhir(observation_data)
        
        # Save to DynamoDB
        observation_dict = observation.dict()
        observation_table.put_item(Item=observation_dict)
        
        # Publish to Kinesis
        kinesis.put_record(
            StreamName=FHIR_INGESTION_STREAM,
            Data=json.dumps({
                "resource_type": "Observation",
                "operation": "create",
                "data": observation_dict
            }),
            PartitionKey=observation.observation_id
        )
        
        # Publish notification
        kinesis.put_record(
            StreamName=NOTIFICATION_STREAM,
            Data=json.dumps({
                "type": "observation_created",
                "observation_id": observation.observation_id,
                "patient_id": observation.patient_id,
                "observation_type": observation.observation_type,
                "timestamp": observation.created_at
            }),
            PartitionKey=observation.patient_id
        )
        
        return observation_dict
    except Exception as e:
        logger.error(f"Error creating observation: {str(e)}")
        raise


def get_patient_observations(patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get observations for a patient.
    
    Args:
        patient_id: Patient ID
        limit: Maximum number of observations to return
        
    Returns:
        List of observations
    """
    try:
        response = observation_table.query(
            IndexName="PatientIndex",
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": patient_id
            },
            ScanIndexForward=False,
            Limit=limit
        )
        
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"Error getting observations for patient {patient_id}: {str(e)}")
        return []


@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for FHIR API.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info("Received FHIR API request")
    
    try:
        # Parse API Gateway event
        api_event = APIGatewayProxyEvent(event)
        
        # Extract path parameters
        path_parameters = api_event.path_parameters or {}
        resource_id = path_parameters.get("id")
        
        # Extract query parameters
        query_parameters = api_event.query_string_parameters or {}
        
        # Determine resource type and operation from path
        path = api_event.path
        http_method = api_event.http_method
        
        # Handle Patient resource
        if "/fhir/Patient" in path:
            if http_method == "GET":
                if resource_id:
                    # Get specific patient
                    patient = get_patient(resource_id)
                    if not patient:
                        return {
                            "statusCode": 404,
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": json.dumps({
                                "message": f"Patient {resource_id} not found"
                            })
                        }
                    
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(patient)
                    }
                else:
                    # List patients (simplified implementation)
                    # In a real implementation, this would include pagination and filtering
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps({
                            "message": "Patient search not implemented"
                        })
                    }
            
            elif http_method == "POST":
                # Create patient
                body = parse_json_body(api_event.body)
                patient = create_patient(body)
                
                return {
                    "statusCode": 201,
                    "headers": {
                        "Content-Type": "application/json",
                        "Location": f"/fhir/Patient/{patient['patient_id']}"
                    },
                    "body": json.dumps(patient)
                }
            
            elif http_method == "PUT" and resource_id:
                # Update patient
                body = parse_json_body(api_event.body)
                patient = update_patient(resource_id, body)
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps(patient)
                }
        
        # Handle Observation resource
        elif "/fhir/Observation" in path:
            if http_method == "GET":
                if resource_id:
                    # Get specific observation
                    observation = get_observation(resource_id)
                    if not observation:
                        return {
                            "statusCode": 404,
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": json.dumps({
                                "message": f"Observation {resource_id} not found"
                            })
                        }
                    
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(observation)
                    }
                else:
                    # List observations (simplified implementation)
                    # In a real implementation, this would include pagination and filtering
                    patient_id = query_parameters.get("patient")
                    if patient_id:
                        observations = get_patient_observations(patient_id)
                        return {
                            "statusCode": 200,
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": json.dumps({
                                "resourceType": "Bundle",
                                "type": "searchset",
                                "entry": [{"resource": obs} for obs in observations]
                            })
                        }
                    else:
                        return {
                            "statusCode": 400,
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": json.dumps({
                                "message": "Missing required parameter: patient"
                            })
                        }
            
            elif http_method == "POST":
                # Create observation
                body = parse_json_body(api_event.body)
                observation = create_observation(body)
                
                return {
                    "statusCode": 201,
                    "headers": {
                        "Content-Type": "application/json",
                        "Location": f"/fhir/Observation/{observation['observation_id']}"
                    },
                    "body": json.dumps(observation)
                }
        
        # Handle unsupported resources or methods
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Unsupported resource or method: {path} {http_method}"
            })
        }
    
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Invalid request: {str(e)}"
            })
        }
    except Exception as e:
        logger.exception("Error processing FHIR request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Internal server error: {str(e)}"
            })
        } 