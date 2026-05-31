"""Entry point for Uvicorn server."""
import uvicorn
from config import settings
from loguru import logger

if __name__ == "__main__":
    logger.info(f"Mortarium AI starting on 0.0.0.0:8000")
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False, workers=1, log_level=settings.LOG_LEVEL.lower(), access_log=True)
