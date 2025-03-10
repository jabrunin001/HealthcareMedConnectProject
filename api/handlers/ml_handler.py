import json
import os
import uuid
from typing import Dict, Any, List, Optional
import boto3
import httpx
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.parser import parse_json_body

# Import models
import sys
sys.path.append('/opt/python')  # Lambda layer path
from api.models.prediction import Prediction, PredictionInput, PredictionOutput, PredictionRequest, PredictionResponse

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = Logger(service="ml-service", level=log_level)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kinesis = boto3.client('kinesis')

# Get table names from environment variables
PATIENT_TABLE_NAME = os.environ.get("PATIENT_TABLE_NAME", "PatientTable")
OBSERVATION_TABLE_NAME = os.environ.get("OBSERVATION_TABLE_NAME", "ObservationTable")
PREDICTION_TABLE_NAME = os.environ.get("PREDICTION_TABLE_NAME", "PredictionTable")
ML_PREDICTION_STREAM = os.environ.get("ML_PREDICTION_STREAM", "med-connect-ml-prediction")
NOTIFICATION_STREAM = os.environ.get("NOTIFICATION_STREAM", "med-connect-notification")

# ML model endpoint
ML_ENDPOINT = os.environ.get("ML_ENDPOINT", "http://ml-inference-service.default.svc.cluster.local/predict")

# Initialize DynamoDB tables
patient_table = dynamodb.Table(PATIENT_TABLE_NAME)
observation_table = dynamodb.Table(OBSERVATION_TABLE_NAME)
prediction_table = dynamodb.Table(PREDICTION_TABLE_NAME)


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


