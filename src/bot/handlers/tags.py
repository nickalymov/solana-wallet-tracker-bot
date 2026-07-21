"""Handlers for managing category tags.

This module provides interfaces for creating and deleting tags that
can be assigned to tracked wallets for better organization.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import tags as tags_kb
from src.bot.states import BotStates
from src.database.repository import DatabaseRepository

router = Router(name="tags")


@router.callback_query(F.data == "menu_tags")
async def show_tags_menu(callback: CallbackQuery) -> None:
    """Displays the main tags management menu.

    Args:
        callback: The incoming callback query.
    """
    await callback.message.edit_text(
        "🏷️ <b>Tags Management</b>\n\n"
        "Tags help you categorize discovered wallets (e.g., 'Whale', 'Insider'). "
        "Each tag consists of a name and an optional emoji.",
        reply_markup=tags_kb.get_tags_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "tag_create")
async def start_create_tag(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for creating a new tag.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    await state.set_state(BotStates.waiting_for_tag_name)
    await callback.message.edit_text(
        "📝 <b>Step 1/2: Tag Name</b>\n\n"
        "Please enter a unique name for the new tag (e.g., 'Whale'):",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_tag_name)
async def process_tag_name(message: Message, state: FSMContext) -> None:
    """Handles the tag name and asks for an emoji.

    Args:
        message: The incoming message containing the name.
        state: The FSM context.
    """
    name = message.text.strip()

    if len(name) > 20:
        await message.answer(
            "❌ <b>Name too long.</b>\n\nPlease use up to 20 characters:"
        )
        return

    await state.update_data(tag_name=name)
    await state.set_state(BotStates.waiting_for_tag_emoji)
    await message.answer(
        f"✅ Name set: <b>{name}</b>\n\n"
        "<b>Step 2/2: Tag Emoji</b>\n"
        "Now, please send an emoji for this tag (or any single character):"
    )


@router.message(BotStates.waiting_for_tag_emoji)
async def process_tag_emoji(
        message: Message,
        state: FSMContext,
        db: DatabaseRepository
) -> None:
    """Finalizes tag creation by saving it to the database.

    Args:
        message: The incoming message containing the emoji.
        state: The FSM context.
        db: The database repository.
    """
    emoji = message.text.strip()[:2]

    user_data = await state.get_data()
    name = user_data.get("tag_name")

    await db.add_tag(name=name, emoji=emoji)
    await state.clear()

    await message.answer(
        f"🎉 <b>Tag Created!</b>\n\n"
        f"Tag: {emoji} {name}\n"
        "You can now assign it to any discovered wallet.",
        reply_markup=tags_kb.get_tags_menu()
    )


@router.callback_query(F.data == "tag_delete_list")
async def show_delete_tags_list(
        callback: CallbackQuery,
        db: DatabaseRepository
) -> None:
    """Displays a list of all tags with delete buttons.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    all_tags = await db.get_all_tags()

    if not all_tags:
        await callback.answer("You don't have any tags to delete.", show_alert=True)
        return

    await callback.message.edit_text(
        "🗑️ <b>Select a tag to delete:</b>\n\n"
        "Warning: This will remove the tag from all assigned wallets.",
        reply_markup=tags_kb.get_tags_delete_keyboard(all_tags)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tag_confirm_del_"))
async def process_delete_tag(
        callback: CallbackQuery,
        db: DatabaseRepository
) -> None:
    """Handles the deletion of a specific tag.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    tag_id = int(callback.data.replace("tag_confirm_del_", ""))

    await db.delete_tag(tag_id)
    await callback.answer("Tag removed.")

    await show_delete_tags_list(callback, db)
