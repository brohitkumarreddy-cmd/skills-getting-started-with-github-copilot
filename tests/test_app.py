"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for fetching activities"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert len(activities) == 9

    def test_activity_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]

        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for signing up for activities"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Signed up" in result["message"]
        assert "test@mergington.edu" in result["message"]

    def test_signup_verification(self, client):
        """Test that signup actually adds the participant"""
        # Sign up
        client.post("/activities/Tennis Club/signup?email=newstudent@mergington.edu")

        # Verify in activities list
        response = client.get("/activities")
        tennis_club = response.json()["Tennis Club"]
        assert "newstudent@mergington.edu" in tennis_club["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_duplicate_registration(self, client):
        """Test preventing duplicate signup for same activity"""
        email = "duplicate@mergington.edu"

        # First signup should succeed
        response1 = client.post(
            f"/activities/Drama Club/signup?email={email}"
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            f"/activities/Drama Club/signup?email={email}"
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]


class TestUnregisterFromActivity:
    """Tests for unregistering from activities"""

    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        email = "unreg@mergington.edu"

        # First sign up
        client.post(f"/activities/Art Studio/signup?email={email}")

        # Then unregister
        response = client.post(
            f"/activities/Art Studio/unregister?email={email}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_verification(self, client):
        """Test that unregister actually removes the participant"""
        email = "removetest@mergington.edu"

        # Sign up
        client.post(f"/activities/Science Club/signup?email={email}")

        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Science Club"]["participants"]

        # Unregister
        client.post(f"/activities/Science Club/unregister?email={email}")

        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Science Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Fake Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_not_signed_up(self, client):
        """Test unregistering when not signed up"""
        response = client.post(
            "/activities/Debate Team/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static HTML"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestIntegration:
    """Integration tests for complete user workflows"""

    def test_full_signup_workflow(self, client):
        """Test a complete signup workflow"""
        email = "workflow@mergington.edu"
        activity = "Programming Class"

        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])

        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200

        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1

    def test_signup_unregister_workflow(self, client):
        """Test signup followed by unregister"""
        email = "workflow2@mergington.edu"
        activity = "Gym Class"

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Verify signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert email in participants
        initial_count = len(participants)

        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")

        # Verify unregistered
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()[activity]["participants"]
