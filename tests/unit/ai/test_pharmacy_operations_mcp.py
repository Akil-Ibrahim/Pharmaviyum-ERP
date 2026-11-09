"""Registration and contract tests for Mortarium pharmacy operations tools."""

import pytest

# Importing the public MCP package must register every shipped tool exactly once.
from src.pharmaviyum.ai.mcp import tool_registry  # noqa: E402
from src.pharmaviyum.ai.mcp.tools.pharmacy_operations import (  # noqa: E402
    InventoryOverviewRequest,
    ProductSearchRequest,
    SalesSummaryRequest,
)


@pytest.mark.unit
def test_pharmacy_operations_tools_are_registered_and_read_only():
    expected = {
        "search_pharmacy_products": "pharmacy_catalog",
        "get_inventory_overview": "pharmacy_inventory",
        "get_expiring_inventory": "pharmacy_inventory",
        "get_sales_summary": "pharmacy_sales",
    }
    registered = {item.name: item for item in tool_registry.list_tools()}

    for name, category in expected.items():
        assert name in registered
        assert registered[name].category == category
        assert registered[name].execution_class == "read"
        assert registered[name].requires_pharmacist_confirmation is False


@pytest.mark.unit
def test_pharmacy_operation_tool_inputs_are_bounded():
    assert ProductSearchRequest(query="omeprazole").limit == 10
    assert InventoryOverviewRequest(low_stock_only=True).limit == 25

    with pytest.raises(ValueError):
        ProductSearchRequest(query="x")
    with pytest.raises(ValueError):
        InventoryOverviewRequest(limit=101)


@pytest.mark.unit
def test_sales_summary_rejects_invalid_or_unbounded_date_ranges():
    with pytest.raises(ValueError, match="end_date"):
        SalesSummaryRequest(start_date="2026-11-10", end_date="2026-11-09")

    with pytest.raises(ValueError, match="367"):
        SalesSummaryRequest(start_date="2025-01-01", end_date="2026-01-04")
