"""
Focused API Tests for FastAPI Backend.

Uses FastAPI TestClient and mock objects so that all endpoint logic,
session isolation, validation, and error states are thoroughly tested
without requiring a live Ollama server or downloading external models.
"""

import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.api.main import app, get_ollama_client, get_session_manager
from src.api.session_manager import SessionManager


class TestBackendAPI(unittest.TestCase):
    """Test suite for FastAPI endpoints."""

    def setUp(self):
        self.mock_ollama = MagicMock()
        self.session_manager = SessionManager()

        # Override dependencies
        app.dependency_overrides[get_ollama_client] = lambda: self.mock_ollama
        app.dependency_overrides[get_session_manager] = lambda: self.session_manager

        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_health_endpoint_when_ollama_online(self):
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.host = "http://localhost:11434"

        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["ollama_reachable"])
        self.assertEqual(data["ollama_host"], "http://localhost:11434")

    def test_health_endpoint_when_ollama_offline(self):
        self.mock_ollama.is_server_online.return_value = False
        self.mock_ollama.host = None

        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertFalse(data["ollama_reachable"])

    def test_get_models_success(self):
        self.mock_ollama.list_local_models.return_value = ["llama3.2:3b", "qwen2.5:3b"]

        response = self.client.get("/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["models"], ["llama3.2:3b", "qwen2.5:3b"])

    def test_get_models_offline_raises_503(self):
        self.mock_ollama.list_local_models.side_effect = ConnectionError("Server offline")
        self.mock_ollama.host = "http://localhost:11434"

        response = self.client.get("/models")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Cannot connect to local Ollama server", response.json()["detail"])

    def test_post_chat_success_and_session_creation(self):
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.is_model_available.return_value = True
        self.mock_ollama.model_name = "llama3.2:3b"
        self.mock_ollama.chat.return_value = {
            "content": "A binary search tree maintains sorted order.",
            "latency_seconds": 0.42,
        }

        # Send without session_id (should auto-generate one)
        payload = {"message": "What is a BST?", "model": "llama3.2:3b"}
        response = self.client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("session_id", data)
        self.assertTrue(len(data["session_id"]) > 0)
        self.assertEqual(data["model"], "llama3.2:3b")
        self.assertEqual(data["response"], "A binary search tree maintains sorted order.")
        self.assertEqual(data["latency_seconds"], 0.42)

        # Verify message was stored in session history
        history = self.session_manager.get_history(data["session_id"])
        self.assertEqual(len(history), 3)  # [system, user, assistant]
        self.assertEqual(history[1]["content"], "What is a BST?")
        self.assertEqual(history[2]["content"], "A binary search tree maintains sorted order.")

    def test_post_chat_multi_turn_session_continuity(self):
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.is_model_available.return_value = True
        self.mock_ollama.model_name = "llama3.2:3b"

        # Turn 1
        self.mock_ollama.chat.return_value = {"content": "Turn 1 answer", "latency_seconds": 0.2}
        resp1 = self.client.post("/chat", json={"message": "First message"})
        session_id = resp1.json()["session_id"]

        # Turn 2 using the same session_id
        self.mock_ollama.chat.return_value = {"content": "Turn 2 answer", "latency_seconds": 0.3}
        resp2 = self.client.post("/chat", json={"message": "Second message", "session_id": session_id})
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["session_id"], session_id)

        # Inspect history sent to client.chat on Turn 2
        calls = self.mock_ollama.chat.call_args_list
        turn2_messages = calls[1].kwargs["messages"]
        self.assertEqual(len(turn2_messages), 4)  # [system, user1, assist1, user2]
        self.assertEqual(turn2_messages[1]["content"], "First message")
        self.assertEqual(turn2_messages[2]["content"], "Turn 1 answer")
        self.assertEqual(turn2_messages[3]["content"], "Second message")

    def test_post_chat_session_isolation(self):
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.is_model_available.return_value = True
        self.mock_ollama.model_name = "llama3.2:3b"
        self.mock_ollama.chat.return_value = {"content": "response", "latency_seconds": 0.1}

        # Create two distinct sessions
        r1 = self.client.post("/chat", json={"message": "User A message", "session_id": "session-A"})
        r2 = self.client.post("/chat", json={"message": "User B message", "session_id": "session-B"})

        h_a = self.session_manager.get_history("session-A")
        h_b = self.session_manager.get_history("session-B")

        self.assertEqual(h_a[1]["content"], "User A message")
        self.assertEqual(h_b[1]["content"], "User B message")
        self.assertNotEqual(h_a, h_b)

    def test_post_chat_missing_model_raises_404(self):
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.is_model_available.return_value = False
        self.mock_ollama.list_local_models.return_value = ["llama3.2:3b"]

        response = self.client.post("/chat", json={"message": "Hello", "model": "nonexistent:latest"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("is not installed locally", response.json()["detail"])

    def test_post_chat_server_offline_raises_503(self):
        self.mock_ollama.is_server_online.return_value = False

        response = self.client.post("/chat", json={"message": "Hello"})
        self.assertEqual(response.status_code, 503)

    def test_post_chat_empty_message_raises_422(self):
        response = self.client.post("/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 422)

    def test_delete_history_specific_session(self):
        self.session_manager.get_or_create_session("sess-1")
        self.session_manager.add_message("sess-1", "user", "Hello")

        response = self.client.delete("/chat/history?session_id=sess-1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["cleared"])
        self.assertEqual(data["session_id"], "sess-1")

        # History should be reset to system prompt only
        history = self.session_manager.get_history("sess-1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "system")

    def test_delete_history_nonexistent_session_raises_404(self):
        response = self.client.delete("/chat/history?session_id=fake-session")
        self.assertEqual(response.status_code, 404)

    def test_delete_history_all_sessions(self):
        self.session_manager.get_or_create_session("sess-1")
        self.session_manager.get_or_create_session("sess-2")

        response = self.client.delete("/chat/history")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["session_id"])
        self.assertEqual(len(self.session_manager.list_active_sessions()), 0)

    def test_metrics_endpoint(self):
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("system", data)
        self.assertIn("total_ram_gb", data["system"])
        self.assertIn("ollama_rss_mb", data)


if __name__ == "__main__":
    unittest.main()
