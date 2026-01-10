"""Shared pytest fixtures for Caerus API tests."""
import uuid
import pytest
from fastapi.testclient import TestClient

from main import app

# API prefix
API = "/api/v1"


@pytest.fixture(scope="session")
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def unique_id():
    """Generate a unique ID for test data."""
    return str(uuid.uuid4())[:8]


@pytest.fixture
def founder_auth(client, unique_id):
    """Create a test founder and return auth data."""
    response = client.post(
        f"{API}/auth/signup",
        json={
            "firebase_token": f"dev_test_founder_{unique_id}",
            "email": f"test_founder_{unique_id}@test.com",
            "role": "founder"
        }
    )

    if response.status_code != 200:
        pytest.skip(f"Could not create test founder: {response.text}")

    return response.json()


@pytest.fixture
def founder_token(founder_auth):
    """Get just the token from founder auth."""
    return founder_auth["token"]


@pytest.fixture
def investor_auth(client, unique_id):
    """Create a test investor and return auth data."""
    response = client.post(
        f"{API}/auth/signup",
        json={
            "firebase_token": f"dev_test_investor_{unique_id}",
            "email": f"test_investor_{unique_id}@test.com",
            "role": "investor"
        }
    )

    if response.status_code != 200:
        pytest.skip(f"Could not create test investor: {response.text}")

    return response.json()


@pytest.fixture
def investor_token(investor_auth):
    """Get just the token from investor auth."""
    return investor_auth["token"]


@pytest.fixture
def talent_auth(client, unique_id):
    """Create a test talent user and return auth data."""
    response = client.post(
        f"{API}/auth/signup",
        json={
            "firebase_token": f"dev_test_talent_{unique_id}",
            "email": f"test_talent_{unique_id}@test.com",
            "role": "talent"
        }
    )

    if response.status_code != 200:
        pytest.skip(f"Could not create test talent: {response.text}")

    return response.json()


@pytest.fixture
def talent_token(talent_auth):
    """Get just the token from talent auth."""
    return talent_auth["token"]


@pytest.fixture
def auth_headers(founder_token):
    """Return auth headers for founder."""
    return {"Authorization": f"Bearer {founder_token}"}


@pytest.fixture
def investor_headers(investor_token):
    """Return auth headers for investor."""
    return {"Authorization": f"Bearer {investor_token}"}


@pytest.fixture
def talent_headers(talent_token):
    """Return auth headers for talent."""
    return {"Authorization": f"Bearer {talent_token}"}


@pytest.fixture
def test_startup(client, founder_token, unique_id):
    """Create a test startup and return its data."""
    response = client.post(
        f"{API}/startups",
        json={
            "name": f"Test Startup {unique_id}",
            "tagline": "A test startup for testing",
            "sectors": ["SaaS", "AI"],
            "stage": "seed",
            "location": "San Francisco"
        },
        headers={"Authorization": f"Bearer {founder_token}"}
    )

    if response.status_code != 200:
        pytest.skip(f"Could not create test startup: {response.text}")

    return response.json()
