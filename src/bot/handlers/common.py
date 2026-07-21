"""Common handlers for the Telegram bot.

This module handles basic commands like /start and general navigation
between menus using callback queries.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import general
from src.config import settings
from src.database.repository import DatabaseRepository

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handles the /start command and shows the main menu.

    Args:
        message: The incoming Telegram message.
    """
    await message.answer(
        "👋 <b>Welcome to Solana Wallet Tracker!</b>\n\n"
        "Use the menu below to manage your sources and view discovered wallets.",
        reply_markup=general.get_main_menu()
    )


@router.callback_query(F.data == "back_to_main")
async def nav_back_to_main(callback: CallbackQuery) -> None:
    """Returns the user to the main menu by editing the current message.

    Args:
        callback: The incoming callback query.
    """
    await callback.message.edit_text(
        "🏠 <b>Main Menu</b>\n\nSelect a section to manage:",
        reply_markup=general.get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "menu_status")
async def show_status(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Displays the current bot status and statistics.

    Args:
        callback: The incoming callback query.
        db: The database repository instance.
    """
    stats = await db.get_stats()

    min_sol = await db.get_setting("min_sol", str(settings.default_min_sol))
    max_sol = await db.get_setting("max_sol", str(settings.default_max_sol))

    status_text = (
        "📊 <b>Bot Status</b>\n\n"
        f"📡 <b>Active Sources:</b> {stats['active_sources']}\n"
        f"👛 <b>Total Wallets Found:</b> {stats['total_wallets']}\n\n"
        "⚙️ <b>Global Filters:</b>\n"
        f"└ Min: <code>{min_sol} SOL</code>\n"
        f"└ Max: <code>{max_sol} SOL</code>"
    )

    await callback.message.edit_text(
        status_text,
        reply_markup=general.get_main_menu()
    )
    await callback.answer()
