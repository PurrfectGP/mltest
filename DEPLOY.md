# Harmonia Phase 1 - Google Cloud Deployment Guide

## Prerequisites

1. Google Cloud account with billing enabled
2. `gcloud` CLI installed and authenticated
3. A GCP project created

## Quick Deploy (5 minutes)

### Step 1: Set up your project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Deploy the backend

```bash
# Navigate to the project directory
cd /path/to/mltest

# Build and deploy using Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Or deploy directly to Cloud Run
cd backend
gcloud run deploy harmonia-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### Step 3: Get your service URL

```bash
# Get the deployed URL
gcloud run services describe harmonia-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

This will output something like: `https://harmonia-backend-xxxxx-uc.a.run.app`

## Testing the Deployment

### 1. Health Check
```bash
curl https://YOUR_SERVICE_URL/api/health
# Expected: {"status":"healthy","service":"harmonia-phase1"}
```

### 2. Check Status
```bash
curl https://YOUR_SERVICE_URL/api/status
```

### 3. View API Documentation
Open in browser: `https://YOUR_SERVICE_URL/docs`

## Using the API (Testing Flow)

### 1. Register a User
```bash
curl -X POST https://YOUR_SERVICE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "gender": "male",
    "preference_target": "female"
  }'
```
Save the `access_token` from the response.

### 2. Get Psychometric Questions
```bash
curl https://YOUR_SERVICE_URL/api/psychometric/questions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Submit Psychometric Answers
```bash
curl -X POST https://YOUR_SERVICE_URL/api/psychometric/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "answers": [
      {"question_id": "dinner_check", "selected_option_id": "dc_a"},
      {"question_id": "tech_meltdown", "selected_option_id": "tm_a"},
      {"question_id": "found_wallet", "selected_option_id": "fw_a"},
      {"question_id": "restaurant_choice", "selected_option_id": "rc_c"},
      {"question_id": "spontaneous_trip", "selected_option_id": "st_a"}
    ]
  }'
```

### 4. Submit Calibration Ratings
```bash
curl -X POST https://YOUR_SERVICE_URL/api/calibration/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ratings": {
      "placeholder_1": 5,
      "placeholder_2": 4,
      "placeholder_3": 2,
      "placeholder_4": 5,
      "placeholder_5": 3
    }
  }'
```

## Checking if Profiles Were Created

### List All Users
```bash
curl https://YOUR_SERVICE_URL/api/admin/users
```

### List All Profiles
```bash
curl https://YOUR_SERVICE_URL/api/admin/profiles
```

### Get Specific Profile Detail
```bash
curl https://YOUR_SERVICE_URL/api/admin/profiles/USER_ID
```

### Check Database Info
```bash
curl https://YOUR_SERVICE_URL/api/admin/db-info
```

## Example: Full Test Script

Save this as `test_deployment.sh`:

```bash
#!/bin/bash
BASE_URL="${1:-https://harmonia-backend-xxxxx-uc.a.run.app}"

echo "=== Testing Harmonia API at $BASE_URL ==="

# Health check
echo -e "\n1. Health Check:"
curl -s "$BASE_URL/api/health" | jq .

# Register user
echo -e "\n2. Registering user..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test'$(date +%s)'@example.com",
    "username": "testuser'$(date +%s)'",
    "password": "password123"
  }')
echo "$RESPONSE" | jq .

TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')
echo "Token: ${TOKEN:0:50}..."

# Submit psychometric
echo -e "\n3. Submitting psychometric answers..."
curl -s -X POST "$BASE_URL/api/psychometric/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "answers": [
      {"question_id": "dinner_check", "selected_option_id": "dc_a"},
      {"question_id": "tech_meltdown", "selected_option_id": "tm_a"},
      {"question_id": "found_wallet", "selected_option_id": "fw_a"},
      {"question_id": "restaurant_choice", "selected_option_id": "rc_c"},
      {"question_id": "spontaneous_trip", "selected_option_id": "st_a"}
    ]
  }' | jq .

# Submit calibration
echo -e "\n4. Submitting calibration ratings..."
curl -s -X POST "$BASE_URL/api/calibration/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "ratings": {
      "placeholder_1": 5,
      "placeholder_2": 4,
      "placeholder_3": 2,
      "placeholder_4": 5,
      "placeholder_5": 3
    }
  }' | jq .

# Check profiles
echo -e "\n5. Checking created profiles..."
curl -s "$BASE_URL/api/admin/profiles" | jq .

# List users
echo -e "\n6. Listing all users..."
curl -s "$BASE_URL/api/admin/users" | jq .

echo -e "\n=== Test Complete ==="
```

Run it with:
```bash
chmod +x test_deployment.sh
./test_deployment.sh https://YOUR_SERVICE_URL
```

## Important Notes

1. **Data Persistence**: Cloud Run instances are ephemeral. Data stored in SQLite will be lost when the container restarts. For production, use Cloud SQL or Firestore.

2. **Scaling**: The default config allows Cloud Run to scale to multiple instances. Each instance has its own SQLite database, which means users might not see their data if routed to a different instance.

3. **For Production**:
   - Use Cloud SQL (PostgreSQL) instead of SQLite
   - Use Cloud Storage for profile vectors
   - Add proper authentication for admin endpoints

## Troubleshooting

### Check Logs
```bash
gcloud run services logs read harmonia-backend --region us-central1 --limit 50
```

### View Live Logs
```bash
gcloud run services logs tail harmonia-backend --region us-central1
```

### Redeploy After Changes
```bash
cd backend
gcloud run deploy harmonia-backend --source . --region us-central1
```
