#!/usr/bin/env python3
"""
Seed data script for MedConnect.

This script generates sample data for the MedConnect platform.
"""

import os
import sys
import json
import uuid
import random
import argparse
import logging
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Sample data
FIRST_NAMES = [
    "John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Jennifer",
    "William", "Elizabeth", "James", "Linda", "Richard", "Patricia", "Thomas",
    "Barbara", "Charles", "Mary", "Daniel", "Susan"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
    "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Thompson", "Garcia", "Martinez", "Robinson"
]

GENDERS = ["male", "female"]

MARITAL_STATUSES = ["single", "married", "divorced", "widowed"]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "San Francisco", "Charlotte", "Indianapolis",
    "Seattle", "Denver", "Washington"
]

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

OBSERVATION_TYPES = [
    "heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation",
    "lab-glucose", "lab-wbc", "lab-creatinine", "lab-bun", "lab-potassium", "lab-sodium",
    "condition-diabetes", "condition-hypertension", "condition-copd", "condition-chf",
    "condition-ckd", "condition-cad", "condition-stroke", "condition-cancer",
    "medication-insulin", "medication-antihypertensive", "medication-anticoagulant",
    "medication-steroid", "medication-opioid"
]

OBSERVATION_STATUSES = ["registered", "preliminary", "final", "amended", "corrected"]

OBSERVATION_UNITS = {
    "heart-rate": {"unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"},
    "respiratory-rate": {"unit": "breaths/minute", "system": "http://unitsofmeasure.org", "code": "/min"},
    "temperature": {"unit": "Celsius", "system": "http://unitsofmeasure.org", "code": "Cel"},
    "oxygen-saturation": {"unit": "%", "system": "http://unitsofmeasure.org", "code": "%"},
    "lab-glucose": {"unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
    "lab-wbc": {"unit": "10^3/uL", "system": "http://unitsofmeasure.org", "code": "10*3/uL"},
    "lab-creatinine": {"unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
    "lab-bun": {"unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
    "lab-potassium": {"unit": "mmol/L", "system": "http://unitsofmeasure.org", "code": "mmol/L"},
    "lab-sodium": {"unit": "mmol/L", "system": "http://unitsofmeasure.org", "code": "mmol/L"}
}

OBSERVATION_RANGES = {
    "heart-rate": (60, 100),
    "respiratory-rate": (12, 20),
    "temperature": (36.1, 37.8),
    "oxygen-saturation": (95, 100),
    "lab-glucose": (70, 140),
    "lab-wbc": (4.5, 11.0),
    "lab-creatinine": (0.6, 1.2),
    "lab-bun": (7, 20),
    "lab-potassium": (3.5, 5.0),
    "lab-sodium": (135, 145)
}


def generate_patient():
    """Generate a random patient."""
    gender = random.choice(GENDERS)
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    birth_date = (datetime.now() - timedelta(days=random.randint(365*18, 365*90))).strftime("%Y-%m-%d")
    
    return {
        "patient_id": str(uuid.uuid4()),
        "version": datetime.utcnow().isoformat(),
        "active": True,
        "identifiers": [
            {
                "system": "http://example.org/fhir/identifier/mrn",
                "value": f"MRN{random.randint(10000, 99999)}",
                "type": "MRN"
            }
        ],
        "name": [
            {
                "family": last_name,
                "given": [first_name],
                "use": "official"
            }
        ],
        "gender": gender,
        "birth_date": birth_date,
        "deceased": False,
        "address": [
            {
                "line": [f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Blvd', 'Rd', 'Ln'])}"],
                "city": random.choice(CITIES),
                "state": random.choice(STATES),
                "postal_code": f"{random.randint(10000, 99999)}",
                "country": "USA",
                "use": "home"
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "use": "home"
            },
            {
                "system": "email",
                "value": f"{first_name.lower()}.{last_name.lower()}@example.com",
                "use": "work"
            }
        ],
        "marital_status": random.choice(MARITAL_STATUSES),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def generate_observation(patient_id, observation_type=None):
    """Generate a random observation for a patient."""
    if observation_type is None:
        observation_type = random.choice(OBSERVATION_TYPES)
    
    effective_date = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
    
    observation = {
        "observation_id": str(uuid.uuid4()),
        "status": random.choice(OBSERVATION_STATUSES),
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs" if observation_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"] else "laboratory",
                        "display": "Vital Signs" if observation_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"] else "Laboratory"
                    }
                ],
                "text": "Vital Signs" if observation_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"] else "Laboratory"
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": observation_type,
                    "display": observation_type.replace("-", " ").title()
                }
            ],
            "text": observation_type.replace("-", " ").title()
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "patient_id": patient_id,
        "effective_date_time": effective_date,
        "timestamp": datetime.utcnow().isoformat(),
        "issued": datetime.utcnow().isoformat(),
        "observation_type": observation_type,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Add value based on observation type
    if observation_type.startswith("condition-") or observation_type.startswith("medication-"):
        observation["value_boolean"] = True
    elif observation_type == "blood-pressure":
        observation["component"] = [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }
                    ],
                    "text": "Systolic blood pressure"
                },
                "value_quantity": {
                    "value": random.randint(90, 180),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure"
                        }
                    ],
                    "text": "Diastolic blood pressure"
                },
                "value_quantity": {
                    "value": random.randint(60, 110),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            }
        ]
    elif observation_type in OBSERVATION_RANGES:
        min_val, max_val = OBSERVATION_RANGES[observation_type]
        value = round(random.uniform(min_val, max_val), 1)
        
        observation["value_quantity"] = {
            "value": value,
            "unit": OBSERVATION_UNITS[observation_type]["unit"],
            "system": OBSERVATION_UNITS[observation_type]["system"],
            "code": OBSERVATION_UNITS[observation_type]["code"]
        }
    
    return observation


