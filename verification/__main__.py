"""
CLI entry point for verification module.

Usage:
    # Run all built-in scenarios
    uv run python -m verification --scenarios all

    # Run specific scenario
    uv run python -m verification --scenario session_lifecycle

    # Run scenarios by tag
    uv run python -m verification --tag core

    # Start E2E harness for manual testing
    uv run python -m verification --e2e

    # List available scenarios
    uv run python -m verification --list
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from verification.scenarios import Scenario, ScenarioRunner
from verification.e2e_harness import E2EHarness, HarnessConfig


SCENARIOS_DIR = Path(__file__).parent / "scenarios" / "data"


def get_builtin_scenarios() -> list[tuple[str, Path]]:
    """Get list of built-in scenario files."""
    if not SCENARIOS_DIR.exists():
        return []
    return [(f.stem, f) for f in sorted(SCENARIOS_DIR.glob("*.yaml"))]


def load_scenario_by_name(name: str) -> Scenario | None:
    """Load a scenario by name."""
    path = SCENARIOS_DIR / f"{name}.yaml"
    if path.exists():
        return Scenario.from_yaml(path)
    return None


def load_all_scenarios() -> list[Scenario]:
    """Load all built-in scenarios."""
    scenarios = []
    for name, path in get_builtin_scenarios():
        scenarios.append(Scenario.from_yaml(path))
    return scenarios


def load_scenarios_by_tag(tag: str) -> list[Scenario]:
    """Load scenarios that have a specific tag."""
    scenarios = []
    for name, path in get_builtin_scenarios():
        scenario = Scenario.from_yaml(path)
        if tag in scenario.tags:
            scenarios.append(scenario)
    return scenarios


async def run_scenarios(scenarios: list[Scenario], verbose: bool = False) -> bool:
    """Run scenarios and return True if all passed."""
    config_dir = Path.home() / ".slipstream-test"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "sessions").mkdir(exist_ok=True)

    runner = ScenarioRunner(config_dir=config_dir)

    try:
        await runner.setup()
        results = await runner.run_all(scenarios)
    finally:
        await runner.teardown()

    # Print results
    all_passed = True
    for result in results:
        print(result.summary())
        print()
        if not result.success:
            all_passed = False

    # Summary
    passed = sum(1 for r in results if r.success)
    total = len(results)
    print(f"{'=' * 50}")
    print(f"Total: {passed}/{total} scenarios passed")

    return all_passed


async def run_e2e(args: argparse.Namespace) -> None:
    """Run E2E harness."""
    config = HarnessConfig(
        websocket_port=args.port or 8765,
        dashboard_port=args.dashboard_port or 5173,
        open_browser=not args.no_browser,
        config_dir=Path(args.config_dir) if args.config_dir else None,
    )

    harness = E2EHarness(config)

    try:
        await harness.start()
        await harness.run_interactive()
    finally:
        await harness.stop()


def list_scenarios() -> None:
    """List all available scenarios."""
    scenarios = get_builtin_scenarios()
    if not scenarios:
        print("No built-in scenarios found.")
        return

    print("Available scenarios:")
    print()
    for name, path in scenarios:
        scenario = Scenario.from_yaml(path)
        tags = ", ".join(scenario.tags) if scenario.tags else "none"
        print(f"  {name}")
        print(f"    {scenario.description}")
        print(f"    Tags: {tags}")
        print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verification suite for Slipstream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m verification --scenarios all       # Run all scenarios
  uv run python -m verification --scenario session_lifecycle
  uv run python -m verification --tag core            # Run scenarios tagged 'core'
  uv run python -m verification --e2e                 # Start E2E harness
  uv run python -m verification --list                # List scenarios
""",
    )

    # Scenario options
    parser.add_argument(
        "--scenarios",
        metavar="TYPE",
        help="Run scenarios (all)",
    )
    parser.add_argument(
        "--scenario",
        metavar="NAME",
        help="Run specific scenario by name",
    )
    parser.add_argument(
        "--tag",
        metavar="TAG",
        help="Run scenarios with specific tag",
    )

    # E2E options
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Start E2E harness for manual testing",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="WebSocket port (default: 8765)",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        help="Dashboard port (default: 5173)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser for E2E",
    )
    parser.add_argument(
        "--config-dir",
        help="Config directory",
    )

    # Other options
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_scenarios()
        return

    # Handle --e2e
    if args.e2e:
        asyncio.run(run_e2e(args))
        return

    # Handle scenarios
    scenarios: list[Scenario] = []

    if args.scenarios == "all":
        scenarios = load_all_scenarios()
    elif args.scenario:
        scenario = load_scenario_by_name(args.scenario)
        if scenario:
            scenarios = [scenario]
        else:
            print(f"Scenario not found: {args.scenario}")
            print("Use --list to see available scenarios")
            sys.exit(1)
    elif args.tag:
        scenarios = load_scenarios_by_tag(args.tag)
        if not scenarios:
            print(f"No scenarios found with tag: {args.tag}")
            sys.exit(1)
    else:
        parser.print_help()
        return

    if not scenarios:
        print("No scenarios to run.")
        return

    # Run scenarios
    success = asyncio.run(run_scenarios(scenarios, verbose=args.verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
