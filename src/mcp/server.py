"""FastMCP server for swim coaching."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.mcp.state_store import StateStore
from src.mcp.storage.config import Config
from src.mcp.storage.session_storage import SessionStorage
from src.mcp.tools.session_tools import create_session_tools
from src.mcp.websocket_server import WebSocketServer

logger = logging.getLogger(__name__)


def _default_config_dir() -> Path:
    """Get default config directory."""
    return Path.home() / ".slipstream"


class SwimCoachServer:
    """MCP server for swim coaching with WebSocket state push."""

    def __init__(
        self,
        websocket_port: int = 8765,
        push_interval: float = 0.25,
        config_dir: Path | None = None,
    ):
        """Initialize the swim coach server.

        Args:
            websocket_port: Port for WebSocket server (0 for random)
            push_interval: Interval for state push in seconds
            config_dir: Directory for config and session files
        """
        self.config_dir = config_dir or _default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "sessions").mkdir(exist_ok=True)

        # Load config
        self.config = Config.load(self.config_dir / "config.json")

        # Initialize components
        self.state_store = StateStore(dps_ratio=self.config.dps_ratio)
        self.session_storage = SessionStorage(
            sessions_dir=self.config_dir / "sessions"
        )
        self.websocket_server = WebSocketServer(
            self.state_store,
            port=websocket_port,
            push_interval=push_interval,
        )

        # Create MCP server
        self.mcp = FastMCP("swim-coach")

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register session management tools with MCP."""
        tools = create_session_tools(self.state_store, self.session_storage)

        for tool_fn in tools:
            # Store reference for direct calls
            setattr(self, f"_{tool_fn.__name__}", tool_fn)

            # Register with MCP
            self.mcp.tool()(tool_fn)

    async def start(self) -> None:
        """Start the WebSocket server."""
        await self.websocket_server.start()
        logger.info(
            f"SwimCoachServer started. WebSocket on port {self.websocket_server.port}"
        )

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        await self.websocket_server.stop()
        logger.info("SwimCoachServer stopped")

    def run(self) -> None:
        """Run the MCP server (main entry point for stdio transport)."""
        # Start WebSocket server in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.start())

            # Run MCP server (blocks until shutdown)
            self.mcp.run()
        finally:
            loop.run_until_complete(self.stop())
            loop.close()


def main() -> None:
    """Entry point for MCP server."""
    logging.basicConfig(level=logging.INFO)
    server = SwimCoachServer()
    server.run()


if __name__ == "__main__":
    main()
