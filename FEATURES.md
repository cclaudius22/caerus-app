# Caerus - Product Features & Functionality

**Tagline:** Tinder for Founders & Investors

**Version:** MVP 1.0
**Last Updated:** December 31, 2024

---

## Executive Summary

Caerus is a mobile-first video pitch marketplace that connects startup founders with investors through a familiar, swipe-based discovery experience. Founders upload 30-second video pitches; investors swipe to discover, save, and engage with startups that match their investment thesis.

---

## Core Value Proposition

| For Founders | For Investors |
|--------------|---------------|
| Reach investors beyond your network | Discover startups efficiently |
| Video-first pitching (show, don't tell) | Swipe-based discovery (like Tinder) |
| Know when investors are interested | Filter by sector, stage, geography |
| Answer questions asynchronously | Pre-saved questions for quick DD |
| Affordable premium features | Freemium with subscription upgrade |

---

## User Personas

### Founder
- Early-stage startup (Idea to Series A)
- Actively fundraising or building investor relationships
- Wants efficient, scalable way to pitch beyond warm intros
- Values async communication

### Investor
- Angel investors, VCs, Family Offices, Syndicate Leads
- Looks at 100s of deals, needs efficient filtering
- Has specific investment thesis (sector, stage, check size)
- Wants to ask quick due diligence questions

---

## Feature Overview

### 1. Swipe-Based Discovery (Investor)

**The Core Experience:**
```
┌─────────────────────────────┐
│                             │
│     [VIDEO AUTOPLAYS]       │
│                             │
│  ─────────────────────────  │
│  TechStartup Inc.           │
│  Seed • SaaS • San Francisco│
│  "AI-powered sales tools"   │
└─────────────────────────────┘
       ✕      💬       ♥
      Pass  Q&A Me   Save
```

**Gestures:**
- **Swipe Left** → Pass (not interested)
- **Swipe Right** → Save (interested, adds to saved list)
- **Swipe Up** → Q&A Me (send questions to founder)

**Features:**
- Full-screen video cards with gradient overlay
- Video autoplays when card is active
- Stacked cards (see next 2-3 pitches behind)
- Smooth animations and haptic feedback
- Action buttons for accessibility

---

### 2. Q&A Me (Investor → Founder Communication)

**Concept:** Investors can quickly send due diligence questions without composing messages from scratch.

**How It Works:**
1. Investor taps "Q&A Me" on a pitch
2. Modal shows their pre-saved question templates
3. Multi-select questions (e.g., "What's your MRR?", "How did you validate the problem?")
4. Optionally add a custom question
5. Tap "Send" → Creates thread with founder

**Default Question Templates:**
- What's your current MRR/ARR?
- How did you validate the problem?
- What's your unfair advantage?
- Who are your main competitors?
- What's your go-to-market strategy?
- Tell me about your team's background
- What are you looking for in an investor?
- What's your runway and burn rate?

**Question Management:**
- Investors can add/edit/delete their templates
- Reorder questions by priority
- Templates persist across sessions

---

### 3. Onboarding Wizard (Typeform-Style)

**Purpose:** Capture investment preferences for personalization and matching.

**Investor Onboarding (5 Steps):**
1. **Investor Type:** Angel / VC / Family Office / Syndicate Lead
2. **Sectors:** Multi-select (SaaS, Fintech, HealthTech, AI/ML, etc.)
3. **Stages:** Multi-select (Idea, Pre-seed, Seed, Series A)
4. **Geographies:** Multi-select (US, Europe, Asia, etc.)
5. **Ticket Size:** $10K-$25K / $25K-$50K / ... / $500K+

**Founder Onboarding (3 Steps):**
1. **Investor Types Seeking:** Angel / VC / Family Office / Syndicate
2. **Desired Check Size:** $25K-$50K / $50K-$100K / ... / $1M+
3. **Value-Add Preferences:** Network & Intros / Operational Support / Domain Expertise / Hands-Off Capital

**UX:**
- Progress bar at top
- One question per screen
- Large tap targets for options
- Checkmark feedback on selection
- Back button to revise answers

---

### 4. Freemium Model (Investor)

**Free Tier:**
- 15 lifetime pitch views
- Full access to onboarding
- Access to saved pitches and conversations
- Question templates

**Premium Subscription:**
- Unlimited pitch views
- Priority support
- Future: Advanced filters, deal flow analytics

**Paywall Flow:**
```
Free views remaining: 15 → 14 → 13 → ... → 0
                                            ↓
                                      [Paywall Screen]
                                "Free Views Exhausted"
                                   [Subscribe Now]
```

**Technical:**
- `free_views_remaining` counter on InvestorProfile
- Decrements on each unique pitch view
- 402 Payment Required when exhausted
- Views counter badge in header

---

### 5. Founder Dashboard

**Stats Overview:**
- Total views across all pitches
- Unique investors reached
- Questions received

**Startup Management:**
- List of created startups
- Pitch status (Draft / Published)
- View count per pitch
- Quick actions (Edit, Record New)

---

### 6. Video Pitch Recording (Founder)

**30-Second Free Pitch:**
- In-app camera recording
- Countdown timer (30s limit)
- Auto-stops at limit
- Preview before publishing
- Re-record option

**5-Minute Premium Pitch (Future):**
- Extended format for deep dives
- Paid unlock ($4.99)
- For serious investor engagement

---

### 7. Startup Profile (Founder)

**Required Fields:**
- Startup name
- Tagline (one-liner)
- Sector (from predefined list)
- Stage (Idea / Pre-seed / Seed / Series A)

**Optional Fields:**
- Website URL
- Location
- Fundraising round size (min/max)
- Traction bullets (3-5 key metrics)
- Logo upload

---

### 8. Q&A Threads (Both Sides)

**For Investors:**
- View all conversations
- See which startups responded
- Continue discussions
- Thread organized by startup

**For Founders:**
- Inbox of investor questions
- Reply with text or video
- See investor profiles
- Mark as read/unread

---

## User Flows

### Investor Journey
```
Download App
    ↓
Sign Up (Email)
    ↓
Select Role: Investor
    ↓
Onboarding Wizard (5 steps)
    ↓
Swipe Feed (15 free views)
    ↓
Swipe Right → Saved
Swipe Up → Q&A Me Modal → Send Questions
    ↓
Messages Tab → View Responses
    ↓
Views Exhausted → Paywall → Subscribe
    ↓
Unlimited Access
```

### Founder Journey
```
Download App
    ↓
Sign Up (Email)
    ↓
Select Role: Founder
    ↓
Onboarding Wizard (3 steps)
    ↓
Dashboard (empty state)
    ↓
Create Startup Profile
    ↓
Record 30s Pitch
    ↓
Publish → Live on Feed
    ↓
Receive Questions → Reply
    ↓
Track Views & Engagement
```

---

## Technical Architecture

### Mobile App (React Native + Expo)
- iOS-first (App Store)
- TypeScript for type safety
- React Navigation for routing
- expo-camera for recording
- expo-av for video playback
- react-native-deck-swiper for cards
- AsyncStorage for persistence

### Backend (FastAPI + Python)
- RESTful API
- SQLAlchemy ORM
- Alembic migrations
- JWT authentication
- Firebase token verification
- Presigned URLs for video upload/download

### Database (PostgreSQL via Supabase)
- Users, Profiles (Founder/Investor)
- Startups, Pitches, PitchViews
- QAThreads, QAMessages
- QuestionTemplates
- Subscriptions, PitchUnlocks

### Storage (Cloudflare R2)
- Video file storage
- 10GB free tier
- Zero egress costs
- S3-compatible API
- Presigned URLs for security

### Authentication (Firebase)
- Email/password
- Apple Sign-In (iOS)
- Secure token verification

---

## Monetization Model

| Product | Type | Price | Target |
|---------|------|-------|--------|
| Investor Monthly | Subscription | $29.99/mo | Power users |
| Investor Annual | Subscription | $249.99/yr | Committed users |
| 5-Min Pitch Unlock | One-time | $4.99 | Founders wanting deep-dive format |

**Revenue Projections (Hypothetical):**
- 1,000 investor subscribers × $30/mo = $30K MRR
- 500 founder unlocks × $5 = $2.5K one-time

---

## Competitive Advantages

1. **Video-First:** Unlike text-heavy platforms (AngelList, LinkedIn), video conveys personality and passion
2. **Swipe UX:** Familiar, engaging, low-friction (borrowed from dating apps)
3. **Q&A Me:** Structured communication reduces friction vs. cold emails
4. **Freemium:** Low barrier to entry, clear upgrade path
5. **Mobile-First:** Investors can review pitches anywhere (commute, coffee break)

---

## Future Roadmap

### Phase 2 (Post-MVP)
- [ ] Smart matching based on preferences
- [ ] Push notifications for new messages
- [ ] Video replies from founders
- [ ] Investor verification badges
- [ ] Startup analytics dashboard

### Phase 3 (Scale)
- [ ] AI-powered pitch feedback
- [ ] Deal room for serious negotiations
- [ ] Intro requests (investor-to-investor)
- [ ] Syndicate formation tools
- [ ] API for VC CRM integrations

### Phase 4 (Platform)
- [ ] Android app
- [ ] Web dashboard for founders
- [ ] White-label for accelerators
- [ ] International expansion (localization)

---

## Success Metrics

| Metric | Description | Target (MVP) |
|--------|-------------|--------------|
| DAU | Daily active users | 500 |
| Pitches Uploaded | Founder engagement | 200 |
| Swipes per Session | Investor engagement | 15+ |
| Q&A Messages Sent | Meaningful connections | 10% of saves |
| Conversion to Paid | Monetization | 5% of investors |
| NPS | User satisfaction | 40+ |

---

## Security & Compliance

- **Data Encryption:** TLS in transit, encrypted at rest
- **Auth:** Firebase + JWT, secure token handling
- **Video Privacy:** Presigned URLs with expiration
- **GDPR Ready:** Data export and deletion capabilities
- **App Store Compliant:** IAP for all payments

---

## Team Requirements (For Handover)

| Role | Responsibility |
|------|----------------|
| iOS Developer | Expo/React Native, video handling, IAP integration |
| Backend Developer | FastAPI, PostgreSQL, API development |
| Designer | UI/UX polish, empty states, animations |
| DevOps | Deployment, CI/CD, monitoring |
| Product | Feature prioritization, user feedback |

---

## Appendix: API Endpoints

### Auth
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `GET /auth/me` - Current user + profile
- `POST /auth/onboarding/investor` - Complete investor onboarding
- `POST /auth/onboarding/founder` - Complete founder onboarding

### Startups
- `POST /startups` - Create startup
- `GET /startups` - List founder's startups
- `PUT /startups/{id}` - Update startup
- `DELETE /startups/{id}` - Delete startup

### Pitches
- `POST /pitches/upload-url` - Get video upload URL
- `POST /pitches/{id}/publish` - Publish pitch
- `GET /pitches/feed` - Investor feed
- `GET /pitches/{id}` - Pitch detail with video URL
- `POST /pitches/{id}/view` - Record view

### Q&A
- `GET /qa/threads` - List threads
- `POST /qa/threads` - Create thread
- `GET /qa/threads/{id}/messages` - Get messages
- `POST /qa/threads/{id}/messages` - Send message

### Question Templates
- `GET /questions/templates` - List templates
- `POST /questions/templates` - Create template
- `POST /questions/send-questions` - Send questions to founder

### Subscriptions
- `POST /iap/verify-subscription` - Verify App Store receipt
- `GET /investor/subscription` - Subscription status

---

*Document prepared for development handover and pitch deck creation.*
