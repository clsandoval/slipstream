"""WebSocket server for dashboard state push."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import websockets
from websockets.asyncio.server import Server, ServerConnection

from src.mcp.state_store import StateStore

logger = logging.getLogger(__name__)


@dataclass
class WebSocketServer:
    """Push state updates to dashboard via WebSocket."""

    state_store: StateStore
    port: int = 8765
    push_interval: float = 0.25
    _clients: set[ServerConnection] = field(default_factory=set, repr=False)
    _server: Server | None = field(default=None, repr=False)
    _push_task: asyncio.Task[None] | None = field(default=None, repr=False)
    _running: bool = field(default=False, repr=False)

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._running = True
        self._server = await websockets.serve(
            self._handle_client,
            "localhost",
            self.port,
        )

        # Get actual port if 0 was specified
        for socket in self._server.sockets:
            addr = socket.getsockname()
            if addr:
                self.port = addr[1]
                break

        self._push_task = asyncio.create_task(self._push_loop())
        logger.info(f"WebSocket server started on port {self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False

        if self._push_task:
            self._push_task.cancel()
            try:
                await self._push_task
            except asyncio.CancelledError:
                pass
            self._push_task = None

        # Close all client connections
        if self._clients:
            await asyncio.gather(
                *[client.close() for client in self._clients],
                return_exceptions=True,
            )
            self._clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("WebSocket server stopped")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients.

        Args:
            message: Dict to serialize and send as JSON
        """
        if not self._clients:
            return

        json_message = json.dumps(message)
        await asyncio.gather(
            *[client.send(json_message) for client in self._clients],
            return_exceptions=True,
        )

    async def _handle_client(self, websocket: ServerConnection) -> None:
        """Handle client connection.

        Args:
            websocket: Client WebSocket connection
        """
        self._clients.add(websocket)
        logger.debug(f"Client connected. Total clients: {len(self._clients)}")

        try:
            # Send initial state
            state_update = self.state_store.get_state_update()
            await websocket.send(state_update.to_json())

            # Keep connection open
            async for message in websocket:
                # Handle any client messages if needed
                logger.debug(f"Received from client: {message}")
        except websockets.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.debug(f"Client disconnected. Total clients: {len(self._clients)}")

    async def _push_loop(self) -> None:
        """Periodically push state updates to all clients."""
        while self._running:
            try:
                await asyncio.sleep(self.push_interval)

                if self._clients:
                    state_update = self.state_store.get_state_update()
                    await self.broadcast(json.loads(state_update.to_json()))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in push loop: {e}")