def get_prediction(prediction_id: str) -> Optional[Dict[str, Any]]:
    """
    Get prediction by ID.
    
    Args:
        prediction_id: Prediction ID
        
    Returns:
        Prediction data or None if not found
    """
    try:
        response = prediction_table.query(
            KeyConditionExpression="prediction_id = :pid",
            ExpressionAttributeValues={
                ":pid": prediction_id
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error getting prediction {prediction_id}: {str(e)}")
        return None


def get_patient_predictions(patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get predictions for a patient.
    
    Args:
        patient_id: Patient ID
        limit: Maximum number of predictions to return
        
    Returns:
        List of predictions
    """
    try:
        response = prediction_table.query(
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
        logger.error(f"Error getting predictions for patient {patient_id}: {str(e)}")
        return []


def extract_features(patient: Dict[str, Any], observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract features for ML prediction.
    
    Args:
        patient: Patient data
        observations: Patient observations
        
    Returns:
        Features for ML prediction
    """
    # In a real implementation, this would extract and transform
    # relevant features from the patient data and observations
    # For simplicity, we're creating a basic feature set
    
    features = {
        "demographics": {
            "gender": patient.get("gender"),
            "age": calculate_age(patient.get("birth_date", "")),
            "deceased": patient.get("deceased", False)
        },
        "vital_signs": {},
        "lab_results": {},
        "medications": [],
        "conditions": []
    }
    
    # Extract vital signs
    for obs in observations:
        obs_type = obs.get("observation_type", "unknown")
        
        # Process vital signs
        if obs_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"]:
            # Extract the value based on the observation's value type
            value = None
            if "value_quantity" in obs and obs["value_quantity"]:
                value = obs["value_quantity"]["value"]
            elif "value_integer" in obs and obs["value_integer"] is not None:
                value = obs["value_integer"]
            
            if value is not None:
                if obs_type not in features["vital_signs"]:
                    features["vital_signs"][obs_type] = []
                
                features["vital_signs"][obs_type].append({
                    "value": value,
                    "timestamp": obs["timestamp"]
                })
        
        # Process lab results
        elif obs_type.startswith("lab-"):
            # Extract the value based on the observation's value type
            value = None
            if "value_quantity" in obs and obs["value_quantity"]:
                value = obs["value_quantity"]["value"]
            elif "value_integer" in obs and obs["value_integer"] is not None:
                value = obs["value_integer"]
            
            if value is not None:
                if obs_type not in features["lab_results"]:
                    features["lab_results"][obs_type] = []
                
                features["lab_results"][obs_type].append({
                    "value": value,
                    "timestamp": obs["timestamp"]
                })
        
        # Process conditions
        elif obs_type.startswith("condition-"):
            condition = obs_type.replace("condition-", "")
            if condition not in features["conditions"]:
                features["conditions"].append(condition)
        
        # Process medications
        elif obs_type.startswith("medication-"):
            medication = obs_type.replace("medication-", "")
            if medication not in features["medications"]:
                features["medications"].append(medication)
    
    return features


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


async def call_ml_model(model_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call ML model for prediction.
    
    Args:
        model_id: Model ID
        features: Features for prediction
        
    Returns:
        Prediction result
    """
    try:
        # In a real implementation, this would call the ML model service
        # For simplicity, we're returning mock predictions
        
        # Mock risk prediction
        if model_id == "risk-predictor":
            return {
                "prediction": "medium-risk",
                "probability": 0.65,
                "scores": {
                    "low-risk": 0.15,
                    "medium-risk": 0.65,
                    "high-risk": 0.20
                },
                "explanation": {
                    "factors": [
                        {"name": "age", "importance": 0.3, "direction": "positive"},
                        {"name": "blood-pressure", "importance": 0.25, "direction": "positive"},
                        {"name": "heart-rate", "importance": 0.2, "direction": "negative"}
                    ]
                },
                "thresholds": {
                    "low-risk": 0.3,
                    "medium-risk": 0.6,
                    "high-risk": 0.8
                }
            }
        
        # Mock condition classifier
        elif model_id == "condition-classifier":
            return {
                "prediction": "type-2-diabetes",
                "probability": 0.78,
                "scores": {
                    "type-2-diabetes": 0.78,
                    "hypertension": 0.45,
                    "coronary-artery-disease": 0.30
                },
                "explanation": {
                    "factors": [
                        {"name": "glucose-level", "importance": 0.4, "direction": "positive"},
                        {"name": "age", "importance": 0.2, "direction": "positive"},
                        {"name": "bmi", "importance": 0.25, "direction": "positive"}
                    ]
                },
                "thresholds": {
                    "positive": 0.7
                }
            }
        
        # Unknown model
        else:
            raise ValueError(f"Unknown model ID: {model_id}")
    
    except Exception as e:
        logger.error(f"Error calling ML model {model_id}: {str(e)}")
        raise


def create_prediction(request: PredictionRequest) -> Dict[str, Any]:
    """
    Create a new prediction.
    
    Args:
        request: Prediction request
        
    Returns:
        Created prediction data
    """
    try:
        # Validate patient exists
        patient = get_patient(request.patient_id)
        if not patient:
            raise ValueError(f"Patient {request.patient_id} not found")
        
        # Get patient observations
        observations = get_patient_observations(request.patient_id)
        if not observations:
            logger.warning(f"No observations found for patient {request.patient_id}")
        
        # Extract features
        features = extract_features(patient, observations)
        
        # Call ML model
        import asyncio
        prediction_result = asyncio.run(call_ml_model(request.model_id, features))
        
        # Create prediction record
        prediction_id = str(uuid.uuid4())
        model_version = "1.0.0"  # In a real implementation, this would come from the model service
        prediction_type = "risk" if request.model_id == "risk-predictor" else "diagnosis"
        
        # Create input and output data
        input_data = PredictionInput(
            patient_id=request.patient_id,
            observation_ids=[obs["observation_id"] for obs in observations] if request.observation_ids is None else request.observation_ids,
            features=features,
            context=request.context
        )
        
        output_data = PredictionOutput(
            prediction=prediction_result["prediction"],
            probability=prediction_result.get("probability"),
            scores=prediction_result.get("scores"),
            explanation=prediction_result.get("explanation"),
            thresholds=prediction_result.get("thresholds")
        )
        
        # Create prediction
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        
        prediction = Prediction(
            prediction_id=prediction_id,
            model_id=request.model_id,
            model_version=model_version,
            patient_id=request.patient_id,
            timestamp=timestamp,
            prediction_type=prediction_type,
            input_data=input_data,
            output_data=output_data,
            status="completed",
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # Save to DynamoDB
        prediction_dict = prediction.to_dict()
        prediction_table.put_item(Item=prediction_dict)
        
        # Publish to Kinesis
        kinesis.put_record(
            StreamName=ML_PREDICTION_STREAM,
            Data=json.dumps({
                "type": "prediction_created",
                "prediction_id": prediction_id,
                "patient_id": request.patient_id,
                "model_id": request.model_id,
                "prediction": prediction_result["prediction"],
                "timestamp": timestamp
            }),
            PartitionKey=request.patient_id
        )
        
        # Publish notification
        kinesis.put_record(
            StreamName=NOTIFICATION_STREAM,
            Data=json.dumps({
                "type": "prediction_created",
                "prediction_id": prediction_id,
                "patient_id": request.patient_id,
                "model_id": request.model_id,
                "prediction": prediction_result["prediction"],
                "timestamp": timestamp
            }),
            PartitionKey=request.patient_id
        )
        
        # Create response
        response = PredictionResponse(
            prediction_id=prediction_id,
            patient_id=request.patient_id,
            model_id=request.model_id,
            model_version=model_version,
            prediction_type=prediction_type,
            prediction=prediction_result["prediction"],
            probability=prediction_result.get("probability"),
            explanation=prediction_result.get("explanation"),
            timestamp=timestamp
        )
        
        return response.dict()
    except Exception as e:
        logger.error(f"Error creating prediction: {str(e)}")
        raise


@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for ML API.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info("Received ML API request")
    
    try:
        # Parse API Gateway event
        api_event = APIGatewayProxyEvent(event)
        
        # Extract path parameters
        path_parameters = api_event.path_parameters or {}
        prediction_id = path_parameters.get("id")
        
        # Extract query parameters
        query_parameters = api_event.query_string_parameters or {}
        patient_id = query_parameters.get("patient")
        
        # Determine operation from path
        path = api_event.path
        http_method = api_event.http_method
        
        # Handle predictions
        if "/ml/predictions" in path:
            if http_method == "GET":
                if prediction_id:
                    # Get specific prediction
                    prediction = get_prediction(prediction_id)
                    if not prediction:
                        return {
                            "statusCode": 404,
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": json.dumps({
                                "message": f"Prediction {prediction_id} not found"
                            })
                        }
                    
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(prediction)
                    }
                elif patient_id:
                    # Get predictions for patient
                    predictions = get_patient_predictions(patient_id)
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps({
                            "patient_id": patient_id,
                            "predictions": predictions
                        })
                    }
                else:
                    # List predictions (simplified implementation)
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
                # Create prediction
                body = parse_json_body(api_event.body)
                request = PredictionRequest(**body)
                prediction = create_prediction(request)
                
                return {
                    "statusCode": 201,
                    "headers": {
                        "Content-Type": "application/json",
                        "Location": f"/ml/predictions/{prediction['prediction_id']}"
                    },
                    "body": json.dumps(prediction)
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
        logger.exception("Error processing ML request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Internal server error: {str(e)}"
            })
        } 