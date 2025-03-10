import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class PredictionRepository:
    """Repository for ML prediction data."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize prediction repository.
        
        Args:
            table_name: DynamoDB table name (optional)
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("PREDICTION_TABLE_NAME", "PredictionTable")
        self.table = self.dynamodb.Table(self.table_name)
    
    async def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get prediction by ID.
        
        Args:
            prediction_id: Prediction ID
            
        Returns:
            Prediction data or None if not found
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("prediction_id").eq(prediction_id),
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return items[0]
        except ClientError as e:
            logger.error(f"Error getting prediction {prediction_id}: {str(e)}")
            return None
    
    async def get_patient_predictions(
        self, 
        patient_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get predictions for a patient.
        
        Args:
            patient_id: Patient ID
            start_date: Start date for filtering predictions
            end_date: End date for filtering predictions
            model_id: Model ID to filter by
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions
        """
        try:
            if model_id:
                # Query by patient ID and model ID
                response = self.table.query(
                    IndexName="ModelIndex",
                    KeyConditionExpression=Key("model_id").eq(model_id),
                    FilterExpression=Attr("patient_id").eq(patient_id),
                    ScanIndexForward=False,
                    Limit=limit
                )
            else:
                # Query by patient ID
                key_condition = Key("patient_id").eq(patient_id)
                
                if start_date and end_date:
                    # Filter by date range
                    key_condition = key_condition & Key("timestamp").between(start_date, end_date)
                elif start_date:
                    # Filter by start date
                    key_condition = key_condition & Key("timestamp").gte(start_date)
                elif end_date:
                    # Filter by end date
                    key_condition = key_condition & Key("timestamp").lte(end_date)
                
                response = self.table.query(
                    IndexName="PatientIndex",
                    KeyConditionExpression=key_condition,
                    ScanIndexForward=False,
                    Limit=limit
                )
            
            return response.get("Items", [])
        except ClientError as e:
            logger.error(f"Error getting predictions for patient {patient_id}: {str(e)}")
            return []
    
    async def get_model_predictions(
        self, 
        model_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get predictions for a model.
        
        Args:
            model_id: Model ID
            start_date: Start date for filtering predictions
            end_date: End date for filtering predictions
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions
        """
        try:
            key_condition = Key("model_id").eq(model_id)
            
            if start_date and end_date:
                # Filter by date range
                key_condition = key_condition & Key("timestamp").between(start_date, end_date)
            elif start_date:
                # Filter by start date
                key_condition = key_condition & Key("timestamp").gte(start_date)
            elif end_date:
                # Filter by end date
                key_condition = key_condition & Key("timestamp").lte(end_date)
            
            response = self.table.query(
                IndexName="ModelIndex",
                KeyConditionExpression=key_condition,
                ScanIndexForward=False,
                Limit=limit
            )
            
            return response.get("Items", [])
        except ClientError as e:
            logger.error(f"Error getting predictions for model {model_id}: {str(e)}")
            return []
    
    async def create_prediction(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new prediction.
        
        Args:
            prediction_data: Prediction data
            
        Returns:
            Created prediction data
        """
        try:
            # Ensure prediction_id is present
            if "prediction_id" not in prediction_data:
                raise ValueError("prediction_id is required")
            
            # Ensure patient_id is present
            if "patient_id" not in prediction_data:
                raise ValueError("patient_id is required")
            
            # Ensure model_id is present
            if "model_id" not in prediction_data:
                raise ValueError("model_id is required")
            
            # Save to DynamoDB
            self.table.put_item(Item=prediction_data)
            
            return prediction_data
        except ClientError as e:
            logger.error(f"Error creating prediction: {str(e)}")
            raise
    
    async def update_prediction(
        self, 
        prediction_id: str, 
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing prediction.
        
        Args:
            prediction_id: Prediction ID
            prediction_data: Prediction data
            
        Returns:
            Updated prediction data
        """
        try:
            # Ensure prediction exists
            existing_prediction = await self.get_prediction(prediction_id)
            if not existing_prediction:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            # Ensure prediction_id matches
            if prediction_data.get("prediction_id") != prediction_id:
                raise ValueError("prediction_id in data does not match prediction_id parameter")
            
            # Save to DynamoDB
            self.table.put_item(Item=prediction_data)
            
            return prediction_data
        except ClientError as e:
            logger.error(f"Error updating prediction {prediction_id}: {str(e)}")
            raise
    
    async def delete_prediction(self, prediction_id: str) -> bool:
        """
        Delete a prediction.
        
        Args:
            prediction_id: Prediction ID
            
        Returns:
            True if prediction was deleted, False otherwise
        """
        try:
            # Ensure prediction exists
            existing_prediction = await self.get_prediction(prediction_id)
            if not existing_prediction:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            # Delete from DynamoDB
            self.table.delete_item(
                Key={
                    "prediction_id": prediction_id,
                    "timestamp": existing_prediction["timestamp"]
                }
            )
            
            return True
        except ClientError as e:
            logger.error(f"Error deleting prediction {prediction_id}: {str(e)}")
            return False
    
    async def search_predictions(
        self, 
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for predictions.
        
        Args:
            query: Search query
            filters: Search filters
            limit: Maximum number of results
            
        Returns:
            List of matching predictions
        """
        try:
            # In a real implementation, this would use a more sophisticated search
            # For simplicity, we're using a scan with filters
            filter_expression = None
            
            if query:
                # Search by prediction type or model ID
                filter_expression = (
                    Attr("prediction_type").contains(query) | 
                    Attr("model_id").contains(query)
                )
            
            if filters:
                # Apply additional filters
                for key, value in filters.items():
                    if key == "patient_id":
                        attr_filter = Attr("patient_id").eq(value)
                    elif key == "model_id":
                        attr_filter = Attr("model_id").eq(value)
                    elif key == "prediction_type":
                        attr_filter = Attr("prediction_type").eq(value)
                    elif key == "status":
                        attr_filter = Attr("status").eq(value)
                    elif key == "date_from":
                        attr_filter = Attr("timestamp").gte(value)
                    elif key == "date_to":
                        attr_filter = Attr("timestamp").lte(value)
                    else:
                        attr_filter = Attr(key).eq(value)
                    
                    if filter_expression:
                        filter_expression = filter_expression & attr_filter
                    else:
                        filter_expression = attr_filter
            
            # Execute query
            if filter_expression:
                response = self.table.scan(
                    FilterExpression=filter_expression,
                    Limit=limit
                )
            else:
                response = self.table.scan(Limit=limit)
            
            return response.get("Items", [])
        except ClientError as e:
            logger.error(f"Error searching predictions: {str(e)}")
            return [] 