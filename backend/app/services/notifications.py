"""
Push notification service using Expo's push notification API.

Expo push notifications are sent via HTTP POST to https://exp.host/--/api/v2/push/send
"""

import httpx
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class NotificationType:
    """Notification types for the app."""
    INVESTOR_INTERESTED = "investor_interested"
    INVESTOR_DECLINED = "investor_declined"
    NEW_QUESTION = "new_question"
    NEW_MESSAGE = "new_message"
    TALENT_INTEREST = "talent_interest"


async def send_push_notification(
    push_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
    sound: str = "default",
) -> bool:
    """
    Send a single push notification via Expo.

    Args:
        push_token: The Expo push token (starts with ExponentPushToken[)
        title: Notification title
        body: Notification body text
        data: Optional extra data to include (for deep linking)
        badge: Optional badge number to show on app icon
        sound: Sound to play ("default" or None)

    Returns:
        True if sent successfully, False otherwise
    """
    if not push_token or not push_token.startswith("ExponentPushToken["):
        logger.warning(f"Invalid push token format: {push_token}")
        return False

    message = {
        "to": push_token,
        "title": title,
        "body": body,
        "sound": sound,
    }

    if data:
        message["data"] = data

    if badge is not None:
        message["badge"] = badge

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=message,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                result = response.json()
                # Check for errors in the response
                if result.get("data", {}).get("status") == "error":
                    logger.error(f"Expo push error: {result}")
                    return False
                logger.info(f"Push notification sent successfully to {push_token[:30]}...")
                return True
            else:
                logger.error(f"Expo push failed with status {response.status_code}: {response.text}")
                return False

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False


async def send_bulk_notifications(
    messages: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Send multiple push notifications in bulk.

    Args:
        messages: List of message dicts with keys: to, title, body, data (optional)

    Returns:
        Dict with "sent" and "failed" counts
    """
    if not messages:
        return {"sent": 0, "failed": 0}

    # Filter out invalid tokens
    valid_messages = [
        m for m in messages
        if m.get("to") and m["to"].startswith("ExponentPushToken[")
    ]

    if not valid_messages:
        return {"sent": 0, "failed": len(messages)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=valid_messages,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                data = result.get("data", [])
                sent = sum(1 for d in data if d.get("status") == "ok")
                failed = len(data) - sent
                return {"sent": sent, "failed": failed}
            else:
                logger.error(f"Bulk push failed: {response.text}")
                return {"sent": 0, "failed": len(valid_messages)}

    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {e}")
        return {"sent": 0, "failed": len(valid_messages)}


# Convenience functions for specific notification types

async def notify_founder_investor_interested(
    founder_push_token: str,
    investor_name: str,
    startup_name: str,
    thread_id: str,
) -> bool:
    """Notify founder that an investor expressed interest."""
    return await send_push_notification(
        push_token=founder_push_token,
        title="An investor is interested!",
        body=f"{investor_name} wants to connect about {startup_name}",
        data={
            "type": NotificationType.INVESTOR_INTERESTED,
            "thread_id": thread_id,
            "screen": "FounderThread",
        },
    )


async def notify_founder_investor_declined(
    founder_push_token: str,
    investor_name: str,
    startup_name: str,
    thread_id: str,
    has_message: bool = False,
) -> bool:
    """Notify founder that an investor passed (politely)."""
    body = f"{investor_name} responded to your Q&A for {startup_name}"
    if has_message:
        body += " with feedback"

    return await send_push_notification(
        push_token=founder_push_token,
        title="Investor response received",
        body=body,
        data={
            "type": NotificationType.INVESTOR_DECLINED,
            "thread_id": thread_id,
            "screen": "FounderThread",
        },
    )


async def notify_founder_new_question(
    founder_push_token: str,
    investor_name: str,
    startup_name: str,
    thread_id: str,
) -> bool:
    """Notify founder of a new question from an investor."""
    return await send_push_notification(
        push_token=founder_push_token,
        title="New question from an investor",
        body=f"{investor_name} asked about {startup_name}",
        data={
            "type": NotificationType.NEW_QUESTION,
            "thread_id": thread_id,
            "screen": "FounderThread",
        },
    )


async def notify_investor_founder_replied(
    investor_push_token: str,
    founder_name: str,
    startup_name: str,
    thread_id: str,
) -> bool:
    """Notify investor that a founder replied to their question."""
    return await send_push_notification(
        push_token=investor_push_token,
        title=f"{startup_name} replied",
        body=f"{founder_name} answered your question",
        data={
            "type": NotificationType.NEW_MESSAGE,
            "thread_id": thread_id,
            "screen": "InvestorThread",
        },
    )


async def notify_talent_new_interest(
    talent_push_token: str,
    company_name: str,
    recruiter_name: str,
    thread_id: str,
) -> bool:
    """Notify talent of interest from a founder/investor."""
    return await send_push_notification(
        push_token=talent_push_token,
        title="Someone's interested!",
        body=f"{recruiter_name} from {company_name} wants to connect",
        data={
            "type": NotificationType.TALENT_INTEREST,
            "thread_id": thread_id,
            "screen": "TalentThread",
        },
    )
