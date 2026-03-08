"""
AWS Lambda Function — Virtual AI Spotter Session Logger.

Receives workout session data via API Gateway (HTTP API),
validates the payload, and writes it to DynamoDB.

Table: SpotterAI_Workout_Logs
    Partition Key: user_id (String)
    Sort Key: Timestamp (String, ISO 8601)

Trigger: API Gateway HTTP API → POST /sessions
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# --- Configuration ---
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "SpotterAI_Workout_Logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# --- Payload Schema ---
REQUIRED_FIELDS = ["session_id", "user_id", "exercise_name", "start_time"]

# Maximum payload size guard (256 KB — DynamoDB item limit is 400 KB)
MAX_PAYLOAD_BYTES = 256 * 1024


# =============================================================================
# Validation
# =============================================================================

def validate_payload(body: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates the incoming session payload.

    Checks:
    - Required fields are present and non-empty
    - Field types are correct
    - Timestamps are valid ISO 8601
    - Numeric values are within sane ranges

    Returns:
        (is_valid, error_message)
    """
    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in body or not body[field]:
            return False, f"Missing or empty required field: '{field}'"

    # 2. String fields
    string_fields = ["session_id", "user_id", "exercise_name", "start_time"]
    for field in string_fields:
        if field in body and not isinstance(body[field], str):
            return False, f"Field '{field}' must be a string, got {type(body[field]).__name__}"

    # 3. Validate ISO 8601 timestamps
    for ts_field in ["start_time", "end_time"]:
        if ts_field in body and body[ts_field]:
            try:
                datetime.fromisoformat(body[ts_field])
            except (ValueError, TypeError):
                return False, f"Field '{ts_field}' must be a valid ISO 8601 timestamp"

    # 4. Numeric ranges
    if "duration_seconds" in body:
        duration = body["duration_seconds"]
        if not isinstance(duration, (int, float)) or duration < 0:
            return False, "Field 'duration_seconds' must be a non-negative number"

    for int_field in ["target_sets", "target_reps"]:
        if int_field in body:
            val = body[int_field]
            if not isinstance(val, int) or val < 1 or val > 100:
                return False, f"Field '{int_field}' must be an integer between 1 and 100"

    # 5. Sets array validation
    if "sets" in body:
        if not isinstance(body["sets"], list):
            return False, "Field 'sets' must be an array"
        for i, s in enumerate(body["sets"]):
            if not isinstance(s, dict):
                return False, f"sets[{i}] must be an object"
            if "set_index" in s and not isinstance(s["set_index"], int):
                return False, f"sets[{i}].set_index must be an integer"
            if "reps" in s and not isinstance(s["reps"], (int, float)):
                return False, f"sets[{i}].reps must be a number"

    # 6. Summary validation
    if "summary" in body:
        if not isinstance(body["summary"], dict):
            return False, "Field 'summary' must be an object"

    return True, None


# =============================================================================
# DynamoDB Writer
# =============================================================================

def build_dynamo_item(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the DynamoDB item from the validated payload.

    Maps start_time → Timestamp (Sort Key).
    Adds server-side metadata (received_at).
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    item = {
        # Keys
        "user_id": body["user_id"],
        "Timestamp": body["start_time"],  # Sort Key maps from start_time
        # Session data
        "session_id": body["session_id"],
        "exercise_name": body["exercise_name"],
        "start_time": body["start_time"],
        # Server-side metadata
        "received_at": now_utc,
    }

    # Optional fields — only include if present
    optional_fields = [
        "end_time", "duration_seconds", "target_sets", "target_reps",
        "sets", "summary", "app_version", "device_id"
    ]
    for field in optional_fields:
        if field in body and body[field] is not None:
            item[field] = body[field]

    return item


def write_to_dynamodb(item: Dict[str, Any]) -> None:
    """
    Writes the item to DynamoDB.

    Raises ClientError if DynamoDB rejects the write.
    """
    table.put_item(Item=item)
    logger.info(
        f"Item written successfully: user_id={item['user_id']}, "
        f"Timestamp={item['Timestamp']}, session_id={item['session_id']}"
    )


# =============================================================================
# Lambda Handler
# =============================================================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main entry point for the Lambda function.

    Expected event format (from API Gateway HTTP API):
        event['body'] = JSON string with session data

    Returns:
        API Gateway response with statusCode and body.
    """
    logger.info(f"Received event: requestId={context.aws_request_id if context else 'N/A'}")

    # --- 1. Parse Body ---
    try:
        raw_body = event.get("body", "")

        # Size guard
        if len(raw_body.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            return _response(400, {"error": "Payload too large", "max_bytes": MAX_PAYLOAD_BYTES})

        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Invalid JSON: {e}")
        return _response(400, {"error": "Invalid JSON in request body"})

    # --- 2. Validate ---
    is_valid, error_msg = validate_payload(body)
    if not is_valid:
        logger.warning(f"Validation failed: {error_msg}")
        return _response(400, {"error": error_msg})

    # --- 3. Build DynamoDB Item ---
    item = build_dynamo_item(body)

    # --- 4. Write to DynamoDB ---
    try:
        write_to_dynamodb(item)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"DynamoDB error: {error_code} - {error_message}")
        return _response(500, {
            "error": "Database write failed",
            "detail": error_code
        })
    except Exception as e:
        logger.error(f"Unexpected error writing to DynamoDB: {e}", exc_info=True)
        return _response(500, {"error": "Internal server error"})

    # --- 5. Success ---
    return _response(201, {
        "message": "Session saved successfully",
        "session_id": body["session_id"],
        "user_id": body["user_id"],
        "timestamp": item["Timestamp"]
    })


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Builds a standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
