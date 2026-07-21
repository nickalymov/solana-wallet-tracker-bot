"""FSM states for the Telegram bot.

This module defines the state groups used to manage multi-step user
interactions such as adding sources, creating tags, or changing settings.
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    """Collection of all states for the bot's interactive flows."""

    # Source management
    waiting_for_source_address = State()
    waiting_for_source_label = State()

    # Tag management
    waiting_for_tag_name = State()
    waiting_for_tag_emoji = State()

    # Global settings
    waiting_for_min_sol = State()
    waiting_for_max_sol = State()
    waiting_for_timezone = State()

    # Wallet management
    waiting_for_wallet_label = State()
