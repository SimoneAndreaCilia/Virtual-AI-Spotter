"""
Unit Tests for CloudSessionUploader — API Client.

Tests the serialization, HTTP POST logic, retry behavior, and thread-based
async upload. All HTTP calls are mocked — no real network requests.

Run with: python -m pytest tests/test_api_client.py -v
"""
import json
import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
from threading import Event

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.api_client import CloudSessionUploader
from src.core.entities.session import Session


# =============================================================================
# Fixtures
# =============================================================================

def _sample_session() -> Session:
    """Returns a complete Session entity for testing."""
    session = Session(
        user_id="user-123",
        start_time=datetime(2026, 3, 8, 16, 30, 0),
        target_sets=3,
        target_reps=15
    )
    session.exercises = [
        {"name": "Squat", "set_index": 1, "reps": 15, "config": {"side": "right", "up_angle": 160}},
        {"name": "Squat", "set_index": 2, "reps": 15, "config": {"side": "right", "up_angle": 160}},
        {"name": "Squat", "set_index": 3, "reps": 12, "config": {"side": "right", "up_angle": 160}},
    ]
    session.end_time = datetime(2026, 3, 8, 16, 45, 0)
    return session


def _make_uploader(**kwargs) -> CloudSessionUploader:
    """Creates a CloudSessionUploader with test defaults."""
    defaults = {
        "api_url": "https://test.execute-api.eu-west-1.amazonaws.com/prod/sessions",
        "api_key": "test-api-key-123",
        "timeout": 5,
        "max_retries": 2,
        "enabled": True,
    }
    defaults.update(kwargs)
    return CloudSessionUploader(**defaults)


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSessionSerialization(unittest.TestCase):
    """Tests for _serialize_session method."""

    def setUp(self):
        self.uploader = _make_uploader()
        self.session = _sample_session()

    def test_serializes_required_fields(self):
        """Payload must contain all required Lambda fields."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["session_id"], self.session.id)
        self.assertEqual(payload["user_id"], "user-123")
        self.assertEqual(payload["exercise_name"], "Squat")
        self.assertIn("start_time", payload)

    def test_maps_start_time_as_iso_string(self):
        """start_time should be an ISO 8601 string."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["start_time"], "2026-03-08T16:30:00")

    def test_includes_end_time_when_present(self):
        """end_time should be included when session is ended."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["end_time"], "2026-03-08T16:45:00")

    def test_excludes_end_time_when_none(self):
        """end_time should not be in payload if session not ended."""
        self.session.end_time = None
        payload = self.uploader._serialize_session(self.session)

        self.assertNotIn("end_time", payload)

    def test_computes_duration_seconds(self):
        """duration_seconds should be computed from start/end."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["duration_seconds"], 900.0)  # 15 minutes

    def test_serializes_sets_array(self):
        """sets array should contain all exercise records."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(len(payload["sets"]), 3)
        self.assertEqual(payload["sets"][0]["set_index"], 1)
        self.assertEqual(payload["sets"][0]["reps"], 15)
        self.assertIn("config", payload["sets"][0])

    def test_computes_summary_metrics(self):
        """summary should include total_reps, completed_sets, completion_rate."""
        payload = self.uploader._serialize_session(self.session)

        summary = payload["summary"]
        self.assertEqual(summary["total_reps"], 42)  # 15 + 15 + 12
        self.assertEqual(summary["completed_sets"], 3)
        self.assertEqual(summary["completion_rate"], 1.0)  # 3/3

    def test_includes_app_version(self):
        """Payload should include the app version."""
        payload = self.uploader._serialize_session(self.session)

        self.assertIn("app_version", payload)
        self.assertIsInstance(payload["app_version"], str)

    def test_includes_device_id(self):
        """Payload should include a hashed device identifier."""
        payload = self.uploader._serialize_session(self.session)

        self.assertIn("device_id", payload)
        self.assertEqual(len(payload["device_id"]), 16)  # SHA256 truncated to 16 chars

    def test_includes_target_sets_and_reps(self):
        """Payload should include configured targets."""
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["target_sets"], 3)
        self.assertEqual(payload["target_reps"], 15)

    def test_empty_exercises_list(self):
        """Session with no exercises should serialize without errors."""
        self.session.exercises = []
        payload = self.uploader._serialize_session(self.session)

        self.assertEqual(payload["exercise_name"], "Unknown")
        self.assertEqual(payload["sets"], [])
        self.assertEqual(payload["summary"]["total_reps"], 0)

    def test_payload_is_json_serializable(self):
        """The entire payload must be JSON-serializable."""
        payload = self.uploader._serialize_session(self.session)

        # Should not raise
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)


# =============================================================================
# HTTP POST Tests (with mocked requests)
# =============================================================================

class TestPostWithRetry(unittest.TestCase):
    """Tests for _post_with_retry method."""

    def setUp(self):
        self.uploader = _make_uploader()
        self.payload = {"session_id": "test-123", "user_id": "user-1"}

    @patch("src.data.api_client.requests.post")
    def test_success_on_first_attempt(self, mock_post):
        """HTTP 201 on first try should return True."""
        mock_post.return_value = MagicMock(status_code=201)

        result = self.uploader._post_with_retry(self.payload)

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("src.data.api_client.requests.post")
    def test_sends_correct_headers(self, mock_post):
        """Request should include Content-Type and x-api-key headers."""
        mock_post.return_value = MagicMock(status_code=201)

        self.uploader._post_with_retry(self.payload)

        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(call_kwargs["headers"]["x-api-key"], "test-api-key-123")

    @patch("src.data.api_client.requests.post")
    def test_sends_to_correct_url(self, mock_post):
        """Request should be sent to the configured API URL."""
        mock_post.return_value = MagicMock(status_code=201)

        self.uploader._post_with_retry(self.payload)

        call_args = mock_post.call_args
        self.assertIn("test.execute-api.eu-west-1", call_args[0][0])

    @patch("src.data.api_client.requests.post")
    def test_client_error_no_retry(self, mock_post):
        """HTTP 400 (client error) should NOT retry."""
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")

        result = self.uploader._post_with_retry(self.payload)

        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 1)  # No retry

    @patch("src.data.api_client.time.sleep")  # Mock sleep to speed up tests
    @patch("src.data.api_client.requests.post")
    def test_server_error_retries(self, mock_post, mock_sleep):
        """HTTP 500 should trigger retry."""
        mock_post.return_value = MagicMock(status_code=500, text="Internal Error")

        result = self.uploader._post_with_retry(self.payload)

        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 2)  # 1 attempt + 1 retry

    @patch("src.data.api_client.time.sleep")
    @patch("src.data.api_client.requests.post")
    def test_retry_succeeds_on_second_attempt(self, mock_post, mock_sleep):
        """If first attempt 500, second 201, should return True."""
        mock_post.side_effect = [
            MagicMock(status_code=500, text="Error"),
            MagicMock(status_code=201),
        ]

        result = self.uploader._post_with_retry(self.payload)

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)

    @patch("src.data.api_client.time.sleep")
    @patch("src.data.api_client.requests.post")
    def test_timeout_triggers_retry(self, mock_post, mock_sleep):
        """requests.Timeout should trigger retry."""
        import requests as req
        mock_post.side_effect = [
            req.Timeout("Connection timed out"),
            MagicMock(status_code=201),
        ]

        result = self.uploader._post_with_retry(self.payload)

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)

    @patch("src.data.api_client.time.sleep")
    @patch("src.data.api_client.requests.post")
    def test_connection_error_triggers_retry(self, mock_post, mock_sleep):
        """requests.ConnectionError should trigger retry."""
        import requests as req
        mock_post.side_effect = [
            req.ConnectionError("No network"),
            MagicMock(status_code=201),
        ]

        result = self.uploader._post_with_retry(self.payload)

        self.assertTrue(result)

    @patch("src.data.api_client.time.sleep")
    @patch("src.data.api_client.requests.post")
    def test_all_retries_exhausted(self, mock_post, mock_sleep):
        """After all retries fail, should return False."""
        import requests as req
        mock_post.side_effect = req.Timeout("Timeout forever")

        result = self.uploader._post_with_retry(self.payload)

        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 2)


# =============================================================================
# Upload Session (Threading) Tests
# =============================================================================

class TestUploadSession(unittest.TestCase):
    """Tests for the upload_session method (thread launching)."""

    @patch.object(CloudSessionUploader, "_upload_worker")
    def test_launches_background_thread(self, mock_worker):
        """upload_session should start a background thread."""
        uploader = _make_uploader()
        session = _sample_session()

        uploader.upload_session(session)

        # Give thread a moment to start
        time.sleep(0.1)
        mock_worker.assert_called_once_with(session)

    def test_disabled_uploader_skips_upload(self):
        """When enabled=False, no thread should be started."""
        uploader = _make_uploader(enabled=False)
        session = _sample_session()

        # Should not raise, should not start a thread
        uploader.upload_session(session)

    def test_empty_url_disables_uploader(self):
        """Empty API URL should auto-disable the uploader."""
        uploader = _make_uploader(api_url="")

        self.assertFalse(uploader.enabled)

    @patch("src.data.api_client.requests.post")
    def test_upload_worker_catches_exceptions(self, mock_post):
        """_upload_worker should never raise, even on unexpected errors."""
        mock_post.side_effect = RuntimeError("Unexpected catastrophe")
        uploader = _make_uploader()
        session = _sample_session()

        # Should not raise
        uploader._upload_worker(session)


# =============================================================================
# Protocol Conformance Tests
# =============================================================================

class TestProtocolConformance(unittest.TestCase):
    """Tests that CloudSessionUploader satisfies CloudUploaderProtocol."""

    def test_implements_cloud_uploader_protocol(self):
        """CloudSessionUploader should be a runtime-checkable CloudUploaderProtocol."""
        from src.core.protocols import CloudUploaderProtocol
        uploader = _make_uploader()

        self.assertIsInstance(uploader, CloudUploaderProtocol)


# =============================================================================
# Device ID Tests
# =============================================================================

class TestDeviceId(unittest.TestCase):
    """Tests for device ID generation."""

    def test_device_id_is_deterministic(self):
        """Same machine should produce the same device_id."""
        uploader1 = _make_uploader()
        uploader2 = _make_uploader()

        self.assertEqual(uploader1._device_id, uploader2._device_id)

    def test_device_id_is_16_chars(self):
        """Device ID should be 16 characters (truncated SHA256)."""
        uploader = _make_uploader()

        self.assertEqual(len(uploader._device_id), 16)


if __name__ == "__main__":
    unittest.main()
