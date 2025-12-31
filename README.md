# Caerus

A two-sided video pitch marketplace where founders upload short pitch videos and investors pay subscriptions to browse opportunities and ask Q&A.

## Tech Stack

- **Mobile**: React Native (Expo) with TypeScript
- **Backend**: Python (FastAPI) with PostgreSQL
- **Database**: Supabase PostgreSQL
- **Storage**: Cloudflare R2 for videos
- **Auth**: Firebase Authentication
- **Payments**: Apple StoreKit (In-App Purchases)

## Project Structure

```
dealflow-app/
├── mobile/           # Expo React Native app
├── backend/          # FastAPI Python backend
└── infrastructure/   # Docker Compose, deployment configs
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker Desktop
- Expo Go app (for mobile testing)

### Backend Setup

1. Start the database:
```bash
cd infrastructure
docker-compose up -d
```

2. Set up Python environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Firebase and GCS credentials
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the backend:
```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Mobile Setup

1. Install dependencies:
```bash
cd mobile
npm install
```

2. Start the Expo development server:
```bash
npx expo start
```

3. Scan the QR code with Expo Go (iOS/Android) or press `i` for iOS simulator

## Cloud Services Setup

### Firebase

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication with Email/Password and Apple Sign-In
3. Download the service account JSON from Project Settings > Service Accounts
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of this file

### Supabase Database

1. Create a project at https://supabase.com
2. Get your database connection string from Settings > Database
3. Update `DATABASE_URL` in your `.env`

### Cloudflare R2 Storage

1. Create a Cloudflare account at https://cloudflare.com
2. Go to R2 > Create Bucket > Name it `caerus-videos`
3. Go to R2 > Manage R2 API Tokens > Create API Token
4. Copy the Account ID, Access Key ID, and Secret Access Key
5. Configure CORS in the bucket settings:
```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

### Apple Developer (for IAP)

1. Create App ID in Apple Developer Portal
2. Configure In-App Purchases in App Store Connect:
   - `com.caerus.founder.5min` - Non-consumable ($4.99)
   - `com.caerus.investor.monthly` - Auto-renewable subscription ($29.99/mo)
   - `com.caerus.investor.annual` - Auto-renewable subscription ($249.99/yr)
3. Get the Shared Secret from App Store Connect

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Mobile:
```bash
cd mobile
npm test
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Features

### Founders (Free)
- Record 30-second elevator pitch videos
- Create startup profiles
- Receive Q&A from investors

### Founders (Paid - $4.99)
- Upload 5-minute pitch presentations

### Investors (Subscription Required)
- Browse all startup pitches
- Filter by sector, stage, location
- Ask questions to founders
- Save and track deals

## License

Private - All rights reserved
