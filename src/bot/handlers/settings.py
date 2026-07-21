"""Handlers for managing global bot settings.

This module allows users to configure SOL deposit filters and 
timezone offsets for notifications.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import general as general_kb
from src.bot.states import BotStates
from src.config import settings
from src.database.repository import DatabaseRepository

router = Router(name="settings")


@router.callback_query(F.data == "menu_settings")
async def show_settings_menu(callback: CallbackQuery, db: DatabaseRepository) -> None:
    """Displays the global settings menu with current values.

    Args:
        callback: The incoming callback query.
        db: The database repository.
    """
    min_sol = await db.get_setting("min_sol", str(settings.default_min_sol))
    max_sol = await db.get_setting("max_sol", str(settings.default_max_sol))
    tz_offset = await db.get_setting("timezone_offset", str(settings.timezone_offset))

    text = (
        "⚙️ <b>Global Settings</b>\n\n"
        f"💰 <b>Min SOL Filter:</b> <code>{min_sol} SOL</code>\n"
        f"💰 <b>Max SOL Filter:</b> <code>{max_sol} SOL</code>\n"
        f"🕒 <b>Timezone Offset:</b> <code>UTC{'+' if int(tz_offset) >= 0 else ''}{tz_offset}</code>\n\n"
        "Select a parameter to change:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=general_kb.get_settings_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "set_min_sol")
async def start_set_min_sol(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for changing the minimum SOL threshold.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    await state.set_state(BotStates.waiting_for_min_sol)
    await callback.message.edit_text(
        "💰 <b>Setting Minimum SOL</b>\n\n"
        "Enter the minimum amount of SOL for the first transaction (e.g., 0.5):",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_min_sol)
async def process_min_sol(
    message: Message, state: FSMContext, db: DatabaseRepository
) -> None:
    """Validates and saves the new minimum SOL threshold.

    Args:
        message: The incoming message containing the value.
        state: The FSM context.
        db: The database repository.
    """
    try:
        value = float(message.text.replace(",", "."))
        if value < 0:
            raise ValueError()

        await db.update_setting("min_sol", str(value))
        await state.clear()

        await message.answer(
            f"✅ Minimum SOL updated to: <b>{value}</b>",
            reply_markup=general_kb.get_main_menu()
        )
    except ValueError:
        await message.answer("❌ <b>Invalid input.</b> Please enter a positive number:")


@router.callback_query(F.data == "set_max_sol")
async def start_set_max_sol(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for changing the maximum SOL threshold.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    await state.set_state(BotStates.waiting_for_max_sol)
    await callback.message.edit_text(
        "💰 <b>Setting Maximum SOL</b>\n\n"
        "Enter the maximum amount of SOL for the first transaction (e.g., 50.0):",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_max_sol)
async def process_max_sol(
    message: Message, state: FSMContext, db: DatabaseRepository
) -> None:
    """Validates and saves the new maximum SOL threshold.

    Args:
        message: The incoming message containing the value.
        state: The FSM context.
        db: The database repository.
    """
    try:
        value = float(message.text.replace(",", "."))
        if value < 0:
            raise ValueError()

        await db.update_setting("max_sol", str(value))
        await state.clear()

        await message.answer(
            f"✅ Maximum SOL updated to: <b>{value}</b>",
            reply_markup=general_kb.get_main_menu()
        )
    except ValueError:
        await message.answer("❌ <b>Invalid input.</b> Please enter a positive number:")


@router.callback_query(F.data == "set_timezone")
async def start_set_timezone(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the FSM flow for changing the timezone offset.

    Args:
        callback: The incoming callback query.
        state: The FSM context.
    """
    await state.set_state(BotStates.waiting_for_timezone)
    await callback.message.edit_text(
        "🕒 <b>Setting Timezone Offset</b>\n\n"
        "Enter the UTC offset in hours (e.g., 3 for Moscow, -5 for New York):",
        reply_markup=None
    )
    await callback.answer()


@router.message(BotStates.waiting_for_timezone)
async def process_timezone(
    message: Message, state: FSMContext, db: DatabaseRepository
) -> None:
    """Validates and saves the new timezone offset.

    Args:
        message: The incoming message containing the offset.
        state: The FSM context.
        db: The database repository.
    """
    try:
        value = int(message.text)
        if not (-12 <= value <= 14):
            raise ValueError()

        await db.update_setting("timezone_offset", str(value))
        await state.clear()

        await message.answer(
            f"✅ Timezone offset updated to: <b>UTC{'+' if value >= 0 else ''}{value}</b>",
            reply_markup=general_kb.get_main_menu()
        )
    except ValueError:
        await message.answer(
            "❌ <b>Invalid input.</b> Please enter an integer between -12 and 14:"
        )
