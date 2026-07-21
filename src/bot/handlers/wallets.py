"""Handlers for viewing and managing discovered wallets.

This module provides a paginated list of wallets and detailed views
for each wallet, including its source and assigned tags.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import wallets as wallets_kb
from src.bot.keyboards import general as general_kb
from src.bot.states import BotStates
from src.core import formatter
from src.database.repository import DatabaseRepository

router = Router(name="wallets")

ITEMS_PER_PAGE = 5


@router.callback_query(F.data == "menu_wallets")
@router.callback_query(F.data.startswith("wl_page_"))
async def show_wallets_list(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Displays a paginated list of all tracked wallets.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    page = 0
    if callback.data.startswith("wl_page_"):
        page = int(callback.data.replace("wl_page_", ""))

    limit = ITEMS_PER_PAGE
    offset = page * limit
    wallets = await db.get_tracked_wallets(limit=limit + 1, offset=offset)

    has_next = len(wallets) > limit
    display_wallets = wallets[:limit]

    if not display_wallets and page == 0:
        await callback.message.edit_text(
            "👛 <b>No wallets found yet.</b>\n\n"
            "The bot will notify you once a new wallet matching your "
            "filters is discovered.",
            reply_markup=general_kb.get_main_menu()
        )
        return

    await callback.message.edit_text(
        f"👛 <b>Tracked Wallets</b>\n\nSelect a wallet to view details:",
        reply_markup=wallets_kb.get_wallets_list_keyboard(
            display_wallets, page, has_next
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wl_view_"))
async def show_wallet_details(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Displays detailed information about a specific wallet.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    wallet_id = int(callback.data.replace("wl_view_", ""))

    wallet = await db.get_wallet_by_id(wallet_id)

    if not wallet:
        await callback.answer("❌ Error: Wallet not found.", show_alert=True)
        return

    text = formatter.format_wallet_card(wallet)

    await callback.message.edit_text(
        text,
        reply_markup=wallets_kb.get_wallet_details_menu(wallet_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wl_rename_"))
async def start_rename_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for renaming a wallet.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    wallet_id = int(callback.data.replace("wl_rename_", ""))
    await state.update_data(edit_wallet_id=wallet_id)
    await state.set_state(BotStates.waiting_for_wallet_label)

    await callback.message.edit_text(
        "✏️ <b>Renaming Wallet</b>\n\n"
        "Please send a new name (label) for this wallet:",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_wallet_label)
async def process_wallet_label(
        message: Message,
        state: FSMContext,
        db: DatabaseRepository
) -> None:
    """Updates the wallet label and returns to the details view.

    Args:
        message: The incoming message with the new label.
        state: The FSM context.
        db: The database repository.
    """
    new_label = message.text.strip()[:50]
    data = await state.get_data()
    wallet_id = data.get("edit_wallet_id")

    await db.update_wallet_label(wallet_id, new_label)
    await state.clear()

    wallet = await db.get_wallet_by_id(wallet_id)
    await message.answer(
        formatter.format_wallet_card(wallet),
        reply_markup=wallets_kb.get_wallet_details_menu(wallet_id)
    )


@router.callback_query(F.data.startswith("wl_tags_"))
async def show_wallet_tags_menu(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Displays the interactive tag toggle menu for a wallet.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    wallet_id = int(callback.data.replace("wl_tags_", ""))

    all_tags = await db.get_all_tags()
    assigned_ids = await db.get_wallet_tag_ids(wallet_id)

    await callback.message.edit_text(
        "🏷️ <b>Manage Wallet Tags</b>\n\n"
        "Click on a tag to add or remove it from this wallet:",
        reply_markup=wallets_kb.get_wallet_tags_keyboard(
            wallet_id, all_tags, assigned_ids
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wl_tag_toggle_"))
async def process_tag_toggle(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Toggles a tag for a wallet and refreshes the menu.

    Args:
        callback: The incoming callback query (wl_tag_toggle_{wallet_id}_{tag_id}).
        db: The database repository.
    """
    parts = callback.data.split("_")
    wallet_id, tag_id = int(parts[3]), int(parts[4])

    assigned_ids = await db.get_wallet_tag_ids(wallet_id)

    if tag_id in assigned_ids:
        await db.remove_tag_from_wallet(wallet_id, tag_id)
    else:
        await db.assign_tag_to_wallet(wallet_id, tag_id)

    await show_wallet_tags_menu(callback, db)
