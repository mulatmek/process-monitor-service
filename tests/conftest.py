import pytest
from fastapi.testclient import TestClient
from monitor import ProcessMonitor
from server import app, monitor

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_monitor():
    # Automatically reset monitor before each
    with monitor.lock:
        monitor.processes_to_monitor.clear()
        monitor.status.clear()
