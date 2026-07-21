"""Helius Webhook management service.

This module provides a manager to programmatically update Helius webhooks,
allowing the bot to add or remove monitored Solana addresses.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from src.config import settings

logger = logging.getLogger(__name__)


class HeliusWebhookManager:
    """Manages Helius webhooks via their REST API."""

    def __init__(self) -> None:
        """Initializes the manager with API credentials and a concurrency lock."""
        self._api_key = settings.helius_api_key
        self._base_url = "https://api.helius.xyz/v0/webhooks"
        self._lock = asyncio.Lock()

    async def _send_request(
        self,
        method: str,
        webhook_id: str,
        payload: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Sends an authenticated request to the Helius Webhook API.

        Args:
            method: HTTP method (GET, PUT).
            webhook_id: The unique ID of the webhook.
            payload: Data to send in the request body.

        Returns:
            The JSON response from Helius, or None on failure.
        """
        url = f"{self._base_url}/{webhook_id}?api-key={self._api_key}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.request(method, url, json=payload)
                if response.status_code != 200:
                    logger.error(
                        "Helius API error (%s) on %s: %d - %s",
                        method, webhook_id, response.status_code, response.text
                    )
                    return None
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    "Connection error (%s) on %s: %s", method, webhook_id, e
                )
                return None

    async def update_addresses(
        self, webhook_id: str, addresses: list[str]
    ) -> bool:
        """Updates the list of monitored addresses for a webhook.

        Args:
            webhook_id: The ID of the webhook to update.
            addresses: The new complete list of addresses to monitor.

        Returns:
            True if the update was successful, False otherwise.
        """
        current_info = await self.get_webhook_info(webhook_id)
        if not current_info:
            return False

        if not addresses:
            addresses = ["11111111111111111111111111111111"]

        payload = {
            "webhookURL": current_info["webhookURL"],
            "transactionTypes": current_info["transactionTypes"],
            "accountAddresses": list(set(addresses)),
            "webhookType": current_info["webhookType"],
        }

        result = await self._send_request("PUT", webhook_id, payload)
        return result is not None

    async def get_webhook_info(self, webhook_id: str) -> dict[str, Any] | None:
        """Fetches the current configuration of a specific webhook.

        Args:
            webhook_id: The unique ID of the webhook.

        Returns:
            A dictionary containing webhook details, or None.
        """
        return await self._send_request("GET", webhook_id)

    async def add_address_to_tracked(self, new_address: str) -> bool:
        """Appends a single new address to the tracked webhook list.

        Args:
            new_address: The Solana address to add.

        Returns:
            True if added successfully or already present, False otherwise.
        """
        async with self._lock:
            await asyncio.sleep(1.0)

            current_info = await self.get_webhook_info(settings.tracked_webhook_id)
            if not current_info:
                return False

            addresses = current_info.get("accountAddresses", [])
            if new_address in addresses:
                logger.debug("Address %s already in webhook.", new_address)
                return True

            addresses.append(new_address)
            return await self.update_addresses(
                settings.tracked_webhook_id, addresses
            )
