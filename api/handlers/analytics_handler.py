import json
import os
import uuid
from typing import Dict, Any, List, Optional
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.parser import parse_json_body

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = Logger(service="analytics-service", level=log_level)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kinesis = boto3.client('kinesis')

# Get table names from environment variables
PATIENT_TABLE_NAME = os.environ.get("PATIENT_TABLE_NAME", "PatientTable")
OBSERVATION_TABLE_NAME = os.environ.get("OBSERVATION_TABLE_NAME", "ObservationTable")
ANALYTICS_STREAM = os.environ.get("ANALYTICS_STREAM", "med-connect-analytics")

# Initialize DynamoDB tables
patient_table = dynamodb.Table(PATIENT_TABLE_NAME)
observation_table = dynamodb.Table(OBSERVATION_TABLE_NAME)


def get_patient_analytics(patient_id: str) -> Dict[str, Any]:
    """
    Get analytics for a specific patient.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Patient analytics data
    """
    try:
        # Get patient data
        patient_response = patient_table.query(
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": patient_id
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        patient_items = patient_response.get("Items", [])
        if not patient_items:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_items[0]
        
        # Get patient observations
        observation_response = observation_table.query(
            IndexName="PatientIndex",
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": patient_id
            },
            ScanIndexForward=False
        )
        
        observations = observation_response.get("Items", [])
        
        # Calculate analytics
        # In a real implementation, this would include more sophisticated analytics
        # based on the patient's observations and medical history
        
        # Count observations by type
        observation_counts = {}
        for obs in observations:
            obs_type = obs.get("observation_type", "unknown")
            observation_counts[obs_type] = observation_counts.get(obs_type, 0) + 1
        
        # Get latest vital signs
        vital_signs = {}
        for obs in observations:
            obs_type = obs.get("observation_type", "unknown")
            if obs_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"]:
                if obs_type not in vital_signs:
                    # Extract the value based on the observation's value type
                    value = None
                    if "value_quantity" in obs and obs["value_quantity"]:
                        value = {
                            "value": obs["value_quantity"]["value"],
                            "unit": obs["value_quantity"]["unit"]
                        }
                    elif "value_string" in obs and obs["value_string"]:
                        value = obs["value_string"]
                    elif "value_integer" in obs and obs["value_integer"] is not None:
                        value = obs["value_integer"]
                    
                    if value:
                        vital_signs[obs_type] = {
                            "value": value,
                            "timestamp": obs["timestamp"]
                        }
        
        # Publish analytics event
        kinesis.put_record(
            StreamName=ANALYTICS_STREAM,
            Data=json.dumps({
                "type": "patient_analytics_accessed",
                "patient_id": patient_id,
                "timestamp": patient["updated_at"]
            }),
            PartitionKey=patient_id
        )
        
        # Return analytics data
        return {
            "patient_id": patient_id,
            "demographics": {
                "gender": patient.get("gender"),
                "age": calculate_age(patient.get("birth_date", "")),
                "deceased": patient.get("deceased", False)
            },
            "observation_summary": {
                "total_count": len(observations),
                "counts_by_type": observation_counts
            },
            "vital_signs": vital_signs,
            "timestamp": patient.get("updated_at")
        }
    except Exception as e:
        logger.error(f"Error getting analytics for patient {patient_id}: {str(e)}")
        raise


def get_population_analytics() -> Dict[str, Any]:
    """
    Get population-level analytics.
    
    Returns:
        Population analytics data
    """
    try:
        # In a real implementation, this would query aggregated data
        # or perform real-time calculations on the patient population
        # For simplicity, we're returning mock data
        
        # Publish analytics event
        kinesis.put_record(
            StreamName=ANALYTICS_STREAM,
            Data=json.dumps({
                "type": "population_analytics_accessed",
                "timestamp": get_current_timestamp()
            }),
            PartitionKey="population"
        )
        
        # Return mock analytics data
        return {
            "patient_count": 1000,
            "gender_distribution": {
                "male": 480,
                "female": 510,
                "other": 10
            },
            "age_distribution": {
                "0-18": 220,
                "19-35": 280,
                "36-50": 240,
                "51-65": 160,
                "65+": 100
            },
            "condition_prevalence": {
                "hypertension": 250,
                "diabetes": 120,
                "asthma": 80,
                "depression": 150,
                "anxiety": 180
            },
            "timestamp": get_current_timestamp()
        }
    except Exception as e:
        logger.error(f"Error getting population analytics: {str(e)}")
        raise


def calculate_age(birth_date: str) -> Optional[int]:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Birth date in YYYY-MM-DD format
        
    Returns:
        Age in years or None if birth date is invalid
    """
    if not birth_date:
        return None
    
    try:
        from datetime import datetime
        birth_year = int(birth_date.split("-")[0])
        current_year = datetime.now().year
        return current_year - birth_year
    except Exception:
        return None


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        Current timestamp
    """
    from datetime import datetime
    return datetime.utcnow().isoformat()


@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for analytics API.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info("Received analytics API request")
    
    try:
        # Parse API Gateway event
        api_event = APIGatewayProxyEvent(event)
        
        # Extract path parameters
        path_parameters = api_event.path_parameters or {}
        patient_id = path_parameters.get("id")
        
        # Determine operation from path
        path = api_event.path
        http_method = api_event.http_method
        
        # Handle patient analytics
        if "/analytics/patient" in path:
            if http_method == "GET":
                if patient_id:
                    # Get analytics for specific patient
                    analytics = get_patient_analytics(patient_id)
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(analytics)
                    }
                else:
                    # List patients with analytics (simplified implementation)
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps({
                            "message": "Patient ID is required"
                        })
                    }
        
        # Handle population analytics
        elif "/analytics/population" in path:
            if http_method == "GET":
                # Get population analytics
                analytics = get_population_analytics()
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps(analytics)
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
        logger.exception("Error processing analytics request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Internal server error: {str(e)}"
            })
        } 