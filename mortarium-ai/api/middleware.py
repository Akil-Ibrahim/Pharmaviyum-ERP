"""CORS, Request ID tracking, and tracing middleware."""
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry.trace import get_current_span
import uuid, os

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        span = get_current_span()
        if span.is_recording():
            span.set_attribute("http.request_id", request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

def setup_cors(app):
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
