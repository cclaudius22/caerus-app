from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
from app.config import settings

# Initialize Firebase Admin SDK
_firebase_app = None


def get_firebase_app():
    """Get or initialize Firebase Admin app."""
    global _firebase_app
    if _firebase_app is None:
        try:
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
                _firebase_app = firebase_admin.initialize_app(cred)
            else:
                # Use default credentials (for Cloud Run, etc.)
                _firebase_app = firebase_admin.initialize_app()
        except ValueError:
            # Already initialized
            _firebase_app = firebase_admin.get_app()
    return _firebase_app


async def verify_firebase_token(token: str) -> Optional[str]:
    """
    Verify Firebase ID token and return the user's UID.

    Args:
        token: Firebase ID token from client

    Returns:
        Firebase UID if valid, None otherwise
    """
    try:
        # In development, allow a mock token for testing
        if settings.ENVIRONMENT == "development" and token.startswith("dev_"):
            # Return mock UID for development
            return token.replace("dev_", "mock_uid_")

        # Initialize Firebase if needed
        get_firebase_app()

        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception as e:
        print(f"Firebase token verification error: {e}")
        return None


async def get_firebase_user(uid: str) -> Optional[dict]:
    """
    Get Firebase user info by UID.

    Args:
        uid: Firebase user UID

    Returns:
        User info dict if found, None otherwise
    """
    try:
        get_firebase_app()
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "email_verified": user.email_verified
        }
    except Exception as e:
        print(f"Firebase get user error: {e}")
        return None
