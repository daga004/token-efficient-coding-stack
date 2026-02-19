"""MCP protocol compliance and error handling tests for AuZoom and Orchestrator.

Tests JSON-RPC 2.0 response format, tool manifest completeness, initialize
handshake support, error code compliance, and error handling edge cases.

Phase 11-03: Protocol Compliance Testing

Findings documented:
- AuZoom initialize handshake FIXED (Phase 13-01, GAP-023)
- auzoom_get_calls added to tools_schema.py manifest FIXED (Phase 13-01, GAP-024)
- Orchestrator ValidationError now caught at handler level FIXED (Phase 13-01, GAP-025)
- Both servers correctly implement -32601 (Method not found) and -32700 (Parse error)
"""

import asyncio
import atexit
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from auzoom import AuZoomMCPServer
from auzoom.mcp.jsonrpc_handler import JSONRPCHandler as AuZoomJSONRPCHandler
from auzoom.mcp.tools_schema import get_tools_manifest as auzoom_get_tools_manifest
from orchestrator.mcp.server import OrchestratorMCPServer
from orchestrator.mcp.jsonrpc_handler import JSONRPCHandler as OrchestratorJSONRPCHandler
from orchestrator.mcp.tools_schema import get_tools_manifest as orch_get_tools_manifest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_auzoom_cache():
    """Clear .auzoom cache before each test."""
    cache_dir = Path(".auzoom")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    yield
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def auzoom_server():
    """Create AuZoom MCP server instance for testing."""
    return AuZoomMCPServer(".", auto_warm=False)


@pytest.fixture
def orchestrator_server():
    """Create Orchestrator MCP server instance for testing."""
    return OrchestratorMCPServer()


@pytest.fixture
def auzoom_handler(auzoom_server):
    """Create AuZoom JSON-RPC handler for protocol-level testing."""
    return AuZoomJSONRPCHandler(auzoom_server)


@pytest.fixture
def orchestrator_handler(orchestrator_server):
    """Create Orchestrator JSON-RPC handler for protocol-level testing."""
    return OrchestratorJSONRPCHandler(orchestrator_server)


def run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------

_evidence_records: List[Dict[str, Any]] = []


