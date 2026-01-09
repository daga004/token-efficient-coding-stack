"""JSON-RPC 2.0 protocol handler for MCP server."""

import json
import sys


class JSONRPCHandler:
    """Handle JSON-RPC 2.0 protocol for MCP communication."""

    def __init__(self, server):
        self.server = server

    def run(self):
        """Process JSON-RPC requests from stdin."""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self._handle_request(request)
                self._send_response(response)

            except json.JSONDecodeError as e:
                self._send_parse_error(e)
            except Exception as e:
                self._send_internal_error(e, locals().get('request'))

    def _handle_request(self, request: dict) -> dict:
        """Route request to appropriate handler."""
        method = request.get("method")

        if method == "tools/list":
            return self._handle_tools_list(request)
        elif method == "tools/call":
            return self._handle_tools_call(request)
        else:
            return self._create_error_response(
                request.get("id"),
                -32601,
                f"Method not found: {method}"
            )

    def _handle_tools_list(self, request: dict) -> dict:
        """Handle tools/list request."""
        from .tools_schema import get_tools_manifest
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": get_tools_manifest()
        }

    def _handle_tools_call(self, request: dict) -> dict:
        """Handle tools/call request."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        result = self.server.handle_tool_call(tool_name, arguments)

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
        response = self._create_error_response(None, -32700, f"Parse error: {error}")
        self._send_response(response)

    def _send_internal_error(self, error: Exception, request: dict = None):
        """Send internal error response."""
        request_id = request.get("id") if request else None
        response = self._create_error_response(request_id, -32603, f"Internal error: {error}")
        self._send_response(response)

    def _create_error_response(self, request_id, code: int, message: str) -> dict:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
