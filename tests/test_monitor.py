import json
import os
from monitor import ProcessMonitor

def test_monitor_initialization():
    m = ProcessMonitor("config.json")
    assert isinstance(m.processes_to_monitor, list)
    assert isinstance(m.sampling_interval, int)

def test_add_and_remove_process_internal():
    m = ProcessMonitor("config.json")
    with m.lock:
        m.processes_to_monitor = []
        m.processes_to_monitor.append("testprocess")
        assert "testprocess" in m.processes_to_monitor

        m.processes_to_monitor.remove("testprocess")
        assert "testprocess" not in m.processes_to_monitor

def test_monitor_loads_processes_from_config():
    dummy_json = os.path.join("tests","json_files", "dummy.json")

    with open(dummy_json, 'r') as f:
        config = json.load(f)

    # Initialize monitor with the temporary config
    monitor = ProcessMonitor(dummy_json)

    # Check that all processes from config are loaded (case-insensitive)
    expected = [p.lower() for p in config["processes"]]
    assert sorted(monitor.processes_to_monitor) == sorted(expected)
