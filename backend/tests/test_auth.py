import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_music.db")

from fastapi.testclient import TestClient

from app.main import app


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_public_song_endpoints_work_without_auth(self):
        response = self.client.get("/api/songs")
        self.assertEqual(response.status_code, 200)

        search_response = self.client.get("/api/songs", params={"search": "test"})
        self.assertEqual(search_response.status_code, 200)

    def test_register_login_and_protected_access(self):
        register_response = self.client.post(
            "/api/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        self.assertEqual(register_response.status_code, 200)

        login_response = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "secret123"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]

        me_response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["username"], "alice")

        protected_response = self.client.post(
            "/api/playlists",
            json={"name": "My playlist", "description": "Demo"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(protected_response.status_code, 200)

        unauthorized_response = self.client.post(
            "/api/playlists",
            json={"name": "Blocked", "description": "Demo"},
        )
        self.assertEqual(unauthorized_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
