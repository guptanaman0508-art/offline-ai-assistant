"""
Unit Tests for Pydantic Schema Validation and Bounded Retries.

Tests:
- Valid JSON matching schema
- Invalid JSON syntax
- Missing required fields
- Incorrect field types
- Successful retry recovery on attempt 2
- Exhausted retries after 3 attempts
"""

import unittest
from unittest.mock import MagicMock
from src.schemas import StructuredAssistantResponse
from src.evaluation import (
    validate_structured_response,
    classify_validation_error,
    run_bounded_retry_structured_call,
    ErrorCategory,
    MAX_ATTEMPTS,
)


class TestStructuredValidation(unittest.TestCase):
    """Test suite ensuring robust error categorization and Pydantic validation."""

    def test_valid_json_success(self):
        valid_json = (
            '{"answer": "Binary search is O(log n).", '
            '"key_points": ["Sorted array required", "Divides interval in half"]}'
        )
        obj, cat, err = validate_structured_response(valid_json, StructuredAssistantResponse)
        self.assertIsNotNone(obj)
        self.assertEqual(cat, ErrorCategory.NONE)
        self.assertEqual(err, "")
        self.assertEqual(obj.answer, "Binary search is O(log n).")
        self.assertEqual(len(obj.key_points), 2)

    def test_valid_json_with_markdown_wrapper(self):
        wrapped_json = (
            "```json\n"
            '{"answer": "Process vs Thread", "key_points": ["Memory isolated", "Lightweight context"]}\n'
            "```"
        )
        obj, cat, err = validate_structured_response(wrapped_json, StructuredAssistantResponse)
        self.assertIsNotNone(obj)
        self.assertEqual(cat, ErrorCategory.NONE)
        self.assertEqual(obj.answer, "Process vs Thread")

    def test_invalid_json_syntax(self):
        broken_json = '{"answer": "Missing closing brace", "key_points": ["point"]'
        obj, cat, err = validate_structured_response(broken_json, StructuredAssistantResponse)
        self.assertIsNone(obj)
        self.assertEqual(cat, ErrorCategory.INVALID_JSON)
        self.assertNotEqual(err, "")

    def test_missing_required_field(self):
        # Missing key_points
        missing_field_json = '{"answer": "Only answer is provided here."}'
        obj, cat, err = validate_structured_response(missing_field_json, StructuredAssistantResponse)
        self.assertIsNone(obj)
        self.assertEqual(cat, ErrorCategory.MISSING_FIELD)
        self.assertIn("key_points", err)

    def test_incorrect_field_type(self):
        # key_points is a string instead of a list of strings
        type_error_json = '{"answer": "Answer text", "key_points": "not-a-list"}'
        obj, cat, err = validate_structured_response(type_error_json, StructuredAssistantResponse)
        self.assertIsNone(obj)
        self.assertEqual(cat, ErrorCategory.TYPE_ERROR)

    def test_empty_string_response(self):
        obj, cat, err = validate_structured_response("", StructuredAssistantResponse)
        self.assertIsNone(obj)
        self.assertEqual(cat, ErrorCategory.INVALID_JSON)


class TestBoundedRetries(unittest.TestCase):
    """Test suite ensuring retries are strictly bounded and recover properly."""

    def test_bounded_retry_succeeds_on_first_try(self):
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "content": '{"answer": "Valid on attempt 1", "key_points": ["pt1"]}',
            "latency_seconds": 0.45,
        }

        result = run_bounded_retry_structured_call(
            client=mock_client,
            prompt="Explain QuickSort",
            schema_cls=StructuredAssistantResponse,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts_used"], 1)
        self.assertEqual(result["validated_data"]["answer"], "Valid on attempt 1")
        self.assertEqual(mock_client.chat.call_count, 1)

    def test_bounded_retry_recovers_on_second_attempt(self):
        mock_client = MagicMock()
        # Attempt 1 returns broken JSON, Attempt 2 returns valid JSON
        mock_client.chat.side_effect = [
            {"content": '{"answer": "broken json...', "latency_seconds": 0.3},
            {"content": '{"answer": "Corrected on attempt 2", "key_points": ["repaired"]}', "latency_seconds": 0.5},
        ]

        result = run_bounded_retry_structured_call(
            client=mock_client,
            prompt="Explain QuickSort",
            schema_cls=StructuredAssistantResponse,
            max_attempts=3,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts_used"], 2)
        self.assertEqual(result["validated_data"]["answer"], "Corrected on attempt 2")
        self.assertEqual(mock_client.chat.call_count, 2)
        self.assertAlmostEqual(result["total_latency_seconds"], 0.8)

    def test_bounded_retry_exhausted_after_max_attempts(self):
        mock_client = MagicMock()
        # All 3 attempts return missing field
        mock_client.chat.return_value = {
            "content": '{"answer": "Still missing key_points"}',
            "latency_seconds": 0.2,
        }

        result = run_bounded_retry_structured_call(
            client=mock_client,
            prompt="Explain QuickSort",
            schema_cls=StructuredAssistantResponse,
            max_attempts=3,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["attempts_used"], 3)
        self.assertIsNone(result["validated_data"])
        self.assertEqual(result["error_category"], ErrorCategory.MISSING_FIELD.value)
        self.assertEqual(mock_client.chat.call_count, 3)  # Never loops beyond max_attempts!


if __name__ == "__main__":
    unittest.main()
