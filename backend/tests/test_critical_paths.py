"""Critical path tests for Caerus API.

These tests cover the main user flows:
- Authentication (signup, login, profile)
- Pitch management (create, publish, feed)
- Q&A threads (create, message, status)
- Subscriptions (IAP verification)
- Talent (pitches, approval)
"""
import pytest
from unittest.mock import patch, MagicMock

API = "/api/v1"


class TestAuthenticationFlow:
    """Test authentication critical paths."""

    def test_founder_signup_creates_user(self, client, unique_id):
        """Test that founder signup creates a user with correct role."""
        response = client.post(
            f"{API}/auth/signup",
            json={
                "firebase_token": f"dev_test_founder_{unique_id}",
                "email": f"founder_{unique_id}@test.com",
                "role": "founder"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "founder"
        assert "token" in data
        assert data["user"]["email"] == f"founder_{unique_id}@test.com"

    def test_investor_signup_creates_user(self, client, unique_id):
        """Test that investor signup creates a user with correct role."""
        response = client.post(
            f"{API}/auth/signup",
            json={
                "firebase_token": f"dev_test_investor_{unique_id}",
                "email": f"investor_{unique_id}@test.com",
                "role": "investor"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "investor"
        assert "token" in data

    def test_talent_signup_creates_pending_user(self, client, unique_id):
        """Test that talent signup creates user with pending status."""
        response = client.post(
            f"{API}/auth/signup",
            json={
                "firebase_token": f"dev_test_talent_{unique_id}",
                "email": f"talent_{unique_id}@test.com",
                "role": "talent"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "talent"

        # Check profile is pending
        token = data["token"]
        me_response = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["profile"]["status"] == "pending"

    def test_me_endpoint_returns_user_data(self, client, founder_token):
        """Test /auth/me returns correct user data."""
        response = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data or "email" in data
        user = data.get("user", data)
        assert user["role"] == "founder"

    def test_unauthorized_access_rejected(self, client):
        """Test that requests without token are rejected."""
        response = client.get(f"{API}/auth/me")
        assert response.status_code in [401, 403]

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected."""
        response = client.get(
            f"{API}/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code in [401, 403]


class TestInvestorOnboarding:
    """Test investor onboarding flow."""

    def test_investor_can_complete_onboarding(self, client, investor_token):
        """Test investor can complete onboarding with preferences."""
        response = client.post(
            f"{API}/auth/onboarding/investor",
            json={
                "investor_type": "angel",
                "sectors": ["SaaS", "AI/ML"],
                "stages": ["seed", "series_a"],
                "geographies": ["US", "UK"],
                "ticket_size_min": 25000,
                "ticket_size_max": 100000
            },
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("message") or data.get("onboarding_completed")


class TestFounderOnboarding:
    """Test founder onboarding flow."""

    def test_founder_can_complete_onboarding(self, client, founder_token):
        """Test founder can complete onboarding."""
        response = client.post(
            f"{API}/auth/onboarding/founder",
            json={
                "seeking_investor_types": ["angel", "vc"],
                "desired_check_size_min": 50000,
                "desired_check_size_max": 500000,
                "value_add_preferences": ["network", "mentorship"]
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200


class TestTalentOnboarding:
    """Test talent onboarding flow."""

    def test_talent_can_complete_onboarding(self, client, talent_token):
        """Test talent can complete onboarding."""
        response = client.post(
            f"{API}/auth/onboarding/talent",
            json={
                "job_title_seeking": "Software Engineer",
                "skills": ["Python", "React", "AWS"],
                "experience_level": "senior",
                "compensation_type": "salary_equity",
                "availability": "immediate",
                "remote_preference": "hybrid"
            },
            headers={"Authorization": f"Bearer {talent_token}"}
        )

        assert response.status_code == 200


class TestStartupManagement:
    """Test startup CRUD operations."""

    def test_founder_can_create_startup(self, client, founder_token, unique_id):
        """Test founder can create a startup."""
        response = client.post(
            f"{API}/startups",
            json={
                "name": f"Test Startup {unique_id}",
                "tagline": "Testing startup creation",
                "sectors": ["SaaS"],
                "stage": "seed"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == f"Test Startup {unique_id}"
        assert "id" in data

    def test_founder_can_list_startups(self, client, founder_token, test_startup):
        """Test founder can list their startups."""
        response = client.get(
            f"{API}/startups",
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_founder_can_update_startup(self, client, founder_token, test_startup):
        """Test founder can update startup details."""
        startup_id = test_startup["id"]
        response = client.put(
            f"{API}/startups/{startup_id}",
            json={
                "tagline": "Updated tagline"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tagline"] == "Updated tagline"


class TestPitchFlow:
    """Test pitch creation and feed flow."""

    def test_founder_can_get_upload_url(self, client, founder_token, test_startup):
        """Test founder can get signed upload URL for pitch video."""
        startup_id = test_startup["id"]
        response = client.post(
            f"{API}/pitches/upload-url",
            json={
                "startup_id": startup_id,
                "type": "30s_free",
                "filename": "test_pitch.mp4",
                "content_type": "video/mp4"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "video_id" in data or "pitch_id" in data

    def test_investor_can_view_feed(self, client, investor_token):
        """Test investor can view pitch feed."""
        response = client.get(
            f"{API}/pitches/feed",
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "pitches" in data or isinstance(data, list)

    def test_founder_can_view_dashboard(self, client, founder_token):
        """Test founder can view their dashboard."""
        response = client.get(
            f"{API}/pitches/founder/dashboard",
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200


class TestQuestionTemplates:
    """Test question template management."""

    def test_investor_gets_default_templates(self, client, investor_token):
        """Test investor has default question templates."""
        response = client.get(
            f"{API}/questions/templates",
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        templates = data.get("templates", data)
        assert len(templates) >= 5  # Default templates

    def test_investor_can_create_template(self, client, investor_token):
        """Test investor can create custom question template."""
        response = client.post(
            f"{API}/questions/templates",
            json={
                "question_text": "What is your customer acquisition cost?"
            },
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question_text"] == "What is your customer acquisition cost?"
        assert data["is_default"] == False

    def test_investor_can_delete_custom_template(self, client, investor_token):
        """Test investor can delete their custom template."""
        # First create a template
        create_response = client.post(
            f"{API}/questions/templates",
            json={
                "question_text": "Template to delete"
            },
            headers={"Authorization": f"Bearer {investor_token}"}
        )
        template_id = create_response.json()["id"]

        # Then delete it
        delete_response = client.delete(
            f"{API}/questions/templates/{template_id}",
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert delete_response.status_code in [200, 204]


class TestProfileManagement:
    """Test profile update and management."""

    def test_user_can_update_profile(self, client, founder_token):
        """Test user can update their profile."""
        response = client.put(
            f"{API}/auth/profile",
            json={
                "full_name": "Test Founder",
                "company_name": "Test Company"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200

    def test_user_can_complete_profile(self, client, founder_token):
        """Test user can complete profile step."""
        response = client.post(
            f"{API}/auth/profile/complete",
            json={
                "full_name": "Test User",
                "company_name": "Test Corp",
                "linkedin_url": "https://linkedin.com/in/testuser"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200


class TestSubscriptionEndpoints:
    """Test subscription-related endpoints."""

    def test_iap_endpoints_registered(self, client):
        """Test IAP-related endpoints are registered."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]

        # Check IAP verification endpoints exist
        assert f"{API}/iap/verify-subscription" in paths
        assert f"{API}/iap/verify-unlock" in paths

    def test_iap_verify_endpoint_exists(self, client, investor_token):
        """Test IAP verification endpoint is accessible."""
        # Should reject invalid receipt but endpoint should exist
        response = client.post(
            f"{API}/iap/verify-subscription",
            json={
                "receipt_data": "invalid_receipt",
                "transaction_id": "test_txn",
                "product_id": "com.caerus.investor.monthly"
            },
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        # Should fail with bad receipt, but not 404
        assert response.status_code != 404


class TestTalentPitchFlow:
    """Test talent pitch creation and viewing."""

    def test_pending_talent_cannot_upload(self, client, talent_token):
        """Test that pending talent cannot upload pitch (needs approval first)."""
        response = client.post(
            f"{API}/talent-pitches/upload-url",
            json={
                "filename": "talent_pitch.mp4",
                "content_type": "video/mp4"
            },
            headers={"Authorization": f"Bearer {talent_token}"}
        )

        # Pending talent should be forbidden from uploading
        assert response.status_code == 403

    def test_talent_feed_accessible(self, client, investor_token):
        """Test talent feed is accessible to investors."""
        response = client.get(
            f"{API}/talent-pitches/feed",
            headers={"Authorization": f"Bearer {investor_token}"}
        )

        assert response.status_code == 200

    def test_talent_can_view_dashboard(self, client, talent_token):
        """Test talent can view their dashboard."""
        response = client.get(
            f"{API}/talent-pitches/dashboard",
            headers={"Authorization": f"Bearer {talent_token}"}
        )

        assert response.status_code == 200


class TestSupportFlow:
    """Test support ticket functionality."""

    def test_user_can_use_ai_chat(self, client, founder_token):
        """Test user can use AI support chat."""
        response = client.post(
            f"{API}/support/ai-chat",
            json={
                "content": "How do I record a pitch video?"
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_user_can_create_support_ticket(self, client, founder_token):
        """Test user can create support ticket."""
        response = client.post(
            f"{API}/support/tickets",
            json={
                "subject": "Test Support Request",
                "message": "This is a test support message."
            },
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Response can have ticket nested or at top level
        ticket = data.get("ticket", data)
        assert "id" in ticket

    def test_user_can_list_tickets(self, client, founder_token):
        """Test user can list their support tickets."""
        response = client.get(
            f"{API}/support/tickets",
            headers={"Authorization": f"Bearer {founder_token}"}
        )

        assert response.status_code == 200
