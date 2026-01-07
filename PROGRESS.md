# Caerus Development Progress

**Last Updated:** January 7, 2026

---

## Project Vision

Caerus is "Tinder for Founders & Investors" - a mobile-first video pitch marketplace where founders upload 30-second pitches and investors swipe to discover startups, send questions, and connect.

---

## What's Next? 🎯

### Immediate TODO:
1. **Test Video Uploads** - End-to-end video flow: Record → Upload to GCS → Play in feed
2. **Deploy Admin Panel** - Push admin/ to Vercel
3. **Deploy Backend** - Choose hosting (see options below)
4. **TestFlight Setup** - iOS beta testing

### Backend Hosting Options:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Railway** | Easy deploy, good DX, auto-scaling | Smaller community | ~$5-20/mo |
| **Render** | Simple, free tier available, good for startups | Cold starts on free tier | Free-$25/mo |
| **Fly.io** | Fast global deployment, generous free tier | Learning curve | Free-$20/mo |
| **Google Cloud Run** | GCS integration (already using), auto-scale to zero | GCP complexity | Pay-per-use |
| **DigitalOcean App Platform** | Simple, predictable pricing | Less features | $5-25/mo |
| **AWS Lambda + API Gateway** | Scales infinitely, pay-per-request | Complex setup, cold starts | Pay-per-use |

**Recommendation:** Railway or Render for MVP simplicity. Cloud Run if wanting to stay in GCP ecosystem.

### Then:
5. Complete IAP integration (StoreKit)
6. Polish UI/UX (loading states, error handling)
7. App Store submission

---

## Phase 1: Project Scaffolding & Cloud Setup ✅ COMPLETE

### 1.1 Project Structure ✅
- [x] Create `mobile/` directory (Expo React Native)
- [x] Create `backend/` directory (FastAPI Python)
- [x] Create `infrastructure/` directory (Docker, configs)

### 1.2 Mobile App Setup ✅
- [x] Initialize Expo project with TypeScript
- [x] Configure React Navigation (native-stack)
- [x] Set up folder structure (screens, components, services, hooks, context)
- [x] Install dependencies (expo-camera, expo-av, axios, react-native-iap, etc.)

### 1.3 Backend Setup ✅
- [x] Initialize FastAPI project
- [x] Configure SQLAlchemy + Alembic
- [x] Set up project structure (models, schemas, api, services)
- [x] Create requirements.txt

### 1.4 Infrastructure ✅
- [x] Create Docker Compose for PostgreSQL + pgAdmin
- [x] Create .env.example template
- [x] Create README with setup instructions

### 1.5 Cloud Services Setup ✅ COMPLETE
- [x] Create Firebase project (`caerus-c29c9`)
- [x] Enable Firebase Auth (Email + Apple Sign-In ready)
- [x] Download Firebase service account JSON
- [x] Create Supabase project (PostgreSQL)
- [x] Get database connection string (pooler URL)
- [x] Run Alembic migrations (11 tables created)
- [x] Create GCS bucket `caerus-pitch-videos` (in R&D project with credits)
- [x] Configure CORS on GCS bucket
- [x] Grant Firebase service account access to bucket
- [x] Test signed URL upload/download flow
- [ ] (Later) Set up Apple Developer account for IAP

---

## Phase 2: Authentication & User Profiles ✅ COMPLETE

### 2.1 Backend - Auth ✅
- [x] User model (id, firebase_uid, email, role)
- [x] FounderProfile model
- [x] InvestorProfile model
- [x] POST /auth/signup endpoint
- [x] POST /auth/login endpoint
- [x] GET /auth/me endpoint
- [x] PUT /auth/profile endpoint
- [x] Firebase token verification service
- [x] JWT token generation

### 2.2 Mobile - Auth Screens ✅
- [x] LoginScreen.tsx
- [x] SignupScreen.tsx
- [x] RoleSelectScreen.tsx
- [x] AuthContext.tsx (with AsyncStorage persistence)
- [x] Role-based navigation (Founder vs Investor stacks)

