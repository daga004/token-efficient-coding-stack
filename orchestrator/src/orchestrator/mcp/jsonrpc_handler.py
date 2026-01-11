"""JSON-RPC 2.0 protocol handler for MCP communication."""

import asyncio
import json
import sys

from .tools_schema import get_tools_manifest


class JSONRPCHandler:
    """Handle JSON-RPC 2.0 protocol for MCP communication."""

    def __init__(self, server):
        """
        Initialize handler.

        Args:
            server: OrchestratorMCPServer instance
        """
        self.server = server

    def run(self):
        """Process JSON-RPC requests from stdin."""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())

                # Handle async tool calls
                if request.get("method") in ["tools/call"]:
                    response = asyncio.run(self._handle_request_async(request))
                else:
                    response = self._handle_request(request)

                self._send_response(response)

            except json.JSONDecodeError as e:
                self._send_parse_error(e)
            except Exception as e:
                self._send_internal_error(e, locals().get('request'))

    def _handle_request(self, request: dict) -> dict:
        """Route request to appropriate handler."""
        method = request.get("method")

        if method == "initialize":
            return self._handle_initialize(request)
        elif method == "tools/list":
            return self._handle_tools_list(request)
        else:
            return self._create_error_response(
                request.get("id"),
                -32601,
                f"Method not found: {method}"
            )

    async def _handle_request_async(self, request: dict) -> dict:
        """Route async request to appropriate handler."""
        method = request.get("method")

        if method == "tools/call":
            return await self._handle_tools_call(request)
        else:
            return self._create_error_response(
                request.get("id"),
                -32601,
                f"Method not found: {method}"
            )

    def _handle_initialize(self, request: dict) -> dict:
        """Handle initialize request - MCP protocol handshake."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "orchestrator",
                    "version": "0.1.0"
                }
            }
        }

    def _handle_tools_list(self, request: dict) -> dict:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": get_tools_manifest()
        }

    async def _handle_tools_call(self, request: dict) -> dict:
        """Handle tools/call request."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Call server's async tool handler
        result = await self.server.handle_tool_call(tool_name, arguments)

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        }

    def _send_response(self, response: dict):
        """Send JSON-RPC response to stdout."""
        print(json.dumps(response), flush=True)

    def _send_parse_error(self, error: Exception):
        """Send parse error response."""
        response = self._create_error_response(
            None, -32700, f"Parse error: {error}"
        )
        self._send_response(response)

    def _send_internal_error(self, error: Exception, request: dict = None):
        """Send internal error response."""
        request_id = request.get("id") if request else None
        response = self._create_error_response(
            request_id, -32603, f"Internal error: {error}"
        )
        self._send_response(response)

    def _create_error_response(
        self, request_id, code: int, message: str
    ) -> dict:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