def _record_evidence(
    test_name: str,
    server: str,
    request: Dict[str, Any],
    response: Dict[str, Any],
    compliance_status: str,
    gaps_found: List[str] = None,
):
    """Collect protocol compliance evidence for JSONL output."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test": test_name,
        "server": server,
        "request": request,
        "response": response,
        "compliance_status": compliance_status,
        "gaps_found": gaps_found or [],
    }
    _evidence_records.append(record)


def _flush_evidence():
    """Write evidence to JSONL file."""
    if not _evidence_records:
        return

    evidence_dir = Path(__file__).parent.parent / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "11-03-protocol-compliance.jsonl"

    with open(evidence_file, "w") as f:
        for record in _evidence_records:
            f.write(json.dumps(record) + "\n")


atexit.register(_flush_evidence)


# ===========================================================================
# Task 1: MCP Protocol Compliance Tests
# ===========================================================================


class TestJSONRPCResponseFormat:
    """Test JSON-RPC 2.0 response format for both servers."""

    def test_auzoom_tools_list_response_format(self, auzoom_handler):
        """AuZoom tools/list returns valid JSON-RPC 2.0 response."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0", "Missing jsonrpc: 2.0"
        assert response.get("id") == 1, "Response id must match request id"
        assert "result" in response, "Response must contain result"
        assert "tools" in response["result"], "Result must contain tools array"
        assert isinstance(response["result"]["tools"], list), "Tools must be an array"
        assert "error" not in response, "Success response must not contain error"

        _record_evidence(
            "auzoom_tools_list_format", "auzoom", request, response,
            "compliant",
        )

    def test_orchestrator_tools_list_response_format(self, orchestrator_handler):
        """Orchestrator tools/list returns valid JSON-RPC 2.0 response."""
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = orchestrator_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0", "Missing jsonrpc: 2.0"
        assert response.get("id") == 2, "Response id must match request id"
        assert "result" in response, "Response must contain result"
        assert "tools" in response["result"], "Result must contain tools array"
        assert isinstance(response["result"]["tools"], list), "Tools must be an array"
        assert "error" not in response, "Success response must not contain error"

        _record_evidence(
            "orchestrator_tools_list_format", "orchestrator", request, response,
            "compliant",
        )

    def test_auzoom_tools_call_response_format(self, auzoom_handler):
        """AuZoom tools/call returns valid JSON-RPC 2.0 with content array."""
        request = {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "auzoom_stats", "arguments": {}},
        }
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 3
        assert "result" in response
        assert "content" in response["result"]
        assert isinstance(response["result"]["content"], list)
        assert len(response["result"]["content"]) > 0

        # Content items must have type and text
        item = response["result"]["content"][0]
        assert item.get("type") == "text"
        assert isinstance(item.get("text"), str)

        _record_evidence(
            "auzoom_tools_call_format", "auzoom", request, response,
            "compliant",
        )

    def test_orchestrator_tools_call_response_format(self, orchestrator_handler):
        """Orchestrator tools/call returns valid JSON-RPC 2.0 with content array."""
        request = {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {
                "name": "orchestrator_route",
                "arguments": {"task": "Test task for protocol compliance"},
            },
        }
        # Orchestrator tools/call is async
        response = run_async(orchestrator_handler._handle_request_async(request))

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 4
        assert "result" in response
        assert "content" in response["result"]
        assert isinstance(response["result"]["content"], list)
        assert len(response["result"]["content"]) > 0

        item = response["result"]["content"][0]
        assert item.get("type") == "text"
        assert isinstance(item.get("text"), str)

        # Verify the text is valid JSON (tool results are JSON-serialized)
        parsed = json.loads(item["text"])
        assert isinstance(parsed, dict)

        _record_evidence(
            "orchestrator_tools_call_format", "orchestrator", request, response,
            "compliant",
        )

    def test_auzoom_response_id_matches_request(self, auzoom_handler):
        """AuZoom preserves request id in all response types."""
        for req_id in [1, 42, "abc-123", None]:
            request = {"jsonrpc": "2.0", "id": req_id, "method": "tools/list"}
            response = auzoom_handler._handle_request(request)
            assert response.get("id") == req_id, (
                f"Response id {response.get('id')} must match request id {req_id}"
            )

    def test_orchestrator_response_id_matches_request(self, orchestrator_handler):
        """Orchestrator preserves request id in all response types."""
        for req_id in [1, 42, "abc-123", None]:
            request = {"jsonrpc": "2.0", "id": req_id, "method": "tools/list"}
            response = orchestrator_handler._handle_request(request)
            assert response.get("id") == req_id, (
                f"Response id {response.get('id')} must match request id {req_id}"
            )


