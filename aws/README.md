# AWS Infrastructure — Virtual AI Spotter

This directory contains the AWS backend infrastructure for cloud persistence of workout sessions.

## Architecture

```
Client (Python App)  →  API Gateway (HTTP API)  →  Lambda  →  DynamoDB
```

The app sends a **single JSON payload per session** (Data Batching pattern) to the HTTP API after the workout is complete.

---

## Prerequisites

- AWS CLI configured (`aws configure`)
- IAM user `spotter-dev-client` with appropriate permissions
- Python 3.12+ (Lambda runtime)

---

## DynamoDB Table

**Table:** `SpotterAI_Workout_Logs` (already created)

| Key       | Attribute  | Type   |
|-----------|-----------|--------|
| Partition | `user_id`  | String |
| Sort      | `Timestamp`| String (ISO 8601) |

---

## Lambda Deployment

### 1. Create the Execution Role

1. Go to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service → Lambda**
3. Attach the inline policy from [`iam-policy.json`](iam-policy.json)
4. Role name: `SpotterAI-Lambda-Role`

### 2. Package and Deploy

```bash
# From the aws/lambda/ directory
cd aws/lambda
zip lambda_function.zip lambda_function.py

# Create the function
aws lambda create-function \
  --function-name SpotterAI-SessionLogger \
  --runtime python3.12 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SpotterAI-Lambda-Role \
  --zip-file fileb://lambda_function.zip \
  --timeout 10 \
  --memory-size 128 \
  --environment Variables="{DYNAMODB_TABLE=SpotterAI_Workout_Logs}"

# Update (after changes)
aws lambda update-function-code \
  --function-name SpotterAI-SessionLogger \
  --zip-file fileb://lambda_function.zip
```

### 3. Create API Gateway (HTTP API)

1. Go to **API Gateway → Create API → HTTP API**
2. Add integration: **Lambda → SpotterAI-SessionLogger**
3. Route: `POST /sessions`
4. Stage: `prod` (auto-deploy)
5. Note the **Invoke URL** (e.g., `https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/prod`)

### 4. Add API Key Authentication

1. Go to **API Gateway → API Keys → Create API Key**
2. Create a **Usage Plan** and associate it with the `prod` stage
3. Associate the API Key with the Usage Plan
4. On the route `POST /sessions`, set **API Key Required = true**

### 5. Configure the App

Create a `.env` file in the project root:

```env
AWS_API_URL=https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/prod/sessions
AWS_API_KEY=your-api-key-here
CLOUD_UPLOAD_ENABLED=true
```

---

## Testing with cURL

```bash
curl -X POST https://YOUR-API-URL/sessions \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "session_id": "test-uuid-123",
    "user_id": "user-uuid-456",
    "exercise_name": "Squat",
    "start_time": "2026-03-08T16:30:00",
    "end_time": "2026-03-08T16:45:00",
    "duration_seconds": 900,
    "target_sets": 3,
    "target_reps": 15,
    "sets": [
        {"set_index": 1, "reps": 15, "config": {"side": "right"}},
        {"set_index": 2, "reps": 15, "config": {"side": "right"}},
        {"set_index": 3, "reps": 15, "config": {"side": "right"}}
    ],
    "summary": {
        "total_reps": 45,
        "completed_sets": 3,
        "completion_rate": 1.0
    }
  }'
```

**Expected response:** `HTTP 201`
```json
{
    "message": "Session saved successfully",
    "session_id": "test-uuid-123",
    "user_id": "user-uuid-456",
    "timestamp": "2026-03-08T16:30:00"
}
```

---

## IAM Policy (Least Privilege)

See [`iam-policy.json`](iam-policy.json) — grants only:
- `dynamodb:PutItem` on `SpotterAI_Workout_Logs`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` for CloudWatch

---

## Payload Schema

| Field             | Type    | Required | Description                        |
|-------------------|---------|----------|------------------------------------|
| `session_id`      | String  | ✅       | UUID of the session                |
| `user_id`         | String  | ✅       | UUID of the user                   |
| `exercise_name`   | String  | ✅       | Canonical exercise name            |
| `start_time`      | String  | ✅       | ISO 8601 timestamp (→ Sort Key)    |
| `end_time`        | String  | ❌       | ISO 8601 timestamp                 |
| `duration_seconds`| Number  | ❌       | Total session duration             |
| `target_sets`     | Integer | ❌       | Configured target sets             |
| `target_reps`     | Integer | ❌       | Configured target reps per set     |
| `sets`            | Array   | ❌       | Array of set records               |
| `summary`         | Object  | ❌       | Aggregated session metrics         |
| `app_version`     | String  | ❌       | Client app version                 |
| `device_id`       | String  | ❌       | Hashed device identifier           |
