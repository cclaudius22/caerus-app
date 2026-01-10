# Caerus Test Results

## 2026-01-10 - Initial Test Suite Setup

### Summary
| Component | Tests | Passed | Failed | Coverage |
|-----------|-------|--------|--------|----------|
| Backend   | 50    | 50     | 0      | Critical paths |
| Mobile    | 32    | 32     | 0      | Business logic |
| **Total** | **82**| **82** | **0**  | - |

---

## Backend Tests

### How to Run
```bash
cd backend
source venv/bin/activate
pytest -v
```

### Test Coverage
- **Authentication**: Signup, login, token validation, unauthorized access
- **Onboarding**: Investor, founder, and talent onboarding flows
- **Startups**: Create, list, update operations
- **Pitches**: Upload URL generation, feed retrieval, dashboard
- **Question Templates**: CRUD operations, default templates
- **Profile Management**: Update profile, complete profile
- **Subscriptions**: IAP endpoint registration, verification
- **Talent**: Pitch upload (approval required), feed access, dashboard
- **Support**: AI chat, ticket creation, ticket listing

### Test Output
```
tests/test_api.py::TestHealthCheck::test_root_endpoint PASSED
tests/test_api.py::TestHealthCheck::test_docs_accessible PASSED
tests/test_api.py::TestHealthCheck::test_openapi_schema PASSED
tests/test_api.py::TestAPIRoutes::test_auth_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_startup_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_pitch_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_qa_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_question_template_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_talent_routes_exist PASSED
tests/test_api.py::TestAPIRoutes::test_auth_onboarding_talent_route_exists PASSED
tests/test_api.py::TestGCSService::test_gcs_service_initialization PASSED
tests/test_api.py::TestGCSService::test_gcs_credentials_loaded PASSED
tests/test_api.py::TestGCSService::test_gcs_upload_url_generation PASSED
tests/test_api.py::TestGCSService::test_gcs_download_url_generation PASSED
tests/test_api.py::TestGCSService::test_gcs_upload_url_custom_content_type PASSED
tests/test_api.py::TestGCSService::test_gcs_object_not_exists PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_founder_signup_returns_token PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_investor_signup_returns_token PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_founder_can_create_startup PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_investor_gets_default_questions PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_me_endpoint_returns_user PASSED
tests/test_api.py::TestEndToEndWithLiveDB::test_talent_signup_returns_pending_status PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_founder_signup_creates_user PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_investor_signup_creates_user PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_talent_signup_creates_pending_user PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_me_endpoint_returns_user_data PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_unauthorized_access_rejected PASSED
tests/test_critical_paths.py::TestAuthenticationFlow::test_invalid_token_rejected PASSED
tests/test_critical_paths.py::TestInvestorOnboarding::test_investor_can_complete_onboarding PASSED
tests/test_critical_paths.py::TestFounderOnboarding::test_founder_can_complete_onboarding PASSED
tests/test_critical_paths.py::TestTalentOnboarding::test_talent_can_complete_onboarding PASSED
tests/test_critical_paths.py::TestStartupManagement::test_founder_can_create_startup PASSED
tests/test_critical_paths.py::TestStartupManagement::test_founder_can_list_startups PASSED
tests/test_critical_paths.py::TestStartupManagement::test_founder_can_update_startup PASSED
tests/test_critical_paths.py::TestPitchFlow::test_founder_can_get_upload_url PASSED
tests/test_critical_paths.py::TestPitchFlow::test_investor_can_view_feed PASSED
tests/test_critical_paths.py::TestPitchFlow::test_founder_can_view_dashboard PASSED
tests/test_critical_paths.py::TestQuestionTemplates::test_investor_gets_default_templates PASSED
tests/test_critical_paths.py::TestQuestionTemplates::test_investor_can_create_template PASSED
tests/test_critical_paths.py::TestQuestionTemplates::test_investor_can_delete_custom_template PASSED
tests/test_critical_paths.py::TestProfileManagement::test_user_can_update_profile PASSED
tests/test_critical_paths.py::TestProfileManagement::test_user_can_complete_profile PASSED
tests/test_critical_paths.py::TestSubscriptionEndpoints::test_iap_endpoints_registered PASSED
tests/test_critical_paths.py::TestSubscriptionEndpoints::test_iap_verify_endpoint_exists PASSED
tests/test_critical_paths.py::TestTalentPitchFlow::test_pending_talent_cannot_upload PASSED
tests/test_critical_paths.py::TestTalentPitchFlow::test_talent_feed_accessible PASSED
tests/test_critical_paths.py::TestTalentPitchFlow::test_talent_can_view_dashboard PASSED
tests/test_critical_paths.py::TestSupportFlow::test_user_can_use_ai_chat PASSED
tests/test_critical_paths.py::TestSupportFlow::test_user_can_create_support_ticket PASSED
tests/test_critical_paths.py::TestSupportFlow::test_user_can_list_tickets PASSED

======================== 50 passed in 13.75s ========================
```

