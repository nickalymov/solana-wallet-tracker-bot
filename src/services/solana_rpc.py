"""Helius-native Solana RPC client implementation.

This module provides a client for interacting with the Solana blockchain
using Helius RPC and DAS API methods to verify wallet status.
"""

from __future__ import annotations

import logging
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


class SolanaRpcClient:
    """Client for Helius RPC and DAS API."""

    def __init__(self) -> None:
        """Initializes the RPC client with Helius URL."""
        self._url = settings.helius_rpc_url

    async def _send_request(
        self,
        method: str,
        params: list | dict | None = None
    ) -> dict | None:
        """Sends an asynchronous JSON-RPC request to Helius.

        Args:
            method: The RPC method name.
            params: The parameters for the RPC method.

        Returns:
            The 'result' field from the JSON response, or None on error.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(self._url, json=payload)
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    logger.error("RPC error in %s: %s", method, data["error"])
                    return None

                return data.get("result")
            except httpx.HTTPError as e:
                logger.error("HTTP error during RPC call %s: %s", method, e)
                return None

    async def get_balance(self, address: str) -> float | None:
        """Retrieves the SOL balance for a given address.

        Args:
            address: The Solana wallet address.

        Returns:
            The balance in SOL, or None if the request failed.
        """
        result = await self._send_request("getBalance", [address])
        if result and "value" in result:
            return float(result["value"]) / 10 ** 9
        return None

    async def get_assets_by_owner(self, address: str) -> list | None:
        """Retrieves all assets (tokens/NFTs) owned by the address using DAS API.

        Args:
            address: The Solana wallet address.

        Returns:
            A list of asset items, or None if the request failed.
        """
        params = {
            "ownerAddress": address,
            "page": 1,
            "limit": 1,
            "displayOptions": {"showFungible": True}
        }
        result = await self._send_request("getAssetsByOwner", params)
        if isinstance(result, dict):
            return result.get("items")
        return None

    async def get_signatures_for_address(
            self, address: str, limit: int = 2
    ) -> list[dict] | None:
        """Retrieves transaction signatures for a given address.

        Args:
            address: The Solana wallet address.
            limit: Maximum number of signatures to return.

        Returns:
            A list of signature info dictionaries, or None if the request failed.
        """
        result = await self._send_request(
            "getSignaturesForAddress", [address, {"limit": limit}]
        )
        if isinstance(result, list):
            return result
        return None
