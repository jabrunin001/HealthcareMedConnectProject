import os
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class RiskPredictor:
    """Model for predicting patient health risks."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize risk predictor.
        
        Args:
            model_path: Path to model file (optional)
        """
        self.model_id = "risk-predictor"
        self.model_version = "1.0.0"
        
        # Load model if path is provided
        if model_path:
            self._load_model(model_path)
        else:
            # Use default model parameters
            self._initialize_default_model()
    
    def _load_model(self, model_path: str) -> None:
        """
        Load model from file.
        
        Args:
            model_path: Path to model file
        """
        try:
            # In a real implementation, this would load a trained model
            # For simplicity, we're just loading model parameters from a JSON file
            with open(model_path, "r") as f:
                model_data = json.load(f)
            
            self.feature_weights = model_data.get("feature_weights", {})
            self.thresholds = model_data.get("thresholds", {
                "low-risk": 0.3,
                "medium-risk": 0.6,
                "high-risk": 0.8
            })
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")
            self._initialize_default_model()
    
    def _initialize_default_model(self) -> None:
        """Initialize default model parameters."""
        # In a real implementation, these would be learned from training data
        # For simplicity, we're using predefined weights
        self.feature_weights = {
            # Demographic features
            "age": 0.05,
            "gender_male": 0.02,
            "gender_female": -0.01,
            
            # Vital signs
            "heart_rate_high": 0.15,
            "heart_rate_low": 0.1,
            "blood_pressure_systolic_high": 0.2,
            "blood_pressure_systolic_low": 0.05,
            "blood_pressure_diastolic_high": 0.15,
            "blood_pressure_diastolic_low": 0.05,
            "respiratory_rate_high": 0.15,
            "respiratory_rate_low": 0.1,
            "temperature_high": 0.15,
            "temperature_low": 0.05,
            "oxygen_saturation_low": 0.25,
            
            # Lab results
            "glucose_high": 0.1,
            "glucose_low": 0.05,
            "wbc_high": 0.1,
            "wbc_low": 0.05,
            "creatinine_high": 0.15,
            "bun_high": 0.1,
            "potassium_high": 0.1,
            "potassium_low": 0.1,
            "sodium_high": 0.05,
            "sodium_low": 0.05,
            
            # Conditions
            "diabetes": 0.15,
            "hypertension": 0.1,
            "copd": 0.2,
            "chf": 0.25,
            "ckd": 0.2,
            "cad": 0.15,
            "stroke": 0.2,
            "cancer": 0.15,
            
            # Medications
            "insulin": 0.05,
            "antihypertensive": 0.05,
            "anticoagulant": 0.1,
            "steroid": 0.05,
            "opioid": 0.1
        }
        
        self.thresholds = {
            "low-risk": 0.3,
            "medium-risk": 0.6,
            "high-risk": 0.8
        }
    
    def _extract_features(self, patient_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from patient data.
        
        Args:
            patient_data: Patient data
            
        Returns:
            Extracted features
        """
        features = {}
        
        # Extract demographic features
        demographics = patient_data.get("demographics", {})
        age = demographics.get("age")
        if age is not None:
            features["age"] = min(age / 100.0, 1.0)  # Normalize age
        
        gender = demographics.get("gender")
        if gender == "male":
            features["gender_male"] = 1.0
            features["gender_female"] = 0.0
        elif gender == "female":
            features["gender_male"] = 0.0
            features["gender_female"] = 1.0
        
        # Extract vital signs features
        vital_signs = patient_data.get("vital_signs", {})
        
        # Heart rate
        heart_rate = self._get_latest_value(vital_signs.get("heart-rate"))
        if heart_rate is not None:
            features["heart_rate_high"] = 1.0 if heart_rate > 100 else 0.0
            features["heart_rate_low"] = 1.0 if heart_rate < 60 else 0.0
        
        # Blood pressure
        blood_pressure = self._get_latest_value(vital_signs.get("blood-pressure"))
        if blood_pressure is not None and isinstance(blood_pressure, dict):
            systolic = blood_pressure.get("systolic")
            diastolic = blood_pressure.get("diastolic")
            
            if systolic is not None:
                features["blood_pressure_systolic_high"] = 1.0 if systolic > 140 else 0.0
                features["blood_pressure_systolic_low"] = 1.0 if systolic < 90 else 0.0
            
            if diastolic is not None:
                features["blood_pressure_diastolic_high"] = 1.0 if diastolic > 90 else 0.0
                features["blood_pressure_diastolic_low"] = 1.0 if diastolic < 60 else 0.0
        
        # Respiratory rate
        respiratory_rate = self._get_latest_value(vital_signs.get("respiratory-rate"))
        if respiratory_rate is not None:
            features["respiratory_rate_high"] = 1.0 if respiratory_rate > 20 else 0.0
            features["respiratory_rate_low"] = 1.0 if respiratory_rate < 12 else 0.0
        
        # Temperature
        temperature = self._get_latest_value(vital_signs.get("temperature"))
        if temperature is not None:
            features["temperature_high"] = 1.0 if temperature > 38.0 else 0.0
            features["temperature_low"] = 1.0 if temperature < 36.0 else 0.0
        
        # Oxygen saturation
        oxygen_saturation = self._get_latest_value(vital_signs.get("oxygen-saturation"))
        if oxygen_saturation is not None:
            features["oxygen_saturation_low"] = 1.0 if oxygen_saturation < 95 else 0.0
        
        # Extract lab results features
        lab_results = patient_data.get("lab_results", {})
        
        # Glucose
        glucose = self._get_latest_value(lab_results.get("lab-glucose"))
        if glucose is not None:
            features["glucose_high"] = 1.0 if glucose > 200 else 0.0
            features["glucose_low"] = 1.0 if glucose < 70 else 0.0
        
        # White blood cell count
        wbc = self._get_latest_value(lab_results.get("lab-wbc"))
        if wbc is not None:
            features["wbc_high"] = 1.0 if wbc > 11 else 0.0
            features["wbc_low"] = 1.0 if wbc < 4 else 0.0
        
        # Creatinine
        creatinine = self._get_latest_value(lab_results.get("lab-creatinine"))
        if creatinine is not None:
            features["creatinine_high"] = 1.0 if creatinine > 1.2 else 0.0
        
        # Blood urea nitrogen
        bun = self._get_latest_value(lab_results.get("lab-bun"))
        if bun is not None:
            features["bun_high"] = 1.0 if bun > 20 else 0.0
        
        # Potassium
        potassium = self._get_latest_value(lab_results.get("lab-potassium"))
        if potassium is not None:
            features["potassium_high"] = 1.0 if potassium > 5.0 else 0.0
            features["potassium_low"] = 1.0 if potassium < 3.5 else 0.0
        
        # Sodium
        sodium = self._get_latest_value(lab_results.get("lab-sodium"))
        if sodium is not None:
            features["sodium_high"] = 1.0 if sodium > 145 else 0.0
            features["sodium_low"] = 1.0 if sodium < 135 else 0.0
        
        # Extract conditions features
        conditions = patient_data.get("conditions", [])
        for condition in conditions:
            if condition in self.feature_weights:
                features[condition] = 1.0
        
        # Extract medications features
        medications = patient_data.get("medications", [])
        for medication in medications:
            if medication in self.feature_weights:
                features[medication] = 1.0
        
        return features
    
    def _get_latest_value(self, data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]) -> Optional[float]:
        """
        Get latest value from a list of timestamped values.
        
        Args:
            data: List of timestamped values or single value
            
        Returns:
            Latest value or None if no values
        """
        if not data:
            return None
        
        if isinstance(data, list):
            # Sort by timestamp (descending)
            sorted_data = sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)
            if sorted_data:
                value = sorted_data[0].get("value")
                if isinstance(value, dict) and "value" in value:
                    return value["value"]
                return value
        elif isinstance(data, dict):
            value = data.get("value")
            if isinstance(value, dict) and "value" in value:
                return value["value"]
            return value
        
        return None
    
    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk level for a patient.
        
        Args:
            patient_data: Patient data
            
        Returns:
            Prediction result
        """
        try:
            # Extract features
            features = self._extract_features(patient_data)
            
            # Calculate risk score
            risk_score = 0.0
            for feature, value in features.items():
                if feature in self.feature_weights:
                    risk_score += value * self.feature_weights[feature]
            
            # Normalize risk score to [0, 1]
            risk_score = min(max(risk_score, 0.0), 1.0)
            
            # Determine risk level
            risk_level = "low-risk"
            if risk_score >= self.thresholds["high-risk"]:
                risk_level = "high-risk"
            elif risk_score >= self.thresholds["medium-risk"]:
                risk_level = "medium-risk"
            
            # Calculate risk scores for each level
            risk_scores = {
                "low-risk": max(0.0, 1.0 - risk_score / self.thresholds["medium-risk"]),
                "medium-risk": max(0.0, min(1.0, (risk_score - self.thresholds["low-risk"]) / (self.thresholds["high-risk"] - self.thresholds["low-risk"]))),
                "high-risk": max(0.0, (risk_score - self.thresholds["medium-risk"]) / (1.0 - self.thresholds["medium-risk"]))
            }
            
            # Identify top contributing factors
            contributing_factors = []
            for feature, weight in sorted(self.feature_weights.items(), key=lambda x: x[1], reverse=True):
                if feature in features and features[feature] > 0:
                    contributing_factors.append({
                        "name": feature,
                        "importance": weight,
                        "direction": "positive"
                    })
                    if len(contributing_factors) >= 5:
                        break
            
            # Return prediction result
            return {
                "prediction": risk_level,
                "probability": risk_score,
                "scores": risk_scores,
                "explanation": {
                    "factors": contributing_factors
                },
                "thresholds": self.thresholds
            }
        
        except Exception as e:
            logger.error(f"Error predicting risk: {str(e)}")
            raise 