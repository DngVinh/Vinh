from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("campus247_worker")


@dataclass
class WorkerConfig:
    """Worker runtime configuration."""
    service_name: str = "campus247-worker"
    version: str = "0.1.0"
    poll_interval_seconds: float = 1.0
    running: bool = field(default=False, init=False)


class WorkerProcess:
    """Worker process managing outbox polling, event dispatching, and ingestion."""

    def __init__(self, config: WorkerConfig | None = None) -> None:
        self.config = config or WorkerConfig()

    def start(self) -> None:
        """Start worker loop."""
        self.config.running = True
        logger.info("Worker process %s (v%s) started", self.config.service_name, self.config.version)

    def stop(self) -> None:
        """Stop worker loop safely."""
        self.config.running = False
        logger.info("Worker process %s stopped", self.config.service_name)


def create_worker() -> WorkerProcess:
    """Factory creating worker process instance."""
    return WorkerProcess()


def main() -> None:
    """Worker CLI entrypoint."""
    worker = create_worker()
    worker.start()
