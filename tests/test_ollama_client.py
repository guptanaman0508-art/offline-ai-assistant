"""Tests for Phase 1 components (src.ollama_client and CLI structure)."""

import unittest
from unittest.mock import MagicMock, patch
from src.ollama_client import OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Unit tests verifying OllamaClient logic and error handling."""

    def test_default_initialization(self):
        client = OllamaClient()
        self.assertEqual(client.model_name, "llama3.2:3b")
        self.assertEqual(client.timeout, 60.0)

    @patch("src.ollama_client.ollama.Client")
    def test_is_server_online_true(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.list.return_value = MagicMock(models=[])

        client = OllamaClient()
        self.assertTrue(client.is_server_online())

    @patch("src.ollama_client.ollama.Client")
    def test_is_server_online_false(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.list.side_effect = Exception("Connection refused")

        client = OllamaClient()
        self.assertFalse(client.is_server_online())

    @patch("src.ollama_client.ollama.Client")
    def test_list_local_models(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        item1 = MagicMock()
        item1.model = "llama3.2:3b"
        item2 = MagicMock()
        item2.model = "mistral:latest"
        mock_instance.list.return_value = MagicMock(models=[item1, item2])

        client = OllamaClient()
        models = client.list_local_models()
        self.assertEqual(models, ["llama3.2:3b", "mistral:latest"])
        self.assertTrue(client.is_model_available("llama3.2:3b"))
        self.assertFalse(client.is_model_available("phi3:mini"))

    @patch("src.ollama_client.ollama.Client")
    def test_chat_success_and_latency(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        
        # Mock list() for model availability check
        model_item = MagicMock()
        model_item.model = "llama3.2:3b"
        mock_instance.list.return_value = MagicMock(models=[model_item])

        # Mock chat response
        mock_response = MagicMock()
        mock_response.message.content = "Hello from local Ollama!"
        mock_instance.chat.return_value = mock_response

        client = OllamaClient(model_name="llama3.2:3b")
        result = client.chat(messages=[{"role": "user", "content": "Hi"}])

        self.assertEqual(result["content"], "Hello from local Ollama!")
        self.assertIn("latency_seconds", result)
        self.assertGreaterEqual(result["latency_seconds"], 0.0)

    @patch("src.ollama_client.ollama.Client")
    def test_chat_missing_model_raises_lookup_error(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.list.return_value = MagicMock(models=[])

        client = OllamaClient(model_name="nonexistent-model")
        with self.assertRaises(LookupError):
            client.chat(messages=[{"role": "user", "content": "Hi"}])


if __name__ == "__main__":
    unittest.main()
