from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MCP_CONFIG_PATH = PROJECT_ROOT / ".mcp.json"


async def call_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
    config = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))["mcpServers"]["campus-customs"]
    transport = StdioTransport(
        command=config["command"],
        args=config["args"],
        cwd=config["cwd"],
    )
    async with Client(transport) as client:
        result = await client.call_tool(tool_name, arguments or {})
        return result.structured_content