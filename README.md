# Harmonia Phase 1 - Visual Calibration PWA

A Progressive Web App for visual preference calibration using the MetaFBP algorithm.

---

## Table of Contents
- [Overview](#overview)
- [Google Cloud Free Trial Benefits](#google-cloud-free-trial-benefits)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Production Deployment (Cloud SQL + Cloud Run)](#production-deployment)
- [API Endpoints](#api-endpoints)
- [User Flow](#user-flow)
- [For Christian](#for-christian---full-setup-guide)
- [For Avery](#for-avery---full-setup-guide)

---

## Overview

Harmonia Phase 1 captures user visual preferences through image ratings and generates personalized embedding vectors using the MetaFBP (Meta Face Beauty Prediction) algorithm.

### Features
- User registration with gender/preference selection
- 5-question psychometric assessment
- Visual calibration (rate 10 portrait images, 1-5 stars)
- MetaFBP vector generation (512-dimensional embeddings)
- Profile data export (JSON download)
- **Persistent PostgreSQL database** (Cloud SQL)

---

## Google Cloud Free Trial Benefits

### $300 Credit for 90 Days

You get **$300 in free credits** to use across all Google Cloud services for 90 days!

**What's Included:**

| Service | What We Use It For | Est. Monthly Cost |
|---------|-------------------|-------------------|
| **Cloud Run** | Host the FastAPI app | ~$0-10 (free tier covers most) |
| **Cloud SQL PostgreSQL** | Persistent database | ~$7-15/month |
| **Cloud Storage** | Store calibration images | ~$0-2/month |
| **Cloud Build** | Build Docker images | Free (120 min/day) |
| **Artifact Registry** | Store Docker images | ~$0-1/month |

**Total estimated: ~$10-30/month** (well within $300 credit!)

### Cloud SQL Free Trial Instance

Additionally, Google offers a **30-day Cloud SQL free trial** with:
- Enterprise Plus edition
- High availability
- Data cache enabled
- No credit card charge during trial

### Always Free Tier (After Trial)

Even after the $300 credit, these remain free:
- Cloud Run: 2 million requests/month
- Cloud Build: 120 build-minutes/day
- Cloud Storage: 5GB
- 1 e2-micro VM instance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  Cloud Run   │──────│  Cloud SQL   │                     │
│  │  (FastAPI)   │      │ (PostgreSQL) │                     │
│  │  2 vCPU/2GB  │      │  Enterprise  │                     │
│  └──────────────┘      └──────────────┘                     │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │Cloud Storage │ (optional - for images)                   │
│  └──────────────┘                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, PyTorch (CPU)
- **Frontend**: React 18, TypeScript, Vite, React Router
- **Auth**: JWT tokens, Argon2 password hashing
- **ML**: ResNet-18 backbone, custom DynamicLearner
- **Database**: Cloud SQL PostgreSQL (persistent!)

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup (SQLite for local dev)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu

uvicorn main:app --reload --port 8080
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Production Deployment

### Step 1: Create Google Cloud Project

```bash
# Install gcloud CLI (if not installed)
# macOS: brew install google-cloud-sdk
# Windows: https://cloud.google.com/sdk/docs/install

# Login and create project
gcloud auth login
gcloud projects create harmonia-phase1 --name="Harmonia Phase 1"
gcloud config set project harmonia-phase1

# Enable billing (required, but won't charge during free trial)
# Do this in Console: https://console.cloud.google.com/billing
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### Step 3: Create Cloud SQL PostgreSQL Instance

```bash
# Create a PostgreSQL instance (free trial eligible!)
gcloud sql instances create harmonia-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_SECURE_PASSWORD

# Create the database
gcloud sql databases create harmonia --instance=harmonia-db

# Create a user
gcloud sql users create harmonia_user \
  --instance=harmonia-db \
  --password=YOUR_USER_PASSWORD
```

### Step 4: Store Secrets in Secret Manager

```bash
# Store database password
echo -n "YOUR_USER_PASSWORD" | gcloud secrets create db-password --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 5: Deploy to Cloud Run

```bash
cd backend

# Deploy with Cloud SQL connection
gcloud run deploy harmonia-phase1 \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "DB_USER=harmonia_user,DB_NAME=harmonia" \
  --set-secrets "DB_PASS=db-password:latest" \
  --add-cloudsql-instances PROJECT_ID:us-central1:harmonia-db \
  --set-env-vars "CLOUD_SQL_CONNECTION_NAME=PROJECT_ID:us-central1:harmonia-db"
```

### Step 6: Verify Deployment

```bash
# Get the URL
gcloud run services describe harmonia-phase1 --region us-central1 --format="value(status.url)"

# Test health endpoint
curl https://YOUR_URL/api/health
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new user |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/auth/me` | Get current user info |
| GET | `/api/psychometric/questions` | Get 5 questions |
| POST | `/api/psychometric/submit` | Submit answers |
| POST | `/api/setup/download-images` | Download calibration images |
| GET | `/api/setup/status` | Check if images ready |
| GET | `/api/calibration/images` | Get calibration images |
| POST | `/api/calibration/submit` | Submit ratings, get vector |
| GET | `/api/calibration/vector` | Get user's vector |
| GET | `/api/profile/download` | Download full profile JSON |

---

## User Flow

```
Signup → Setup (download images) → Psychometric (5 questions) → Calibration (rate 10 images) → Complete
```

---

## For Christian - Full Setup Guide

Hey Christian! Here's how to set up the full production environment with your $300 free credits.

### 1. Create Google Cloud Account

1. Go to https://cloud.google.com/free
2. Click "Get started for free"
3. Sign in with Google account
4. Add payment method (won't be charged during trial!)
5. You now have **$300 credit for 90 days**

### 2. Install gcloud CLI

**macOS:**
```bash
brew install google-cloud-sdk
```

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

### 3. Set Up Project

```bash
# Login
gcloud auth login

# Create project
gcloud projects create harmonia-christian --name="Harmonia"
gcloud config set project harmonia-christian

# Enable APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
```

### 4. Create Cloud SQL Database

```bash
# This creates a PostgreSQL database (uses ~$7-15/month of your credit)
gcloud sql instances create harmonia-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=ChooseSecurePassword123

# Create database and user
gcloud sql databases create harmonia --instance=harmonia-db
gcloud sql users create app_user --instance=harmonia-db --password=AppUserPassword456
```

### 5. Store Password as Secret

```bash
echo -n "AppUserPassword456" | gcloud secrets create db-password --data-file=-
```

### 6. Deploy the App

```bash
# Clone repo
git clone <repo-url>
cd mltest/backend

# Get your project number
PROJECT_NUMBER=$(gcloud projects describe harmonia-christian --format="value(projectNumber)")

# Grant secret access
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy!
gcloud run deploy harmonia-phase1 \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "DB_USER=app_user,DB_NAME=harmonia,CLOUD_SQL_CONNECTION_NAME=harmonia-christian:us-central1:harmonia-db" \
  --set-secrets "DB_PASS=db-password:latest" \
  --add-cloudsql-instances harmonia-christian:us-central1:harmonia-db
```

### 7. Get Your URL

```bash
gcloud run services describe harmonia-phase1 --region us-central1 --format="value(status.url)"
```

Share this URL with the team!

---

## For Avery - Full Setup Guide

Hey Avery! Here's your complete guide to setting up Harmonia with the $300 Google Cloud credits.

### 1. Sign Up for Google Cloud

1. Visit https://cloud.google.com/free
2. Click "Get started for free"
3. Use your Google account
4. Add a payment method (you won't be charged!)
5. Receive **$300 credit valid for 90 days**

### 2. Install Command Line Tools

**macOS:**
```bash
brew install google-cloud-sdk
```

**Windows:**
Download installer: https://cloud.google.com/sdk/docs/install

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 3. Initial Setup

```bash
# Authenticate
gcloud auth login

# Create your project
gcloud projects create harmonia-avery --name="Harmonia Avery"
gcloud config set project harmonia-avery

# Enable required services
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### 4. Create PostgreSQL Database

```bash
# Create Cloud SQL instance (~$7-15/month from your $300 credit)
gcloud sql instances create harmonia-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YourRootPassword123!

# Wait for instance to be ready (2-3 minutes)
gcloud sql instances describe harmonia-db

# Create the app database
gcloud sql databases create harmonia --instance=harmonia-db

# Create app user
gcloud sql users create harmonia_app \
  --instance=harmonia-db \
  --password=YourAppPassword456!
```

### 5. Secure Your Password

```bash
# Store password in Secret Manager
echo -n "YourAppPassword456!" | gcloud secrets create harmonia-db-pass --data-file=-

# Get project number for permissions
PROJECT_NUM=$(gcloud projects describe harmonia-avery --format="value(projectNumber)")

# Allow Cloud Run to access the secret
gcloud secrets add-iam-policy-binding harmonia-db-pass \
  --member="serviceAccount:${PROJECT_NUM}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 6. Deploy the Application

```bash
# Get the code
git clone <repo-url>
cd mltest/backend

# Deploy to Cloud Run with database connection
gcloud run deploy harmonia-phase1 \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "DB_USER=harmonia_app" \
  --set-env-vars "DB_NAME=harmonia" \
  --set-env-vars "CLOUD_SQL_CONNECTION_NAME=harmonia-avery:us-central1:harmonia-db" \
  --set-secrets "DB_PASS=harmonia-db-pass:latest" \
  --add-cloudsql-instances harmonia-avery:us-central1:harmonia-db
```

### 7. Verify Everything Works

```bash
# Get your app URL
URL=$(gcloud run services describe harmonia-phase1 --region us-central1 --format="value(status.url)")
echo "Your app is live at: $URL"

# Test the health endpoint
curl $URL/api/health

# Test the API docs
echo "API docs at: $URL/docs"
```

### 8. Monitor Your Usage

```bash
# View logs
gcloud run logs read harmonia-phase1 --region us-central1

# Check billing (in Console)
# https://console.cloud.google.com/billing
```

### Cost Tracking

Your $300 credit should last well beyond the 90-day trial:
- Cloud SQL (db-f1-micro): ~$7-15/month
- Cloud Run: ~$0-10/month (mostly free tier)
- Storage/Build: ~$1-5/month

**Estimated total: $10-30/month = 10+ months of usage!**

---

## Troubleshooting

### "Session expired" error
- Database was reset (SQLite only) - use Cloud SQL for persistence
- Clear localStorage and re-login

### Images not loading
- Check `/api/setup/status`
- Trigger download: `POST /api/setup/download-images`
- Or add images to `backend/calibration_images/`

### Database connection issues
```bash
# Check Cloud SQL status
gcloud sql instances describe harmonia-db

# View Cloud Run logs
gcloud run logs read harmonia-phase1 --region us-central1 --limit 50
```

---

## Sources

- [Google Cloud Free Trial](https://cloud.google.com/free)
- [Cloud SQL Free Trial](https://docs.cloud.google.com/sql/docs/postgres/free-trial-instance)
- [Connect Cloud Run to Cloud SQL](https://cloud.google.com/sql/docs/postgres/connect-run)
- [Cloud SQL Python Connector](https://github.com/GoogleCloudPlatform/cloud-sql-python-connector)

---

## License

Private - Harmonia Project