### Test Files
- `backend/tests/test_api.py` - API health checks, route verification, GCS service
- `backend/tests/test_critical_paths.py` - Critical user flow tests
- `backend/tests/conftest.py` - Shared fixtures

---

## Mobile Tests

### How to Run
```bash
cd mobile
npm test
```

### Test Coverage
- **Subscription Plans**: Plan configuration, pricing, features
- **User Initials**: Generation logic for avatars
- **Role Capitalization**: Display formatting
- **Subscription Status**: Active/expired/cancelled logic
- **View Counters**: Free tier limits for pitches and talent

### Test Output
```
PASS src/__tests__/logic/business-logic.test.ts
  Subscription Plans
    Plan Configuration
      ✓ should have two plans available
      ✓ should have monthly plan with correct price
      ✓ should have annual plan with correct price
      ✓ should mark annual plan as highlighted
      ✓ should have cancel text on monthly plan
    Plan Features
      ✓ should have at least 5 features for monthly plan
      ✓ should have at least 4 features for annual plan
      ✓ should include DM capability in monthly features
  User Initials Generator
      ✓ should return two initials for full name
      ✓ should return first and last initial for multiple names
      ✓ should return single initial for single name
      ✓ should fallback to email initial when no name
      ✓ should return U when no name or email
      ✓ should handle names with extra whitespace
      ✓ should handle uppercase names
      ✓ should handle lowercase names
  Role Capitalization
      ✓ should capitalize founder role
      ✓ should capitalize investor role
      ✓ should capitalize talent role
      ✓ should handle undefined role
      ✓ should handle already capitalized role
  Subscription Status Logic
      ✓ should return false for null subscription
      ✓ should return false for expired status
      ✓ should return false for cancelled status
      ✓ should return true for active subscription with future expiry
      ✓ should return false for active subscription with past expiry
  Pitch View Counter
      ✓ should allow view when under free limit
      ✓ should block view when at free limit
      ✓ should allow view with subscription regardless of count
      ✓ should allow talent view under daily limit
      ✓ should block talent view at daily limit
      ✓ should allow talent view with subscription

Test Suites: 1 passed, 1 total
Tests:       32 passed, 32 total
Time:        1.462 s
```

### Test Files
- `mobile/src/__tests__/logic/business-logic.test.ts` - Business logic tests
- `mobile/jest.config.js` - Jest configuration

---

## Notes

### Backend Prerequisites
- Python virtual environment activated
- Environment variables configured in `.env`
- Database accessible (uses live Supabase for E2E tests)

### Mobile Prerequisites
- Node modules installed (`npm install`)
- Uses ts-jest for TypeScript transformation

### Known Limitations
- Mobile component tests (React Native) require additional Expo-specific configuration
- Current setup focuses on business logic tests that don't require React Native runtime
- Backend E2E tests create real test data in the database

---

## Quick Reference

```bash
# Run all backend tests
cd backend && source venv/bin/activate && pytest -v

# Run all mobile tests
cd mobile && npm test

# Run backend tests with coverage
cd backend && source venv/bin/activate && pytest --cov=app tests/

# Run mobile tests with coverage
cd mobile && npm run test:coverage
```
