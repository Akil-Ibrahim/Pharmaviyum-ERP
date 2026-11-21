"""
=============================================================================
PharmaViyum CRM - API Documentation Configuration
=============================================================================
This module provides enhanced OpenAPI documentation for the PharmaViyum API.

Features:
    - Detailed endpoint descriptions
    - Request/response examples
    - Security scheme documentation
    - Tag-based organization
=============================================================================
"""

from fastapi import APIRouter
from fastapi.openapi.utils import get_openapi

from src.pharmaviyum.main import app

router = APIRouter(tags=["Documentation"])


def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="PharmaViyum CRM API",
        version="1.0.0",
        description="""
# PharmaViyum CRM API

## Overview
PharmaViyum CRM is a comprehensive pharmacy management system with AI-powered analytics.

## Features
- **Client Management**: Track customer information and purchase history
- **Product Management**: Manage inventory and product catalog
- **Sales Tracking**: Record and analyze sales transactions
- **AI Assistant**: Natural language queries for business insights

## Authentication
All API endpoints (except `/health` and `/docs`) require JWT authentication.
### Getting a Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{"username": "your_username", "password": "your_password"}'
```

### Using the Token
Include the token in the Authorization header:
```bash
curl -X GET "http://localhost:8000/api/v1/clients/" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Rate Limiting
API requests are rate-limited to prevent abuse:
- **Standard endpoints**: 100 requests per minute
- **AI endpoints**: 20 requests per minute

## Error Responses
All errors follow a consistent format:
```json
{
    "detail": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Support
For API support, contact: support@pharmaviyum.com
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "User authentication and token management",
            },
            {"name": "Clients", "description": "Client management operations"},
            {
                "name": "Products",
                "description": "Product catalog and inventory management",
            },
            {
                "name": "Sales",
                "description": "Sales transaction tracking and analytics",
            },
            {
                "name": "AI Assistant",
                "description": "AI-powered business intelligence queries",
            },
            {"name": "Health", "description": "System health checks and monitoring"},
        ],
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token",
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "tags" in method and not any(
                tag in ["Health", "Documentation"] for tag in method["tags"]
            ):
                method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return openapi_schema
    return app.openapi_schema


setattr(app, "openapi", custom_openapi)


@router.get("/api-docs", include_in_schema=False)
async def api_documentation():
    """Redirect to Swagger UI documentation."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")
