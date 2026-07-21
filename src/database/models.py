"""Database models for the Solana Wallet Tracker using SQLAlchemy ORM.

This module defines the schema for sources, tracked wallets, tags,
and global settings.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import Column
from sqlalchemy import Table


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Source(Base):
    """Represents a funding source like an exchange hot wallet.

    Attributes:
        id: Unique identifier from the database.
        address: The Solana wallet address of the source.
        label: A human-readable name for the source.
        is_active: Whether the source is currently being monitored.
        created_at: Timestamp when the source was added.
        wallets: List of wallets discovered from this source.
    """

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(44), unique=True, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

    # Связь: один источник может иметь много найденных кошельков
    wallets: Mapped[List["Wallet"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


wallet_tags = Table(
    "wallet_tags",
    Base.metadata,
    Column("wallet_id", ForeignKey("wallets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Wallet(Base):
    """Represents a discovered wallet being tracked by the bot.

    Attributes:
        id: Unique identifier from the database.
        address: The Solana wallet address.
        label: A human-readable name for the wallet.
        source_id: The ID of the source that funded this wallet.
        first_deposit_amount: The amount of the initial SOL transfer.
        is_active: Whether activity notifications are enabled.
        created_at: Timestamp when the wallet was discovered.
        source: The Source object that funded this wallet.
        tags: List of tags assigned to this wallet.
    """

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(44), unique=True, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(100))
    source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL")
    )
    first_deposit_amount: Mapped[float] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

    source: Mapped[Optional["Source"]] = relationship(back_populates="wallets")
    tags: Mapped[List["Tag"]] = relationship(
        secondary=wallet_tags, back_populates="wallets"
    )


class Tag(Base):
    """Represents a category tag that can be assigned to wallets.

    Attributes:
        id: Unique identifier from the database.
        name: The unique name of the tag.
        emoji: A visual icon associated with the tag.
        wallets: List of wallets assigned this tag.
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))

    wallets: Mapped[List["Wallet"]] = relationship(
        secondary=wallet_tags, back_populates="tags"
    )


class Setting(Base):
    """Represents a global configuration setting.

    Attributes:
        id: Unique identifier from the database.
        key: The unique name of the setting.
        value: The value of the setting stored as a string.
    """

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True)
    value: Mapped[str] = mapped_column(String(255))
