from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.pharmaviyum import constants
from src.pharmaviyum.utils.logger import setup_logging
from src.pharmaviyum.api.v1 import api_router
from src.pharmaviyum.middleware.auth_middleware import add_auth_middleware

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

# =============================================================================
# CORS Configuration - Production Security
# =============================================================================
# Define allowed origins based on environment
ALLOWED_ORIGINS = [
    "http://localhost:3000",           # Frontend dev server
    "http://localhost:8000",           # Backend direct access
    "http://127.0.0.1:3000",          # Alternative localhost
    # Add production domains here:
    # "https://your-domain.com",
    # "https://admin.your-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,     # Restricted origins (not wildcard)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID"],
    max_age=600,  # Cache preflight response for 10 minutes
)

# Attach auth middleware and include routers
add_auth_middleware(app)
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
