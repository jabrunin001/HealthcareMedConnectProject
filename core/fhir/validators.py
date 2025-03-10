import logging
import re
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from fhir.resources.resource import Resource
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation

# Configure logging
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for FHIR validation errors."""
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        """
        Initialize ValidationError.
        
        Args:
            message: Error message
            errors: List of specific errors
        """
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class FHIRValidator:
    """Validator for FHIR resources."""
    
    @staticmethod
    def validate_resource(resource: Resource) -> None:
        """
        Validate a FHIR resource.
        
        Args:
            resource: FHIR resource to validate
            
        Raises:
            ValidationError: If resource is invalid
        """
        # Basic validation is performed by the FHIR model itself
        # This method can be extended with additional validation logic
        pass
    
    @staticmethod
    def validate_patient(patient: Patient) -> None:
        """
        Validate a FHIR Patient resource.
        
        Args:
            patient: FHIR Patient resource to validate
            
        Raises:
            ValidationError: If patient is invalid
        """
        errors = []
        
        # Validate resource type
        if patient.resource_type != "Patient":
            errors.append("Resource type must be 'Patient'")
        
        # Validate required fields
        if not patient.id:
            errors.append("Patient ID is required")
        
        # Validate name
        if not patient.name or len(patient.name) == 0:
            errors.append("Patient must have at least one name")
        else:
            for name in patient.name:
                if not name.family:
                    errors.append("Patient name must have a family name")
                if not name.given or len(name.given) == 0:
                    errors.append("Patient name must have at least one given name")
        
        # Validate gender
        if not patient.gender:
            errors.append("Patient gender is required")
        elif patient.gender not in ["male", "female", "other", "unknown"]:
            errors.append("Patient gender must be 'male', 'female', 'other', or 'unknown'")
        
        # Validate birth date
        if not patient.birthDate:
            errors.append("Patient birth date is required")
        else:
            try:
                datetime.strptime(patient.birthDate, "%Y-%m-%d")
            except ValueError:
                errors.append("Patient birth date must be in YYYY-MM-DD format")
        
        # Validate identifiers
        if not patient.identifier or len(patient.identifier) == 0:
            errors.append("Patient must have at least one identifier")
        else:
            for identifier in patient.identifier:
                if not identifier.system:
                    errors.append("Patient identifier must have a system")
                if not identifier.value:
                    errors.append("Patient identifier must have a value")
        
        # Raise validation error if there are any errors
        if errors:
            raise ValidationError("Patient validation failed", errors)
    
    @staticmethod
    def validate_observation(observation: Observation) -> None:
        """
        Validate a FHIR Observation resource.
        
        Args:
            observation: FHIR Observation resource to validate
            
        Raises:
            ValidationError: If observation is invalid
        """
        errors = []
        
        # Validate resource type
        if observation.resource_type != "Observation":
            errors.append("Resource type must be 'Observation'")
        
        # Validate required fields
        if not observation.id:
            errors.append("Observation ID is required")
        
        # Validate status
        if not observation.status:
            errors.append("Observation status is required")
        elif observation.status not in [
            "registered", "preliminary", "final", "amended", 
            "corrected", "cancelled", "entered-in-error", "unknown"
        ]:
            errors.append("Observation status is invalid")
        
        # Validate code
        if not observation.code:
            errors.append("Observation code is required")
        elif not observation.code.coding or len(observation.code.coding) == 0:
            errors.append("Observation code must have at least one coding")
        else:
            for coding in observation.code.coding:
                if not coding.system:
                    errors.append("Observation code coding must have a system")
                if not coding.code:
                    errors.append("Observation code coding must have a code")
        
        # Validate subject
        if not observation.subject:
            errors.append("Observation subject is required")
        elif not observation.subject.reference:
            errors.append("Observation subject reference is required")
        elif not observation.subject.reference.startswith("Patient/"):
            errors.append("Observation subject reference must be a Patient")
        
        # Validate effective date/time
        if not observation.effectiveDateTime and not observation.effectivePeriod:
            errors.append("Observation must have an effective date/time or period")
        elif observation.effectiveDateTime:
            try:
                datetime.fromisoformat(observation.effectiveDateTime.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Observation effective date/time must be in ISO format")
        
        # Validate value
        has_value = (
            observation.valueQuantity or 
            observation.valueCodeableConcept or 
            observation.valueString or 
            observation.valueBoolean or 
            observation.valueInteger or 
            observation.valueRange or 
            observation.valueRatio or 
            observation.valueSampledData or 
            observation.valueTime or 
            observation.valueDateTime or 
            observation.valuePeriod
        )
        
        has_data_absent_reason = observation.dataAbsentReason is not None
        has_component = observation.component and len(observation.component) > 0
        
        if not has_value and not has_data_absent_reason and not has_component:
            errors.append("Observation must have a value, data absent reason, or component")
        
        # Raise validation error if there are any errors
        if errors:
            raise ValidationError("Observation validation failed", errors)
    
    @staticmethod
    def validate_identifier(identifier: str, system: str) -> bool:
        """
        Validate an identifier for a specific system.
        
        Args:
            identifier: Identifier value to validate
            system: Identifier system
            
        Returns:
            True if identifier is valid, False otherwise
        """
        if not identifier:
            return False
        
        # Validate based on system
        if system == "http://hl7.org/fhir/sid/us-ssn":
            # Validate US Social Security Number
            return bool(re.match(r"^\d{3}-\d{2}-\d{4}$", identifier))
        elif system == "http://hl7.org/fhir/sid/us-medicare":
            # Validate US Medicare Number
            return bool(re.match(r"^\d{1,9}[A-Z]$", identifier))
        elif system == "http://hl7.org/fhir/sid/us-npi":
            # Validate US National Provider Identifier
            return bool(re.match(r"^\d{10}$", identifier))
        elif system.endswith("/mrn"):
            # Validate Medical Record Number (generic)
            return bool(identifier)
        
        # Default validation
        return bool(identifier)
    
    @staticmethod
    def validate_date_format(date_str: str, format_str: str) -> bool:
        """
        Validate a date string against a format.
        
        Args:
            date_str: Date string to validate
            format_str: Expected format (e.g., "%Y-%m-%d")
            
        Returns:
            True if date is valid, False otherwise
        """
        try:
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_iso_date(date_str: str) -> bool:
        """
        Validate an ISO format date string.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date is valid, False otherwise
        """
        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False 