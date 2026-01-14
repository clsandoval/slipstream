"""
End-to-end testing harness for manual verification.

Usage:
    uv run python -m verification.e2e_harness [--port PORT] [--no-browser]

This starts the server with mocked vision and provides an interactive
console for controlling the mock state while you test the dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from src.mcp.server import SwimCoachServer
from verification.mocks import MockVisionStateStore


VERIFICATION_CHECKLIST = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         VERIFICATION CHECKLIST                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DASHBOARD DISPLAY (verify from 10ft)                                        ║
║  [ ] Large stroke rate number visible                                        ║
║  [ ] Stroke count displays correctly                                         ║
║  [ ] Session timer updates                                                   ║
║  [ ] Swimming/not-swimming indicator works                                   ║
║  [ ] Workout segment info displays (if workout active)                       ║
║                                                                              ║
║  SESSION FLOW                                                                ║
║  [ ] "Start session" creates new session                                     ║
║  [ ] Metrics update during session                                           ║
║  [ ] "End session" saves and shows summary                                   ║
║                                                                              ║
║  STROKE QUERIES (if testing voice)                                           ║
║  [ ] "What's my stroke rate?" returns current rate                           ║
║  [ ] "How many strokes?" returns stroke count                                ║
║  [ ] "How far have I swum?" returns distance estimate                        ║
║                                                                              ║
║  WORKOUT FLOW                                                                ║
║  [ ] Can create workout via voice/tool                                       ║
║  [ ] Segment transitions display correctly                                   ║
║  [ ] Progress indicator updates                                              ║
║  [ ] "Skip this segment" advances to next                                    ║
║  [ ] Workout completion shows summary                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

INTERACTIVE_HELP = """
Interactive Commands:
  swim [rate]     - Start swimming (default rate: 50 spm)
  stop            - Stop swimming
  strokes <n>     - Set stroke count to n
  rate <n>        - Set stroke rate to n
  session start   - Start a session
  session end     - End current session
  status          - Show current mock state
  checklist       - Show verification checklist
  help            - Show this help
  quit            - Exit harness
"""


@dataclass
class HarnessConfig:
    """Configuration for E2E harness."""

    websocket_port: int = 8765
    dashboard_port: int = 5173
    config_dir: Path = Path.home() / ".slipstream-test"
    open_browser: bool = True


class E2EHarness:
    """
    Interactive harness for end-to-end testing.

    Runs the server with mocked vision and provides
    console commands for controlling mock state.
    """

    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or HarnessConfig()
        self.mock_vision = MockVisionStateStore()
        self.server: SwimCoachServer | None = None
        self._running = False

    async def start(self) -> None:
        """Start the harness."""
        self.config.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config.config_dir / "sessions").mkdir(exist_ok=True)

        self.server = SwimCoachServer(
            websocket_port=self.config.websocket_port,
            config_dir=self.config.config_dir,
            vision_state_store=self.mock_vision,
        )
        await self.server.start()
        self._running = True

        print(
            f"\n✓ Server started on WebSocket port {self.server.websocket_server.port}"
        )
        print(
            f"✓ Dashboard should connect to ws://localhost:{self.server.websocket_server.port}"
        )

        if self.config.open_browser:
            url = f"http://localhost:{self.config.dashboard_port}"
            print(f"✓ Opening dashboard at {url}")
            webbrowser.open(url)

    async def stop(self) -> None:
        """Stop the harness."""
        self._running = False
        if self.server:
            await self.server.stop()
        print("\n✓ Harness stopped")

    def get_dashboard_url(self) -> str:
        """Get dashboard URL."""
        return f"http://localhost:{self.config.dashboard_port}"

    async def run_interactive(self) -> None:
        """Run interactive console."""
        print(INTERACTIVE_HELP)
        print("\nReady for commands. Type 'checklist' to see verification items.\n")

        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("harness> ")
                )
                await self._handle_command(line.strip())
            except (EOFError, KeyboardInterrupt):
                break

    async def _handle_command(self, line: str) -> None:
        """Handle a console command."""
        if not line:
            return

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd == "swim":
                rate = float(args[0]) if args else 50.0
                self.mock_vision.set_swimming(True)
                self.mock_vision.set_stroke_rate(rate)
                print(f"Swimming at {rate} spm")

            elif cmd == "stop":
                self.mock_vision.set_swimming(False)
                print("Stopped swimming")

            elif cmd == "strokes":
                count = int(args[0])
                self.mock_vision.set_stroke_count(count)
                print(f"Stroke count: {count}")

            elif cmd == "rate":
                rate = float(args[0])
                self.mock_vision.set_stroke_rate(rate)
                print(f"Stroke rate: {rate}")

            elif cmd == "session":
                if args and args[0] == "start":
                    result = self.server._start_session()
                    print(f"Session started: {result.get('session_id', 'unknown')}")
                elif args and args[0] == "end":
                    result = await self.server._end_session()
                    print(f"Session ended: {result}")
                else:
                    print("Usage: session start|end")

            elif cmd == "status":
                state = self.mock_vision.get_state()
                print(f"Swimming: {state.is_swimming}")
                print(f"Strokes: {state.stroke_count}")
                print(f"Rate: {state.stroke_rate}")

            elif cmd == "checklist":
                print(VERIFICATION_CHECKLIST)

            elif cmd == "help":
                print(INTERACTIVE_HELP)

            elif cmd in ("quit", "exit", "q"):
                self._running = False

            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")

        except Exception as e:
            print(f"Error: {e}")

    def print_checklist(self) -> None:
        """Print verification checklist."""
        print(VERIFICATION_CHECKLIST)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="E2E Testing Harness")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port")
    parser.add_argument(
        "--dashboard-port", type=int, default=5173, help="Dashboard port"
    )
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--config-dir", type=Path, help="Config directory")
    args = parser.parse_args()

    config = HarnessConfig(
        websocket_port=args.port,
        dashboard_port=args.dashboard_port,
        open_browser=not args.no_browser,
        config_dir=args.config_dir or Path.home() / ".slipstream-test",
    )

    harness = E2EHarness(config)

    try:
        await harness.start()
        await harness.run_interactive()
    finally:
        await harness.stop()


if __name__ == "__main__":
    asyncio.run(main())
