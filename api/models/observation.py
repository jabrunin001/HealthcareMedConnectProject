from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class Quantity(BaseModel):
    """Quantity model for observation values."""
    
    value: float = Field(..., description="Numerical value")
    unit: str = Field(..., description="Unit of measurement")
    system: Optional[str] = Field(None, description="System that defines the unit")
    code: Optional[str] = Field(None, description="Coded form of the unit")


class CodeableConcept(BaseModel):
    """Codeable concept model for coded values."""
    
    coding: List[Dict[str, str]] = Field(..., description="Coding details")
    text: Optional[str] = Field(None, description="Plain text representation")


class ObservationComponent(BaseModel):
    """Component of an observation."""
    
    code: CodeableConcept = Field(..., description="Type of component observation")
    value_quantity: Optional[Quantity] = Field(None, description="Quantity value")
    value_string: Optional[str] = Field(None, description="String value")
    value_boolean: Optional[bool] = Field(None, description="Boolean value")
    value_integer: Optional[int] = Field(None, description="Integer value")
    value_codeable_concept: Optional[CodeableConcept] = Field(None, description="Codeable concept value")
    
    @property
    def value(self) -> Any:
        """Get the value regardless of type."""
        if self.value_quantity is not None:
            return self.value_quantity
        elif self.value_string is not None:
            return self.value_string
        elif self.value_boolean is not None:
            return self.value_boolean
        elif self.value_integer is not None:
            return self.value_integer
        elif self.value_codeable_concept is not None:
            return self.value_codeable_concept
        return None