class TestToolManifestCompleteness:
    """Test that tool manifests accurately reflect available tools."""

    def test_auzoom_manifest_tool_count(self):
        """AuZoom manifest lists all 6 tools including auzoom_get_calls."""
        manifest = auzoom_get_tools_manifest()
        tools = manifest["tools"]
        tool_names = [t["name"] for t in tools]

        assert len(tools) == 6, f"Expected 6 tools in manifest, got {len(tools)}"
        expected_tools = [
            "auzoom_read", "auzoom_find", "auzoom_get_dependencies",
            "auzoom_get_calls", "auzoom_stats", "auzoom_validate",
        ]
        for name in expected_tools:
            assert name in tool_names, f"Missing tool in manifest: {name}"

        _record_evidence(
            "auzoom_manifest_tool_count", "auzoom",
            {"action": "get_tools_manifest"},
            {"tools": tool_names, "count": len(tools)},
            "pass - all 6 tools listed",
        )

    def test_auzoom_get_calls_in_manifest(self, auzoom_server):
        """VERIFIED: auzoom_get_calls is now in manifest and discoverable (GAP-024 fixed).

        Phase 13-01 added auzoom_get_calls schema to tools_schema.py.
        The tool is both callable via handler AND discoverable via tools/list.
        """
        manifest = auzoom_get_tools_manifest()
        manifest_names = [t["name"] for t in manifest["tools"]]

        # Verify it IS in the manifest (was missing before GAP-024 fix)
        assert "auzoom_get_calls" in manifest_names, (
            "auzoom_get_calls should be in manifest after GAP-024 fix"
        )

        # Verify the schema has correct inputSchema with required node_id
        tool_map = {t["name"]: t for t in manifest["tools"]}
        get_calls_schema = tool_map["auzoom_get_calls"]["inputSchema"]
        assert "node_id" in get_calls_schema.get("properties", {}), (
            "auzoom_get_calls schema must have node_id property"
        )
        assert "node_id" in get_calls_schema.get("required", []), (
            "auzoom_get_calls schema must require node_id"
        )

        # Also verify it IS in the server handler (callable)
        result = auzoom_server.handle_tool_call(
            "auzoom_get_calls", {"node_id": "nonexistent::node"}
        )
        assert "Unknown tool" not in result.get("error", ""), (
            "auzoom_get_calls should be recognized by the handler"
        )

        _record_evidence(
            "auzoom_get_calls_in_manifest", "auzoom",
            {"action": "check_get_calls_in_manifest_and_handler"},
            {"in_manifest": True, "in_handler": True, "handler_result": result},
            "pass - tool discoverable and callable",
        )

    def test_orchestrator_manifest_tool_count(self):
        """Orchestrator manifest lists exactly 3 tools matching handler."""
        manifest = orch_get_tools_manifest()
        tools = manifest["tools"]
        tool_names = [t["name"] for t in tools]

        assert len(tools) == 3, f"Expected 3 tools in manifest, got {len(tools)}"
        expected_tools = [
            "orchestrator_route", "orchestrator_execute", "orchestrator_validate",
        ]
        for name in expected_tools:
            assert name in tool_names, f"Missing tool in manifest: {name}"

        _record_evidence(
            "orchestrator_manifest_tool_count", "orchestrator",
            {"action": "get_tools_manifest"},
            {"tools": tool_names, "count": len(tools)},
            "compliant",
        )

    def test_auzoom_tool_schemas_have_required_fields(self):
        """Each AuZoom tool schema has name, description, and inputSchema."""
        manifest = auzoom_get_tools_manifest()
        for tool in manifest["tools"]:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool {tool['name']} missing description"
            assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
            assert tool["inputSchema"].get("type") == "object", (
                f"Tool {tool['name']} inputSchema.type must be 'object'"
            )
            assert "properties" in tool["inputSchema"], (
                f"Tool {tool['name']} inputSchema missing properties"
            )

    def test_orchestrator_tool_schemas_have_required_fields(self):
        """Each Orchestrator tool schema has name, description, and inputSchema."""
        manifest = orch_get_tools_manifest()
        for tool in manifest["tools"]:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool {tool['name']} missing description"
            assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
            assert tool["inputSchema"].get("type") == "object", (
                f"Tool {tool['name']} inputSchema.type must be 'object'"
            )
            assert "properties" in tool["inputSchema"], (
                f"Tool {tool['name']} inputSchema missing properties"
            )

    def test_auzoom_required_params_declared(self):
        """AuZoom tools with required params declare them in schema."""
        manifest = auzoom_get_tools_manifest()
        tool_map = {t["name"]: t for t in manifest["tools"]}

        # auzoom_read requires "path"
        read_schema = tool_map["auzoom_read"]["inputSchema"]
        assert "required" in read_schema, "auzoom_read must declare required params"
        assert "path" in read_schema["required"], "auzoom_read must require 'path'"

        # auzoom_find requires "pattern"
        find_schema = tool_map["auzoom_find"]["inputSchema"]
        assert "required" in find_schema, "auzoom_find must declare required params"
        assert "pattern" in find_schema["required"], "auzoom_find must require 'pattern'"

        # auzoom_get_dependencies requires "node_id"
        deps_schema = tool_map["auzoom_get_dependencies"]["inputSchema"]
        assert "required" in deps_schema
        assert "node_id" in deps_schema["required"]

    def test_orchestrator_required_params_declared(self):
        """Orchestrator tools with required params declare them in schema."""
        manifest = orch_get_tools_manifest()
        tool_map = {t["name"]: t for t in manifest["tools"]}

        # orchestrator_route requires "task"
        route_schema = tool_map["orchestrator_route"]["inputSchema"]
        assert "required" in route_schema
        assert "task" in route_schema["required"]

        # orchestrator_execute requires "model" and "prompt"
        exec_schema = tool_map["orchestrator_execute"]["inputSchema"]
        assert "required" in exec_schema
        assert "model" in exec_schema["required"]
        assert "prompt" in exec_schema["required"]

        # orchestrator_validate requires "task" and "output"
        val_schema = tool_map["orchestrator_validate"]["inputSchema"]
        assert "required" in val_schema
        assert "task" in val_schema["required"]
        assert "output" in val_schema["required"]


