"""
Cloud Session Uploader — Sends workout session data to AWS API Gateway.

This module handles the client-side HTTP communication with the cloud backend.
The upload runs in a background thread to avoid blocking the OpenCV main loop.

Architecture:
    SessionManager.end_session()
        → db_manager.save_session()       (local SQLite — synchronous)
        → cloud_uploader.upload_session() (AWS cloud — async background thread)

Usage:
    uploader = CloudSessionUploader(
        api_url="https://xxx.execute-api.eu-west-1.amazonaws.com/prod/sessions",
        api_key="your-api-key"
    )
    uploader.upload_session(session)  # Non-blocking, returns immediately
"""
import json
import hashlib
import logging
import platform
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from src.core.entities.session import Session

logger = logging.getLogger(__name__)

# App metadata
APP_VERSION = "1.0.0"


class CloudSessionUploader:
    """
    Uploads workout session reports to AWS via API Gateway.

    Key design decisions:
    - Non-blocking: upload runs in a daemon thread (won't freeze OpenCV UI)
    - Fire-and-forget: failures are logged but never raise to the caller
    - Retry with exponential backoff (configurable)
    - Disabled by default if api_url is empty
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 10,
        max_retries: int = 2,
        enabled: bool = True
    ):
        """
        Args:
            api_url: Full URL of the API Gateway endpoint (e.g. .../prod/sessions)
            api_key: API Key for x-api-key header authentication
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts on failure
            enabled: If False, upload_session() is a no-op
        """
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled and bool(api_url)

        # Generate a stable, hashed device identifier (privacy-safe)
        self._device_id = self._generate_device_id()

        if self.enabled:
            logger.info(f"CloudSessionUploader initialized (endpoint: {api_url[:50]}...)")
        else:
            logger.info("CloudSessionUploader disabled (no API URL or explicitly disabled)")

    # =========================================================================
    # Public API
    # =========================================================================

    def upload_session(self, session: Session) -> None:
        """
        Launches a background thread to upload the session data.

        This method returns immediately — it does NOT block the calling thread.
        The upload result is logged asynchronously.

        Args:
            session: The completed Session entity to upload.
        """
        if not self.enabled:
            logger.debug("Cloud upload skipped (uploader disabled)")
            return

        # Daemon thread: will be killed when main app exits
        thread = threading.Thread(
            target=self._upload_worker,
            args=(session,),
            name="cloud-upload-worker",
            daemon=True
        )
        thread.start()
        logger.info(f"Cloud upload started in background thread for session {session.id}")

    # =========================================================================
    # Internal Workers
    # =========================================================================

    def _upload_worker(self, session: Session) -> None:
        """
        Background worker: serializes the session, sends POST with retry.

        Runs in a separate thread. Never raises exceptions to the caller.
        """
        try:
            payload = self._serialize_session(session)
            self._post_with_retry(payload)
        except Exception as e:
            # Catch-all: log but never crash the background thread
            logger.error(f"Cloud upload failed (unrecoverable): {e}", exc_info=True)

    def _post_with_retry(self, payload: Dict[str, Any]) -> bool:
        """
        Sends POST request with exponential backoff retry.

        Args:
            payload: JSON-serializable dict to send as body.

        Returns:
            True if upload succeeded, False otherwise.
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 201:
                    logger.info(
                        f"Cloud upload successful (attempt {attempt}): "
                        f"session_id={payload.get('session_id')}"
                    )
                    return True

                # Client error (4xx) — don't retry, the payload is wrong
                if 400 <= response.status_code < 500:
                    logger.warning(
                        f"Cloud upload rejected (HTTP {response.status_code}): "
                        f"{response.text[:200]}"
                    )
                    return False

                # Server error (5xx) — retry
                logger.warning(
                    f"Cloud upload server error (HTTP {response.status_code}), "
                    f"attempt {attempt}/{self.max_retries}"
                )

            except requests.Timeout:
                logger.warning(
                    f"Cloud upload timeout ({self.timeout}s), "
                    f"attempt {attempt}/{self.max_retries}"
                )
            except requests.ConnectionError:
                logger.warning(
                    f"Cloud upload connection error (no network?), "
                    f"attempt {attempt}/{self.max_retries}"
                )
            except requests.RequestException as e:
                logger.warning(
                    f"Cloud upload request error: {e}, "
                    f"attempt {attempt}/{self.max_retries}"
                )

            # Exponential backoff before next retry (1s, 2s)
            if attempt < self.max_retries:
                backoff = 2 ** (attempt - 1)
                time.sleep(backoff)

        logger.error(
            f"Cloud upload failed after {self.max_retries} attempts: "
            f"session_id={payload.get('session_id')}"
        )
        return False

    # =========================================================================
    # Serialization
    # =========================================================================

    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """
        Converts a Session entity into the JSON payload expected by the Lambda.

        Maps the local Session dataclass fields to the cloud API schema.
        Computes derived fields (duration, summary) for the batched report.
        """
        # Compute duration
        duration_seconds = None
        if session.start_time and session.end_time:
            delta = session.end_time - session.start_time
            duration_seconds = round(delta.total_seconds(), 1)

        # Build sets array from exercises list
        sets_data = []
        for ex in session.exercises:
            set_record = {
                "set_index": ex.get("set_index", 1),
                "reps": ex.get("reps", 0),
            }
            if "config" in ex:
                set_record["config"] = ex["config"]
            sets_data.append(set_record)

        # Compute summary metrics
        total_reps = sum(s.get("reps", 0) for s in sets_data)
        completed_sets = len(sets_data)

        # Extract exercise name (all sets in a session are the same exercise)
        exercise_name = "Unknown"
        if session.exercises:
            exercise_name = session.exercises[0].get("name", "Unknown")

        payload = {
            "session_id": session.id,
            "user_id": str(session.user_id),
            "exercise_name": exercise_name,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "target_sets": session.target_sets,
            "target_reps": session.target_reps,
            "sets": sets_data,
            "summary": {
                "total_reps": total_reps,
                "completed_sets": completed_sets,
                "completion_rate": round(
                    completed_sets / session.target_sets, 2
                ) if session.target_sets > 0 else 0.0
            },
            "app_version": APP_VERSION,
            "device_id": self._device_id,
        }

        # Optional fields
        if session.end_time:
            payload["end_time"] = session.end_time.isoformat()
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds

        return payload

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _generate_device_id() -> str:
        """
        Generates a stable, privacy-safe device identifier.

        Uses a hash of the hostname — not reversible, not PII.
        """
        raw = platform.node() or "unknown-device"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
