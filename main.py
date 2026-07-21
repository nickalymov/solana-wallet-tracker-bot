"""Main entry point for the Solana Wallet Tracker.

This module orchestrates the asynchronous execution of the FastAPI webhook
server and the Aiogram Telegram bot, linking them through the
TransactionProcessor.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI

from src.api.router import router as webhook_router
from src.bot.bot_instance import setup_bot
from src.config import settings
from src.core import formatter
from src.core.processor import TransactionProcessor
from src.database.repository import DatabaseRepository
from src.services.helius import HeliusWebhookManager
from src.services.solana_rpc import SolanaRpcClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initializes and starts all application components concurrently."""
    logger.info("Starting Solana Wallet Tracker...")

    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    db = DatabaseRepository(settings.db_url)
    await db.setup()

    rpc = SolanaRpcClient()
    helius_mgr = HeliusWebhookManager()

    bot, dp = setup_bot(db, helius_mgr)

    async def telegram_notifier(event_type: str, data: dict[str, Any]) -> None:
        """Callback to send formatted messages from Processor to Telegram.

        Args:
            event_type: The type of event (e.g., 'new_wallet').
            data: The data dictionary containing event details.
        """
        try:
            if event_type == "new_wallet":
                text = formatter.format_new_wallet_message(data)
            else:
                text = formatter.format_activity_message(data)

            await bot.send_message(settings.admin_id, text)
        except Exception as e:
            logger.error("Failed to send Telegram notification: %s", e)

    processor = TransactionProcessor(
        db=db, rpc=rpc, helius=helius_mgr, notifier=telegram_notifier
    )

    app: Any = FastAPI(title="SolanaTrackerAPI")
    app.state.processor = processor
    app.state.settings = settings
    app.include_router(webhook_router)

    server_config = uvicorn.Config(
        app=app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="error",
    )
    server = uvicorn.Server(server_config)

    try:
        logger.info("Services are ready. Starting event loop...")
        await asyncio.gather(dp.start_polling(bot), server.serve())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received.")
    finally:
        await bot.session.close()
        logger.info("All services stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
