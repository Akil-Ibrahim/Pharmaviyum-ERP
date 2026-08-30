"""Graceful shutdown handler for clean termination."""
import signal
import asyncio
from typing import Callable


class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.cleanup_callbacks: list[Callable] = []
    
    def setup(self):
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._handle_signal)
        print("✅ Graceful shutdown handlers registered")
    
    def _handle_signal(self, signum, frame):
        signal_name = signal.Signals(signum).name
        print(f"Received {signal_name}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    def register_cleanup(self, callback: Callable):
        self.cleanup_callbacks.append(callback)
    
    async def shutdown(self):
        print("Starting graceful shutdown sequence...")
        for callback in reversed(self.cleanup_callbacks):
            try:
                await callback()
            except Exception as e:
                print(f"Cleanup callback failed: {e}")
        
        try:
            from src.pharmaviyum.database import engine
            await engine.dispose()
            print("✅ Database connections closed")
        except Exception as e:
            print(f"Failed to close database: {e}")
        
        try:
            from src.pharmaviyum.redis_client import redis_client
            if redis_client:
                await redis_client.close()
                print("✅ Redis connection closed")
        except Exception:
            pass
        
        print("✅ Graceful shutdown complete")


shutdown_handler = GracefulShutdown()
