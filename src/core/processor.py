"""Core logic for processing Solana transactions.

This module coordinates between the database, RPC client, and webhook
manager to identify new wallets and track their activity.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

from src.config import settings
from src.database.repository import DatabaseRepository
from src.services.helius import HeliusWebhookManager
from src.services.solana_rpc import SolanaRpcClient

logger = logging.getLogger(__name__)

NotifierFunc = Callable[[str, dict[str, Any]], Awaitable[None]]


class TransactionProcessor:
    """Coordinates the discovery and tracking of Solana wallets."""

    def __init__(
        self,
        db: DatabaseRepository,
        rpc: SolanaRpcClient,
        helius: HeliusWebhookManager,
        notifier: NotifierFunc
    ) -> None:
        """Initializes the processor with required services."""
        self._db = db
        self._rpc = rpc
        self._helius = helius
        self._notifier = notifier

    async def process_source_transaction(self, tx: dict[str, Any]) -> None:
        """Analyzes a transaction from a source to find new clean wallets.

        Args:
            tx: Parsed transaction data from Helius Enhanced Webhook.
        """
        transfers = tx.get("nativeTransfers", [])
        if not transfers:
            return

        for transfer in transfers:
            sender = transfer.get("fromUserAccount")
            receiver = transfer.get("toUserAccount")
            amount_sol = transfer.get("amount", 0) / 10**9

            if await self._db.is_wallet_known(receiver):
                continue

            min_sol = float(await self._db.get_setting(
                "min_sol", str(settings.default_min_sol))
            )
            max_sol = float(await self._db.get_setting(
                "max_sol", str(settings.default_max_sol))
            )

            if not (min_sol <= amount_sol <= max_sol):
                continue

            signatures = await self._rpc.get_signatures_for_address(receiver, limit=2)
            if signatures is None or len(signatures) > 1:
                logger.debug("Wallet %s is not new (history found).", receiver[:8])
                continue

            assets = await self._rpc.get_assets_by_owner(receiver)
            if assets is None or len(assets) > 0:
                logger.debug("Wallet %s is not clean (assets found).", receiver[:8])
                continue

            source = await self._db.get_source_by_address(sender)
            if not source:
                logger.warning("Source address %s not found in database.", sender)
                continue

            await self._db.register_new_wallet(
                address=receiver,
                source_id=source.id,
                amount=amount_sol,
                label=f"Wallet from {source.label or sender[:8]}"
            )

            await self._helius.add_address_to_tracked(receiver)

            await self._notifier("new_wallet", {
                "address": receiver,
                "amount": amount_sol,
                "source_label": source.label or sender[:8],
                "signature": tx.get("signature")
            })

            logger.info("🚀 New clean wallet registered: %s", receiver)

    async def process_tracked_transaction(self, tx: dict[str, Any]) -> None:
        """Processes activity for wallets already in the tracking list.

        Args:
            tx: Parsed transaction data from Helius Enhanced Webhook.
        """
        signature = tx.get("signature")
        tx_type = tx.get("type", "UNKNOWN")
        description = tx.get("description", "")

        involved_accounts = [
            acc.get("account") for acc in tx.get("accountData", [])
        ]

        for address in involved_accounts:
            wallet = await self._db.get_wallet_by_address(address)
            if not wallet:
                continue

            await self._notifier("tracked_activity", {
                "address": address,
                "label": wallet.label,
                "description": description,
                "type": tx_type,
                "signature": signature,
                "source": tx.get("source"),
                "wallet_obj": wallet
            })

            break
