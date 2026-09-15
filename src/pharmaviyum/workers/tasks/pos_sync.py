"""
POS synchronization tasks
Best practice 2026: Bidirectional sync with KiotViet/Sapo/Viettel PMS
"""

from datetime import datetime, timezone
from typing import Optional

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import BaseTask, RetryConfig
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class SyncProductsTask(BaseTask):
    """Sync products from POS to CRM"""

    name = "sync_products"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3, base_delay_seconds=5.0)

    async def execute(
        self,
        pos_system: str,
        pharmacy_id: int,
        since: Optional[str] = None,
    ) -> dict:
        """
        Sync products from POS

        Args:
            pos_system: POS system name (kiotviet/sapo/viettel)
            pharmacy_id: Pharmacy ID
            since: ISO datetime to sync from (optional)

        Returns:
            Sync result with counts
        """
        logger.info(
            "Starting product sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "since": since,
            },
        )

        # Get POS client
        pos_client = self._get_pos_client(pos_system, pharmacy_id)

        # Fetch products from POS
        products = await pos_client.fetch_products(since=since)

        # Sync to CRM
        synced = 0
        created = 0
        updated = 0

        from src.pharmaviyum.core.database import async_session

        async with async_session() as session:
            for product_data in products:
                # Check if product exists
                from sqlalchemy import select

                from src.pharmaviyum.models.integrations import Product

                result = await session.execute(
                    select(Product).where(
                        Product.external_id == product_data["id"],
                        Product.pos_system == pos_system,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update
                    for key, value in product_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.synced_at = datetime.now(timezone.utc)
                    updated += 1
                else:
                    # Create
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

    def _get_pos_client(self, pos_system: str, pharmacy_id: int):
        """Get POS client for given system"""
        # TODO: Implement POS client factory
        # from src.pharmaviyum.integrations.pos import get_pos_client
        # return get_pos_client(pos_system, pharmacy_id)
        raise NotImplementedError(f"POS client for {pos_system} not implemented")


class SyncInventoryTask(BaseTask):
    """Sync inventory levels from POS"""

    name = "sync_inventory"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(
        self,
        pos_system: str,
        pharmacy_id: int,
    ) -> dict:
        """
        Sync inventory from POS

        Args:
            pos_system: POS system name
            pharmacy_id: Pharmacy ID

        Returns:
            Sync result
        """
        logger.info(
            "Starting inventory sync",
            extra={"pos_system": pos_system, "pharmacy_id": pharmacy_id},
        )

        # TODO: Implement inventory sync logic
        # Similar to SyncProductsTask but for inventory

        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }


class SyncCustomersTask(BaseTask):
    """Sync customers from POS to CRM"""

    name = "sync_customers"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(
        self,
        pos_system: str,
        pharmacy_id: int,
        since: Optional[str] = None,
    ) -> dict:
        """
        Sync customers from POS

        Args:
            pos_system: POS system name
            pharmacy_id: Pharmacy ID
            since: ISO datetime to sync from

        Returns:
            Sync result
        """
        logger.info(
            "Starting customer sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "since": since,
            },
        )

        # TODO: Implement customer sync logic

        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }


class SyncSalesTask(BaseTask):
    """Sync sales transactions from POS"""

    name = "sync_sales"
    queue = TaskQueue.POS_SYNC.value
    timeout_seconds = 300
    retry_config = RetryConfig(max_attempts=3)

    async def execute(
        self,
        pos_system: str,
        pharmacy_id: int,
        date_from: str,
        date_to: str,
    ) -> dict:
        """
        Sync sales from POS

        Args:
            pos_system: POS system name
            pharmacy_id: Pharmacy ID
            date_from: Start date (ISO)
            date_to: End date (ISO)

        Returns:
            Sync result
        """
        logger.info(
            "Starting sales sync",
            extra={
                "pos_system": pos_system,
                "pharmacy_id": pharmacy_id,
                "date_from": date_from,
                "date_to": date_to,
            },
        )

        # TODO: Implement sales sync logic

        return {
            "pos_system": pos_system,
            "pharmacy_id": pharmacy_id,
            "status": "not_implemented",
        }
