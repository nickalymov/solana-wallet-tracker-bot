"""Inline keyboards for wallet management.

This module provides interfaces for viewing tracked wallets with
pagination and managing individual wallet settings like tags and labels.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.database import models


def get_wallets_list_keyboard(
        wallets: list[models.Wallet],
        page: int,
        has_next: bool
) -> InlineKeyboardMarkup:
    """Generates a paginated list of wallets.

    Args:
        wallets: List of Wallet objects for the current page.
        page: Current page index.
        has_next: Whether there is a next page available.

    Returns:
        An InlineKeyboardMarkup object.
    """
    buttons = []

    for wallet in wallets:
        label = wallet.label or wallet.address[:8]
        buttons.append([
            InlineKeyboardButton(
                text=f"👛 {label}",
                callback_data=f"wl_view_{wallet.id}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"wl_page_{page - 1}"))

    nav_row.append(InlineKeyboardButton(text=f"Page {page + 1}", callback_data="ignore"))

    if has_next:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"wl_page_{page + 1}"))

    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_wallet_details_menu(wallet_id: int) -> InlineKeyboardMarkup:
    """Generates the management menu for a specific wallet.

    Args:
        wallet_id: The database ID of the wallet.

    Returns:
        An InlineKeyboardMarkup object.
    """
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Rename", callback_data=f"wl_rename_{wallet_id}"),
            InlineKeyboardButton(text="🏷️ Tags", callback_data=f"wl_tags_{wallet_id}"),
        ],
        [
            InlineKeyboardButton(text="❌ Stop Tracking", callback_data=f"wl_delete_{wallet_id}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to List", callback_data="menu_wallets"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_wallet_tags_keyboard(
        wallet_id: int,
        all_tags: list[models.Tag],
        assigned_ids: set[int]
) -> InlineKeyboardMarkup:
    """Generates a toggle menu for wallet tags.

    Args:
        wallet_id: ID of the wallet being edited.
        all_tags: List of all available tags.
        assigned_ids: Set of tag IDs already assigned to this wallet.

    Returns:
        An InlineKeyboardMarkup object.
    """
    buttons = []
    for tag in all_tags:
        is_assigned = tag.id in assigned_ids
        prefix = "✅" if is_assigned else "➕"
        emoji = tag.emoji if tag.emoji else ""

        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix} {emoji} {tag.name}",
                callback_data=f"wl_tag_toggle_{wallet_id}_{tag.id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Back to Details", callback_data=f"wl_view_{wallet_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
