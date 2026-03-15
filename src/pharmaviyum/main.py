"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.pharmaviyum import constants
from src.pharmaviyum.utils.logger import setup_logging
from src.pharmaviyum.api.v1 import api_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting PharmaViyum...")
    yield
    # Shutdown
    print("🛑 Shutting down PharmaViyum...")


app = FastAPI(
    title=constants.PROJECT_NAME,
    version=constants.PROJECT_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=constants.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to PharmaViyum CRM"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.pharmaviyum.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
