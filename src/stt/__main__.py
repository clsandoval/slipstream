"""STT Service entry point.

Run with: python -m src.stt
"""

import asyncio
import logging
import signal
import sys

from .stt_service import STTService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the STT service."""
    logger.info("Starting Slipstream STT Service")

    service = STTService()

    # Handle shutdown signals
    def shutdown(sig: int, frame) -> None:
        logger.info(f"Received signal {sig}, shutting down...")
        service.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        logger.info("STT Service stopped")


if __name__ == "__main__":
    main()
