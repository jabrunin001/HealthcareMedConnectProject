import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.bundle import Bundle

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class FHIRClient:
    """Client for interacting with FHIR servers."""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize FHIR client.
        
        Args:
            base_url: Base URL of the FHIR server
            auth_token: Authentication token for the FHIR server
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
        
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def get_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Get a resource by ID.
        
        Args:
            resource_type: Type of resource (Patient, Observation, etc.)
            resource_id: Resource ID
            
        Returns:
            Resource data
            
        Raises:
            ValueError: If resource is not found or request fails
        """
        url = f"{self.base_url}/{resource_type}/{resource_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"{resource_type} {resource_id} not found")
            else:
                logger.error(f"Error getting {resource_type} {resource_id}: {str(e)}")
                raise ValueError(f"Error getting {resource_type} {resource_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting {resource_type} {resource_id}: {str(e)}")
            raise ValueError(f"Error getting {resource_type} {resource_id}: {str(e)}")
    
    async def search_resources(
        self, 
        resource_type: str, 
        params: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Search for resources.
        
        Args:
            resource_type: Type of resource (Patient, Observation, etc.)
            params: Search parameters
            
        Returns:
            List of resources
            
        Raises:
            ValueError: If request fails
        """
        url = f"{self.base_url}/{resource_type}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                if data.get("resourceType") == "Bundle":
                    return [entry["resource"] for entry in data.get("entry", [])]
                else:
                    return [data]
        except Exception as e:
            logger.error(f"Error searching {resource_type}: {str(e)}")
            raise ValueError(f"Error searching {resource_type}: {str(e)}")
    
    async def create_resource(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new resource.
        
        Args:
            resource_type: Type of resource (Patient, Observation, etc.)
            data: Resource data
            
        Returns:
            Created resource data
            
        Raises:
            ValueError: If request fails
        """
        url = f"{self.base_url}/{resource_type}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating {resource_type}: {str(e)}")
            raise ValueError(f"Error creating {resource_type}: {str(e)}")
    
    async def update_resource(
        self, 
        resource_type: str, 
        resource_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing resource.
        
        Args:
            resource_type: Type of resource (Patient, Observation, etc.)
            resource_id: Resource ID
            data: Resource data
            
        Returns:
            Updated resource data
            
        Raises:
            ValueError: If resource is not found or request fails
        """
        url = f"{self.base_url}/{resource_type}/{resource_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"{resource_type} {resource_id} not found")
            else:
                logger.error(f"Error updating {resource_type} {resource_id}: {str(e)}")
                raise ValueError(f"Error updating {resource_type} {resource_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating {resource_type} {resource_id}: {str(e)}")
            raise ValueError(f"Error updating {resource_type} {resource_id}: {str(e)}")
    
    async def delete_resource(self, resource_type: str, resource_id: str) -> None:
        """
        Delete a resource.
        
        Args:
            resource_type: Type of resource (Patient, Observation, etc.)
            resource_id: Resource ID
            
        Raises:
            ValueError: If resource is not found or request fails
        """
        url = f"{self.base_url}/{resource_type}/{resource_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"{resource_type} {resource_id} not found")
            else:
                logger.error(f"Error deleting {resource_type} {resource_id}: {str(e)}")
                raise ValueError(f"Error deleting {resource_type} {resource_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting {resource_type} {resource_id}: {str(e)}")
            raise ValueError(f"Error deleting {resource_type} {resource_id}: {str(e)}")
    
    async def get_patient(self, patient_id: str) -> Patient:
        """
        Get a patient by ID.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Patient resource
            
        Raises:
            ValueError: If patient is not found or request fails
        """
        data = await self.get_resource("Patient", patient_id)
        return Patient.parse_obj(data)
    
    async def search_patients(self, params: Dict[str, str]) -> List[Patient]:
        """
        Search for patients.
        
        Args:
            params: Search parameters
            
        Returns:
            List of patients
            
        Raises:
            ValueError: If request fails
        """
        data = await self.search_resources("Patient", params)
        return [Patient.parse_obj(item) for item in data]
    
    async def create_patient(self, patient: Union[Patient, Dict[str, Any]]) -> Patient:
        """
        Create a new patient.
        
        Args:
            patient: Patient data
            
        Returns:
            Created patient
            
        Raises:
            ValueError: If request fails
        """
        if isinstance(patient, Patient):
            data = patient.dict()
        else:
            data = patient
        
        result = await self.create_resource("Patient", data)
        return Patient.parse_obj(result)
    
    async def update_patient(
        self, 
        patient_id: str, 
        patient: Union[Patient, Dict[str, Any]]
    ) -> Patient:
        """
        Update an existing patient.
        
        Args:
            patient_id: Patient ID
            patient: Patient data
            
        Returns:
            Updated patient
            
        Raises:
            ValueError: If patient is not found or request fails
        """
        if isinstance(patient, Patient):
            data = patient.dict()
        else:
            data = patient
        
        result = await self.update_resource("Patient", patient_id, data)
        return Patient.parse_obj(result)
    
    async def get_observation(self, observation_id: str) -> Observation:
        """
        Get an observation by ID.
        
        Args:
            observation_id: Observation ID
            
        Returns:
            Observation resource
            
        Raises:
            ValueError: If observation is not found or request fails
        """
        data = await self.get_resource("Observation", observation_id)
        return Observation.parse_obj(data)
    
    async def search_observations(self, params: Dict[str, str]) -> List[Observation]:
        """
        Search for observations.
        
        Args:
            params: Search parameters
            
        Returns:
            List of observations
            
        Raises:
            ValueError: If request fails
        """
        data = await self.search_resources("Observation", params)
        return [Observation.parse_obj(item) for item in data]
    
    async def create_observation(
        self, 
        observation: Union[Observation, Dict[str, Any]]
    ) -> Observation:
        """
        Create a new observation.
        
        Args:
            observation: Observation data
            
        Returns:
            Created observation
            
        Raises:
            ValueError: If request fails
        """
        if isinstance(observation, Observation):
            data = observation.dict()
        else:
            data = observation
        
        result = await self.create_resource("Observation", data)
        return Observation.parse_obj(result)
    
    async def get_patient_observations(self, patient_id: str) -> List[Observation]:
        """
        Get observations for a patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List of observations
            
        Raises:
            ValueError: If request fails
        """
        return await self.search_observations({"patient": patient_id}) 