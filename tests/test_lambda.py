"""
Unit Tests for AWS Lambda Function — SpotterAI Session Logger.

Tests the lambda_handler, validate_payload, and build_dynamo_item functions
using mocked DynamoDB to avoid any real AWS calls.

Run with: python -m pytest tests/test_lambda.py -v
"""
import json
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path so we can import the Lambda function
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aws", "lambda"))

from lambda_function import lambda_handler, validate_payload, build_dynamo_item


# =============================================================================
# Fixtures
# =============================================================================

def _valid_payload() -> dict:
    """Returns a complete, valid session payload."""
    return {
        "SessionID": "abc-123-def",
        "UserID": "user-456-ghi",
        "ExerciseName": "Squat",
        "StartTime": "2026-03-08T16:30:00",
        "end_time": "2026-03-08T16:45:00",
        "DurationSeconds": 900,
        "target_sets": 3,
        "target_reps": 15,
        "sets": [
            {"set_index": 1, "reps": 15, "config": {"side": "right", "up_angle": 160}},
            {"set_index": 2, "reps": 15, "config": {"side": "right", "up_angle": 160}},
            {"set_index": 3, "reps": 12, "config": {"side": "right", "up_angle": 160}},
        ],
        "summary": {
            "total_reps": 42,
            "completed_sets": 3,
            "completion_rate": 0.93
        },
        "app_version": "1.0.0",
        "device_id": "hashed-host-id"
    }


def _minimal_payload() -> dict:
    """Returns a payload with only required fields."""
    return {
        "session_id": "min-session-001",
        "UserID": "min-user-001",
        "ExerciseName": "Bicep Curl",
        "StartTime": "2026-03-08T10:00:00"
    }


def _make_event(body: dict) -> dict:
    """Wraps a payload dict into an API Gateway event."""
    return {"body": json.dumps(body)}


def _mock_context():
    """Creates a mock Lambda context."""
    ctx = MagicMock()
    ctx.aws_request_id = "test-request-id-001"
    return ctx


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidatePayload(unittest.TestCase):
    """Tests for the validate_payload function."""

    def test_valid_full_payload(self):
        """Complete payload should pass validation."""
        is_valid, error = validate_payload(_valid_payload())
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_valid_minimal_payload(self):
        """Minimal payload (only required fields) should pass."""
        is_valid, error = validate_payload(_minimal_payload())
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_missing_session_id(self):
        """Missing session_id should fail."""
        payload = _valid_payload()
        del payload["session_id"]
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("session_id", error)

    def test_missing_user_id(self):
        """Missing user_id should fail."""
        payload = _valid_payload()
        del payload["user_id"]
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("user_id", error)

    def test_missing_exercise_name(self):
        """Missing exercise_name should fail."""
        payload = _valid_payload()
        del payload["exercise_name"]
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("exercise_name", error)

    def test_missing_start_time(self):
        """Missing start_time should fail."""
        payload = _valid_payload()
        del payload["start_time"]
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("start_time", error)

    def test_empty_string_field(self):
        """Empty string for required field should fail."""
        payload = _valid_payload()
        payload["session_id"] = ""
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("session_id", error)

    def test_invalid_start_time_format(self):
        """Non-ISO 8601 timestamp should fail."""
        payload = _valid_payload()
        payload["start_time"] = "not-a-timestamp"
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("start_time", error)

    def test_invalid_end_time_format(self):
        """Non-ISO 8601 end_time should fail."""
        payload = _valid_payload()
        payload["end_time"] = "yesterday"
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("end_time", error)

    def test_negative_duration(self):
        """Negative duration_seconds should fail."""
        payload = _valid_payload()
        payload["duration_seconds"] = -10
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("duration_seconds", error)

    def test_target_sets_too_high(self):
        """target_sets > 100 should fail."""
        payload = _valid_payload()
        payload["target_sets"] = 999
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("target_sets", error)

    def test_target_reps_zero(self):
        """target_reps = 0 should fail (must be >= 1)."""
        payload = _valid_payload()
        payload["target_reps"] = 0
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("target_reps", error)

    def test_string_type_for_numeric_field(self):
        """String value for target_sets should fail."""
        payload = _valid_payload()
        payload["target_sets"] = "three"
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)

    def test_sets_must_be_array(self):
        """sets must be an array, not a string."""
        payload = _valid_payload()
        payload["sets"] = "not-an-array"
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("sets", error)

    def test_set_entry_must_be_object(self):
        """Each entry in sets must be an object."""
        payload = _valid_payload()
        payload["sets"] = ["not-an-object"]
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("sets[0]", error)

    def test_summary_must_be_object(self):
        """summary must be an object, not a string."""
        payload = _valid_payload()
        payload["summary"] = "not-an-object"
        is_valid, error = validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("summary", error)


# =============================================================================
# DynamoDB Item Builder Tests
# =============================================================================

