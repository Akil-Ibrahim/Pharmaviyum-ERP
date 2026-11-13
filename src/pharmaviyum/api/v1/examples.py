"""
=============================================================================
PharmaViyum CRM - API Request/Response Examples
=============================================================================
This module contains example payloads for OpenAPI documentation.
These examples are used in Swagger UI to help developers understand
the expected request/response formats.
=============================================================================
"""

# =============================================================================
# Authentication Examples
# =============================================================================

LOGIN_REQUEST_EXAMPLE = {"username": "admin", "password": "secure_password_123"}

LOGIN_RESPONSE_EXAMPLE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@pharmacy.com",
        "role": "admin",
    },
}

# =============================================================================
# Client Examples
# =============================================================================

CREATE_CLIENT_REQUEST_EXAMPLE = {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-15",
    "address": "123 Main St, City, Country",
    "notes": "Regular customer, prefers brand medications",
}

CLIENT_RESPONSE_EXAMPLE = {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-15",
    "address": "123 Main St, City, Country",
    "notes": "Regular customer, prefers brand medications",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "total_spent": 1250.50,
}

CLIENTS_LIST_RESPONSE_EXAMPLE = {
    "items": [
        CLIENT_RESPONSE_EXAMPLE,
        {
            "id": 2,
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+0987654321",
            "email": "jane.smith@example.com",
            "created_at": "2024-01-05T09:00:00Z",
            "total_spent": 650.00,
        },
    ],
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1,
}

# =============================================================================
# Product Examples
# =============================================================================

CREATE_PRODUCT_REQUEST_EXAMPLE = {
    "name": "Paracetamol 500mg",
    "sku": "MED-PARA-500-001",
    "category": "Pain Relief",
    "manufacturer": "PharmaCorp",
    "price": 5.99,
    "cost": 3.50,
    "stock_quantity": 500,
    "reorder_level": 100,
    "expiry_date": "2026-12-31",
    "description": "Common pain reliever and fever reducer",
    "requires_prescription": False,
}

PRODUCT_RESPONSE_EXAMPLE = {
    "id": 1,
    "name": "Paracetamol 500mg",
    "sku": "MED-PARA-500-001",
    "category": "Pain Relief",
    "manufacturer": "PharmaCorp",
    "price": 5.99,
    "cost": 3.50,
    "stock_quantity": 500,
    "reorder_level": 100,
    "expiry_date": "2026-12-31",
    "description": "Common pain reliever and fever reducer",
    "requires_prescription": False,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "is_low_stock": False,
    "is_expired": False,
}

# =============================================================================
# Sales Examples
# =============================================================================

CREATE_SALE_REQUEST_EXAMPLE = {
    "client_id": 1,
    "items": [
        {"product_id": 1, "quantity": 2, "unit_price": 5.99},
        {"product_id": 5, "quantity": 1, "unit_price": 12.50},
    ],
    "payment_method": "cash",
    "discount": 0.0,
    "notes": "Customer requested bag",
}

SALE_RESPONSE_EXAMPLE = {
    "id": 1,
    "client_id": 1,
    "client_name": "John Doe",
    "items": [
        {
            "product_id": 1,
            "product_name": "Paracetamol 500mg",
            "quantity": 2,
            "unit_price": 5.99,
            "subtotal": 11.98,
        },
        {
            "product_id": 5,
            "product_name": "Vitamin C 1000mg",
            "quantity": 1,
            "unit_price": 12.50,
            "subtotal": 12.50,
        },
    ],
    "subtotal": 24.48,
    "discount": 0.0,
    "total": 24.48,
    "payment_method": "cash",
    "notes": "Customer requested bag",
    "created_at": "2024-01-15T14:30:00Z",
    "pharmacist_id": 1,
    "pharmacist_name": "Admin User",
}

# =============================================================================
# AI Assistant Examples
# =============================================================================

AI_QUERY_REQUEST_EXAMPLE = {
    "question": "What are the top selling products this month?",
    "context": "pharmacy_sales",
    "max_tokens": 500,
    "temperature": 0.7,
}

AI_QUERY_RESPONSE_EXAMPLE = {
    "question": "What are the top selling products this month?",
    "answer": "Based on the sales data for this month, the top 5 selling products are:\n\n1. **Paracetamol 500mg** - 342 units sold ($2,048.58 revenue)\n2. **Vitamin C 1000mg** - 287 units sold ($3,587.50 revenue)\n3. **Ibuprofen 400mg** - 198 units sold ($1,584.00 revenue)\n4. **Amoxicillin 500mg** - 156 units sold ($2,340.00 revenue)\n5. **Omeprazole 20mg** - 143 units sold ($2,145.00 revenue)\n\nTotal revenue from top 5 products: $11,705.08\n\nWould you like more detailed analytics on any specific product?",
    "sources": [{"source": "sales_data", "relevance": 0.95, "data_points": 1250}],
    "processing_time_ms": 2340,
    "model": "mortarium-rag",
    "timestamp": "2024-01-15T14:30:00Z",
}

# =============================================================================
# Error Examples
# =============================================================================
ERROR_400_EXAMPLE = {
    "detail": "Invalid request payload",
    "error_code": "VALIDATION_ERROR",
    "timestamp": "2024-01-15T14:30:00Z",
    "path": "/api/v1/clients/",
    "method": "POST",
}

ERROR_401_EXAMPLE = {
    "detail": "Invalid credentials",
    "error_code": "AUTHENTICATION_FAILED",
    "timestamp": "2024-01-15T14:30:00Z",
}

ERROR_403_EXAMPLE = {
    "detail": "Insufficient permissions",
    "error_code": "FORBIDDEN",
    "timestamp": "2024-01-15T14:30:00Z",
    "required_role": "admin",
}

ERROR_404_EXAMPLE = {
    "detail": "Client with id 999 not found",
    "error_code": "RESOURCE_NOT_FOUND",
    "timestamp": "2024-01-15T14:30:00Z",
    "resource_type": "client",
    "resource_id": 999,
}

ERROR_429_EXAMPLE = {
    "detail": "Rate limit exceeded",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "timestamp": "2024-01-15T14:30:00Z",
    "retry_after": 60,
    "limit": 100,
    "window": "1 minute",
}

ERROR_500_EXAMPLE = {
    "detail": "Internal server error",
    "error_code": "INTERNAL_ERROR",
    "timestamp": "2024-01-15T14:30:00Z",
    "request_id": "req_abc123def456",
}
