"""
Ollama Client Module for Offline AI Assistant.

Handles communication with the local Ollama instance using the official Ollama SDK.
Gracefully manages connection errors, missing models, and request timeouts.
"""

import time
from typing import Any, Dict, List, Optional
import ollama
from ollama import ResponseError


class OllamaClient:
    """Wrapper client around the official Ollama Python library."""

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        host: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize the Ollama client.

        :param model_name: Target model tag (e.g. 'llama3.2:3b', 'mistral', 'qwen2.5:3b')
        :param host: Optional custom host URI (defaults to Ollama's http://localhost:11434)
        :param timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.host = host
        self.timeout = timeout
        # Using ollama.Client allows configuring custom hosts and request timeouts cleanly
        self._client = ollama.Client(host=host, timeout=timeout)

    def is_server_online(self) -> bool:
        """Check if the local Ollama daemon/server is running and reachable."""
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        """
        Retrieve a list of model names currently installed on the local Ollama server.

        :return: List of model names/tags.
        """
        try:
            response = self._client.list()
            # ollama.list() returns a ListResponse with a models attribute
            models = getattr(response, "models", [])
            model_names = []
            for item in models:
                # Handle either object attributes or dict mapping
                if hasattr(item, "model"):
                    model_names.append(item.model)
                elif isinstance(item, dict) and "model" in item:
                    model_names.append(item["model"])
                elif hasattr(item, "name"):
                    model_names.append(item.name)
            return model_names
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to Ollama server at {self.host or 'http://localhost:11434'}. "
                "Ensure Ollama is running (`ollama serve` or open Ollama.app)."
            ) from e

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model is installed locally in Ollama.

        :param model_name: Name of model to check (defaults to self.model_name)
        :return: True if model is pulled locally, False otherwise.
        """
        target = model_name or self.model_name
        installed = self.list_local_models()
        # Tags can match either exact name or base name (e.g. 'llama3.2:3b' vs 'llama3.2:3b')
        for m in installed:
            if m == target or m == f"{target}:latest" or target == f"{m}:latest":
                return True
        return False

    def chat(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        format: Optional[Any] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a conversation history to the model and return the response along with latency metrics.

        :param messages: List of message dicts: [{'role': 'user'|'assistant'|'system', 'content': '...'}]
        :param model_name: Optional model override
        :param format: Optional output format ('json' or a JSON schema dict)
        :param options: Optional model generation options (e.g. {'temperature': 0})
        :return: Dict containing 'content' (str) and 'latency_seconds' (float)
        """
        target_model = model_name or self.model_name

        # 1. Pre-flight check: verify model is available locally
        if not self.is_model_available(target_model):
            raise LookupError(
                f"Model '{target_model}' is not installed locally.\n"
                f"To pull it, run in your terminal: ollama pull {target_model}\n"
                f"Or choose from available models: {self.list_local_models() or 'None found'}"
            )

        # 2. Measure latency around the inference call
        start_time = time.perf_counter()
        try:
            chat_kwargs: Dict[str, Any] = {
                "model": target_model,
                "messages": messages,
            }
            if format is not None:
                chat_kwargs["format"] = format
            if options is not None:
                chat_kwargs["options"] = options

            response = self._client.chat(**chat_kwargs)
            elapsed_time = time.perf_counter() - start_time


            # Extract text content safely from the SDK response
            # Response in ollama-python can be a ChatResponse object or dict
            if hasattr(response, "message") and hasattr(response.message, "content"):
                content = response.message.content
            elif isinstance(response, dict) and "message" in response:
                content = response["message"].get("content", "")
            else:
                content = str(response)

            return {
                "content": content,
                "latency_seconds": elapsed_time,
                "raw_response": response,
            }

        except ResponseError as e:
            if e.status_code == 404:
                raise LookupError(
                    f"Model '{target_model}' not found on Ollama server. Run: ollama pull {target_model}"
                ) from e
            raise RuntimeError(f"Ollama returned an error (status {e.status_code}): {e.error}") from e

        except Exception as e:
            # Check for general connection error
            if not self.is_server_online():
                raise ConnectionError(
                    "Connection lost to Ollama server. Please verify that Ollama is still running."
                ) from e
            raise RuntimeError(f"Failed to communicate with model '{target_model}': {e}") from e
