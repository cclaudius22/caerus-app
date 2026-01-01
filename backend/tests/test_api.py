"""API integration tests for Caerus backend."""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# API prefix
API = "/api/v1"


class TestHealthCheck:
    """Test basic API health."""

    def test_root_endpoint(self):
        """Test API root returns correct message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Caerus API"
        assert data["version"] == "1.0.0"

    def test_docs_accessible(self):
        """Test API docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert f"{API}/auth/signup" in data["paths"]
        assert f"{API}/auth/login" in data["paths"]


class TestAPIRoutes:
    """Test that all expected API routes exist."""

    def test_auth_routes_exist(self):
        """Verify auth routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/auth/signup" in paths
        assert f"{API}/auth/login" in paths
        assert f"{API}/auth/me" in paths
        assert f"{API}/auth/onboarding/investor" in paths
        assert f"{API}/auth/onboarding/founder" in paths

    def test_startup_routes_exist(self):
        """Verify startup routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/startups" in paths

    def test_pitch_routes_exist(self):
        """Verify pitch routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/pitches/upload-url" in paths
        assert f"{API}/pitches/feed" in paths
        assert f"{API}/pitches/founder/dashboard" in paths

    def test_qa_routes_exist(self):
        """Verify Q&A routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/qa/threads" in paths

    def test_question_template_routes_exist(self):
        """Verify question template routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/questions/templates" in paths
        assert f"{API}/questions/send-questions" in paths

    def test_talent_routes_exist(self):
        """Verify talent routes are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        # Talent pitch routes
        assert f"{API}/talent-pitches/upload-url" in paths
        assert f"{API}/talent-pitches/feed" in paths
        assert f"{API}/talent-pitches/my-pitch" in paths
        assert f"{API}/talent-pitches/dashboard" in paths

        # Talent Q&A routes
        assert f"{API}/talent-qa/threads" in paths

        # Admin routes
        assert f"{API}/admin/talent/pending" in paths
        assert f"{API}/admin/talent/stats" in paths

    def test_auth_onboarding_talent_route_exists(self):
        """Verify talent onboarding route is registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        assert f"{API}/auth/onboarding/talent" in paths


class TestGCSService:
    """Test GCS service functionality."""

    def test_gcs_service_initialization(self):
        """Test that GCS service can be initialized."""
        from app.services.gcs import GCSService
        service = GCSService()
        assert service is not None

    def test_gcs_credentials_loaded(self):
        """Test that service account credentials are loaded."""
        from app.services.gcs import GCSService
        service = GCSService()
        creds = service.credentials
        assert creds is not None
        assert hasattr(creds, 'service_account_email')

    def test_gcs_upload_url_generation(self):
        """Test generating signed upload URL."""
        from app.services.gcs import GCSService
        service = GCSService()
        url, key = service.generate_upload_url("test_video.mp4")

        assert url.startswith("https://storage.googleapis.com")
        assert "caerus-pitch-videos" in url
        assert "test_video.mp4" in key
        assert key.startswith("videos/")

    def test_gcs_download_url_generation(self):
        """Test generating signed download URL."""
        from app.services.gcs import GCSService
        service = GCSService()
        test_key = "videos/test-uuid/test.mp4"
        url = service.generate_download_url(test_key)

        assert url.startswith("https://storage.googleapis.com")
        assert "caerus-pitch-videos" in url

    def test_gcs_upload_url_custom_content_type(self):
        """Test upload URL with custom content type."""
        from app.services.gcs import GCSService
        service = GCSService()
        url, key = service.generate_upload_url(
            "test.mov",
            content_type="video/quicktime"
        )
        assert url.startswith("https://storage.googleapis.com")

    def test_gcs_object_not_exists(self):
        """Test checking non-existent object."""
        from app.services.gcs import GCSService
        service = GCSService()
        exists = service.object_exists("videos/nonexistent/fake.mp4")
        assert exists == False


class TestEndToEndWithLiveDB:
    """
    Integration tests using the live Supabase database.
    These tests create real data.
    """

    @pytest.fixture
    def founder_auth(self):
        """Create a test founder and return auth token."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

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
    def investor_auth(self):
        """Create a test investor and return auth token."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

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

    def test_founder_signup_returns_token(self, founder_auth):
        """Test that founder signup returns a token."""
        assert founder_auth["user"]["role"] == "founder"
        assert "token" in founder_auth

    def test_investor_signup_returns_token(self, investor_auth):
        """Test that investor signup returns a token."""
        assert investor_auth["user"]["role"] == "investor"
        assert "token" in investor_auth

    def test_founder_can_create_startup(self, founder_auth):
        """Test founder can create a startup."""
        token = founder_auth["token"]

        response = client.post(
            f"{API}/startups",
            json={
                "name": "Test Startup",
                "tagline": "Testing is fun",
                "sector": "SaaS",
                "stage": "seed"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Startup"
        assert "id" in data

    def test_investor_gets_default_questions(self, investor_auth):
        """Test that investors get default question templates."""
        token = investor_auth["token"]

        response = client.get(
            f"{API}/questions/templates",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        templates = data.get("templates", data)  # Handle both formats
        assert len(templates) >= 5  # Should have default templates

    def test_me_endpoint_returns_user(self, founder_auth):
        """Test /auth/me returns correct user data."""
        token = founder_auth["token"]

        response = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Handle nested or flat response
        user = data.get("user", data)
        assert user["role"] == "founder"
        assert "email" in user

    def test_talent_signup_returns_pending_status(self):
        """Test that talent signup returns pending status."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

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

        data = response.json()
        assert data["user"]["role"] == "talent"
        assert "token" in data

        # Verify profile is pending
        token = data["token"]
        me_response = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["profile"]["status"] == "pending"
