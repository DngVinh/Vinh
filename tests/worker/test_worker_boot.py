from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER_SRC = ROOT / "services" / "worker" / "src"

if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.main import create_worker, WorkerProcess, WorkerConfig


def test_worker_bootstrap_initialization():
    """Verify create_worker instantiates a valid WorkerProcess."""
    worker = create_worker()
    assert isinstance(worker, WorkerProcess)
    assert isinstance(worker.config, WorkerConfig)
    assert worker.config.service_name == "campus247-worker"
    assert worker.config.version == "0.1.0"
    assert worker.config.running is False

    worker.start()
    assert worker.config.running is True

    worker.stop()
    assert worker.config.running is False