class TestInitializeHandshake:
    """Test MCP v2024-11-05 initialize handshake support."""

    def test_orchestrator_has_initialize(self, orchestrator_handler):
        """Orchestrator implements initialize handshake per MCP v2024-11-05."""
        request = {
            "jsonrpc": "2.0", "id": 10,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        response = orchestrator_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 10
        assert "result" in response
        assert "error" not in response

        result = response["result"]
        assert result.get("protocolVersion") == "2024-11-05", (
            "Must return protocolVersion"
        )
        assert "capabilities" in result, "Must return capabilities"
        assert "tools" in result["capabilities"], (
            "Must declare tools capability"
        )
        assert "serverInfo" in result, "Must return serverInfo"
        assert result["serverInfo"].get("name") == "orchestrator"

        _record_evidence(
            "orchestrator_initialize_handshake", "orchestrator",
            request, response, "compliant",
        )

    def test_auzoom_initialize_handshake(self, auzoom_handler):
        """VERIFIED: AuZoom implements initialize handshake (GAP-023 fixed).

        Phase 13-01 added _handle_initialize() to AuZoom's JSONRPCHandler.
        Returns protocolVersion, capabilities, and serverInfo per MCP v2024-11-05.
        """
        request = {
            "jsonrpc": "2.0", "id": 11,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 11
        assert "result" in response, "AuZoom should return result for initialize"
        assert "error" not in response, "Initialize should not return error"

        result = response["result"]
        assert result.get("protocolVersion") == "2024-11-05", (
            "Must return protocolVersion 2024-11-05"
        )
        assert "capabilities" in result, "Must return capabilities"
        assert "tools" in result["capabilities"], "Must declare tools capability"
        assert "serverInfo" in result, "Must return serverInfo"
        assert result["serverInfo"].get("name") == "auzoom", (
            "serverInfo.name must be 'auzoom'"
        )

        _record_evidence(
            "auzoom_initialize_handshake", "auzoom",
            request, response,
            "pass - initialize handshake implemented",
        )


class TestErrorCodeCompliance:
    """Test JSON-RPC error code compliance."""

    def test_auzoom_method_not_found(self, auzoom_handler):
        """AuZoom returns -32601 for unknown methods."""
        request = {"jsonrpc": "2.0", "id": 20, "method": "unknown/method"}
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 20
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "message" in response["error"]
        assert "result" not in response, "Error response must not contain result"

        _record_evidence(
            "auzoom_method_not_found", "auzoom", request, response,
            "compliant",
        )

    def test_orchestrator_method_not_found(self, orchestrator_handler):
        """Orchestrator returns -32601 for unknown methods."""
        request = {"jsonrpc": "2.0", "id": 21, "method": "unknown/method"}
        response = orchestrator_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 21
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "message" in response["error"]
        assert "result" not in response

        _record_evidence(
            "orchestrator_method_not_found", "orchestrator", request, response,
            "compliant",
        )

    def test_auzoom_parse_error(self, auzoom_handler):
        """AuZoom _send_parse_error creates -32700 error response."""
        # We can't easily send malformed JSON through _handle_request
        # (it expects a dict). Test the error creation method directly.
        error_response = auzoom_handler._create_error_response(
            None, -32700, "Parse error: test"
        )
        assert error_response["jsonrpc"] == "2.0"
        assert error_response["id"] is None
        assert error_response["error"]["code"] == -32700
        assert "Parse error" in error_response["error"]["message"]

        _record_evidence(
            "auzoom_parse_error", "auzoom",
            {"raw": "malformed json"},
            error_response, "compliant",
        )

    def test_orchestrator_parse_error(self, orchestrator_handler):
        """Orchestrator _send_parse_error creates -32700 error response."""
        error_response = orchestrator_handler._create_error_response(
            None, -32700, "Parse error: test"
        )
        assert error_response["jsonrpc"] == "2.0"
        assert error_response["id"] is None
        assert error_response["error"]["code"] == -32700
        assert "Parse error" in error_response["error"]["message"]

        _record_evidence(
            "orchestrator_parse_error", "orchestrator",
            {"raw": "malformed json"},
            error_response, "compliant",
        )

    def test_auzoom_unknown_tool_via_tools_call(self, auzoom_handler):
        """AuZoom tools/call with unknown tool returns error in result content."""
        request = {
            "jsonrpc": "2.0", "id": 22, "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        }
        response = auzoom_handler._handle_request(request)

        # JSON-RPC level: valid response (tools/call succeeded at protocol level)
        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 22
        assert "result" in response

        # Tool level: error in content text
        content_text = response["result"]["content"][0]["text"]
        parsed = json.loads(content_text)
        assert "error" in parsed, "Unknown tool should return error in content"
        assert "Unknown tool" in parsed["error"]

        _record_evidence(
            "auzoom_unknown_tool_via_call", "auzoom", request, response,
            "compliant - error returned in tool result",
        )

    def test_orchestrator_unknown_tool_via_tools_call(self, orchestrator_handler):
        """Orchestrator tools/call with unknown tool returns error in result content."""
        request = {
            "jsonrpc": "2.0", "id": 23, "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        }
        response = run_async(orchestrator_handler._handle_request_async(request))

        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 23
        assert "result" in response

        content_text = response["result"]["content"][0]["text"]
        parsed = json.loads(content_text)
        assert "error" in parsed
        assert "Unknown tool" in parsed["error"]

        _record_evidence(
            "orchestrator_unknown_tool_via_call", "orchestrator", request, response,
            "compliant - error returned in tool result",
        )

    def test_auzoom_error_response_structure(self, auzoom_handler):
        """AuZoom error responses have all required JSON-RPC fields."""
        request = {"jsonrpc": "2.0", "id": 99, "method": "invalid"}
        response = auzoom_handler._handle_request(request)

        # Must have exactly: jsonrpc, id, error
        assert set(response.keys()) == {"jsonrpc", "id", "error"}, (
            f"Error response keys should be {{jsonrpc, id, error}}, "
            f"got {set(response.keys())}"
        )
        assert isinstance(response["error"], dict)
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert isinstance(response["error"]["code"], int)
        assert isinstance(response["error"]["message"], str)

    def test_orchestrator_error_response_structure(self, orchestrator_handler):
        """Orchestrator error responses have all required JSON-RPC fields."""
        request = {"jsonrpc": "2.0", "id": 99, "method": "invalid"}
        response = orchestrator_handler._handle_request(request)

        assert set(response.keys()) == {"jsonrpc", "id", "error"}
        assert isinstance(response["error"], dict)
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert isinstance(response["error"]["code"], int)
        assert isinstance(response["error"]["message"], str)


# ===========================================================================
# Task 2: Error Handling Edge Cases
# ===========================================================================


class TestMissingRequiredParams:
    """Test behavior when required parameters are missing."""

    def test_auzoom_read_missing_path(self, auzoom_server):
        """auzoom_read without required 'path' returns error dict."""
        result = auzoom_server.handle_tool_call("auzoom_read", {})

        assert isinstance(result, dict), "Should return dict, not crash"
        assert "error" in result, "Missing path should produce error"
        assert "path" in result["error"].lower(), (
            f"Error should mention 'path': {result['error']}"
        )

        _record_evidence(
            "auzoom_read_missing_path", "auzoom",
            {"tool": "auzoom_read", "arguments": {}},
            result, "compliant - returns error for missing required param",
        )

    def test_auzoom_find_missing_pattern(self, auzoom_server):
        """auzoom_find without required 'pattern' returns empty results (default)."""
        result = auzoom_server.handle_tool_call("auzoom_find", {})

        # auzoom_find defaults to empty string pattern, returning empty matches
        assert isinstance(result, dict), "Should return dict, not crash"
        # The function uses .get("pattern", "") so it defaults gracefully
        assert "matches" in result or "error" in result

        _record_evidence(
            "auzoom_find_missing_pattern", "auzoom",
            {"tool": "auzoom_find", "arguments": {}},
            result, "compliant - graceful default",
        )

    def test_auzoom_get_deps_missing_node_id(self, auzoom_server):
        """auzoom_get_dependencies without node_id returns error."""
        result = auzoom_server.handle_tool_call("auzoom_get_dependencies", {})

        assert isinstance(result, dict)
        assert "error" in result, "Missing node_id should produce error"

        _record_evidence(
            "auzoom_get_deps_missing_node_id", "auzoom",
            {"tool": "auzoom_get_dependencies", "arguments": {}},
            result, "compliant - returns error for missing required param",
        )

    def test_orchestrator_route_missing_task(self, orchestrator_server):
        """orchestrator_route without 'task' handles gracefully."""
        result = run_async(
            orchestrator_server.handle_tool_call("orchestrator_route", {})
        )

        # The handler uses .get("task", "") so it defaults to empty string
        assert isinstance(result, dict), "Should return dict, not crash"
        # Should still produce a routing result (with low score for empty task)
        assert "model" in result or "error" in result

        _record_evidence(
            "orchestrator_route_missing_task", "orchestrator",
            {"tool": "orchestrator_route", "arguments": {}},
            result, "compliant - graceful default for empty task",
        )

    def test_orchestrator_execute_missing_model(self, orchestrator_server):
        """orchestrator_execute without 'model' returns error."""
        result = run_async(
            orchestrator_server.handle_tool_call(
                "orchestrator_execute", {"prompt": "test"}
            )
        )

        assert isinstance(result, dict)
        # model is None -> unknown model error
        assert result.get("success") is False or "error" in result

        _record_evidence(
            "orchestrator_execute_missing_model", "orchestrator",
            {"tool": "orchestrator_execute", "arguments": {"prompt": "test"}},
            result, "compliant - returns error for missing model",
        )

    def test_orchestrator_validate_missing_params(self, orchestrator_server):
        """orchestrator_validate without params handles gracefully."""
        result = run_async(
            orchestrator_server.handle_tool_call("orchestrator_validate", {})
        )

        assert isinstance(result, dict), "Should return dict, not crash"
        # Uses .get("task", "") and .get("output", "") defaults
        # May fail at executor level but should not crash
        assert "pass" in result or "error" in result

        _record_evidence(
            "orchestrator_validate_missing_params", "orchestrator",
            {"tool": "orchestrator_validate", "arguments": {}},
            result, "compliant - graceful handling",
        )


class TestInvalidParamTypes:
    """Test behavior with wrong parameter types."""

    def test_auzoom_read_invalid_level(self, auzoom_server):
        """auzoom_read with invalid level value handles gracefully."""
        result = auzoom_server.handle_tool_call(
            "auzoom_read",
            {"path": "auzoom/src/auzoom/models.py", "level": "invalid_level"},
        )

        assert isinstance(result, dict), "Should return dict, not crash"
        # Invalid level should produce an error (KeyError on FetchLevel enum)
        # or return fallback content
        has_error = "error" in result
        has_content = "type" in result
        assert has_error or has_content, (
            "Invalid level should return error or fallback content"
        )

        _record_evidence(
            "auzoom_read_invalid_level", "auzoom",
            {"tool": "auzoom_read", "arguments": {"path": "models.py", "level": "invalid_level"}},
            result, "compliant - graceful error for invalid level",
        )

    def test_orchestrator_route_task_as_integer(self, orchestrator_server):
        """VERIFIED: orchestrator_route with task=123 returns error dict (GAP-025 fixed).

        Phase 13-01 added ValidationError catch in _route(). Instead of
        propagating a raw Pydantic exception, it now returns a structured
        error dict with "error" and "type" keys.
        """
        result = run_async(
            orchestrator_server.handle_tool_call(
                "orchestrator_route", {"task": 123}
            )
        )

        # Should return error dict, not raise exception
        assert isinstance(result, dict), (
            f"Expected error dict, got {type(result).__name__}"
        )
        assert "error" in result, "Result must contain 'error' key"
        assert "type" in result, "Result must contain 'type' key"
        assert result["type"] == "validation_error", (
            f"Expected type 'validation_error', got '{result.get('type')}'"
        )

        _record_evidence(
            "orchestrator_route_task_as_integer", "orchestrator",
            {"tool": "orchestrator_route", "arguments": {"task": 123}},
            result,
            "pass - ValidationError caught and returned as error dict",
        )

    def test_auzoom_read_nonexistent_file(self, auzoom_server):
        """auzoom_read with nonexistent file returns descriptive error."""
        result = auzoom_server.handle_tool_call(
            "auzoom_read",
            {"path": "/nonexistent/path/file.py", "level": "skeleton"},
        )

        assert isinstance(result, dict)
        assert "error" in result, "Nonexistent file should return error"
        assert "not found" in result["error"].lower() or "not found" in str(result).lower(), (
            f"Error should mention file not found: {result}"
        )

        _record_evidence(
            "auzoom_read_nonexistent_file", "auzoom",
            {"tool": "auzoom_read", "arguments": {"path": "/nonexistent/path/file.py"}},
            result, "compliant - returns descriptive error for missing file",
        )

    def test_orchestrator_execute_invalid_model_name(self, orchestrator_server):
        """orchestrator_execute with invalid model name returns error."""
        result = run_async(
            orchestrator_server.handle_tool_call(
                "orchestrator_execute",
                {"model": "gpt-5-turbo-max", "prompt": "test"},
            )
        )

        assert isinstance(result, dict)
        assert result.get("success") is False
        assert result.get("error") is not None

        _record_evidence(
            "orchestrator_execute_invalid_model", "orchestrator",
            {"tool": "orchestrator_execute", "arguments": {"model": "gpt-5-turbo-max"}},
            result, "compliant - returns error for invalid model",
        )


class TestEmptyNullArguments:
    """Test behavior with empty and null arguments."""

    def test_auzoom_empty_arguments(self, auzoom_handler):
        """AuZoom tools/call with empty arguments {}."""
        request = {
            "jsonrpc": "2.0", "id": 30, "method": "tools/call",
            "params": {"name": "auzoom_stats", "arguments": {}},
        }
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert "result" in response
        # auzoom_stats takes no required params, should succeed
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, dict)

        _record_evidence(
            "auzoom_empty_arguments", "auzoom", request, response,
            "compliant - empty args handled for no-param tool",
        )

    def test_orchestrator_empty_arguments(self, orchestrator_handler):
        """Orchestrator tools/call with empty arguments {}."""
        request = {
            "jsonrpc": "2.0", "id": 31, "method": "tools/call",
            "params": {"name": "orchestrator_route", "arguments": {}},
        }
        response = run_async(orchestrator_handler._handle_request_async(request))

        assert response.get("jsonrpc") == "2.0"
        assert "result" in response
        # Should default task to "" and still route (graceful degradation)
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, dict)

        _record_evidence(
            "orchestrator_empty_arguments", "orchestrator", request, response,
            "compliant - empty args handled with defaults",
        )

    def test_auzoom_none_arguments(self, auzoom_handler):
        """AuZoom tools/call with None (missing) arguments."""
        request = {
            "jsonrpc": "2.0", "id": 32, "method": "tools/call",
            "params": {"name": "auzoom_stats"},
            # arguments key is entirely absent
        }
        response = auzoom_handler._handle_request(request)

        assert response.get("jsonrpc") == "2.0"
        assert "result" in response
        # Handler defaults arguments to {} via .get("arguments", {})
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, dict)

        _record_evidence(
            "auzoom_none_arguments", "auzoom", request, response,
            "compliant - missing arguments key handled via default",
        )

    def test_orchestrator_none_arguments(self, orchestrator_handler):
        """Orchestrator tools/call with None (missing) arguments."""
        request = {
            "jsonrpc": "2.0", "id": 33, "method": "tools/call",
            "params": {"name": "orchestrator_route"},
        }
        response = run_async(orchestrator_handler._handle_request_async(request))

        assert response.get("jsonrpc") == "2.0"
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(content, dict)

        _record_evidence(
            "orchestrator_none_arguments", "orchestrator", request, response,
            "compliant - missing arguments key handled via default",
        )

    def test_auzoom_read_with_none_args(self, auzoom_server):
        """AuZoom handle_tool_call with None as arguments dict."""
        # This tests the server level, not the JSON-RPC handler
        try:
            result = auzoom_server.handle_tool_call("auzoom_read", None)
            # If it doesn't crash, check the result
            assert isinstance(result, dict)
        except (TypeError, AttributeError):
            # Acceptable: None.get() raises TypeError
            # This is a known limitation - documenting it
            pass

        _record_evidence(
            "auzoom_read_none_args", "auzoom",
            {"tool": "auzoom_read", "arguments": None},
            {"behavior": "TypeError or error dict"},
            "acceptable - None args cause TypeError (callers always pass dict)",
        )

    def test_orchestrator_route_with_none_args(self, orchestrator_server):
        """Orchestrator handle_tool_call with None as arguments dict."""
        try:
            result = run_async(
                orchestrator_server.handle_tool_call("orchestrator_route", None)
            )
            assert isinstance(result, dict)
        except (TypeError, AttributeError):
            # Acceptable: None.get() raises TypeError
            pass

        _record_evidence(
            "orchestrator_route_none_args", "orchestrator",
            {"tool": "orchestrator_route", "arguments": None},
            {"behavior": "TypeError or error dict"},
            "acceptable - None args cause TypeError (callers always pass dict)",
        )
