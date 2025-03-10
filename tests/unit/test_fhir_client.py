import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from core.fhir.client import FHIRClient
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation


@pytest.fixture
def fhir_client():
    """Create a FHIR client for testing."""
    return FHIRClient(base_url="https://example.com/fhir")


@pytest.fixture
def mock_patient_data():
    """Create mock patient data for testing."""
    return {
        "resourceType": "Patient",
        "id": "123",
        "meta": {
            "versionId": "1",
            "lastUpdated": "2023-01-01T12:00:00Z"
        },
        "active": True,
        "name": [
            {
                "family": "Smith",
                "given": ["John"]
            }
        ],
        "gender": "male",
        "birthDate": "1970-01-01"
    }


@pytest.fixture
def mock_observation_data():
    """Create mock observation data for testing."""
    return {
        "resourceType": "Observation",
        "id": "456",
        "meta": {
            "versionId": "1",
            "lastUpdated": "2023-01-01T12:00:00Z"
        },
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }
            ],
            "text": "Heart rate"
        },
        "subject": {
            "reference": "Patient/123"
        },
        "effectiveDateTime": "2023-01-01T12:00:00Z",
        "valueQuantity": {
            "value": 80,
            "unit": "beats/minute",
            "system": "http://unitsofmeasure.org",
            "code": "/min"
        }
    }


@pytest.mark.asyncio
async def test_get_resource(fhir_client, mock_patient_data):
    """Test getting a resource by ID."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_patient_data
        mock_get.return_value = mock_response
        
        result = await fhir_client.get_resource("Patient", "123")
        
        mock_get.assert_called_once_with(
            "https://example.com/fhir/Patient/123",
            headers=fhir_client.headers
        )
        assert result == mock_patient_data


@pytest.mark.asyncio
async def test_search_resources(fhir_client, mock_patient_data):
    """Test searching for resources."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "resource": mock_patient_data
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = await fhir_client.search_resources("Patient", {"name": "Smith"})
        
        mock_get.assert_called_once_with(
            "https://example.com/fhir/Patient",
            params={"name": "Smith"},
            headers=fhir_client.headers
        )
        assert len(result) == 1
        assert result[0] == mock_patient_data


@pytest.mark.asyncio
async def test_create_resource(fhir_client, mock_patient_data):
    """Test creating a resource."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_patient_data
        mock_post.return_value = mock_response
        
        result = await fhir_client.create_resource("Patient", mock_patient_data)
        
        mock_post.assert_called_once_with(
            "https://example.com/fhir/Patient",
            json=mock_patient_data,
            headers=fhir_client.headers
        )
        assert result == mock_patient_data


@pytest.mark.asyncio
async def test_update_resource(fhir_client, mock_patient_data):
    """Test updating a resource."""
    with patch("httpx.AsyncClient.put") as mock_put:
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_patient_data
        mock_put.return_value = mock_response
        
        result = await fhir_client.update_resource("Patient", "123", mock_patient_data)
        
        mock_put.assert_called_once_with(
            "https://example.com/fhir/Patient/123",
            json=mock_patient_data,
            headers=fhir_client.headers
        )
        assert result == mock_patient_data


@pytest.mark.asyncio
async def test_delete_resource(fhir_client):
    """Test deleting a resource."""
    with patch("httpx.AsyncClient.delete") as mock_delete:
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_delete.return_value = mock_response
        
        await fhir_client.delete_resource("Patient", "123")
        
        mock_delete.assert_called_once_with(
            "https://example.com/fhir/Patient/123",
            headers=fhir_client.headers
        )


@pytest.mark.asyncio
async def test_get_patient(fhir_client, mock_patient_data):
    """Test getting a patient by ID."""
    with patch.object(fhir_client, "get_resource") as mock_get_resource:
        mock_get_resource.return_value = mock_patient_data
        
        result = await fhir_client.get_patient("123")
        
        mock_get_resource.assert_called_once_with("Patient", "123")
        assert isinstance(result, Patient)
        assert result.id == "123"
        assert result.name[0].family == "Smith"


@pytest.mark.asyncio
async def test_get_observation(fhir_client, mock_observation_data):
    """Test getting an observation by ID."""
    with patch.object(fhir_client, "get_resource") as mock_get_resource:
        mock_get_resource.return_value = mock_observation_data
        
        result = await fhir_client.get_observation("456")
        
        mock_get_resource.assert_called_once_with("Observation", "456")
        assert isinstance(result, Observation)
        assert result.id == "456"
        assert result.valueQuantity.value == 80 