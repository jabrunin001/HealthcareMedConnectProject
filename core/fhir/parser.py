import json
import logging
from typing import Dict, Any, List, Optional, Union, Type, TypeVar
from fhir.resources.resource import Resource
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.bundle import Bundle

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for FHIR resources
T = TypeVar('T', bound=Resource)


class FHIRParser:
    """Parser for FHIR resources."""
    
    @staticmethod
    def parse_resource(data: Union[str, Dict[str, Any]], resource_type: Type[T]) -> T:
        """
        Parse FHIR resource from JSON string or dictionary.
        
        Args:
            data: JSON string or dictionary containing FHIR resource
            resource_type: Type of FHIR resource to parse
            
        Returns:
            Parsed FHIR resource
            
        Raises:
            ValueError: If data is invalid or cannot be parsed
        """
        try:
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data
            
            return resource_type.parse_obj(data_dict)
        except Exception as e:
            logger.error(f"Error parsing {resource_type.__name__}: {str(e)}")
            raise ValueError(f"Error parsing {resource_type.__name__}: {str(e)}")
    
    @staticmethod
    def parse_bundle(data: Union[str, Dict[str, Any]]) -> Bundle:
        """
        Parse FHIR Bundle from JSON string or dictionary.
        
        Args:
            data: JSON string or dictionary containing FHIR Bundle
            
        Returns:
            Parsed FHIR Bundle
            
        Raises:
            ValueError: If data is invalid or cannot be parsed
        """
        return FHIRParser.parse_resource(data, Bundle)
    
    @staticmethod
    def parse_patient(data: Union[str, Dict[str, Any]]) -> Patient:
        """
        Parse FHIR Patient from JSON string or dictionary.
        
        Args:
            data: JSON string or dictionary containing FHIR Patient
            
        Returns:
            Parsed FHIR Patient
            
        Raises:
            ValueError: If data is invalid or cannot be parsed
        """
        return FHIRParser.parse_resource(data, Patient)
    
    @staticmethod
    def parse_observation(data: Union[str, Dict[str, Any]]) -> Observation:
        """
        Parse FHIR Observation from JSON string or dictionary.
        
        Args:
            data: JSON string or dictionary containing FHIR Observation
            
        Returns:
            Parsed FHIR Observation
            
        Raises:
            ValueError: If data is invalid or cannot be parsed
        """
        return FHIRParser.parse_resource(data, Observation)
    
    @staticmethod
    def extract_resources_from_bundle(
        bundle: Union[Bundle, Dict[str, Any], str],
        resource_type: Type[T]
    ) -> List[T]:
        """
        Extract resources of a specific type from a FHIR Bundle.
        
        Args:
            bundle: FHIR Bundle
            resource_type: Type of resources to extract
            
        Returns:
            List of extracted resources
            
        Raises:
            ValueError: If bundle is invalid or cannot be parsed
        """
        try:
            if isinstance(bundle, str):
                bundle_obj = FHIRParser.parse_bundle(bundle)
            elif isinstance(bundle, dict):
                bundle_obj = FHIRParser.parse_bundle(bundle)
            else:
                bundle_obj = bundle
            
            resources = []
            for entry in bundle_obj.entry:
                if entry.resource.resource_type == resource_type.__name__:
                    resources.append(resource_type.parse_obj(entry.resource.dict()))
            
            return resources
        except Exception as e:
            logger.error(f"Error extracting {resource_type.__name__} from bundle: {str(e)}")
            raise ValueError(f"Error extracting {resource_type.__name__} from bundle: {str(e)}")
    
    @staticmethod
    def extract_patients_from_bundle(bundle: Union[Bundle, Dict[str, Any], str]) -> List[Patient]:
        """
        Extract Patient resources from a FHIR Bundle.
        
        Args:
            bundle: FHIR Bundle
            
        Returns:
            List of Patient resources
            
        Raises:
            ValueError: If bundle is invalid or cannot be parsed
        """
        return FHIRParser.extract_resources_from_bundle(bundle, Patient)
    
    @staticmethod
    def extract_observations_from_bundle(bundle: Union[Bundle, Dict[str, Any], str]) -> List[Observation]:
        """
        Extract Observation resources from a FHIR Bundle.
        
        Args:
            bundle: FHIR Bundle
            
        Returns:
            List of Observation resources
            
        Raises:
            ValueError: If bundle is invalid or cannot be parsed
        """
        return FHIRParser.extract_resources_from_bundle(bundle, Observation)
    
    @staticmethod
    def to_json(resource: Resource) -> str:
        """
        Convert FHIR resource to JSON string.
        
        Args:
            resource: FHIR resource
            
        Returns:
            JSON string
        """
        return resource.json(indent=2)
    
    @staticmethod
    def to_dict(resource: Resource) -> Dict[str, Any]:
        """
        Convert FHIR resource to dictionary.
        
        Args:
            resource: FHIR resource
            
        Returns:
            Dictionary representation of the resource
        """
        return resource.dict() 