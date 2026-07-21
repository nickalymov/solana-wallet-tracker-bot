"""General inline keyboards for the Telegram bot.

This module defines the main navigation menus and source management
interfaces using aiogram's InlineKeyboardMarkup.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database import models


def get_main_menu() -> InlineKeyboardMarkup:
    """Generates the main menu keyboard.

    Returns:
        An InlineKeyboardMarkup object with main navigation buttons.
    """
    buttons = [
        [
            InlineKeyboardButton(text="📊 Status", callback_data="menu_status")
        ],
        [
            InlineKeyboardButton(text="📡 Sources", callback_data="menu_sources"),
            InlineKeyboardButton(text="👛 Wallets", callback_data="menu_wallets"),
        ],
        [
            InlineKeyboardButton(text="🏷️ Tags", callback_data="menu_tags"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="menu_settings"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sources_menu() -> InlineKeyboardMarkup:
    """Generates the sources management menu keyboard.

    Returns:
        An InlineKeyboardMarkup object with source management buttons.
    """
    buttons = [
        [
            InlineKeyboardButton(text="➕ Add Source", callback_data="add_source"),
            InlineKeyboardButton(text="🗑️ Remove Source", callback_data="remove_source_list"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_remove_sources_keyboard(sources: list[models.Source]) -> InlineKeyboardMarkup:
    """Generates a keyboard with a list of sources for deletion.

    Args:
        sources: A list of Source objects.

    Returns:
        An InlineKeyboardMarkup with a button for each source.
    """
    buttons = []
    for src in sources:
        display_name = src.label or f"{src.address[:8]}..."
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {display_name}",
                callback_data=f"delete_src_{src.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu_sources")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu() -> InlineKeyboardMarkup:
    """Generates the global settings management menu.

    Returns:
        An InlineKeyboardMarkup object.
    """
    buttons = [
        [
            InlineKeyboardButton(text="💰 Set Min SOL", callback_data="set_min_sol"),
            InlineKeyboardButton(text="💰 Set Max SOL", callback_data="set_max_sol"),
        ],
        [
            InlineKeyboardButton(text="🕒 Set Timezone", callback_data="set_timezone"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
