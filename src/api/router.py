"""API router for Helius webhooks.

This module defines the endpoints that receive transaction notifications
from Helius and routes them to the transaction processor.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhooks"])


def _verify_auth(authorization: str | None, expected_token: str) -> None:
    """Verifies the Helius authorization header.

    Args:
        authorization: The value of the Authorization header.
        expected_token: The secret token from configuration.

    Raises:
        HTTPException: If the token is missing or invalid.
    """
    if not expected_token:
        return

    if authorization != expected_token:
        logger.warning("Unauthorized webhook attempt blocked.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token"
        )


@router.post("/sources")
async def handle_sources(
    request: Request,
    authorization: str | None = Header(None)
) -> dict[str, str]:
    """Handles webhooks from source addresses (exchanges).

    Args:
        request: The FastAPI request object.
        authorization: Authorization header from Helius.

    Returns:
        A status confirmation.
    """
    _verify_auth(authorization, request.app.state.settings.helius_api_key)

    payload = await request.json()
    processor = request.app.state.processor

    if isinstance(payload, list):
        for tx in payload:
            try:
                await processor.process_source_transaction(tx)
            except Exception as e:
                logger.error("Error processing source transaction: %s", e)

    return {"status": "ok"}


@router.post("/tracked")
async def handle_tracked(
    request: Request,
    authorization: str | None = Header(None)
) -> dict[str, str]:
    """Handles webhooks for activity of already tracked wallets.

    Args:
        request: The FastAPI request object.
        authorization: Authorization header from Helius.

    Returns:
        A status confirmation.
    """
    _verify_auth(authorization, request.app.state.settings.helius_api_key)

    payload = await request.json()
    processor = request.app.state.processor

    if isinstance(payload, list):
        for tx in payload:
            try:
                await processor.process_tracked_transaction(tx)
            except Exception as e:
                logger.error("Error processing tracked transaction: %s", e)

    return {"status": "ok"}
