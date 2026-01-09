Current Q&A Flow

  1. Investor swipes UP on founder video → "Q&A Me"
  2. Investor selects questions from templates or writes custom ones
  3. Questions sent to founder
  4. Founder sees thread in FounderQAScreen, replies with text
  5. Back-and-forth messaging continues

  Your Proposed Enhancements

  1. Speech-to-Text for Founder Answers

  This is a great UX improvement. Here's how it would work:

  [Question from Investor]
  "What's your go-to-market strategy?"

  [Answer Input]
  ┌─────────────────────────────────────┐
  │ Type your answer or tap mic...      │
  │                                     │
  │                              🎤     │
  └─────────────────────────────────────┘
         [Send]

  ↓ Tap mic ↓

  ┌─────────────────────────────────────┐
  │ 🔴 Listening...                     │
  │ "We're targeting enterprise SaaS    │
  │ companies with a bottom-up PLG      │
  │ motion..."                          │
  │                              ⏹️     │
  └─────────────────────────────────────┘

  ↓ Transcription complete ↓

  ┌─────────────────────────────────────┐
  │ We're targeting enterprise SaaS     │
  │ companies with a bottom-up PLG      │
  │ motion...                           │ ← Editable
  │                              🎤     │
  └─────────────────────────────────────┘
         [Send]

  Tech: expo-speech-recognition or @react-native-voice/voice

  ---
  2. Post-Q&A Investor Decision Flow

  After investor reads founder's Q&A responses:

  ┌─────────────────────────────────────┐
  │  Thread: Acme Corp                  │
  │                                     │
  │  [Q&A messages displayed...]        │
  │                                     │
  │  ─────────────────────────────────  │
  │                                     │
  │  Interested in this startup?        │
  │                                     │
  │  ┌─────────────┐  ┌─────────────┐  │
  │  │  💬 Connect │  │  ✋ Pass    │  │
  │  │  (DM Founder)│  │  (Politely) │  │
  │  └─────────────┘  └─────────────┘  │
  └─────────────────────────────────────┘

  "Connect" Flow:
  - Opens DM/chat with founder
  - Thread status changes to interested
  - Founder notified: "Investor X wants to connect!"

  "Pass Politely" Flow:
  ┌─────────────────────────────────────┐
  │  Decline Politely                   │
  │                                     │
  │  Add an optional message:           │
  │  ┌─────────────────────────────────┐│
  │  │ Thanks for your time. Not the   ││
  │  │ right fit for our fund focus    ││
  │  │ right now, but best of luck!    ││
  │  └─────────────────────────────────┘│
  │                                     │
  │  ┌────────────────────────────────┐ │
  │  │  Send & Close                  │ │
  │  └────────────────────────────────┘ │
  └─────────────────────────────────────┘

  - Thread status changes to declined
  - Founder notified: "Investor X has responded" (shows the message)
  - Closure for founder - they know where they stand

  ---
  3. Thread States

  class QAThreadStatus(str, Enum):
      active = "active"           # Q&A in progress
      awaiting_response = "awaiting_response"  # Waiting for founder
      interested = "interested"   # Investor wants to connect
      declined = "declined"       # Investor passed politely
      connected = "connected"     # DM conversation started

  ---
  4. Talent Flow (Simpler - Instagram-style DMs)

  No questionnaire. Just direct interest + messaging:

  [Talent Video Card]
  ┌─────────────────────────────────────┐
  │  [Video playing...]                 │
  │                                     │
  │  Sarah Chen                         │
  │  Senior Engineer • Seeking: Equity  │
  │                                     │
  │  [❤️ Interested]  [X Pass]          │
  └─────────────────────────────────────┘

  ↓ Tap Interested ↓

  ┌─────────────────────────────────────┐
  │  Message Sarah                      │
  │                                     │
  │  ┌─────────────────────────────────┐│
  │  │ Hi Sarah! Your background in    ││
  │  │ ML infra is exactly what we're  ││
  │  │ looking for. Would love to chat!││
  │  └─────────────────────────────────┘│
  │                                     │
  │  [Send Message]                     │
  └─────────────────────────────────────┘

  Talent gets notified: "New message from Acme Corp"

  ---
  Summary of New Features
  ┌────────────────────────┬────────────────┬──────────────────────────────────────────┐
  │        Feature         │      User      │               Description                │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ Speech-to-text answers │ Founder        │ Mic button on Q&A response input         │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ "Connect" CTA          │ Investor       │ Opens DM with founder after Q&A          │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ "Decline Politely" CTA │ Investor       │ Send closure message, mark declined      │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ Thread status tracking │ Both           │ active → interested/declined → connected │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ Notifications          │ Founder        │ Notified of both outcomes                │
  ├────────────────────────┼────────────────┼──────────────────────────────────────────┤
  │ Direct messaging       │ Talent viewers │ Instagram-style DMs, no questionnaire    │
  └────────────────────────┴────────────────┴──────────────────────────────────────────┘
  ---
  ## Implementation Progress

  ### Phase 1: Speech-to-Text for Founder Q&A Answers - COMPLETE

  Files created/modified:
  - `mobile/src/screens/founder/FounderThreadScreen.tsx` (NEW)
  - `mobile/src/screens/founder/FounderQAScreen.tsx` (updated)
  - `mobile/src/navigation/AppNavigator.tsx` (updated)
  - Added `expo-speech-recognition` package

  Features implemented:
  - Speech-to-text input with mic button
  - Real-time transcription that appends to text
  - Editable text after transcription
  - "Keep it concise" tip banner (shows once, dismissed with "Got it")
  - 500 character limit with counter
  - Pull-to-refresh on thread list
  - Navigate from thread list to conversation

  ### Phase 2: Thread Status + CTAs - COMPLETE

  Files created/modified:
  - `backend/app/models/qa.py` - Added ThreadStatus enum, status and decline_message fields
  - `backend/app/api/qa.py` - Added PUT /qa/threads/{id}/status endpoint, updated responses
  - `mobile/src/screens/investor/InvestorThreadScreen.tsx` (NEW)
  - `mobile/src/screens/investor/InvestorQAScreen.tsx` (updated)
  - `mobile/src/services/api.ts` - Added updateThreadStatus function
  - `mobile/src/navigation/AppNavigator.tsx` (updated)
  - Database migration: `add_thread_status_and_decline_message`

  Features implemented:
  - Thread status tracking: 'active' | 'interested' | 'declined'
  - "Connect" CTA - Express interest to founder
  - "Pass Politely" CTA - Decline with optional message
  - Decline modal with placeholder text for polite message
  - Status badges in thread list (green "Interested", gray "Passed")
  - Status banner in conversation view
  - Pull-to-refresh on thread list
  - Founder sees decline message in their thread view

  ### Phase 3: Notifications - COMPLETE

  Files created/modified:
  - `backend/app/models/user.py` - Added push_token field to User
  - `backend/app/services/notifications.py` (NEW) - Expo push notification service
  - `backend/app/api/auth.py` - Added POST/DELETE /auth/push-token endpoints
  - `backend/app/api/qa.py` - Sends notifications on thread status change
  - `mobile/src/context/AuthContext.tsx` - Auto-registers push token on login
  - `mobile/src/services/api.ts` - Added registerPushToken/unregisterPushToken
  - `mobile/src/hooks/useNotifications.ts` (NEW) - Notification handling hook
  - Database migration: `add_push_token_to_users`

  Features implemented:
  - Expo push notifications via Expo's API
  - Push token stored per user in database
  - Auto-registration on login/signup
  - Auto-unregister on logout
  - Foreground notification display enabled
  - Android notification channel configured
  - Different notification messages:
    - "Interested": "An investor is interested! {name} wants to connect about {startup}"
    - "Declined": "Investor response received. {name} responded with feedback"
  - Deep link data included for navigation (thread_id, screen)

  ### Phase 4: Talent DM Flow with Subscription Limit - COMPLETE

  Files created/modified:
  - `backend/app/models/user.py` - Added DM tracking fields to FounderProfile and InvestorProfile
  - `backend/app/api/deps.py` - Added TalentDMAccess class and get_talent_dm_access dependency
  - `backend/app/api/talent_qa.py` - Added DM limit check to thread creation, GET /dm-access endpoint
  - `backend/app/api/profiles.py` (NEW) - GET /profiles/investor/{id} for trust verification
  - `backend/main.py` - Registered profiles router
  - `mobile/src/services/api.ts` - Added getDMAccess, getInvestorProfile endpoints
  - `mobile/src/components/DMPaywallModal.tsx` (NEW) - Paywall when DM limit reached
  - `mobile/src/components/InvestorProfileModal.tsx` (NEW) - Trust verification modal
  - `mobile/src/screens/investor/TalentContactScreen.tsx` - Added DM limit check and paywall
  - `mobile/src/screens/founder/FounderThreadScreen.tsx` - Added clickable investor avatar
  - `mobile/src/screens/talent/TalentThreadScreen.tsx` - Added clickable investor avatar
  - Database migration: `add_talent_dm_tracking`

  Features implemented:
  - 5 free DMs per month for founders and investors
  - Monthly DM tracking with automatic reset
  - 402 Payment Required when limit reached
  - DMs remaining badge on TalentContactScreen
  - DMPaywallModal with role-specific pricing ($9.99 founders, $20 investors)
  - Investor profile viewing for trust verification (clickable avatar in thread headers)
  - InvestorProfileModal showing: name, firm, LinkedIn, sectors, stages, verified badge
  - Founders and talent can tap investor avatars to view profiles before engaging