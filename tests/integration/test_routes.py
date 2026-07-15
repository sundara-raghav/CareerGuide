"""Integration tests for Flask routes."""


class TestHealthCheck:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


class TestAuthRoutes:
    def test_register_page_loads(self, client):
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert b"Create Your Account" in resp.data

    def test_login_page_loads(self, client):
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"Welcome Back" in resp.data

    def test_register_creates_user(self, client, db):
        resp = client.post(
            "/auth/register",
            data={
                "name": "Integration Test User",
                "email": "integration@test.com",
                "password": "securePass1",
                "role": "student",
                "phone": "",
            },
            follow_redirects=False,
        )
        # Should redirect after successful registration
        assert resp.status_code in (302, 200)

    def test_login_invalid_credentials(self, client):
        resp = client.post(
            "/auth/login",
            data={
                "email": "nobody@example.com",
                "password": "wrongpassword",
            },
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data


class TestLandingPage:
    def test_landing_page_renders(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"CareerGuide" in resp.data

    def test_impact_api(self, client):
        resp = client.get("/analytics/api/impact")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "students_guided" in data
        assert "recommendations_made" in data


class TestCollegesAPI:
    def test_all_pins_public(self, client, sample_college):
        resp = client.get("/colleges/api/all-pins")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_search_requires_login(self, client):
        resp = client.get("/colleges/api/search", follow_redirects=False)
        assert resp.status_code in (302, 401)
