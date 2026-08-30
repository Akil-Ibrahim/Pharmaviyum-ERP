"""
Graceful shutdown handler for clean termination.

Ensures all resources are properly released on SIGTERM/SIGINT.
"""
import signal
import asyncio
from typing import Callable
from .logging import logger


class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.cleanup_callbacks: list[Callable] = []
    
    def setup(self):
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._handle_signal)
        logger.info("Graceful shutdown handlers registered")
    
    def _handle_signal(self, signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    def register_cleanup(self, callback: Callable):
        self.cleanup_callbacks.append(callback)
    
    async def shutdown(self):
        logger.info("Starting graceful shutdown sequence...")
        
        for callback in reversed(self.cleanup_callbacks):
            try:
                await callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        try:
            from .database import engine
            await engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Failed to close database: {e}")
        
        logger.info("Graceful shutdown complete")


shutdown_handler = GracefulShutdown()
