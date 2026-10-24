"""
Evaluation and Bounded Retry Module for Structured Assistant Responses.

Handles:
- Parsing and validation of JSON outputs against Pydantic schemas
- Distinguishing error categories:
  * INVALID_JSON (syntax malformed)
  * MISSING_FIELD (required field omitted)
  * TYPE_ERROR (incorrect data types)
  * VALIDATION_ERROR (generic/constraint violations)
  * OLLAMA_REQUEST_ERROR (timeout, network, or server failures)
- Bounded retry loop (1 initial attempt + up to 2 repair attempts = 3 max attempts)
- Structured reliability measurement
"""

import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError

try:
    from src.schemas import StructuredAssistantResponse
    from src.ollama_client import OllamaClient
except ImportError:
    from schemas import StructuredAssistantResponse
    from ollama_client import OllamaClient


MAX_ATTEMPTS = 3  # 1 initial attempt + 2 repair attempts


class ErrorCategory(str, Enum):
    """Classification of errors that can occur during structured extraction."""
    NONE = "none"
    INVALID_JSON = "invalid_json"
    MISSING_FIELD = "missing_field"
    TYPE_ERROR = "type_error"
    VALIDATION_ERROR = "validation_error"
    OLLAMA_REQUEST_ERROR = "ollama_request_error"


def classify_validation_error(error: ValidationError) -> ErrorCategory:
    """
    Examine Pydantic's error details and classify into clear, explainable categories.
    """
    error_dicts = error.errors()
    error_types = {e.get("type", "") for e in error_dicts}

    # Check for syntax / invalid JSON parsing failures
    if any("json_invalid" in t for t in error_types):
        return ErrorCategory.INVALID_JSON

    # Check for missing required fields
    if any("missing" in t for t in error_types):
        return ErrorCategory.MISSING_FIELD

    # Check for type mismatch errors (e.g. list provided when string expected)
    if any("type" in t for t in error_types):
        return ErrorCategory.TYPE_ERROR

    return ErrorCategory.VALIDATION_ERROR


def validate_structured_response(
    raw_text: str,
    schema_cls: Type[BaseModel] = StructuredAssistantResponse,
) -> Tuple[Optional[BaseModel], ErrorCategory, str]:
    """
    Parse and validate raw model output against the given Pydantic schema.

    :param raw_text: Raw response string from the model.
    :param schema_cls: The Pydantic model class to validate against.
    :return: Tuple of (validated_model or None, ErrorCategory, error_message)
    """
    cleaned_text = raw_text.strip()
    if not cleaned_text:
        return None, ErrorCategory.INVALID_JSON, "Model returned an empty response string."

    # Strip markdown code blocks if the model enclosed JSON in ```json ... ```
    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            if lines[-1].startswith("```"):
                cleaned_text = "\n".join(lines[1:-1]).strip()
            else:
                cleaned_text = "\n".join(lines[1:]).strip()

    try:
        validated_obj = schema_cls.model_validate_json(cleaned_text)
        return validated_obj, ErrorCategory.NONE, ""
    except ValidationError as e:
        category = classify_validation_error(e)
        return None, category, str(e)
    except Exception as e:
        return None, ErrorCategory.INVALID_JSON, f"Failed to parse JSON: {e}"


def run_bounded_retry_structured_call(
    client: OllamaClient,
    prompt: str,
    model_name: Optional[str] = None,
    schema_cls: Type[BaseModel] = StructuredAssistantResponse,
    max_attempts: int = MAX_ATTEMPTS,
) -> Dict[str, Any]:
    """
    Execute bounded retries to obtain a validated structured response.
    
    Guaranteed bounded:
    - Attempt 1: Initial user prompt requesting JSON matching schema.
    - Attempt 2 & 3: Repair prompts feeding back the exact failure reason to the model.
    - Never loops indefinitely.

    :return: Dictionary containing:
        - 'success': bool
        - 'attempts_used': int
        - 'validated_data': Optional[Dict[str, Any]]
        - 'error_category': ErrorCategory
        - 'error_message': str
        - 'total_latency_seconds': float
        - 'raw_responses': List[str]
    """
    schema_json_str = json.dumps(schema_cls.model_json_schema())
    system_instruction = (
        "You must respond ONLY with a valid JSON object matching this exact schema:\n"
        f"{schema_json_str}\n"
        "Do not include any conversational filler, markdown formatting, or preamble."
    )

    conversation_messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
    ]

    total_latency = 0.0
    raw_responses: List[str] = []
    last_error_category = ErrorCategory.NONE
    last_error_message = ""

    # Bounded for-loop prevents any possibility of infinite loops
    for attempt in range(1, max_attempts + 1):
        try:
            # Request JSON format from Ollama client
            response_dict = client.chat(
                messages=conversation_messages,
                model_name=model_name,
                format="json",
                options={"temperature": 0.1},
            )
            latency = response_dict.get("latency_seconds", 0.0)
            total_latency += latency
            raw_text = response_dict.get("content", "")
            raw_responses.append(raw_text)

            # Validate output using Pydantic
            validated_obj, error_cat, error_msg = validate_structured_response(
                raw_text, schema_cls=schema_cls
            )

            if validated_obj is not None:
                return {
                    "success": True,
                    "attempts_used": attempt,
                    "validated_data": validated_obj.model_dump(),
                    "error_category": ErrorCategory.NONE.value,
                    "error_message": "",
                    "total_latency_seconds": round(total_latency, 3),
                    "raw_responses": raw_responses,
                }

            # On validation failure, record error and prepare repair message if attempts remain
            last_error_category = error_cat
            last_error_message = error_msg

            if attempt < max_attempts:
                # Add assistant's invalid output and corrective feedback to message history
                conversation_messages.append({"role": "assistant", "content": raw_text})
                repair_prompt = (
                    f"Your previous response was invalid. Category: {error_cat.value}.\n"
                    f"Details: {error_msg}\n"
                    "Please fix the error and output ONLY the corrected JSON object matching the schema."
                )
                conversation_messages.append({"role": "user", "content": repair_prompt})

        except Exception as e:
            # Handle Ollama connection, timeout, or lookup errors
            last_error_category = ErrorCategory.OLLAMA_REQUEST_ERROR
            last_error_message = str(e)
            # If server is completely offline or model is missing, do not burn useless retries
            if "not installed" in str(e).lower() or "not connect" in str(e).lower():
                return {
                    "success": False,
                    "attempts_used": attempt,
                    "validated_data": None,
                    "error_category": last_error_category.value,
                    "error_message": last_error_message,
                    "total_latency_seconds": round(total_latency, 3),
                    "raw_responses": raw_responses,
                }

    # If loop finishes without returning, retries were exhausted
    return {
        "success": False,
        "attempts_used": max_attempts,
        "validated_data": None,
        "error_category": last_error_category.value,
        "error_message": f"Validation failed after {max_attempts} attempts. Last error: {last_error_message}",
        "total_latency_seconds": round(total_latency, 3),
        "raw_responses": raw_responses,
    }