class TestBuildDynamoItem(unittest.TestCase):
    """Tests for the build_dynamo_item function."""

    def test_maps_start_time_to_timestamp_sort_key(self):
        """start_time should be mapped to the 'Timestamp' sort key."""
        payload = _valid_payload()
        item = build_dynamo_item(payload)

        self.assertEqual(item["Timestamp"], payload["start_time"])

    def test_partition_key_is_user_id(self):
        """user_id should be the partition key."""
        payload = _valid_payload()
        item = build_dynamo_item(payload)

        self.assertEqual(item["user_id"], payload["user_id"])

    def test_includes_required_fields(self):
        """Item should contain all required fields."""
        payload = _valid_payload()
        item = build_dynamo_item(payload)

        self.assertIn("session_id", item)
        self.assertIn("exercise_name", item)
        self.assertIn("start_time", item)
        self.assertIn("received_at", item)

    def test_includes_optional_fields_when_present(self):
        """Optional fields should be included when present."""
        payload = _valid_payload()
        item = build_dynamo_item(payload)

        self.assertIn("end_time", item)
        self.assertIn("duration_seconds", item)
        self.assertIn("sets", item)
        self.assertIn("summary", item)
        self.assertIn("app_version", item)

    def test_excludes_optional_fields_when_missing(self):
        """Optional fields should not be in item when not in payload."""
        payload = _minimal_payload()
        item = build_dynamo_item(payload)

        self.assertNotIn("end_time", item)
        self.assertNotIn("duration_seconds", item)
        self.assertNotIn("sets", item)
        self.assertNotIn("summary", item)

    def test_adds_received_at_metadata(self):
        """Item should include server-side 'received_at' timestamp."""
        payload = _valid_payload()
        item = build_dynamo_item(payload)

        self.assertIn("received_at", item)
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(item["received_at"])


# =============================================================================
# Lambda Handler Tests (Integration with mocked DynamoDB)
# =============================================================================

class TestLambdaHandler(unittest.TestCase):
    """Tests for the lambda_handler function."""

    @patch("lambda_function.table")
    def test_valid_payload_returns_201(self, mock_table):
        """Valid payload should return 201 Created."""
        mock_table.put_item.return_value = {}

        event = _make_event(_valid_payload())
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 201)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "Session saved successfully")
        self.assertEqual(body["session_id"], "abc-123-def")

    @patch("lambda_function.table")
    def test_valid_payload_calls_put_item(self, mock_table):
        """Valid payload should trigger DynamoDB put_item."""
        mock_table.put_item.return_value = {}

        event = _make_event(_valid_payload())
        lambda_handler(event, _mock_context())

        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"] if "Item" in call_args[1] else call_args[0][0]
        self.assertEqual(item["user_id"], "user-456-ghi")

    @patch("lambda_function.table")
    def test_minimal_payload_returns_201(self, mock_table):
        """Minimal payload (required fields only) should return 201."""
        mock_table.put_item.return_value = {}

        event = _make_event(_minimal_payload())
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 201)

    def test_invalid_json_returns_400(self):
        """Malformed JSON should return 400."""
        event = {"body": "not valid json {{{"}
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("error", body)

    def test_missing_required_field_returns_400(self):
        """Missing required field should return 400."""
        payload = _valid_payload()
        del payload["user_id"]

        event = _make_event(payload)
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("user_id", body["error"])

    def test_invalid_timestamp_returns_400(self):
        """Invalid timestamp should return 400."""
        payload = _valid_payload()
        payload["start_time"] = "not-a-date"

        event = _make_event(payload)
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 400)

    @patch("lambda_function.table")
    def test_dynamodb_error_returns_500(self, mock_table):
        """DynamoDB ClientError should return 500."""
        from botocore.exceptions import ClientError
        mock_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Rate exceeded"}},
            "PutItem"
        )

        event = _make_event(_valid_payload())
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertIn("error", body)

    @patch("lambda_function.table")
    def test_unexpected_error_returns_500(self, mock_table):
        """Unexpected exceptions should return 500 without leaking details."""
        mock_table.put_item.side_effect = RuntimeError("Something unexpected")

        event = _make_event(_valid_payload())
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertEqual(body["error"], "Internal server error")

    def test_empty_body_returns_400(self):
        """Empty body should return 400."""
        event = {"body": ""}
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["statusCode"], 400)

    def test_response_has_cors_headers(self):
        """Response should include CORS headers."""
        event = _make_event(_valid_payload())
        response = lambda_handler(event, _mock_context())

        self.assertIn("Access-Control-Allow-Origin", response["headers"])
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], "*")

    def test_response_content_type_is_json(self):
        """Response Content-Type should be application/json."""
        event = _make_event(_valid_payload())
        response = lambda_handler(event, _mock_context())

        self.assertEqual(response["headers"]["Content-Type"], "application/json")


if __name__ == "__main__":
    unittest.main()
