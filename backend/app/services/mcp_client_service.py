import asyncio
import json

from mcp import Client

from backend.app.mcp_server import mcp


class MCPClientService:

    async def _get_employee_async(
        self,
        name: str,
    ) -> dict:

        async with Client(mcp) as client:

            result = await client.call_tool(
                "get_employee",
                {
                    "name": name
                },
            )

            if result.is_error:
                return {
                    "found": False,
                    "error": "MCP tool execution failed.",
                }

            if not result.content:
                return {
                    "found": False,
                    "error": "MCP returned no content.",
                }

            content = result.content[0]

            if not hasattr(content, "text"):
                return {
                    "found": False,
                    "error": "Unexpected MCP response format.",
                }

            return json.loads(content.text)

    def get_employee(
        self,
        name: str,
    ) -> dict:

        return asyncio.run(
            self._get_employee_async(name)
        )