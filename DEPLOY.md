# Harmonia Phase 1 - Google Cloud Deployment Guide

## Overview

This is a **single deployment** - the backend serves both the API and the frontend UI.
Once deployed, you get a URL that shows the full app with signup, login, psychometric questions, and visual calibration.

---

## Deploy via Google Cloud Console (No CLI Required)

### Step 1: Open Google Cloud Console

1. Go to https://console.cloud.google.com
2. Create a new project or select an existing one
3. Make sure billing is enabled for the project

### Step 2: Enable Cloud Run

1. In the search bar at the top, type **"Cloud Run"**
2. Click on **Cloud Run** in the results
3. If prompted, click **"Enable API"**

### Step 3: Create the Service

1. Click **"Create Service"**
2. Select **"Continuously deploy from a repository (source or Dockerfile)"**
3. Click **"Set up with Cloud Build"**

### Step 4: Connect Your Repository

1. If not connected, click **"Authenticate"** to connect your GitHub account
2. Select repository: **`PurrfectGP/mltest`**
3. Select branch: **`claude/read-instructions-prompt-0lCcW`**

### Step 5: Configure Build

1. **Build Type**: Select **"Dockerfile"**
2. **Source location**: Enter **`/backend/Dockerfile`**
3. Click **"Save"**

### Step 6: Configure Service Settings

| Setting | Value |
|---------|-------|
| Service name | `harmonia-phase1` |
| Region | `us-central1` (or closest to you) |
| CPU allocation | "CPU is only allocated during request processing" |
| Minimum instances | `0` |
| Maximum instances | `10` |
| Memory | **`2 GiB`** (important for PyTorch) |
| CPU | `2` |
| Request timeout | `300` seconds |
| **Authentication** | **Allow unauthenticated invocations** (check this!) |

### Step 7: Deploy

1. Click **"Create"**
2. Wait 5-10 minutes for the build to complete
3. Once done, you'll see a URL like: `https://harmonia-phase1-xxxxx-uc.a.run.app`

---

## Using the App

### Access the Frontend

Open your service URL in a browser:
```
https://harmonia-phase1-xxxxx-uc.a.run.app
```

You'll see the **Harmonia login page**. From here you can:

1. **Sign Up** - Create a new account
2. **Answer Fixed Five Questions** - 5 psychometric scenarios
3. **Rate Images** - Visual calibration with 1-5 stars
4. **View Results** - See your generated embedding vector

### The Complete User Flow

```
Sign Up → Fixed Five Questions → Image Rating → Profile Complete!
   │              │                    │              │
   │              │                    │              └─► p1_visual_vector.json saved
   │              │                    │
   │              │                    └─► MetaFBP processes ratings
   │              │                        Generates 512-dim embedding
   │              │
   │              └─► 5 scenario-based questions
   │                  Extracts personality traits
   │
   └─► Creates user account with UUID
```

---

## Check if Profiles Were Created

### Via Browser (Easy)

Open these URLs in your browser:

| URL | What It Shows |
|-----|---------------|
| `YOUR_URL/api/admin/users` | All registered users |
| `YOUR_URL/api/admin/profiles` | All generated p1_visual_vector.json files |
| `YOUR_URL/api/admin/profiles/USER_ID` | Specific user's full vector data |
| `YOUR_URL/api/health` | Health check |
| `YOUR_URL/docs` | Interactive API documentation (Swagger) |

### Example Response: `/api/admin/profiles`

```json
{
  "profiles_dir": "/app/data/profiles",
  "total": 1,
  "profiles": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "has_vector": true,
      "vector_summary": {
        "images_rated": 10,
        "embedding_dim": 512,
        "calibration_confidence": 0.75,
        "timestamp": "2024-01-14T12:00:00Z"
      }
    }
  ]
}
```

### Example Response: `/api/admin/profiles/{user_id}`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "meta": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "gender": "male",
      "preference_target": "female",
      "calibration_timestamp": "2024-01-14T12:00:00Z",
      "images_rated": 10
    },
    "self_analysis": {
      "embedding_vector": [0.123, -0.456, 0.789, ...],  // 512 values
      "detected_traits": {
        "facial_landmarks": ["placeholder"],
        "style_presentation": ["placeholder"],
        "vibe_tags": ["placeholder"]
      }
    },
    "preference_model": {
      "ideal_vector": [0.234, -0.567, ...],  // 512 values
      "attraction_triggers": {
        "mandatory_traits": ["placeholder_positive_trait"],
        "negative_traits": ["placeholder_negative_trait"]
      },
      "calibration_confidence": 0.75
    }
  }
}
```

---

## How MetaFBP Works (What the Code Does)

### 1. ResNetBackbone (feature extraction)
```
Image (224x224 RGB) → ResNet18 → 512-dimensional feature vector
```

### 2. User Calibration
```
User rates 10 images (1-5 stars)
    ↓
Each image → ResNetBackbone → 512-dim features
    ↓
Ratings normalized (1-5 → 0.0-1.0 weights)
    ↓
Weighted average of all features = aggregate preference signal
```

### 3. DynamicLearner (personalization)
```
Aggregate preference signal (512-dim)
    ↓
DynamicLearner.generator neural network
    ↓
Personalized embedding vector (512-dim)
    ↓
Saved to p1_visual_vector.json
```

### 4. Output Schema
```json
{
  "meta": { "user_id", "gender", "timestamp", "images_rated" },
  "self_analysis": {
    "embedding_vector": [512 floats],  // User's visual preference encoding
    "detected_traits": { ... }
  },
  "preference_model": {
    "ideal_vector": [512 floats],  // Centroid of liked images
    "calibration_confidence": 0.0-1.0
  }
}
```

---

## Important Notes

### Data Persistence Warning

Cloud Run instances are **ephemeral**. When the container restarts:
- SQLite database is reset
- Profile JSON files are lost

**For testing this is fine.** For production, you'd use:
- Cloud SQL for the database
- Cloud Storage for profile files

### First-Time Startup

The first request after deployment may take 30-60 seconds because:
1. Container needs to start
2. PyTorch models need to load (~500MB)

Subsequent requests are fast.

---

## Troubleshooting

### "Service Unavailable" Error
- Wait 60 seconds and try again (cold start)
- Check Cloud Run logs in Google Cloud Console

### Build Failed
- Make sure the Dockerfile path is `/backend/Dockerfile`
- Check Cloud Build logs for errors

### View Logs
1. Go to Cloud Run in Google Cloud Console
2. Click on your service
3. Click **"Logs"** tab

---

## Quick Test Checklist

After deployment:

- [ ] Open `YOUR_URL/` - Should show login page
- [ ] Open `YOUR_URL/api/health` - Should return `{"status":"healthy"}`
- [ ] Create an account through the UI
- [ ] Complete the 5 psychometric questions
- [ ] Rate 10 images
- [ ] Check `YOUR_URL/api/admin/profiles` - Should show your profile
