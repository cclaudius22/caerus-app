from typing import Optional, Dict
import httpx
from app.config import settings

SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"


class IAPVerifier:
    """Apple In-App Purchase receipt verification service."""

    def __init__(self):
        self.shared_secret = settings.APPLE_SHARED_SECRET

    async def verify_receipt(self, receipt_data: str) -> Optional[Dict]:
        """
        Verify Apple IAP receipt.

        Args:
            receipt_data: Base64 encoded receipt data from client

        Returns:
            Verified receipt data dict if valid, None otherwise
        """
        payload = {
            "receipt-data": receipt_data,
            "password": self.shared_secret,
            "exclude-old-transactions": True
        }

        async with httpx.AsyncClient() as client:
            # Try production first
            response = await client.post(PRODUCTION_URL, json=payload)
            data = response.json()

            # Status 21007 means it's a sandbox receipt
            if data.get("status") == 21007:
                response = await client.post(SANDBOX_URL, json=payload)
                data = response.json()

            # Status 0 means valid receipt
            if data.get("status") == 0:
                return data

            return None

    def extract_subscription_info(self, receipt_data: Dict) -> Optional[Dict]:
        """
        Extract subscription details from verified receipt.

        Args:
            receipt_data: Verified receipt data from Apple

        Returns:
            Dict with subscription info or None
        """
        latest_info = receipt_data.get("latest_receipt_info", [])

        if not latest_info:
            return None

        # Get the most recent transaction
        latest = sorted(
            latest_info,
            key=lambda x: int(x.get("expires_date_ms", 0)),
            reverse=True
        )[0]

        return {
            "transaction_id": latest.get("transaction_id"),
            "original_transaction_id": latest.get("original_transaction_id"),
            "product_id": latest.get("product_id"),
            "expires_date_ms": int(latest.get("expires_date_ms", 0)),
        }

    def extract_purchase_info(self, receipt_data: Dict, product_id: str) -> Optional[Dict]:
        """
        Extract purchase info for a specific product (non-consumable).

        Args:
            receipt_data: Verified receipt data from Apple
            product_id: The product ID to look for

        Returns:
            Dict with purchase info or None
        """
        in_app = receipt_data.get("receipt", {}).get("in_app", [])

        for purchase in in_app:
            if purchase.get("product_id") == product_id:
                return {
                    "transaction_id": purchase.get("transaction_id"),
                    "original_transaction_id": purchase.get("original_transaction_id"),
                    "product_id": purchase.get("product_id"),
                    "purchase_date_ms": int(purchase.get("purchase_date_ms", 0)),
                }

        return None

    def is_subscription_active(self, receipt_data: Dict) -> bool:
        """
        Check if subscription is currently active.

        Args:
            receipt_data: Verified receipt data from Apple

        Returns:
            True if subscription is active, False otherwise
        """
        import time

        sub_info = self.extract_subscription_info(receipt_data)
        if not sub_info:
            return False

        current_time_ms = int(time.time() * 1000)
        return sub_info["expires_date_ms"] > current_time_ms
