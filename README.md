# Harmonia Phase 1 - Visual Calibration PWA

A Progressive Web App for visual preference calibration using the MetaFBP algorithm.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Google Cloud Deployment](#google-cloud-deployment)
- [API Endpoints](#api-endpoints)
- [User Flow](#user-flow)
- [For Christian](#for-christian---google-cloud-setup)
- [For Avery](#for-avery---google-cloud-setup)

---

## Overview

Harmonia Phase 1 captures user visual preferences through image ratings and generates personalized embedding vectors using the MetaFBP (Meta Face Beauty Prediction) algorithm.

### Features
- User registration with gender/preference selection
- 5-question psychometric assessment
- Visual calibration (rate 10 portrait images, 1-5 stars)
- MetaFBP vector generation (512-dimensional embeddings)
- Profile data export (JSON download)

---

## Architecture

```
mltest/
├── backend/                 # FastAPI Python backend
│   ├── main.py             # Main app, routes, error handling
│   ├── auth.py             # JWT authentication (pwdlib/Argon2)
│   ├── database.py         # SQLite database setup
│   ├── db_models.py        # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── routers/            # API route modules
│   │   ├── auth.py         # /api/auth/*
│   │   ├── calibration.py  # /api/calibration/*
│   │   └── psychometric.py # /api/psychometric/*
│   ├── services/
│   │   └── visual_service.py  # MetaFBP algorithm
│   ├── models/
│   │   ├── resnet.py       # ResNet backbone (512-dim features)
│   │   └── dynamic_maml.py # Dynamic learner for personalization
│   ├── static/             # Built frontend files
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx        # Main app with routing
│   │   ├── pages/         # Page components
│   │   │   ├── Signup.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Setup.tsx      # Image download loading
│   │   │   ├── Psychometric.tsx
│   │   │   ├── Calibration.tsx
│   │   │   └── Complete.tsx
│   │   └── services/
│   │       └── api.ts     # API client
│   ├── package.json
│   └── vite.config.ts
│
└── AI_TOKEN_EFFICIENCY_GUIDE.md  # AI agent guidelines
```

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite, PyTorch (CPU)
- **Frontend**: React 18, TypeScript, Vite, React Router
- **Auth**: JWT tokens, Argon2 password hashing
- **ML**: ResNet-18 backbone, custom DynamicLearner

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install PyTorch CPU
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Backend runs at: `http://localhost:8080`
API docs at: `http://localhost:8080/docs`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Build Frontend for Production

```bash
cd frontend
npm run build

# Copy to backend static folder
cp -r dist/* ../backend/static/
```

---

## Google Cloud Deployment

### URLs (after deployment)
- **App URL**: `https://harmonia-phase1-XXXXXXXXXX-uc.a.run.app`
- **API Docs**: `https://harmonia-phase1-XXXXXXXXXX-uc.a.run.app/docs`
- **Health Check**: `https://harmonia-phase1-XXXXXXXXXX-uc.a.run.app/api/health`

### Deploy to Cloud Run

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
cd backend
gcloud run deploy harmonia-phase1 \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### View Logs
```bash
gcloud run logs read harmonia-phase1 --region us-central1
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
| GET | `/api/health` | Health check |
| GET | `/api/logs` | View debug logs |

---

## User Flow

```
1. Signup (/signup)
   └── Enter email, username, password, gender, preference

2. Setup (/setup)
   └── Loading screen while downloading 10 portrait images

3. Psychometric (/psychometric)
   └── Answer 5 personality questions

4. Calibration (/calibration)
   └── Rate 10 images (1-5 stars)

5. Complete (/complete)
   └── View results, download profile JSON
```

---

## For Christian - Google Cloud Setup

### Request: Please set up Google Cloud Free Tier

Hey Christian! We need a Google Cloud project for deploying Harmonia. Here's what we need:

#### 1. Create Google Cloud Account (Free Tier)
- Go to: https://cloud.google.com/free
- Sign up with a Google account
- Free tier includes:
  - $300 credit for 90 days
  - Cloud Run: 2 million requests/month free
  - Cloud Build: 120 build-minutes/day free

#### 2. Create a New Project
```
Project name: harmonia-phase1
Project ID: harmonia-phase1-XXXXX (auto-generated)
```

#### 3. Enable Required APIs
In Google Cloud Console, enable:
- Cloud Run API
- Cloud Build API
- Container Registry API

#### 4. Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Windows
# Download from: https://cloud.google.com/sdk/docs/install

# Linux
curl https://sdk.cloud.google.com | bash
```

#### 5. Authenticate
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 6. Deploy
```bash
cd backend
gcloud run deploy harmonia-phase1 \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

#### 7. Share the URL
After deployment, share the Cloud Run URL:
`https://harmonia-phase1-XXXXXXXXXX-uc.a.run.app`

---

## For Avery - Google Cloud Setup

### Request: Please set up Google Cloud Free Tier

Hey Avery! We need a Google Cloud project for deploying Harmonia. Here's what we need:

#### 1. Create Google Cloud Account (Free Tier)
- Go to: https://cloud.google.com/free
- Sign up with a Google account
- Free tier includes:
  - $300 credit for 90 days
  - Cloud Run: 2 million requests/month free
  - Cloud Build: 120 build-minutes/day free

#### 2. Create a New Project
```
Project name: harmonia-avery
Project ID: harmonia-avery-XXXXX (auto-generated)
```

#### 3. Enable Required APIs
In Google Cloud Console (https://console.cloud.google.com):
1. Go to "APIs & Services" > "Enable APIs"
2. Search and enable:
   - Cloud Run API
   - Cloud Build API
   - Artifact Registry API

#### 4. Install gcloud CLI

**macOS:**
```bash
brew install google-cloud-sdk
```

**Windows:**
Download installer from: https://cloud.google.com/sdk/docs/install

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

#### 5. First-Time Setup
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config list
```

#### 6. Deploy the App
```bash
# Clone the repo (or pull latest)
git clone <repo-url>
cd mltest/backend

# Deploy to Cloud Run
gcloud run deploy harmonia-phase1 \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

#### 7. After Deployment
You'll get a URL like:
```
https://harmonia-phase1-abc123xyz-uc.a.run.app
```

Share this URL with the team!

#### 8. Useful Commands
```bash
# View logs
gcloud run logs read harmonia-phase1 --region us-central1

# Update deployment (after code changes)
gcloud run deploy harmonia-phase1 --source .

# Check service status
gcloud run services describe harmonia-phase1 --region us-central1
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug logging |
| `SECRET_KEY` | random | JWT signing key (set in production!) |
| `DATA_DIR` | `/app/data` | Data storage directory |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## Troubleshooting

### Images not loading
- Check `/api/setup/status` - should return `{"ready": true, "count": 10}`
- If not, trigger download: `POST /api/setup/download-images`

### Blank page
- Check browser console for JS errors
- Verify static files exist in `backend/static/assets/`

### Auth errors
- Clear localStorage: `localStorage.removeItem('token')`
- Check `/api/logs` for server errors

### Database issues
- SQLite file at `/app/data/harmonia.db`
- Delete to reset: `rm /app/data/harmonia.db`

---

## Recent Changes

1. **Security fixes**: Replaced passlib with pwdlib (Argon2)
2. **Error handling**: Global JSON error handler
3. **Image setup**: Downloads 10 portraits from Unsplash on first use
4. **Profile export**: Download button for user data + MetaFBP vector
5. **Debug logging**: `/api/logs` endpoint for troubleshooting

---

## License

Private - Harmonia Project