---

## Phase 3: Founder Flow - Startup & Video Upload ✅ COMPLETE

### 3.1 Backend - Startup & Pitch ✅
- [x] Startup model
- [x] Pitch model
- [x] PitchView model
- [x] POST /startups endpoint
- [x] GET /startups endpoint
- [x] GET /startups/{id} endpoint
- [x] PUT /startups/{id} endpoint
- [x] DELETE /startups/{id} endpoint
- [x] POST /pitches/upload-url endpoint (GCS signed URL)
- [x] POST /pitches/{id}/publish endpoint
- [x] GET /pitches/founder/dashboard endpoint
- [x] Google Cloud Storage signed URL service

### 3.2 Mobile - Founder Screens ✅
- [x] FounderDashboardScreen.tsx (stats + startup list)
- [x] CreatePitchScreen.tsx (startup form with sectors, stages)
- [x] RecordVideoScreen.tsx (camera with 30s/5min timer)
- [x] FounderQAScreen.tsx (message threads)

---

## Phase 4: Investor Flow - Tinder-Style Swipe Feed ✅ COMPLETE

### 4.1 Backend - Feed & Views ✅
- [x] GET /pitches/feed endpoint (with filters + access info)
- [x] GET /pitches/{id} endpoint (with signed video URL)
- [x] POST /pitches/{id}/view endpoint (with view tracking)

### 4.2 Mobile - Swipeable Card Stack ✅
- [x] SwipeFeedScreen.tsx (Tinder-style swipe interface)
- [x] PitchCard.tsx (full-screen video card with gradient overlay)
- [x] SwipeOverlay.tsx (PASS/SAVE/Q&A Me overlays)
- [x] Swipe LEFT = Pass
- [x] Swipe RIGHT = Save/Interested
- [x] Swipe UP = Q&A Me
- [x] Action buttons (X, Q&A Me, Heart)
- [x] Video autoplay on active card

---

## Phase 5: Q&A Me Feature ✅ COMPLETE

### 5.1 Backend - Q&A & Question Templates ✅
- [x] QAThread model
- [x] QAMessage model
- [x] QuestionTemplate model (with 8 default questions)
- [x] POST /qa/threads endpoint
- [x] GET /qa/threads endpoint
- [x] POST /qa/threads/{id}/messages endpoint
- [x] GET /qa/threads/{id}/messages endpoint
- [x] GET /questions/templates endpoint
- [x] POST /questions/templates endpoint
- [x] PUT /questions/templates/{id} endpoint
- [x] DELETE /questions/templates/{id} endpoint
- [x] POST /questions/send-questions endpoint (bulk send)

### 5.2 Mobile - Q&A Me UI ✅
- [x] QAMeModal.tsx (multi-select question modal)
- [x] QuestionTemplatesScreen.tsx (manage saved questions)
- [x] Thread list in FounderQAScreen
- [x] Thread list in InvestorQAScreen
- [x] Custom question input support

---

## Phase 6: Onboarding Wizard ✅ COMPLETE

### 6.1 Backend - Onboarding Preferences ✅
- [x] Extended InvestorProfile with preferences (investor_type, sectors, stages, geographies, ticket_size)
- [x] Extended FounderProfile with preferences (seeking_investor_types, desired_check_size, value_add_preferences)
- [x] POST /auth/onboarding/investor endpoint
- [x] POST /auth/onboarding/founder endpoint
- [x] onboarding_completed flag on profiles

### 6.2 Mobile - Typeform-Style Wizard ✅
- [x] OnboardingStep.tsx (reusable step component with progress bar)
- [x] InvestorOnboardingScreen.tsx (5 steps)
  - Investor type (Angel, VC, Family Office, Syndicate)
  - Sectors of interest
  - Investment stages
  - Geographic focus
  - Typical check size
