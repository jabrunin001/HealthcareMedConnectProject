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


class ObservationRepository:
    """Repository for observation data."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize observation repository.
        
        Args:
            table_name: DynamoDB table name (optional)
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("OBSERVATION_TABLE_NAME", "ObservationTable")
        self.table = self.dynamodb.Table(self.table_name)
    
    async def get_observation(self, observation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get observation by ID.
        
        Args:
            observation_id: Observation ID
            
        Returns:
            Observation data or None if not found
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("observation_id").eq(observation_id),
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return items[0]
        except ClientError as e:
            logger.error(f"Error getting observation {observation_id}: {str(e)}")
            return None
    
    async def get_patient_observations(
        self, 
        patient_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        observation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get observations for a patient.
        
        Args:
            patient_id: Patient ID
            start_date: Start date for filtering observations
            end_date: End date for filtering observations
            observation_type: Type of observation to filter by
            limit: Maximum number of observations to return
            
        Returns:
            List of observations
        """
        try:
            if observation_type:
                # Query by patient ID and observation type
                response = self.table.query(
                    IndexName="TypeIndex",
                    KeyConditionExpression=Key("observation_type").eq(observation_type),
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
            logger.error(f"Error getting observations for patient {patient_id}: {str(e)}")
            return []
    
    async def get_observations_by_type(
        self, 
        observation_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get observations by type.
        
        Args:
            observation_type: Type of observation
            start_date: Start date for filtering observations
            end_date: End date for filtering observations
            limit: Maximum number of observations to return
            
        Returns:
            List of observations
        """
        try:
            key_condition = Key("observation_type").eq(observation_type)
            
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
                IndexName="TypeIndex",
                KeyConditionExpression=key_condition,
                ScanIndexForward=False,
                Limit=limit
            )
            
            return response.get("Items", [])
        except ClientError as e:
            logger.error(f"Error getting observations of type {observation_type}: {str(e)}")
            return []
    
    async def create_observation(self, observation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new observation.
        
        Args:
            observation_data: Observation data
            
        Returns:
            Created observation data
        """
        try:
            # Ensure observation_id is present
            if "observation_id" not in observation_data:
                raise ValueError("observation_id is required")
            
            # Ensure patient_id is present
            if "patient_id" not in observation_data:
                raise ValueError("patient_id is required")
            
            # Ensure observation_type is present
            if "observation_type" not in observation_data:
                raise ValueError("observation_type is required")
            
            # Save to DynamoDB
            self.table.put_item(Item=observation_data)
            
            return observation_data
        except ClientError as e:
            logger.error(f"Error creating observation: {str(e)}")
            raise
    
    async def update_observation(
        self, 
        observation_id: str, 
        observation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing observation.
        
        Args:
            observation_id: Observation ID
            observation_data: Observation data
            
        Returns:
            Updated observation data
        """
        try:
            # Ensure observation exists
            existing_observation = await self.get_observation(observation_id)
            if not existing_observation:
                raise ValueError(f"Observation {observation_id} not found")
            
            # Ensure observation_id matches
            if observation_data.get("observation_id") != observation_id:
                raise ValueError("observation_id in data does not match observation_id parameter")
            
            # Save to DynamoDB
            self.table.put_item(Item=observation_data)
            
            return observation_data
        except ClientError as e:
            logger.error(f"Error updating observation {observation_id}: {str(e)}")
            raise
    
    async def delete_observation(self, observation_id: str) -> bool:
        """
        Delete an observation.
        
        Args:
            observation_id: Observation ID
            
        Returns:
            True if observation was deleted, False otherwise
        """
        try:
            # Ensure observation exists
            existing_observation = await self.get_observation(observation_id)
            if not existing_observation:
                raise ValueError(f"Observation {observation_id} not found")
            
            # Delete from DynamoDB
            self.table.delete_item(
                Key={
                    "observation_id": observation_id,
                    "timestamp": existing_observation["timestamp"]
                }
            )
            
            return True
        except ClientError as e:
            logger.error(f"Error deleting observation {observation_id}: {str(e)}")
            return False
    
    async def search_observations(
        self, 
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for observations.
        
        Args:
            query: Search query
            filters: Search filters
            limit: Maximum number of results
            
        Returns:
            List of matching observations
        """
        try:
            # In a real implementation, this would use a more sophisticated search
            # For simplicity, we're using a scan with filters
            filter_expression = None
            
            if query:
                # Search by observation type or value
                filter_expression = (
                    Attr("observation_type").contains(query) | 
                    Attr("value_string").contains(query)
                )
            
            if filters:
                # Apply additional filters
                for key, value in filters.items():
                    if key == "patient_id":
                        attr_filter = Attr("patient_id").eq(value)
                    elif key == "observation_type":
                        attr_filter = Attr("observation_type").eq(value)
                    elif key == "status":
                        attr_filter = Attr("status").eq(value)
                    elif key == "date_from":
                        attr_filter = Attr("effective_date_time").gte(value)
                    elif key == "date_to":
                        attr_filter = Attr("effective_date_time").lte(value)
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
            logger.error(f"Error searching observations: {str(e)}")
            return [] 