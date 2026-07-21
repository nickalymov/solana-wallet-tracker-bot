"""Message formatting logic for Telegram notifications.

This module provides functions to convert raw blockchain data and
database models into human-readable HTML messages.
"""

from __future__ import annotations

import datetime
from typing import Any

from src.database import models


def shorten_address(address: str) -> str:
    """Shortens a Solana address for better readability.

    Args:
        address: The full Solana address.

    Returns:
        A string like '5tzF...vAi9'.
    """
    if len(address) < 10:
        return address
    return f"{address[:4]}...{address[-4:]}"


def format_timestamp(dt: datetime.datetime, offset: int) -> str:
    """Formats a datetime object with a timezone offset.

    Args:
        dt: The datetime object (usually UTC).
        offset: Timezone offset in hours.

    Returns:
        A formatted string like '2024-01-01 15:30:00'.
    """
    adjusted_dt = dt + datetime.timedelta(hours=offset)
    return adjusted_dt.strftime("%Y-%m-%d %H:%M:%S")


def format_tags(tags: list[models.Tag]) -> str:
    """Converts a list of Tag objects into a single string.

    Args:
        tags: A list of Tag models.

    Returns:
        A string like '🐋 [Whale] 🚀 [Insider]'.
    """
    if not tags:
        return ""

    tag_strings = []
    for tag in tags:
        emoji = tag.emoji if tag.emoji else "🏷️"
        tag_strings.append(f"{emoji} [{tag.name}]")

    return " ".join(tag_strings)


def format_new_wallet_message(data: dict[str, Any]) -> str:
    """Formats a notification for a newly discovered clean wallet.

    Args:
        data: Dictionary containing 'address', 'amount', 'source_label',
              and 'signature'.

    Returns:
        A formatted HTML string.
    """
    return (
        f"🚀 <b>New Wallet Found!</b>\n\n"
        f"📍 Address: <code>{data['address']}</code>\n"
        f"💰 Amount: {data['amount']:.2f} SOL\n"
        f"🏦 Source: <b>{data['source_label']}</b>\n\n"
        f"🔗 <a href='https://solscan.io/tx/{data['signature']}'>"
        f"View Transaction</a>"
    )


def format_activity_message(data: dict[str, Any]) -> str:
    """Formats a notification for activity on a tracked wallet.

    Args:
        data: Dictionary containing 'label', 'description', 'type',
              'signature', and 'wallet_obj'.

    Returns:
        A formatted HTML string.
    """
    wallet = data["wallet_obj"]
    tags_str = format_tags(wallet.tags)

    header = f"<b>{data['label']}</b>"
    if tags_str:
        header += f" {tags_str}"

    return (
        f"🔔 <b>Activity Detected</b>\n\n"
        f"👛 Wallet: {header}\n"
        f"📝 {data['description']}\n"
        f"⚡ Type: <code>{data['type']}</code>\n\n"
        f"🔗 <a href='https://solscan.io/tx/{data['signature']}'>"
        f"View on Solscan</a>"
    )


def format_wallet_card(wallet: models.Wallet) -> str:
    """Formats a detailed information card for a wallet.

    Args:
        wallet: The Wallet object with source and tags loaded.

    Returns:
        A formatted HTML string.
    """
    source_name = wallet.source.label if wallet.source else "Unknown"
    tags_str = format_tags(wallet.tags) or "None"

    return (
        f"<b>Wallet Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Address:</b>\n<code>{wallet.address}</code>\n\n"
        f"🏷️ <b>Name:</b> {wallet.label or 'Unnamed'}\n"
        f"💰 <b>First Deposit:</b> {wallet.first_deposit_amount:.2f} SOL\n"
        f"🏦 <b>Source:</b> {source_name}\n"
        f"📅 <b>Found:</b> {wallet.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"🏷️ <b>Tags:</b> {tags_str}"
    )