- [x] FounderOnboardingScreen.tsx (3 steps)
  - Types of investors seeking
  - Desired check size range
  - Value-add preferences
- [x] AuthContext updated with onboardingCompleted tracking
- [x] Navigation flow: Signup → Onboarding → Main App

---

## Phase 7: Freemium Model & View Limits ✅ COMPLETE

### 7.1 Backend - Freemium Access ✅
- [x] InvestorAccess class (tracks subscription + free views)
- [x] get_investor_with_access dependency
- [x] 15 free views per investor (one-time allowance)
- [x] View counting with duplicate prevention
- [x] Automatic free views decrement
- [x] 402 Payment Required when exhausted

### 7.2 Mobile - Paywall & Counter ✅
- [x] Free views counter badge in header
- [x] "Pro" badge for subscribers
- [x] Paywall screen when views exhausted
- [x] Real-time counter updates on swipe
- [x] Subscription CTA with friendly messaging

---

## Phase 8: Talent Feature (Job Seekers) ✅ COMPLETE

### 8.1 Backend - Talent Models ✅
- [x] TalentProfile model (with approval status, compensation preferences)
- [x] TalentPitch model (30-second video pitches)
- [x] TalentPitchView model (view tracking)
- [x] TalentQAThread model (recruiter-talent messaging)
- [x] TalentQAMessage model
- [x] Added talent_views_today fields to FounderProfile and InvestorProfile

