"""Tests for WebSocket server."""

import asyncio
import json

import pytest
import pytest_asyncio
import websockets

from src.mcp.state_store import StateStore
from src.mcp.websocket_server import WebSocketServer


@pytest.fixture
def state_store() -> StateStore:
    """Fresh StateStore instance."""
    return StateStore()


@pytest_asyncio.fixture
async def server(state_store: StateStore):
    """Running WebSocket server for tests."""
    ws_server = WebSocketServer(state_store, port=0)  # Random port
    await ws_server.start()
    yield ws_server
    await ws_server.stop()


class TestWebSocketServer:
    """Tests for WebSocketServer class."""

    @pytest.mark.asyncio
    async def test_server_starts(self, state_store: StateStore) -> None:
        """Server starts on specified port."""
        ws_server = WebSocketServer(state_store, port=0)
        await ws_server.start()

        assert ws_server.port > 0
        assert ws_server._server is not None

        await ws_server.stop()

    @pytest.mark.asyncio
    async def test_client_connects(self, server: WebSocketServer) -> None:
        """Client can connect to server."""
        async with websockets.connect(f"ws://localhost:{server.port}"):
            # Connection succeeded
            await asyncio.sleep(0.1)
            assert len(server._clients) == 1

    @pytest.mark.asyncio
    async def test_client_receives_updates(
        self, server: WebSocketServer, state_store: StateStore
    ) -> None:
        """Connected client receives state updates."""
        state_store.start_session()
        state_store.update_strokes(count=42, rate=52.0)

        async with websockets.connect(f"ws://localhost:{server.port}") as ws:
            # Wait for an update
            message = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(message)

            assert data["type"] == "state_update"
            assert data["session"]["active"] is True
            assert data["session"]["stroke_count"] == 42

    @pytest.mark.asyncio
    async def test_multiple_clients(self, server: WebSocketServer) -> None:
        """Multiple clients can connect and receive updates."""
        clients = []
        for _ in range(3):
            ws = await websockets.connect(f"ws://localhost:{server.port}")
            clients.append(ws)

        await asyncio.sleep(0.1)
        assert len(server._clients) == 3

        for ws in clients:
            await ws.close()

    @pytest.mark.asyncio
    async def test_client_disconnect(self, server: WebSocketServer) -> None:
        """Client disconnect handled gracefully."""
        ws = await websockets.connect(f"ws://localhost:{server.port}")
        await asyncio.sleep(0.1)
        assert len(server._clients) == 1

        await ws.close()
        await asyncio.sleep(0.2)
        assert len(server._clients) == 0

    @pytest.mark.asyncio
    async def test_server_shutdown(self, state_store: StateStore) -> None:
        """Server shuts down cleanly."""
        ws_server = WebSocketServer(state_store, port=0)
        await ws_server.start()
        port = ws_server.port

        ws = await websockets.connect(f"ws://localhost:{port}")

        await ws_server.stop()

        # Server should be stopped
        assert ws_server._server is None

        await ws.close()

    @pytest.mark.asyncio
    async def test_push_interval(self, state_store: StateStore) -> None:
        """Server pushes at configured interval."""
        ws_server = WebSocketServer(state_store, port=0, push_interval=0.1)
        await ws_server.start()

        async with websockets.connect(f"ws://localhost:{ws_server.port}") as ws:
            messages = []
            start = asyncio.get_event_loop().time()

            # Collect messages for ~0.5 seconds
            try:
                while asyncio.get_event_loop().time() - start < 0.5:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.2)
                    messages.append(msg)
            except asyncio.TimeoutError:
                pass

            # With 0.1s interval over 0.5s, expect ~4-5 messages
            assert len(messages) >= 3

        await ws_server.stop()

    @pytest.mark.asyncio
    async def test_broadcast_message(self, server: WebSocketServer) -> None:
        """Broadcast custom message to all clients."""
        async with websockets.connect(f"ws://localhost:{server.port}") as ws:
            # Skip initial state update
            await asyncio.wait_for(ws.recv(), timeout=1.0)

            # Broadcast custom message
            await server.broadcast({"custom": "message", "value": 123})

            message = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(message)

            assert data["custom"] == "message"
            assert data["value"] == 123