class Observation(BaseModel):
    """Medical observation model."""
    
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique observation identifier")
    status: str = Field(..., description="Observation status (registered, preliminary, final, amended, corrected, cancelled, entered-in-error, unknown)")
    category: List[CodeableConcept] = Field(..., description="Classification of observation")
    code: CodeableConcept = Field(..., description="Type of observation")
    subject: Dict[str, str] = Field(..., description="Patient reference")
    patient_id: str = Field(..., description="Patient ID for indexing")
    encounter: Optional[Dict[str, str]] = Field(None, description="Healthcare event during which observation was made")
    effective_date_time: str = Field(..., description="Clinically relevant time/time-period for observation")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp for indexing")
    issued: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Date/time observation was issued")
    performer: Optional[List[Dict[str, str]]] = Field(None, description="Who is responsible for the observation")
    value_quantity: Optional[Quantity] = Field(None, description="Quantity value")
    value_string: Optional[str] = Field(None, description="String value")
    value_boolean: Optional[bool] = Field(None, description="Boolean value")
    value_integer: Optional[int] = Field(None, description="Integer value")
    value_codeable_concept: Optional[CodeableConcept] = Field(None, description="Codeable concept value")
    data_absent_reason: Optional[CodeableConcept] = Field(None, description="Why the value is missing")
    interpretation: Optional[List[CodeableConcept]] = Field(None, description="High, low, normal, etc.")
    note: Optional[List[Dict[str, str]]] = Field(None, description="Comments about the observation")
    body_site: Optional[CodeableConcept] = Field(None, description="Observed body part")
    method: Optional[CodeableConcept] = Field(None, description="How it was done")
    specimen: Optional[Dict[str, str]] = Field(None, description="Specimen used for this observation")
    device: Optional[Dict[str, str]] = Field(None, description="Measurement device")
    reference_range: Optional[List[Dict[str, Any]]] = Field(None, description="Provides guide for interpretation")
    has_member: Optional[List[Dict[str, str]]] = Field(None, description="Related resource that belongs to the observation group")
    derived_from: Optional[List[Dict[str, str]]] = Field(None, description="Related measurements the observation is made from")
    component: Optional[List[ObservationComponent]] = Field(None, description="Component observations")
    observation_type: str = Field(..., description="Type of observation for indexing")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record update timestamp")
    
    @validator("status")
    def validate_status(cls, v):
        """Validate observation status."""
        valid_statuses = [
            "registered", "preliminary", "final", "amended", 
            "corrected", "cancelled", "entered-in-error", "unknown"
        ]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    @validator("effective_date_time")
    def validate_effective_date_time(cls, v):
        """Validate effective date time format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("effective_date_time must be in ISO format")
        return v
    
    @property
    def value(self) -> Any:
        """Get the value regardless of type."""
        if self.value_quantity is not None:
            return self.value_quantity
        elif self.value_string is not None:
            return self.value_string
        elif self.value_boolean is not None:
            return self.value_boolean
        elif self.value_integer is not None:
            return self.value_integer
        elif self.value_codeable_concept is not None:
            return self.value_codeable_concept
        return None
    
    def to_fhir(self) -> Dict[str, Any]:
        """Convert to FHIR Observation resource."""
        # Implementation of FHIR conversion logic
        fhir_observation = {
            "resourceType": "Observation",
            "id": self.observation_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": self.updated_at
            },
            "status": self.status,
            "category": [category.dict() for category in self.category],
            "code": self.code.dict(),
            "subject": self.subject,
            "encounter": self.encounter,
            "effectiveDateTime": self.effective_date_time,
            "issued": self.issued,
            "performer": self.performer,
            "dataAbsentReason": self.data_absent_reason.dict() if self.data_absent_reason else None,
            "interpretation": [interp.dict() for interp in self.interpretation] if self.interpretation else None,
            "note": self.note,
            "bodySite": self.body_site.dict() if self.body_site else None,
            "method": self.method.dict() if self.method else None,
            "specimen": self.specimen,
            "device": self.device,
            "referenceRange": self.reference_range,
            "hasMember": self.has_member,
            "derivedFrom": self.derived_from,
            "component": [component.dict() for component in self.component] if self.component else None
        }
        
        # Add the appropriate value field
        if self.value_quantity:
            fhir_observation["valueQuantity"] = self.value_quantity.dict()
        elif self.value_string is not None:
            fhir_observation["valueString"] = self.value_string
        elif self.value_boolean is not None:
            fhir_observation["valueBoolean"] = self.value_boolean
        elif self.value_integer is not None:
            fhir_observation["valueInteger"] = self.value_integer
        elif self.value_codeable_concept:
            fhir_observation["valueCodeableConcept"] = self.value_codeable_concept.dict()
        
        # Remove None values
        return {k: v for k, v in fhir_observation.items() if v is not None}
    
    @classmethod
    def from_fhir(cls, fhir_data: Dict[str, Any]) -> "Observation":
        """Create Observation from FHIR Observation resource."""
        # Implementation of FHIR parsing logic
        
        # Extract categories
        categories = []
        for category in fhir_data.get("category", []):
            categories.append(CodeableConcept(
                coding=category.get("coding", []),
                text=category.get("text")
            ))
        
        # Extract code
        code = CodeableConcept(
            coding=fhir_data.get("code", {}).get("coding", []),
            text=fhir_data.get("code", {}).get("text")
        )
        
        # Extract patient ID from subject reference
        patient_id = ""
        subject = fhir_data.get("subject", {})
        if subject and "reference" in subject:
            reference = subject["reference"]
            if reference.startswith("Patient/"):
                patient_id = reference.split("/")[1]
        
        # Extract observation type from code
        observation_type = "unknown"
        if code.coding and len(code.coding) > 0:
            observation_type = code.coding[0].get("code", "unknown")
        
        # Extract value based on type
        value_quantity = None
        value_string = None
        value_boolean = None
        value_integer = None
        value_codeable_concept = None
        
        if "valueQuantity" in fhir_data:
            value_quantity = Quantity(
                value=fhir_data["valueQuantity"].get("value", 0.0),
                unit=fhir_data["valueQuantity"].get("unit", ""),
                system=fhir_data["valueQuantity"].get("system"),
                code=fhir_data["valueQuantity"].get("code")
            )
        elif "valueString" in fhir_data:
            value_string = fhir_data["valueString"]
        elif "valueBoolean" in fhir_data:
            value_boolean = fhir_data["valueBoolean"]
        elif "valueInteger" in fhir_data:
            value_integer = fhir_data["valueInteger"]
        elif "valueCodeableConcept" in fhir_data:
            value_codeable_concept = CodeableConcept(
                coding=fhir_data["valueCodeableConcept"].get("coding", []),
                text=fhir_data["valueCodeableConcept"].get("text")
            )
        
        # Extract components
        components = []
        for component in fhir_data.get("component", []):
            component_code = CodeableConcept(
                coding=component.get("code", {}).get("coding", []),
                text=component.get("code", {}).get("text")
            )
            
            component_value_quantity = None
            component_value_string = None
            component_value_boolean = None
            component_value_integer = None
            component_value_codeable_concept = None
            
            if "valueQuantity" in component:
                component_value_quantity = Quantity(
                    value=component["valueQuantity"].get("value", 0.0),
                    unit=component["valueQuantity"].get("unit", ""),
                    system=component["valueQuantity"].get("system"),
                    code=component["valueQuantity"].get("code")
                )
            elif "valueString" in component:
                component_value_string = component["valueString"]
            elif "valueBoolean" in component:
                component_value_boolean = component["valueBoolean"]
            elif "valueInteger" in component:
                component_value_integer = component["valueInteger"]
            elif "valueCodeableConcept" in component:
                component_value_codeable_concept = CodeableConcept(
                    coding=component["valueCodeableConcept"].get("coding", []),
                    text=component["valueCodeableConcept"].get("text")
                )
            
            components.append(ObservationComponent(
                code=component_code,
                value_quantity=component_value_quantity,
                value_string=component_value_string,
                value_boolean=component_value_boolean,
                value_integer=component_value_integer,
                value_codeable_concept=component_value_codeable_concept
            ))
        
        # Extract other fields
        data_absent_reason = None
        if "dataAbsentReason" in fhir_data:
            data_absent_reason = CodeableConcept(
                coding=fhir_data["dataAbsentReason"].get("coding", []),
                text=fhir_data["dataAbsentReason"].get("text")
            )
        
        interpretations = []
        for interpretation in fhir_data.get("interpretation", []):
            interpretations.append(CodeableConcept(
                coding=interpretation.get("coding", []),
                text=interpretation.get("text")
            ))
        
        body_site = None
        if "bodySite" in fhir_data:
            body_site = CodeableConcept(
                coding=fhir_data["bodySite"].get("coding", []),
                text=fhir_data["bodySite"].get("text")
            )
        
        method = None
        if "method" in fhir_data:
            method = CodeableConcept(
                coding=fhir_data["method"].get("coding", []),
                text=fhir_data["method"].get("text")
            )
        
        return cls(
            observation_id=fhir_data.get("id", str(uuid.uuid4())),
            status=fhir_data.get("status", "unknown"),
            category=categories,
            code=code,
            subject=subject,
            patient_id=patient_id,
            encounter=fhir_data.get("encounter"),
            effective_date_time=fhir_data.get("effectiveDateTime", datetime.utcnow().isoformat()),
            timestamp=datetime.utcnow().isoformat(),
            issued=fhir_data.get("issued", datetime.utcnow().isoformat()),
            performer=fhir_data.get("performer"),
            value_quantity=value_quantity,
            value_string=value_string,
            value_boolean=value_boolean,
            value_integer=value_integer,
            value_codeable_concept=value_codeable_concept,
            data_absent_reason=data_absent_reason,
            interpretation=interpretations if interpretations else None,
            note=fhir_data.get("note"),
            body_site=body_site,
            method=method,
            specimen=fhir_data.get("specimen"),
            device=fhir_data.get("device"),
            reference_range=fhir_data.get("referenceRange"),
            has_member=fhir_data.get("hasMember"),
            derived_from=fhir_data.get("derivedFrom"),
            component=components if components else None,
            observation_type=observation_type,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        ) 