### 8.2 Backend - Talent APIs ✅
- [x] POST /auth/signup with role="talent"
- [x] POST /auth/onboarding/talent endpoint
- [x] GET /auth/me returns talent profile with approval status
- [x] GET /talent-pitches/feed (for founders/investors, 5/day limit)
- [x] GET /talent-pitches/{id} (pitch detail with video URL)
- [x] POST /talent-pitches/upload-url (approved talent only)
- [x] POST /talent-pitches/{id}/publish
- [x] POST /talent-pitches/{id}/view (with daily view decrement)
- [x] GET /talent-pitches/my-pitch (talent's own pitch)
- [x] GET /talent-pitches/dashboard (talent stats)
- [x] POST /talent-qa/threads (create thread)
- [x] GET /talent-qa/threads (list threads)
- [x] POST/GET /talent-qa/threads/{id}/messages

### 8.3 Backend - Admin Approval ✅
- [x] GET /admin/talent/pending (list pending applications)
- [x] POST /admin/talent/{id}/approve
- [x] POST /admin/talent/{id}/reject
- [x] GET /admin/talent/stats

### 8.4 Quality Control ✅
- [x] Invite-only / Waitlist model (status: pending → approved)
- [x] Compensation types: equity_only, pay_equity, cash_only
- [x] Only approved talent can upload pitches
- [x] Only approved talent with published pitches appear in feed

### 8.5 Freemium for Talent Feed ✅
- [x] 5 talent views per day (daily reset at midnight)
- [x] Investors with subscription get unlimited views
- [x] Founders limited to 5/day (no subscription yet)

### 8.6 Mobile - Talent Screens ✅ COMPLETE (Jan 7, 2026)
- [x] TalentDashboardScreen.tsx (connected to API with loading states)
- [x] TalentOnboardingScreen.tsx (5-step wizard)
- [x] RecordTalentPitchScreen.tsx (with video upload to GCS)
- [x] TalentQAScreen.tsx (message threads list)
- [x] TalentThreadScreen.tsx (NEW - chat interface for conversations)
- [x] TalentSwipeFeedScreen.tsx (for founders/investors, with API)
- [x] TalentContactScreen.tsx (NEW - for initiating contact with talent)
- [x] TalentPitchCard.tsx component
- [x] Feed toggle (Startups | Talent) on SwipeFeedScreen
- [x] "Browse Talent" button on FounderDashboardScreen
- [x] Navigation updated with all talent screens
- [x] RoleSelectScreen already supports "I'm Talent" option

---

## Phase 10: Admin Panel & Support System ✅ COMPLETE (Jan 7, 2026)

### 10.1 Admin Web Panel (Next.js) ✅
- [x] Next.js 14 App Router + Tailwind CSS
- [x] Firebase Auth (shared with mobile, @caerus.app domain only)
- [x] Dashboard with stats (users by role, pending approvals, open tickets)
- [x] Founders list (search, view details)
- [x] Investors list (search, view details)
- [x] Talent list (filter by status, approve/reject actions)
- [x] Support inbox (list all tickets)
- [x] Ticket detail view (conversation thread, reply, resolve/reopen)

### 10.2 Backend - Admin Endpoints ✅
- [x] GET /admin/dashboard/stats
- [x] GET /admin/users/founders
- [x] GET /admin/users/investors
- [x] GET /admin/users/talent (with status filter)
- [x] GET /admin/support/tickets
- [x] GET /admin/support/tickets/{id}
- [x] POST /admin/support/tickets/{id}/reply
- [x] POST /admin/support/tickets/{id}/resolve
- [x] POST /admin/support/tickets/{id}/reopen

### 10.3 In-App Support (Mobile) ✅
- [x] SupportScreen.tsx (AI chat + contact form)
- [x] "Help & Support" button on Profile screen
- [x] Navigation configured for all user roles (Founder, Investor, Talent)

### 10.4 Support Backend ✅
- [x] SupportTicket model
- [x] SupportMessage model (sender_type: user/admin/ai)
- [x] POST /support/ai-chat (AI response without ticket)
- [x] POST /support/tickets (create ticket with initial message)
- [x] GET /support/tickets (user's own tickets)
- [x] GET /support/tickets/{id} (ticket with messages)
- [x] POST /support/tickets/{id}/messages (add message)

### 10.5 AI Support (Claude Haiku) ✅
- [x] Anthropic SDK integration (claude-3-haiku-20240307)
- [x] Context-aware system prompt (Caerus features, FAQ)
- [x] Returns `needs_human: true/false` for escalation
- [x] Graceful fallback if API unavailable

---

## Phase 9: Payments (StoreKit IAP) 🔲 TODO

### 9.1 Backend - IAP Verification
- [x] Subscription model
- [x] PitchUnlock model
- [x] POST /iap/verify-subscription endpoint (stub)
- [x] POST /iap/verify-unlock endpoint (stub)
- [x] GET /investor/subscription endpoint
- [x] Apple receipt verification service (stub)
- [ ] **TODO:** Test with real Apple receipts
- [ ] **TODO:** Handle subscription renewal webhooks

### 8.2 Mobile - Payment Screens
- [x] SubscriptionScreen.tsx (plan selection UI)
- [ ] **TODO:** Integrate react-native-iap purchase flow
- [ ] **TODO:** Handle purchase restoration
- [ ] **TODO:** Add 5-min pitch unlock purchase in CreatePitchScreen

### 8.3 App Store Connect Setup 🔲 (Manual - Chris)
- [ ] Create App ID
- [ ] Configure IAP products:
  - `com.caerus.founder.5min` - Non-consumable ($4.99)
  - `com.caerus.investor.monthly` - Auto-renewable ($29.99/mo)
  - `com.caerus.investor.annual` - Auto-renewable ($249.99/yr)
- [ ] Get Shared Secret for receipt verification
- [ ] Create sandbox test accounts

---

## Phase 9: Polish & Launch Prep 🔲 TODO

### 9.1 Video Upload Flow
- [ ] **TODO:** Complete video upload to GCS in RecordVideoScreen
- [ ] **TODO:** Add upload progress indicator
- [ ] **TODO:** Add retry logic for failed uploads
- [ ] **TODO:** Generate video thumbnails

### 9.2 Push Notifications
- [ ] **TODO:** Set up Expo Push Notifications
- [ ] **TODO:** Backend notification triggers for new Q&A messages
- [ ] **TODO:** Notification permission request flow

### 9.3 Error Handling & Loading States
- [ ] **TODO:** Add skeleton loaders to feed
- [ ] **TODO:** Add error boundaries
- [ ] **TODO:** Improve error messages throughout

### 9.4 UI/UX Polish
- [ ] **TODO:** Add pull-to-refresh on all lists
- [ ] **TODO:** Add empty state illustrations
- [ ] **TODO:** Implement full chat UI for Q&A threads
- [ ] **TODO:** Add startup logo upload
- [ ] **TODO:** Add investor profile editing

### 9.5 Testing
- [ ] **TODO:** Write backend unit tests
- [ ] **TODO:** Write API integration tests
- [ ] **TODO:** TestFlight beta setup

### 9.6 Deployment
- [ ] **TODO:** Deploy backend to Cloud Run (or Railway/Render)
- [ ] **TODO:** Set up production PostgreSQL (Supabase)
- [ ] **TODO:** Configure production environment variables
- [ ] **TODO:** Submit to App Store

---

## Files Created

### Backend (32 files)
```
backend/
├── main.py
├── requirements.txt
├── alembic.ini
├── .env.example
├── alembic/
│   ├── env.py
│   └── script.py.mako
└── app/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── models/
    │   ├── __init__.py
    │   ├── user.py (includes TalentProfile)
    │   ├── startup.py
    │   ├── pitch.py
    │   ├── qa.py
    │   ├── subscription.py
    │   ├── question_template.py
    │   ├── talent_pitch.py (NEW)
    │   └── talent_qa.py (NEW)
    ├── schemas/
    │   └── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── deps.py (includes talent dependencies)
    │   ├── auth.py (includes talent signup/onboarding)
    │   ├── startups.py
    │   ├── pitches.py
    │   ├── qa.py
    │   ├── subscriptions.py
    │   ├── question_templates.py
    │   ├── admin.py (NEW - talent approval)
    │   ├── talent_pitches.py (NEW)
    │   └── talent_qa.py (NEW)
    ├── services/
    │   ├── __init__.py
    │   ├── firebase.py
    │   ├── gcs.py
    │   └── iap_verify.py
    └── utils/
        └── __init__.py
```

### Mobile (30+ screen/component files)
```
mobile/src/
├── context/
│   └── AuthContext.tsx
├── navigation/
│   └── AppNavigator.tsx
├── components/
│   ├── PitchCard.tsx
│   ├── TalentPitchCard.tsx (NEW)
│   ├── SwipeOverlay.tsx
│   ├── QAMeModal.tsx
│   └── OnboardingStep.tsx
├── screens/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   ├── SignupScreen.tsx
│   │   └── RoleSelectScreen.tsx
│   ├── onboarding/
│   │   ├── InvestorOnboardingScreen.tsx
│   │   ├── FounderOnboardingScreen.tsx
│   │   └── TalentOnboardingScreen.tsx (NEW)
│   ├── founder/
│   │   ├── FounderDashboardScreen.tsx (updated with Browse Talent)
│   │   ├── CreatePitchScreen.tsx
│   │   ├── RecordVideoScreen.tsx
│   │   └── FounderQAScreen.tsx
│   ├── investor/
│   │   ├── SwipeFeedScreen.tsx (updated with feed toggle)
│   │   ├── TalentSwipeFeedScreen.tsx (NEW)
│   │   ├── TalentContactScreen.tsx (NEW)
│   │   ├── PitchDetailScreen.tsx
│   │   ├── InvestorQAScreen.tsx
│   │   ├── SubscriptionScreen.tsx
│   │   └── QuestionTemplatesScreen.tsx
│   ├── talent/ (NEW directory)
│   │   ├── TalentDashboardScreen.tsx
│   │   ├── RecordTalentPitchScreen.tsx
│   │   ├── TalentQAScreen.tsx
│   │   └── TalentThreadScreen.tsx
│   └── shared/
│       ├── ProfileScreen.tsx
│       └── SettingsScreen.tsx
├── services/
│   └── api.ts (includes talent APIs)
└── utils/
    └── constants.ts
```

### Admin Panel (New - Jan 7, 2026)
```
admin/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              # Dashboard
│   ├── login/page.tsx
│   ├── users/
│   │   ├── founders/page.tsx
│   │   ├── investors/page.tsx
│   │   └── talent/page.tsx
│   └── support/
│       ├── page.tsx          # Inbox list
│       └── [id]/page.tsx     # Ticket thread
├── components/
│   ├── AdminLayout.tsx
│   └── Sidebar.tsx
├── lib/
│   ├── firebase.ts
│   ├── auth-context.tsx
│   └── api.ts
├── package.json
├── tailwind.config.ts
└── next.config.js
```

### Infrastructure
```
infrastructure/
└── docker-compose.yml

README.md
PROGRESS.md (this file)
```

---

## Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Mobile | React Native + Expo | TypeScript, iOS-first |
| Backend | FastAPI (Python 3.13) | SQLAlchemy ORM, Alembic migrations |
| Admin Panel | Next.js 14 + Tailwind | App Router, Vercel hosting |
| Database | PostgreSQL | Supabase (pooler connection) |
| Auth | Firebase Auth | Email + Apple Sign-In |
| Storage | Google Cloud Storage | `caerus-pitch-videos` bucket (R&D project) |
| Video | expo-camera + expo-video | Record + playback |
| AI Support | Claude Haiku | Anthropic API for in-app support |
| Payments | StoreKit (IAP) | Subscriptions + unlocks |

---

## Quick Start Commands

```bash
# Start backend (uses cloud Supabase DB)
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start mobile
cd mobile
npm install
npx expo start

# Start admin panel (local dev)
cd admin
npm install
npm run dev
# Opens at http://localhost:3000

# Run database migrations (if schema changes)
cd backend
./venv/bin/alembic revision --autogenerate -m "description"
./venv/bin/alembic upgrade head

# Deploy admin to Vercel
cd admin
npx vercel
```

---

## Current Environment

| Service | Details |
|---------|---------|
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Admin Panel** | http://localhost:3000 (dev) / TBD (Vercel) |
| **Firebase Project** | `caerus-c29c9` |
| **Supabase DB** | `aws-1-eu-west-1.pooler.supabase.com` |
| **GCS Bucket** | `gs://caerus-pitch-videos` |
| **GCP Project** | `prj-rnd-4297` (R&D with credits) |
| **AI Support** | Claude Haiku via Anthropic API |

---

## Notes

- **Dev tokens:** Backend accepts `dev_` prefixed tokens in development mode for testing without Firebase
- **Subscription check:** Investor endpoints require subscription OR free views remaining (returns 402 if exhausted)
- **Video URLs:** GCS signed URLs expire after 60 minutes for downloads, 15 minutes for uploads
- **Free views:** Each investor gets 15 lifetime free views, then must subscribe
- **Onboarding:** Users must complete onboarding wizard before accessing main app
- **Service Account:** Firebase service account (`firebase-service-account.json`) is used for both Firebase Auth and GCS signing

### Environment Variables Required

**Backend (.env):**
```
DATABASE_URL=postgresql://...
FIREBASE_PROJECT_ID=caerus-c29c9
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=...
APPLE_SHARED_SECRET=...
```

**Admin (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=caerus-c29c9
```

### Deprecation Warnings - RESOLVED (Jan 7, 2026)
- ~~`expo-av` is deprecated in SDK 54~~ - Migrated to `expo-video` package
- ~~`SafeAreaView` from react-native is deprecated~~ - Migrated to `react-native-safe-area-context`
