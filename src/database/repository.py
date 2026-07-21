"""Database repository for the Solana Wallet Tracker.

This module implements the Data Access Layer (DAL) using SQLAlchemy's
asynchronous engine. It provides a high-level API for managing funding
sources, discovered wallets, category tags, and global bot settings.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy import update
from sqlalchemy import insert
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.database import models


class DatabaseRepository:
    """Data access layer for managing database entities."""

    def __init__(self, db_url: str):
        """Initializes the engine and session factory.

        Args:
            db_url: The connection string for the database.
        """
        self._engine = create_async_engine(db_url)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def setup(self) -> None:
        """Creates all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

    async def add_source(
        self, address: str, label: str | None = None
    ) -> models.Source | None:
        """Adds a new source or returns None if it already exists.

        Args:
            address: The Solana address of the source.
            label: An optional human-readable name.

        Returns:
            The created Source object or None if the address is a duplicate.
        """
        async with self._session_factory() as session:
            query = select(models.Source).where(models.Source.address == address)
            result = await session.execute(query)
            if result.scalar_one_or_none():
                return None

            source = models.Source(address=address, label=label)
            session.add(source)
            await session.commit()
            await session.refresh(source)
            return source

    async def get_all_sources(self) -> list[models.Source]:
        """Retrieves all sources from the database.

        Returns:
            A list of Source objects.
        """
        async with self._session_factory() as session:
            result = await session.execute(select(models.Source))
            return list(result.scalars().all())

    async def get_active_source_addresses(self) -> list[str]:
        """Retrieves a list of all active source Solana addresses.

        Returns:
            A list of strings representing Solana addresses.
        """
        async with self._session_factory() as session:
            query = select(models.Source.address).where(models.Source.is_active)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def delete_source(self, source_id: int) -> None:
        """Removes a source from the database by its ID.

        Args:
            source_id: The database ID of the source to delete.
        """
        async with self._session_factory() as session:
            await session.execute(
                delete(models.Source).where(models.Source.id == source_id)
            )
            await session.commit()

    async def get_source_by_address(self, address: str) -> models.Source | None:
        """Finds a source by its Solana address.

        Args:
            address: The Solana address to search for.

        Returns:
            The Source object if found, otherwise None.
        """
        async with self._session_factory() as session:
            query = select(models.Source).where(models.Source.address == address)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def is_wallet_known(self, address: str) -> bool:
        """Checks if the wallet address already exists in the database.

        Args:
            address: The Solana address to check.

        Returns:
            True if the wallet is already known, False otherwise.
        """
        async with self._session_factory() as session:
            query = select(models.Wallet.id).where(models.Wallet.address == address)
            result = await session.execute(query)
            return result.scalar() is not None

    async def register_new_wallet(
            self,
            address: str,
            source_id: int,
            amount: float,
            label: str | None = None
    ) -> models.Wallet:
        """Registers a newly discovered wallet.

        Args:
            address: The Solana address of the new wallet.
            source_id: The ID of the source that funded it.
            amount: The initial SOL deposit amount.
            label: An optional human-readable name.

        Returns:
            The created Wallet object.
        """
        async with self._session_factory() as session:
            wallet = models.Wallet(
                address=address,
                source_id=source_id,
                first_deposit_amount=amount,
                label=label
            )
            session.add(wallet)
            await session.commit()
            await session.refresh(wallet)
            return wallet

    async def get_tracked_wallets(
            self, limit: int = 50, offset: int = 0
    ) -> list[models.Wallet]:
        """Retrieves a paginated list of tracked wallets.

        Args:
            limit: Maximum number of wallets to return.
            offset: Number of wallets to skip.

        Returns:
            A list of Wallet objects.
        """
        async with self._session_factory() as session:
            query = select(models.Wallet).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def add_tag(self, name: str, emoji: str | None = None) -> models.Tag:
        """Creates a new tag in the dictionary.

        Args:
            name: Unique name of the tag.
            emoji: Optional emoji icon.

        Returns:
            The created Tag object.
        """
        async with self._session_factory() as session:
            tag = models.Tag(name=name, emoji=emoji)
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
            return tag

    async def get_all_tags(self) -> list[models.Tag]:
        """Retrieves all available tags.

        Returns:
            A list of Tag objects.
        """
        async with self._session_factory() as session:
            result = await session.execute(select(models.Tag))
            return list(result.scalars().all())

    async def delete_tag(self, tag_id: int) -> None:
        """Deletes a tag by its ID.

        Args:
            tag_id: The ID of the tag to remove.
        """
        async with self._session_factory() as session:
            await session.execute(
                delete(models.Tag).where(models.Tag.id == tag_id)
            )
            await session.commit()

    async def assign_tag_to_wallet(self, wallet_id: int, tag_id: int) -> None:
        """Links a tag to a wallet.

        Args:
            wallet_id: The ID of the wallet.
            tag_id: The ID of the tag.
        """
        async with self._session_factory() as session:
            statement = insert(models.wallet_tags).values(
                wallet_id=wallet_id, tag_id=tag_id
            )
            await session.execute(statement)
            await session.commit()

    async def remove_tag_from_wallet(self, wallet_id: int, tag_id: int) -> None:
        """Unlinks a tag from a wallet.

        Args:
            wallet_id: The ID of the wallet.
            tag_id: The ID of the tag.
        """
        async with self._session_factory() as session:
            statement = delete(models.wallet_tags).where(
                models.wallet_tags.c.wallet_id == wallet_id,
                models.wallet_tags.c.tag_id == tag_id
            )
            await session.execute(statement)
            await session.commit()

    async def get_setting(self, key: str, default: str) -> str:
        """Retrieves a setting value by its key.

        Args:
            key: The unique name of the setting.
            default: The value to return if the setting is not found.

        Returns:
            The setting value as a string.
        """
        async with self._session_factory() as session:
            query = select(models.Setting.value).where(models.Setting.key == key)
            result = await session.execute(query)
            value = result.scalar()
            return value if value is not None else default

    async def update_setting(self, key: str, value: str) -> None:
        """Updates an existing setting or creates a new one.

        Args:
            key: The unique name of the setting.
            value: The new value to store.
        """
        async with self._session_factory() as session:
            # Проверяем существование
            query = select(models.Setting).where(models.Setting.key == key)
            result = await session.execute(query)
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = value
            else:
                session.add(models.Setting(key=key, value=value))

            await session.commit()

    async def get_stats(self) -> dict[str, int]:
        """Calculates general statistics for the bot status.

        Returns:
            A dictionary with counts of active sources and total wallets.
        """
        async with self._session_factory() as session:
            sources_query = select(func.count(models.Source.id)).where(
                models.Source.is_active
            )
            wallets_query = select(func.count(models.Wallet.id))

            sources_count = await session.execute(sources_query)
            wallets_count = await session.execute(wallets_query)

            return {
                "active_sources": sources_count.scalar() or 0,
                "total_wallets": wallets_count.scalar() or 0,
            }

    async def get_wallet_by_address(self, address: str) -> models.Wallet | None:
        """Retrieves a wallet with its assigned tags by its Solana address.

        Args:
            address: The Solana address to search for.

        Returns:
            The Wallet object with tags loaded, or None if not found.
        """
        async with self._session_factory() as session:
            query = (
                select(models.Wallet)
                .options(joinedload(models.Wallet.tags))
                .where(models.Wallet.address == address)
            )
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

    async def get_wallet_by_id(self, wallet_id: int) -> models.Wallet | None:
        """Retrieves a wallet with its source and tags by ID.

        Args:
            wallet_id: The database ID of the wallet.

        Returns:
            The Wallet object with relations loaded, or None.
        """
        async with self._session_factory() as session:
            query = (
                select(models.Wallet)
                .options(
                    joinedload(models.Wallet.source),
                    joinedload(models.Wallet.tags)
                )
                .where(models.Wallet.id == wallet_id)
            )
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

    async def update_wallet_label(self, wallet_id: int, label: str) -> None:
        """Updates the human-readable label for a wallet.

        Args:
            wallet_id: The database ID of the wallet.
            label: The new label string.
        """
        async with self._session_factory() as session:
            await session.execute(
                update(models.Wallet)
                .where(models.Wallet.id == wallet_id)
                .values(label=label)
            )
            await session.commit()

    async def get_wallet_tag_ids(self, wallet_id: int) -> set[int]:
        """Retrieves only the IDs of tags assigned to a wallet.

        Args:
            wallet_id: The database ID of the wallet.

        Returns:
            A set of tag IDs.
        """
        async with self._session_factory() as session:
            query = select(models.wallet_tags.c.tag_id).where(
                models.wallet_tags.c.wallet_id == wallet_id
            )
            result = await session.execute(query)
            return set(result.scalars().all())
