"""Inline keyboards for tag management.

This module defines interfaces for creating, viewing, and deleting
category tags.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.database import models


def get_tags_menu() -> InlineKeyboardMarkup:
    """Generates the main tags management menu."""
    buttons = [
        [
            InlineKeyboardButton(text="➕ Create Tag", callback_data="tag_create"),
            InlineKeyboardButton(text="🗑️ Delete Tag", callback_data="tag_delete_list"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tags_delete_keyboard(tags: list[models.Tag]) -> InlineKeyboardMarkup:
    """Generates a list of tags with delete buttons.

    Args:
        tags: List of all available Tag objects.

    Returns:
        An InlineKeyboardMarkup object.
    """
    buttons = []
    for tag in tags:
        emoji = tag.emoji if tag.emoji else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {emoji} {tag.name}",
                callback_data=f"tag_confirm_del_{tag.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu_tags")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