def seed_dynamodb(patients, observations, args):
    """Seed DynamoDB with generated data."""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource("dynamodb", region_name=args.region)
        
        # Get table names
        patient_table_name = f"MedConnectStack-DynamoTablesPatientTable{args.environment.capitalize()}"
        observation_table_name = f"MedConnectStack-DynamoTablesObservationTable{args.environment.capitalize()}"
        
        # Get tables
        patient_table = dynamodb.Table(patient_table_name)
        observation_table = dynamodb.Table(observation_table_name)
        
        # Insert patients
        logger.info(f"Inserting {len(patients)} patients into {patient_table_name}")
        with patient_table.batch_writer() as batch:
            for patient in patients:
                batch.put_item(Item=patient)
        
        # Insert observations
        logger.info(f"Inserting {len(observations)} observations into {observation_table_name}")
        with observation_table.batch_writer() as batch:
            for observation in observations:
                batch.put_item(Item=observation)
        
        logger.info("Data seeding completed successfully")
    
    except ClientError as e:
        logger.error(f"Error seeding DynamoDB: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Seed data for MedConnect")
    parser.add_argument("--count", type=int, default=10, help="Number of patients to generate")
    parser.add_argument("--observations", type=int, default=5, help="Number of observations per patient")
    parser.add_argument("--environment", default="dev", help="Deployment environment")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--output", help="Output file for generated data (optional)")
    args = parser.parse_args()
    
    logger.info(f"Generating {args.count} patients with {args.observations} observations each")
    
    # Generate patients
    patients = [generate_patient() for _ in range(args.count)]
    
    # Generate observations
    observations = []
    for patient in patients:
        patient_observations = []
        
        # Generate vital signs for all patients
        for obs_type in ["heart-rate", "blood-pressure", "respiratory-rate", "temperature", "oxygen-saturation"]:
            patient_observations.append(generate_observation(patient["patient_id"], obs_type))
        
        # Generate random observations
        for _ in range(args.observations - 5):
            patient_observations.append(generate_observation(patient["patient_id"]))
        
        observations.extend(patient_observations)
    
    # Save to file if output is specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump({
                "patients": patients,
                "observations": observations
            }, f, indent=2)
        logger.info(f"Generated data saved to {args.output}")
    
    # Seed DynamoDB
    seed_dynamodb(patients, observations, args)


if __name__ == "__main__":
    main() 