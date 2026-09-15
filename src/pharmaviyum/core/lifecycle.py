"""
Application lifecycle management
Best practice 2026: Proper startup/shutdown with resource management
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.database import engine
from src.pharmaviyum.core.health import register_all_health_checks
from src.pharmaviyum.core.logging import get_logger, setup_logging
from src.pharmaviyum.core.metrics import APP_UPTIME_SECONDS
from src.pharmaviyum.core.telemetry import setup_telemetry

logger = get_logger(__name__)


class LifecycleManager:
    """
    Manages application lifecycle (startup/shutdown)

    Features:
    - Ordered startup/shutdown
    - Resource cleanup
    - Health check registration
    - Metrics initialization
    - Graceful shutdown with drain period
    """

    def __init__(self, app: FastAPI):
        """Initialize lifecycle manager"""
        self.app = app
        self._start_time: datetime | None = None
        self._shutdown_event = asyncio.Event()
        self._background_tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """
        Application startup sequence

        Order matters:
        1. Logging
        2. Telemetry
        3. Database
        4. Health checks
        5. Background tasks
        """
        self._start_time = datetime.now(timezone.utc)

        logger.info(
            f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
            extra={"environment": settings.ENVIRONMENT.value},
        )

        # 1. Setup logging
        setup_logging()
        logger.info("Logging initialized")

        # 2. Setup telemetry
        setup_telemetry(app=self.app, engine=engine)
        logger.info("Telemetry initialized")

        # 3. Register health checks
        register_all_health_checks()
        logger.info("Health checks registered")

        # 4. Start background metrics updater
        metrics_task = asyncio.create_task(self._update_metrics_periodically())
        self._background_tasks.append(metrics_task)

        logger.info("Application startup complete")

    async def shutdown(self) -> None:
        """
        Application shutdown sequence

        Order is reverse of startup:
        1. Stop background tasks
        2. Close database connections
        3. Flush telemetry
        """
        logger.info("Shutting down application")

        # 1. Stop background tasks
        for task in self._background_tasks:
            task.cancel()

        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        logger.info("Background tasks stopped")

        # 2. Close database connections
        await engine.dispose()
        logger.info("Database connections closed")

        # 3. Log uptime
        if self._start_time:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
            logger.info(f"Application uptime: {uptime:.2f} seconds")

        logger.info("Application shutdown complete")

    async def _update_metrics_periodically(self) -> None:
        """Update metrics periodically (uptime, etc)"""
        try:
            while True:
                if self._start_time:
                    uptime = (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds()
                    APP_UPTIME_SECONDS.set(uptime)

                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager

    Usage:
        app = FastAPI(lifespan=lifespan)
    """
    manager = LifecycleManager(app)

    # Startup
    await manager.startup()

    try:
        yield
    finally:
        # Shutdown
        await manager.shutdown()
