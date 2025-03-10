from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class PredictionInput(BaseModel):
    """Input data for ML prediction."""
    
    patient_id: str = Field(..., description="Patient ID")
    observation_ids: Optional[List[str]] = Field(None, description="Observation IDs used for prediction")
    features: Dict[str, Any] = Field(..., description="Features used for prediction")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for prediction")


class PredictionOutput(BaseModel):
    """Output data from ML prediction."""
    
    prediction: Any = Field(..., description="Prediction result")
    probability: Optional[float] = Field(None, description="Prediction probability or confidence")
    scores: Optional[Dict[str, float]] = Field(None, description="Detailed prediction scores")
    explanation: Optional[Dict[str, Any]] = Field(None, description="Explanation of prediction")
    thresholds: Optional[Dict[str, float]] = Field(None, description="Thresholds used for classification")


class Prediction(BaseModel):
    """ML prediction model."""
    
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique prediction identifier")
    model_id: str = Field(..., description="Model identifier")
    model_version: str = Field(..., description="Model version")
    patient_id: str = Field(..., description="Patient ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Prediction timestamp")
    prediction_type: str = Field(..., description="Type of prediction (risk, diagnosis, etc.)")
    input_data: PredictionInput = Field(..., description="Input data for prediction")
    output_data: PredictionOutput = Field(..., description="Output data from prediction")
    status: str = Field("completed", description="Prediction status (pending, completed, failed)")
    error: Optional[str] = Field(None, description="Error message if prediction failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Record update timestamp")
    
    @validator("status")
    def validate_status(cls, v):
        """Validate prediction status."""
        valid_statuses = ["pending", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    @validator("timestamp")
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("timestamp must be in ISO format")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "prediction_id": self.prediction_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "patient_id": self.patient_id,
            "timestamp": self.timestamp,
            "prediction_type": self.prediction_type,
            "input_data": self.input_data.dict(),
            "output_data": self.output_data.dict(),
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prediction":
        """Create Prediction from dictionary."""
        input_data = PredictionInput(**data.get("input_data", {}))
        output_data = PredictionOutput(**data.get("output_data", {}))
        
        return cls(
            prediction_id=data.get("prediction_id", str(uuid.uuid4())),
            model_id=data.get("model_id", ""),
            model_version=data.get("model_version", ""),
            patient_id=data.get("patient_id", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            prediction_type=data.get("prediction_type", ""),
            input_data=input_data,
            output_data=output_data,
            status=data.get("status", "completed"),
            error=data.get("error"),
            metadata=data.get("metadata"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat())
        )


class PredictionRequest(BaseModel):
    """Request for ML prediction."""
    
    patient_id: str = Field(..., description="Patient ID")
    model_id: str = Field(..., description="Model identifier")
    observation_ids: Optional[List[str]] = Field(None, description="Observation IDs to use for prediction")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for prediction")
    
    
class PredictionResponse(BaseModel):
    """Response for ML prediction."""
    
    prediction_id: str = Field(..., description="Prediction identifier")
    patient_id: str = Field(..., description="Patient ID")
    model_id: str = Field(..., description="Model identifier")
    model_version: str = Field(..., description="Model version")
    prediction_type: str = Field(..., description="Type of prediction")
    prediction: Any = Field(..., description="Prediction result")
    probability: Optional[float] = Field(None, description="Prediction probability")
    explanation: Optional[Dict[str, Any]] = Field(None, description="Explanation of prediction")
    timestamp: str = Field(..., description="Prediction timestamp") 