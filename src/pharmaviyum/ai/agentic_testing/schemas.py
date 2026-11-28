"""Strict, bounded contracts for agentic browser-test scenarios."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class BrowserTestStep(BaseModel):
    """One allowlisted browser instruction; never an arbitrary script."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: Literal["goto", "expect_url", "expect_visible"]
    value: str = Field(min_length=1, max_length=2048)

    @field_validator("value")
    @classmethod
    def value_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("step value must not contain surrounding whitespace")
        return value

    @field_validator("value")
    @classmethod
    def navigation_must_be_relative(cls, value: str, info):
        if info.data.get("action") == "goto" and (
            not value.startswith("/") or value.startswith("//")
        ):
            raise ValueError(
                "goto accepts only an absolute path on the approved origin"
            )
        return value


class AgenticTestScenario(BaseModel):
    """Declarative test scenario with a deliberately small browser action surface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,99}$")
    title: str = Field(min_length=3, max_length=160)
    target_url: AnyHttpUrl
    steps: list[BrowserTestStep] = Field(min_length=1, max_length=8)
    expected_outcome: str = Field(min_length=3, max_length=500)


def normalized_origin(value: str) -> str:
    """Return a canonical scheme/host/port origin, rejecting URL credentials."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("target URL must use HTTP(S) and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not permitted")
    if parsed.query or parsed.fragment:
        raise ValueError("origin allowlist entries must not include query or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("origin allowlist entries must not include a path")
    host = parsed.hostname.lower()
    port = parsed.port
    default_port = (parsed.scheme == "http" and port == 80) or (
        parsed.scheme == "https" and port == 443
    )
    suffix = f":{port}" if port is not None and not default_port else ""
    return f"{parsed.scheme.lower()}://{host}{suffix}"


def validate_scenario_target(
    scenario: AgenticTestScenario, allowed_origins: list[str]
) -> str:
    """Fail closed unless the scenario target exactly matches explicit config."""
    if not allowed_origins:
        raise ValueError("at least one explicitly configured test origin is required")
    target_origin = normalized_origin(str(scenario.target_url))
    normalized_allowed = {normalized_origin(origin) for origin in allowed_origins}
    if target_origin not in normalized_allowed:
        raise ValueError(
            "scenario target is not in the configured test-origin allowlist"
        )
    return target_origin
