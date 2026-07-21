"""Handlers for managing Solana source addresses (exchanges).

This module allows users to add and remove sources via the Telegram
interface and synchronizes these changes with Helius webhooks.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import general
from src.bot.keyboards.general import get_remove_sources_keyboard
from src.bot.states import BotStates
from src.config import settings
from src.database.repository import DatabaseRepository
from src.services.helius import HeliusWebhookManager

logger = logging.getLogger(__name__)
router = Router(name="sources")


@router.callback_query(F.data == "menu_sources")
async def show_sources_menu(callback: CallbackQuery) -> None:
    """Displays the sources management menu.

    Args:
        callback: The incoming callback query.
    """
    await callback.message.edit_text(
        "📡 <b>Sources Management</b>\n\n"
        "Add or remove Solana addresses (exchanges) to monitor for "
        "newly funded wallets.",
        reply_markup=general.get_sources_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "add_source")
async def start_add_source(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for adding a new source.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    await state.set_state(BotStates.waiting_for_source_address)
    await callback.message.edit_text(
        "📝 <b>Step 1/2: Enter Address</b>\n\n"
        "Please send the Solana wallet address you want to monitor:",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_source_address)
async def process_source_address(message: Message, state: FSMContext) -> None:
    """Validates the Solana address and asks for a label.

    Args:
        message: The incoming message containing the address.
        state: The FSM context.
    """
    address = message.text.strip()

    # Базовая валидация длины адреса Solana
    if not (32 <= len(address) <= 44):
        await message.answer(
            "❌ <b>Invalid address format.</b>\n\n"
            "Solana addresses should be between 32 and 44 characters. "
            "Please try again:"
        )
        return

    await state.update_data(address=address)
    await state.set_state(BotStates.waiting_for_source_label)
    await message.answer(
        f"✅ Address: <code>{address}</code>\n\n"
        "<b>Step 2/2: Enter Label</b>\n"
        "Now, enter a name for this source (e.g., 'Binance Hot Wallet'):"
    )


@router.message(BotStates.waiting_for_source_label)
async def process_source_label(
    message: Message,
    state: FSMContext,
    db: DatabaseRepository,
    helius: HeliusWebhookManager,
) -> None:
    """Finalizes source addition by saving the label and syncing with Helius.

    Args:
        message: The incoming message containing the source label.
        state: The FSM context.
        db: The database repository instance.
        helius: The Helius webhook manager instance.
    """
    data = await state.get_data()
    address = data.get("address")
    label = message.text.strip()

    source = await db.add_source(address=address, label=label)

    if source is None:
        await state.clear()
        await message.answer(
            f"❌ <b>Error:</b> Address <code>{address}</code> is already "
            f"registered in your sources.",
            reply_markup=general.get_sources_menu()
        )
        return

    active_addresses = await db.get_active_source_addresses()
    success = await helius.update_addresses(
        settings.source_webhook_id, active_addresses
    )

    await state.clear()

    if success:
        text = (
            f"🎉 <b>Success!</b>\n\nSource <b>{label}</b> added and "
            f"synchronized with Helius."
        )
    else:
        text = (
            f"⚠️ <b>Partial Success.</b>\n\nSource <b>{label}</b> saved "
            f"locally, but Helius sync failed. Check logs."
        )

    await message.answer(text, reply_markup=general.get_sources_menu())


@router.callback_query(F.data == "remove_source_list")
async def show_remove_sources_list(
        callback: CallbackQuery, db: DatabaseRepository
) -> None:
    """Displays a list of sources with delete buttons.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    sources = await db.get_all_sources()
    if not sources:
        await callback.answer("No sources to remove.", show_alert=True)
        return

    await callback.message.edit_text(
        "🗑️ <b>Select a source to remove:</b>\n\n"
        "Note: This will also stop monitoring this address in Helius.",
        reply_markup=get_remove_sources_keyboard(sources)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_src_"))
async def process_delete_source(
        callback: CallbackQuery,
        db: DatabaseRepository,
        helius: HeliusWebhookManager
) -> None:
    """Deletes a source and updates the Helius webhook.

    Args:
        callback: The incoming callback query.
        db: The database repository.
        helius: The Helius webhook manager.
    """
    source_id = int(callback.data.replace("delete_src_", ""))

    await db.delete_source(source_id)

    active_addresses = await db.get_active_source_addresses()
    await helius.update_addresses(
        settings.source_webhook_id, active_addresses
    )

    await callback.answer("Source removed and Helius synced.")
    await show_remove_sources_list(callback, db)
