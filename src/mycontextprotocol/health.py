"""Health check utilities for mycontextprotocol services.

Implements IETF draft-inadarei-api-health-check-06 compatible health responses.
"""

import asyncio
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """Individual health check result."""

    component_name: str = Field(description="Name of the component being checked")
    status: Literal["pass", "fail"] = Field(description="Status of this check")
    time: str = Field(description="ISO 8601 timestamp of the check")
    output: str | None = Field(default=None, description="Human-readable output or error message")


class HealthResponse(BaseModel):
    """IETF-compatible health check response."""

    status: Literal["pass", "warn", "fail"] = Field(description="Overall health status")
    version: str = Field(description="Application version")
    checks: dict[str, HealthCheck] = Field(
        default_factory=dict, description="Individual component checks"
    )


async def check_postgres(connection_string: str, timeout: float = 5.0) -> HealthCheck:
    """Check PostgreSQL connectivity.

    Args:
        connection_string: PostgreSQL connection string
        timeout: Timeout in seconds for the check

    Returns:
        HealthCheck result for PostgreSQL
    """
    try:
        # Import here to avoid requiring asyncpg if not used
        import asyncpg

        conn = await asyncio.wait_for(asyncpg.connect(connection_string), timeout=timeout)
        try:
            await conn.execute("SELECT 1")
            return HealthCheck(
                component_name="postgres",
                status="pass",
                time=datetime.now(UTC).isoformat(),
                output="Connected successfully",
            )
        finally:
            await conn.close()
    except TimeoutError:
        return HealthCheck(
            component_name="postgres",
            status="fail",
            time=datetime.now(UTC).isoformat(),
            output=f"Connection timeout after {timeout}s",
        )
    except Exception as e:
        return HealthCheck(
            component_name="postgres",
            status="fail",
            time=datetime.now(UTC).isoformat(),
            output=f"Connection failed: {e!s}",
        )


async def check_dragonfly(host: str, port: int, timeout: float = 5.0) -> HealthCheck:
    """Check Dragonfly (Redis) connectivity.

    Args:
        host: Dragonfly host
        port: Dragonfly port
        timeout: Timeout in seconds for the check

    Returns:
        HealthCheck result for Dragonfly
    """
    try:
        import redis.asyncio as redis

        client = redis.Redis(host=host, port=port, decode_responses=True)
        try:
            await asyncio.wait_for(client.ping(), timeout=timeout)  # type: ignore[misc]
            return HealthCheck(
                component_name="dragonfly",
                status="pass",
                time=datetime.now(UTC).isoformat(),
                output="Ping successful",
            )
        finally:
            await client.aclose()
    except TimeoutError:
        return HealthCheck(
            component_name="dragonfly",
            status="fail",
            time=datetime.now(UTC).isoformat(),
            output=f"Ping timeout after {timeout}s",
        )
    except Exception as e:
        return HealthCheck(
            component_name="dragonfly",
            status="fail",
            time=datetime.now(UTC).isoformat(),
            output=f"Ping failed: {e!s}",
        )


def aggregate_health_status(checks: dict[str, HealthCheck]) -> Literal["pass", "fail"]:
    """Determine overall health status from individual checks.

    Args:
        checks: Dictionary of component checks

    Returns:
        "pass" if all checks pass, "fail" if any check fails
    """
    if not checks:
        return "fail"

    if any(check.status == "fail" for check in checks.values()):
        return "fail"

    return "pass"
