# Caerus Setup & Testing Checklist

**Goal:** Get the app running locally for end-to-end testing

---

## Prerequisites

- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Docker Desktop installed and running
- [ ] Xcode installed (for iOS simulator)
- [ ] Expo Go app on your iPhone (for device testing)

---

## Part 1: Cloud Services Setup (One-Time)

### 1.1 Firebase Setup (~10 min)
- [ ] Go to [Firebase Console](https://console.firebase.google.com)
- [ ] Create new project: `caerus-app`
- [ ] Enable Authentication:
  - [ ] Go to Authentication → Sign-in method
  - [ ] Enable "Email/Password"
  - [ ] Enable "Apple" (will need Apple Developer account later)
- [ ] Get Firebase config:
  - [ ] Go to Project Settings → General
  - [ ] Add iOS app with bundle ID: `com.caerus.app`
  - [ ] Download `GoogleService-Info.plist`
  - [ ] Copy to `mobile/`
- [ ] Get Service Account:
  - [ ] Go to Project Settings → Service Accounts
  - [ ] Click "Generate new private key"
  - [ ] Save as `backend/firebase-service-account.json`

### 1.2 Supabase Setup (~5 min)
- [ ] Go to [Supabase](https://supabase.com)
- [ ] Create new project: `caerus`
- [ ] Wait for project to initialize (~2 min)
- [ ] Go to Settings → Database
- [ ] Copy the "Connection string" (URI format)
- [ ] Note: Replace `[YOUR-PASSWORD]` with your database password

### 1.3 Cloudflare R2 Setup (~10 min)
- [ ] Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
- [ ] Navigate to R2 Object Storage
- [ ] Create bucket: `caerus-videos`
- [ ] Go to R2 → Manage R2 API Tokens
- [ ] Create API token with:
  - [ ] Permission: Object Read & Write
  - [ ] Specify bucket: `caerus-videos`
- [ ] Copy: Account ID, Access Key ID, Secret Access Key
- [ ] Configure CORS (in bucket settings):
```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

---

## Part 2: Backend Setup

### 2.1 Environment Configuration
```bash
cd backend
cp .env.example .env
```

- [ ] Edit `.env` with your values:
```env
# Database (Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Firebase
FIREBASE_PROJECT_ID=caerus-app

# Cloudflare R2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=caerus-videos

# JWT (generate a random string)
JWT_SECRET=your-super-secret-key-change-this
```

### 2.2 Python Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2.3 Database Migration
```bash
cd backend
source venv/bin/activate

# Generate migration
alembic revision --autogenerate -m "initial tables"

# Apply migration
alembic upgrade head
```

### 2.4 Start Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] Verify: Open http://localhost:8000/docs (Swagger UI)
- [ ] Test health endpoint: http://localhost:8000/

---

## Part 3: Mobile Setup

### 3.1 Install Dependencies
```bash
cd mobile
npm install
```

### 3.2 Configure API URL
- [ ] Edit `mobile/src/utils/constants.ts`:
```typescript
// For local development with simulator
export const API_URL = 'http://localhost:8000';

// For device testing (use your computer's local IP)
// export const API_URL = 'http://192.168.1.XXX:8000';
```

To find your local IP:
```bash
# macOS
ipconfig getifaddr en0

# Or check System Preferences → Network
```

### 3.3 Start Expo
```bash
cd mobile
npx expo start
```

- [ ] Press `i` to open iOS simulator
- [ ] Or scan QR code with Expo Go on your iPhone

---

## Part 4: End-to-End Testing

### 4.1 Test Auth Flow
- [ ] Open app in simulator
- [ ] Tap "Sign Up"
- [ ] Enter test email: `investor@test.com`
- [ ] Enter password: `Test123!`
- [ ] Select role: "Investor"
- [ ] Complete onboarding wizard
- [ ] Verify: Lands on swipe feed

### 4.2 Test Founder Flow
- [ ] Sign out (Settings → Log Out)
- [ ] Sign up as: `founder@test.com`
- [ ] Select role: "Founder"
- [ ] Complete founder onboarding
- [ ] Create startup:
  - [ ] Name: "Test Startup"
  - [ ] Tagline: "Testing the app"
  - [ ] Sector: "SaaS"
  - [ ] Stage: "Seed"
- [ ] Record 30-second pitch (mock for now)

### 4.3 Test Investor Flow
- [ ] Log in as `investor@test.com`
- [ ] Verify swipe feed shows pitches
- [ ] Swipe right on a pitch
- [ ] Verify view counter decrements
- [ ] Tap Q&A Me button
- [ ] Select questions and send
- [ ] Go to Messages tab
- [ ] Verify thread created

### 4.4 Test Paywall
- [ ] Create new investor account
- [ ] Swipe through 15 pitches
- [ ] Verify paywall appears
- [ ] Tap "Subscribe Now"
- [ ] Verify subscription screen shows

---

## Part 5: Development Tips

### Dev Mode Auth Bypass
For quick testing without Firebase, the backend accepts dev tokens:
```typescript
// In your code or Postman
Authorization: Bearer dev_test_user_id
```

### Useful API Endpoints (Swagger UI)
- http://localhost:8000/docs - Interactive API docs
- POST /auth/signup - Create user
- GET /auth/me - Get current user
- POST /startups - Create startup
- GET /pitches/feed - Get pitch feed

### Database Reset
```bash
cd backend
source venv/bin/activate

# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
```

### Logs
```bash
# Backend logs (already shows in uvicorn output)

# Mobile logs
npx expo start
# Press 'j' to open debugger
```

---

## Troubleshooting

### "Network Error" in app
- Check backend is running: http://localhost:8000/
- If on device, make sure API_URL uses your local IP
- Check firewall allows port 8000

### "Invalid Firebase token"
- Make sure `firebase-service-account.json` exists in `backend/`
- Or use dev tokens: `dev_your_test_id`

### Database connection failed
- Verify DATABASE_URL in `.env`
- Check Supabase project is active
- Verify password is URL-encoded if it has special chars

### R2 upload fails
- Check R2 credentials in `.env`
- Verify CORS is configured on bucket
- Check bucket name matches

### Expo build errors
```bash
cd mobile
rm -rf node_modules
npm install
npx expo start --clear
```

---

## Quick Reference

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Firebase Console | https://console.firebase.google.com |
| Supabase Dashboard | https://app.supabase.com |
| Cloudflare R2 | https://dash.cloudflare.com |

---

## Next Steps After Testing

1. [ ] Set up TestFlight for beta testing
2. [ ] Deploy backend to Railway/Render
3. [ ] Configure production environment
4. [ ] Set up App Store Connect for IAP
5. [ ] Submit for App Store review
