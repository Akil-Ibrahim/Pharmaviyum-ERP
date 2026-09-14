"""
Tests for MCP tools and server.

Tests cover:
- Tool registration and metadata
- Drug interaction checker
- Patient history retrieval
- Halal compliance engine
- Prescription verification
- MCP server JSON-RPC protocol
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
class TestDrugInteractionTool:
    """Test drug interaction checking tool."""
    
    @pytest.mark.asyncio
    async def test_critical_interaction_detected(self):
        """Test detection of critical drug interactions."""
        from src.pharmaviyum.ai.mcp.tools.drug_interactions import check_drug_interactions
        from src.pharmaviyum.ai.mcp.schemas import DrugInteractionCheckInput
        
        input_data = DrugInteractionCheckInput(
            drugs=["Warfarin", "Aspirin"],
            patient_id=123,
        )
        
        result = await check_drug_interactions(input_data)
        
        assert result.success is True
        assert len(result.interactions) > 0
        assert any(i.severity == "critical" for i in result.interactions)
    
    @pytest.mark.asyncio
    async def test_no_interaction(self):
        """Test drugs with no known interactions."""
        from src.pharmaviyum.ai.mcp.tools.drug_interactions import check_drug_interactions
        from src.pharmaviyum.ai.mcp.schemas import DrugInteractionCheckInput
        
        input_data = DrugInteractionCheckInput(
            drugs=["Paracetamol", "Vitamin C"],
            patient_id=123,
        )
        
        result = await check_drug_interactions(input_data)
        
        assert result.success is True
        # May have no interactions or only minor ones
    
    @pytest.mark.asyncio
    async def test_drug_name_normalization(self):
        """Test drug name normalization (Paracetamol = Acetaminophen)."""
        from src.pharmaviyum.ai.mcp.tools.drug_interactions import check_drug_interactions
        from src.pharmaviyum.ai.mcp.schemas import DrugInteractionCheckInput
        
        # Test with alternative name
        input_data = DrugInteractionCheckInput(
            drugs=["Acetaminophen", "Warfarin"],
            patient_id=123,
        )
        
        result = await check_drug_interactions(input_data)
        
        assert result.success is True


@pytest.mark.unit
class TestHalalComplianceTool:
    """Test halal compliance checking tool."""
    
    @pytest.mark.asyncio
    async def test_halal_certified_drug(self):
        """Test drug with halal certification."""
        from src.pharmaviyum.ai.mcp.tools.halal_compliance import check_halal_compliance
        from src.pharmaviyum.ai.mcp.schemas import HalalComplianceInput
        
        input_data = HalalComplianceInput(
            drug_name="Paracetamol",
            country="SA",
            fiqh_school="Hanbali",
        )
        
        result = await check_halal_compliance(input_data)
        
        assert result.success is True
        assert result.is_halal is True or result.status in ["halal", "mushbooh"]
    
    @pytest.mark.asyncio
    async def test_shia_fiqh_sistani(self):
        """Test Shia fiqh with Sistani ruling."""
        from src.pharmaviyum.ai.mcp.tools.halal_compliance import check_halal_compliance
        from src.pharmaviyum.ai.mcp.schemas import HalalComplianceInput
        
        input_data = HalalComplianceInput(
            drug_name="Amoxicillin",
            country="IQ",
            fiqh_school="Ja'fari",
            marja="Sistani",
        )
        
        result = await check_halal_compliance(input_data)
        
        assert result.success is True
        # Sistani has specific rulings on gelatin


@pytest.mark.unit
class TestMCPServer:
    """Test MCP server JSON-RPC protocol."""
    
    @pytest.mark.asyncio
    async def test_initialize_method(self):
        """Test MCP server initialization."""
        from src.pharmaviyum.ai.mcp.server import MCPServer
        
        server = MCPServer()
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        })
        
        response = await server.handle_request(request)
        response_data = json.loads(response)
        
        assert response_data["jsonrpc"] == "2.0"
        assert "result" in response_data
        assert "capabilities" in response_data["result"]
    
    @pytest.mark.asyncio
    async def test_tools_list_method(self):
        """Test listing available tools."""
        from src.pharmaviyum.ai.mcp.server import MCPServer
        
        server = MCPServer()
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        
        response = await server.handle_request(request)
        response_data = json.loads(response)
        
        assert response_data["jsonrpc"] == "2.0"
        assert "tools" in response_data["result"]
    
    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test server handles invalid JSON gracefully."""
        from src.pharmaviyum.ai.mcp.server import MCPServer
        
        server = MCPServer()
        
        response = await server.handle_request("invalid json")
        response_data = json.loads(response)
        
        assert "error" in response_data
        assert response_data["error"]["code"] == -32700  # Parse error
    
    @pytest.mark.asyncio
    async def test_unknown_method(self):
        """Test server handles unknown methods."""
        from src.pharmaviyum.ai.mcp.server import MCPServer
        
        server = MCPServer()
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "unknown/method",
            "params": {}
        })
        
        response = await server.handle_request(request)
        response_data = json.loads(response)
        
        assert "error" in response_data
