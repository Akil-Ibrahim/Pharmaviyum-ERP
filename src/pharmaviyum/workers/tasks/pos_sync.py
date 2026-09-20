""" 
POS synchronization tasks
Best practice 2026: Bidirectional sync with KiotViet/Sapo/Viettel PMS
"""

from datetime import datetime, timezone
from typing import Any, NoReturn, cast

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import BaseTask, RetryConfig
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class SyncProductsTask(BaseTask):
    """Sync products from POS."""

    name = "sync_products"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3, base_delay_seconds=5.0)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Sync products from POS."""
        pos_system = cast(str, kwargs["pos_system"])
        pharmacy_id = cast(int, kwargs["pharmacy_id"])
        since = cast(str | None, kwargs.get("since"))

        logger.info(
            "Starting product sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "since": since,
            },
        )

        pos_client = self._get_pos_client(pos_system, pharmacy_id)
        products = await pos_client.fetch_products(since=since)

        synced = 0
        created = 0
        updated = 0

        from sqlalchemy import select

        from src.pharmaviyum.core.database import async_session
        from src.pharmaviyum.models.product import Product

        async with async_session() as session:
            for product_data in products:
                result = await session.execute(
                    select(Product).where(
                        Product.external_id == product_data["id"],
                        Product.pos_system == pos_system,
                        Product.pharmacy_id == pharmacy_id,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    for key, value in product_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.synced_at = datetime.now(timezone.utc)
                    updated += 1
                else:
                    product = Product(
                        external_id=product_data["id"],
                        pos_system=pos_system,
                        pharmacy_id=pharmacy_id,
                        **{
                            k: v for k, v in product_data.items() if hasattr(Product, k)
                        },
                        synced_at=datetime.now(timezone.utc),
                    )
                    session.add(product)
                    created += 1

                synced += 1

            await session.commit()

        logger.info(
            "Product sync completed",
            extra={
                "pos_system": pos_system,
                "synced": synced,
                "created": created,
                "updated": updated,
            },
        )
        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "synced": synced,
            "created": created,
            "updated": updated,
        }

    def _get_pos_client(self, pos_system: str, pharmacy_id: int) -> NoReturn:
        """Get POS client for the given system."""
        raise NotImplementedError(f"POS client for {pos_system} not implemented")


class SyncInventoryTask(BaseTask):
    """Sync inventory levels from POS."""

    name = "sync_inventory"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Sync inventory from POS."""
        pos_system = cast(str, kwargs["pos_system"])
        pharmacy_id = cast(int, kwargs["pharmacy_id"])

        logger.info(
            "Starting inventory sync",
            extra={"pos_system": pos_system, "pharmacy_id": pharmacy_id},
        )
        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }


class SyncCustomersTask(BaseTask):
    """Sync customers from POS to CRM."""

    name = "sync_customers"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Sync customers from POS."""
        pos_system = cast(str, kwargs["pos_system"])
        pharmacy_id = cast(int, kwargs["pharmacy_id"])
        since = cast(str | None, kwargs.get("since"))

        logger.info(
            "Starting customer sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "since": since,
            },
        )
        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }


class SyncSalesTask(BaseTask):
    """Sync sales transactions from POS."""

    name = "sync_sales"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Sync sales from POS."""
        pos_system = cast(str, kwargs["pos_system"])
        pharmacy_id = cast(int, kwargs["pharmacy_id"])
        date_from = cast(str, kwargs["date_from"])
        date_to = cast(str, kwargs["date_to"])

        logger.info(
            "Starting sales sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "date_from": date_from,
                "date_to": date_to,
            },
        )
        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }
