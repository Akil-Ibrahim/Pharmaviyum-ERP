"""
Feature flag middleware for automatic flag checking
Best practice 2026: Inject feature flags into request context
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.pharmaviyum.core.feature_flags import feature_flag_service
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject feature flags into request context

    Adds feature flags to request.state for easy access in endpoints.

    Usage in endpoints:
        @router.get("/endpoint")
        async def endpoint(request: Request):
            if request.state.features.get("new_ui"):
                # Show new UI
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and inject feature flags"""
        # Get user context
        user_id = None
        user_segment = None

        # Try to get user from authentication
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.get("id"))
            user_segment = request.state.user.get("segment")

        # Get all enabled flags
        flags = await feature_flag_service.list_flags()

        # Check each flag
        features = {}
        for flag in flags:
            if flag.enabled:
                is_enabled = await feature_flag_service.is_enabled(
                    key=flag.key,
                    user_id=user_id,
                    user_segment=user_segment,
                )

                if is_enabled:
                    # Get variant if multivariate
                    if flag.flag_type.value == "multivariate" and user_id:
                        variant = await feature_flag_service.get_variant(
                            flag.key, user_id
                        )
                        features[flag.key] = variant
                    else:
                        features[flag.key] = True

                    # Record check
                    await feature_flag_service.record_check(flag.key, True)

        # Inject into request state
        request.state.features = features

        # Process request
        response = await call_next(request)

        return response
