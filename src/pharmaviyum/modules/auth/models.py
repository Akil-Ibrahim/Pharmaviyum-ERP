"""
User and tenant authorization models.

Best practice:
- Explicit application role for MCP authorization
- Explicit user-to-pharmacy membership for tenant isolation
- No implicit privileged/system role at AI boundaries
"""

from typing import Literal

from ...models.user import User
from ...models.pharmacy_membership import PharmacyMembership

UserRole = Literal["patient", "pharmacist", "admin", "system"]

__all__ = ["User", "UserRole", "PharmacyMembership"]
