# DataLens AI

> Upload your data. Find what's wrong. Understand why.

DataLens AI is an AI-powered data quality platform that helps users analyze datasets, detect data quality issues, and understand their root causes.

The goal is to go beyond simply detecting bad data and eventually provide intelligent recommendations and automatically generate a corrected dataset.

## Features

- User authentication
  - JWT authentication with HttpOnly cookies
  - Automatic access-token refresh
- CSV dataset upload
- Dataset profiling
- Data quality scoring
- Missing-value detection
- Duplicate detection
- Anomaly detection
- Invalid-format detection
- Issue severity classification
- Detailed issue exploration
- AI-powered root-cause analysis

## How It Works

```text
Upload Dataset
      ↓
Dataset Profiling
      ↓
Quality Analysis
      ↓
Issue Detection
      ↓
Severity Classification
      ↓
AI Root-Cause Analysis
      ↓
Recommended Fix
      ↓
Corrected Dataset
```

## Tech Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- Axios
- Lucide React

### Backend
- Python
- Django
- Django REST Framework
- Pandas
- Simple JWT

### AI
- LangChain
- LangGraph

## Architecture

```text
                DataLens AI
                     │
          ┌──────────┴──────────┐
          │                     │
       Frontend              Backend
       Next.js               Django
          │                     │
          │      REST API       │
          └──────────┬──────────┘
                      │
                Data Analysis
                      │
                    Pandas
                      │
              Issue Detection
                      │
                 LangChain
                      │
                 LangGraph
                      │
             Root-Cause Analysis
```

## Current Status

The core dataset analysis and AI root-cause analysis functionality is working.

The next major feature is:

**Automatic Data Correction**

The planned workflow is:

```text
Detected Issue
      ↓
AI Recommended Fix
      ↓
User Approves Fix
      ↓
Modify Dataset
      ↓
Generate New CSV
      ↓
Download Corrected Dataset
```

## Project Structure

```text
datalens-ai/
│
├── backend/
│   ├── manage.py
│   ├── users/
│   ├── datasets/
│   └── ...
│
├── frontend/
│   └── my-app/
│       ├── app/
│       ├── components/
│       └── ...
│
└── README.md
```

## Running Locally

### Backend

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Backend: http://localhost:8000

### Frontend

```bash
cd frontend/my-app
npm install
npm run dev
```

Frontend: http://localhost:3000

## Authentication

DataLens AI uses JWT authentication through HttpOnly cookies.

```text
Login
  ↓
Access Token + Refresh Token
  ↓
HttpOnly Cookies
  ↓
Authenticated API Requests
  ↓
Access Token Expires
  ↓
Refresh Token
  ↓
New Access Token
```

Tokens are not stored in browser localStorage.

## API

### Authentication

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
GET  /api/auth/me/
```

### Datasets

```text
POST /api/datasets/
GET  /api/datasets/
```

### Issues

```text
GET /api/issues/<dataset-slug>/issues/
```

## Roadmap

- [x] Authentication
- [x] Dataset upload
- [x] Dataset profiling
- [x] Quality scoring
- [x] Issue detection
- [x] Severity classification
- [x] Issue details
- [x] AI root-cause analysis
- [ ] AI recommended corrections
- [ ] Automatic data correction
- [ ] Generate corrected CSV
- [ ] Download cleaned dataset
- [ ] Production deployment
- [ ] Dockerized deployment

## Why DataLens AI?

Data quality is often treated as a preprocessing problem.

DataLens AI aims to make it an interactive and explainable process.

Instead of simply telling a user:

> 10 missing values found.

the goal is to tell them:

> 10 missing values were found in the `income` column.
>
> **Likely cause:** These records were imported from a source where income was not collected.
>
> **Recommended action:** Review these records and apply the suggested correction.

The long-term goal is to make data cleaning faster, explainable, and actionable.

## Status

🚧 Active Development

DataLens AI is currently being developed and is not yet deployed publicly.
