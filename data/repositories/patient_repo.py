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


class PatientRepository:
    """Repository for patient data."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize patient repository.
        
        Args:
            table_name: DynamoDB table name (optional)
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("PATIENT_TABLE_NAME", "PatientTable")
        self.table = self.dynamodb.Table(self.table_name)
    
    async def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient by ID.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Patient data or None if not found
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("patient_id").eq(patient_id),
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return items[0]
        except ClientError as e:
            logger.error(f"Error getting patient {patient_id}: {str(e)}")
            return None
    
    async def get_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        """
        Get patient by Medical Record Number.
        
        Args:
            mrn: Medical Record Number
            
        Returns:
            Patient data or None if not found
        """
        try:
            response = self.table.query(
                IndexName="MrnIndex",
                KeyConditionExpression=Key("mrn").eq(mrn),
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return items[0]
        except ClientError as e:
            logger.error(f"Error getting patient by MRN {mrn}: {str(e)}")
            return None
    
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new patient.
        
        Args:
            patient_data: Patient data
            
        Returns:
            Created patient data
        """
        try:
            # Ensure patient_id is present
            if "patient_id" not in patient_data:
                raise ValueError("patient_id is required")
            
            # Save to DynamoDB
            self.table.put_item(Item=patient_data)
            
            return patient_data
        except ClientError as e:
            logger.error(f"Error creating patient: {str(e)}")
            raise
    
    async def update_patient(self, patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
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
            existing_patient = await self.get_patient(patient_id)
            if not existing_patient:
                raise ValueError(f"Patient {patient_id} not found")
            
            # Ensure patient_id matches
            if patient_data.get("patient_id") != patient_id:
                raise ValueError("patient_id in data does not match patient_id parameter")
            
            # Save to DynamoDB
            self.table.put_item(Item=patient_data)
            
            return patient_data
        except ClientError as e:
            logger.error(f"Error updating patient {patient_id}: {str(e)}")
            raise
    
    async def delete_patient(self, patient_id: str) -> bool:
        """
        Delete a patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            True if patient was deleted, False otherwise
        """
        try:
            # Ensure patient exists
            existing_patient = await self.get_patient(patient_id)
            if not existing_patient:
                raise ValueError(f"Patient {patient_id} not found")
            
            # Delete from DynamoDB
            self.table.delete_item(
                Key={
                    "patient_id": patient_id,
                    "version": existing_patient["version"]
                }
            )
            
            return True
        except ClientError as e:
            logger.error(f"Error deleting patient {patient_id}: {str(e)}")
            return False
    
    async def search_patients(
        self, 
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for patients.
        
        Args:
            query: Search query
            filters: Search filters
            limit: Maximum number of results
            
        Returns:
            List of matching patients
        """
        try:
            # In a real implementation, this would use a more sophisticated search
            # For simplicity, we're using a scan with filters
            filter_expression = None
            
            if query:
                # Search by name
                filter_expression = Attr("name").contains(query)
            
            if filters:
                # Apply additional filters
                for key, value in filters.items():
                    if key == "gender":
                        attr_filter = Attr("gender").eq(value)
                    elif key == "age_min":
                        # This is a simplified age filter
                        # In a real implementation, this would calculate age from birth_date
                        attr_filter = Attr("birth_date").lte(str(2023 - int(value)))
                    elif key == "age_max":
                        # This is a simplified age filter
                        attr_filter = Attr("birth_date").gte(str(2023 - int(value)))
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
            logger.error(f"Error searching patients: {str(e)}")
            return [] 