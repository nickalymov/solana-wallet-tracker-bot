"""Telegram bot initialization and configuration.

This module sets up the aiogram Bot and Dispatcher, registers all
command routers, and injects necessary dependencies.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import common, settings as settings_handlers, sources, tags, wallets
from src.config import settings
from src.database.repository import DatabaseRepository
from src.services.helius import HeliusWebhookManager


def setup_bot(
    db: DatabaseRepository,
    helius_mgr: HeliusWebhookManager
) -> tuple[Bot, Dispatcher]:
    """Initializes the bot and dispatcher with all routers and dependencies.

    Args:
        db: The database repository instance.
        helius_mgr: The Helius webhook manager instance.

    Returns:
        A tuple containing the Bot and Dispatcher instances.
    """
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp["db"] = db
    dp["helius"] = helius_mgr

    dp.include_routers(
        common.router,
        sources.router,
        tags.router,
        wallets.router,
        settings_handlers.router,
    )

    return bot, dp
