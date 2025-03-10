from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class Address(BaseModel):
    """Patient address model."""
    
    line: List[str] = Field(..., description="Street address lines")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State/Province/Region")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")
    use: str = Field("home", description="Purpose of the address (home, work, etc.)")


class ContactPoint(BaseModel):
    """Patient contact point model."""
    
    system: str = Field(..., description="Type of contact (phone, email, etc.)")
    value: str = Field(..., description="Contact details")
    use: str = Field("home", description="Purpose of the contact point")
    rank: Optional[int] = Field(None, description="Preference order for contact")


class HumanName(BaseModel):
    """Human name model."""
    
    family: str = Field(..., description="Family name")
    given: List[str] = Field(..., description="Given names")
    prefix: Optional[List[str]] = Field(None, description="Name prefixes")
    suffix: Optional[List[str]] = Field(None, description="Name suffixes")
    use: str = Field("official", description="Purpose of the name")


class Identifier(BaseModel):
    """Patient identifier model."""
    
    system: str = Field(..., description="Identifier system")
    value: str = Field(..., description="Identifier value")
    type: Optional[str] = Field(None, description="Identifier type")
    use: Optional[str] = Field(None, description="Purpose of the identifier")


class Patient(BaseModel):
    """Patient data model."""
    
    patient_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique patient identifier")
    version: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Version timestamp")
    active: bool = Field(True, description="Whether the patient record is active")
    identifiers: List[Identifier] = Field(..., description="Patient identifiers (MRN, SSN, etc.)")
    name: List[HumanName] = Field(..., description="Patient names")
    gender: str = Field(..., description="Patient gender")
    birth_date: str = Field(..., description="Patient birth date (YYYY-MM-DD)")
    deceased: bool = Field(False, description="Whether the patient is deceased")
    deceased_date: Optional[str] = Field(None, description="Date of death if deceased")
    address: Optional[List[Address]] = Field(None, description="Patient addresses")
    telecom: Optional[List[ContactPoint]] = Field(None, description="Patient contact points")
    marital_status: Optional[str] = Field(None, description="Marital status")
    communication: Optional[List[Dict[str, Any]]] = Field(None, description="Patient communication preferences")
    extension: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record update timestamp")
    
    @validator("birth_date")
    def validate_birth_date(cls, v):
        """Validate birth date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("birth_date must be in YYYY-MM-DD format")
        return v
    
    @validator("deceased_date")
    def validate_deceased_date(cls, v, values):
        """Validate deceased date if present."""
        if v is not None:
            try:
                deceased_date = datetime.strptime(v, "%Y-%m-%d")
                birth_date = datetime.strptime(values["birth_date"], "%Y-%m-%d")
                if deceased_date < birth_date:
                    raise ValueError("deceased_date cannot be before birth_date")
            except ValueError as e:
                if str(e) == "deceased_date cannot be before birth_date":
                    raise
                raise ValueError("deceased_date must be in YYYY-MM-DD format")
        return v
    
    def to_fhir(self) -> Dict[str, Any]:
        """Convert to FHIR Patient resource."""
        # Implementation of FHIR conversion logic
        fhir_patient = {
            "resourceType": "Patient",
            "id": self.patient_id,
            "meta": {
                "versionId": self.version,
                "lastUpdated": self.updated_at
            },
            "active": self.active,
            "identifier": [
                {
                    "system": identifier.system,
                    "value": identifier.value,
                    "type": {"coding": [{"code": identifier.type}]} if identifier.type else None,
                    "use": identifier.use
                } for identifier in self.identifiers
            ],
            "name": [
                {
                    "family": name.family,
                    "given": name.given,
                    "prefix": name.prefix,
                    "suffix": name.suffix,
                    "use": name.use
                } for name in self.name
            ],
            "gender": self.gender,
            "birthDate": self.birth_date,
            "deceasedBoolean": self.deceased,
            "deceasedDateTime": self.deceased_date,
            "address": [
                {
                    "line": address.line,
                    "city": address.city,
                    "state": address.state,
                    "postalCode": address.postal_code,
                    "country": address.country,
                    "use": address.use
                } for address in (self.address or [])
            ],
            "telecom": [
                {
                    "system": contact.system,
                    "value": contact.value,
                    "use": contact.use,
                    "rank": contact.rank
                } for contact in (self.telecom or [])
            ],
            "maritalStatus": {"coding": [{"code": self.marital_status}]} if self.marital_status else None,
            "communication": self.communication,
            "extension": self.extension
        }
        
        # Remove None values
        return {k: v for k, v in fhir_patient.items() if v is not None}
    
    @classmethod
    def from_fhir(cls, fhir_data: Dict[str, Any]) -> "Patient":
        """Create Patient from FHIR Patient resource."""
        # Implementation of FHIR parsing logic
        identifiers = []
        for identifier in fhir_data.get("identifier", []):
            type_code = None
            if identifier.get("type") and identifier["type"].get("coding"):
                type_code = identifier["type"]["coding"][0].get("code")
            
            identifiers.append(Identifier(
                system=identifier.get("system", ""),
                value=identifier.get("value", ""),
                type=type_code,
                use=identifier.get("use")
            ))
        
        names = []
        for name in fhir_data.get("name", []):
            names.append(HumanName(
                family=name.get("family", ""),
                given=name.get("given", []),
                prefix=name.get("prefix"),
                suffix=name.get("suffix"),
                use=name.get("use", "official")
            ))
        
        addresses = []
        for address in fhir_data.get("address", []):
            addresses.append(Address(
                line=address.get("line", []),
                city=address.get("city", ""),
                state=address.get("state", ""),
                postal_code=address.get("postalCode", ""),
                country=address.get("country", ""),
                use=address.get("use", "home")
            ))
        
        telecoms = []
        for telecom in fhir_data.get("telecom", []):
            telecoms.append(ContactPoint(
                system=telecom.get("system", ""),
                value=telecom.get("value", ""),
                use=telecom.get("use", "home"),
                rank=telecom.get("rank")
            ))
        
        marital_status = None
        if fhir_data.get("maritalStatus") and fhir_data["maritalStatus"].get("coding"):
            marital_status = fhir_data["maritalStatus"]["coding"][0].get("code")
        
        deceased = False
        deceased_date = None
        if "deceasedBoolean" in fhir_data:
            deceased = fhir_data["deceasedBoolean"]
        if "deceasedDateTime" in fhir_data:
            deceased_date = fhir_data["deceasedDateTime"]
            deceased = True
        
        return cls(
            patient_id=fhir_data.get("id", str(uuid.uuid4())),
            version=fhir_data.get("meta", {}).get("versionId", datetime.utcnow().isoformat()),
            active=fhir_data.get("active", True),
            identifiers=identifiers,
            name=names,
            gender=fhir_data.get("gender", "unknown"),
            birth_date=fhir_data.get("birthDate", ""),
            deceased=deceased,
            deceased_date=deceased_date,
            address=addresses if addresses else None,
            telecom=telecoms if telecoms else None,
            marital_status=marital_status,
            communication=fhir_data.get("communication"),
            extension=fhir_data.get("extension"),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        ) 