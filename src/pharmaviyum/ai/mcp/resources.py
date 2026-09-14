"""
MCP Resources — Passive data endpoints for the AI agent.

Best practice 2026:
- URI-based resource addressing (e.g., pharma://drugs/{id})
- Dynamic content generation based on URI parameters
- Metadata for resource discovery
"""
from __future__ import annotations
from typing import Any, Callable, Awaitable
from pydantic import BaseModel
from src.pharmaviyum.core.logging import logger


class Resource(BaseModel):
    """MCP Resource definition."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class ResourceRegistry:
    """Registry for MCP resources."""
    
    def __init__(self):
        self._resources: dict[str, Resource] = {}
        self._handlers: dict[str, Callable[..., Awaitable[str]]] = {}
    
    def resource(
        self,
        uri_template: str,
        name: str,
        description: str,
        mime_type: str = "application/json",
    ):
        """Decorator to register a resource handler."""
        def decorator(func: Callable[..., Awaitable[str]]):
            self._resources[uri_template] = Resource(
                uri=uri_template,
                name=name,
                description=description,
                mime_type=mime_type,
            )
            self._handlers[uri_template] = func
            logger.info(f"Registered MCP resource: {uri_template}")
            return func
        return decorator
    
    def list_resources(self) -> list[Resource]:
        return list(self._resources.values())
    
    async def read_resource(self, uri: str, **kwargs) -> str:
        """Read resource content by URI."""
        # Simple exact match or template matching
        for template, handler in self._handlers.items():
            if template == uri or ( "{" in template and self._match_template(template, uri, kwargs) ):
                return await handler(**kwargs)
        raise ValueError(f"Resource not found: {uri}")
    
    def _match_template(self, template: str, uri: str, kwargs: dict) -> bool:
        """Basic template matching (e.g., pharma://drugs/{id} -> pharma://drugs/123)"""
        # Simplified for demonstration; in production use a proper URI router
        return template.replace("{id}", kwargs.get("id", "")) == uri


resource_registry = ResourceRegistry()


# ============================================================================
# RESOURCE DEFINITIONS
# ============================================================================

@resource_registry.resource(
    uri_template="pharma://regulations/{country}",
    name="Country Pharmaceutical Regulations",
    description="Regulatory guidelines and controlled substance limits for a specific country",
)
async def get_country_regulations(country: str) -> str:
    """Fetch regulatory data for a country."""
    regulations = {
        "VN": {"controlled_limits": {"Diazepam": 30, "Codeine": 60}, "prescription_validity_days": 30},
        "ID": {"controlled_limits": {"Diazepam": 30, "Codeine": 60}, "prescription_validity_days": 30},
        "SA": {"controlled_limits": {"Diazepam": 30, "Codeine": 30}, "prescription_validity_days": 30},
    }
    import json
    return json.dumps(regulations.get(country.upper(), {"error": "Country not found"}), indent=2)


@resource_registry.resource(
    uri_template="pharma://halal/standards/{body}",
    name="Halal Certification Standards",
    description="Specific halal certification requirements by regulatory body",
)
async def get_halal_standards(body: str) -> str:
    """Fetch halal standards for a specific body."""
    standards = {
        "MUI": "Requires explicit halal slaughter for bovine gelatin. Synthetic ethanol permissible if <0.5%.",
        "JAKIM": "Strict vegetarian capsule preference. HPMC highly recommended.",
        "SFDA": "Zero tolerance for porcine derivatives. Full supply chain audit required.",
    }
    return standards.get(body.upper(), "Standard not found. Supported: MUI, JAKIM, SFDA")
