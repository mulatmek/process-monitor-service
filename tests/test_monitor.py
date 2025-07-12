import json
import os
from monitor import ProcessMonitor

def test_monitor_initialization():
    m = ProcessMonitor("config.json")
    assert isinstance(m.processes_to_monitor, list), f"Expected list for processes_to_monitor, got {type(m.processes_to_monitor)}"
    assert isinstance(m.sampling_interval, int), f"Expected int for sampling_interval, got {type(m.sampling_interval)}"

def test_add_and_remove_process_internal():
    m = ProcessMonitor("config.json")
    with m.lock:
        m.processes_to_monitor = []
        m.processes_to_monitor.append("testprocess")
        assert "testprocess" in m.processes_to_monitor, "'testprocess' should have been added to processes_to_monitor"

        m.processes_to_monitor.remove("testprocess")
        assert "testprocess" not in m.processes_to_monitor, "'testprocess' should have been removed from processes_to_monitor"

def test_monitor_loads_processes_from_config():
    dummy_json = os.path.join("tests", "json_files", "dummy.json")

    with open(dummy_json, 'r') as f:
        config = json.load(f)

    monitor = ProcessMonitor(dummy_json)

    expected_processes = [p.lower() for p in config["processes"]]
    expected_interval = config["sampling_interval"]

    assert sorted(monitor.processes_to_monitor) == sorted(expected_processes), \
        f"Expected processes: {sorted(expected_processes)}, but got: {sorted(monitor.processes_to_monitor)}"

    assert monitor.sampling_interval == expected_interval, \
        f"Expected sampling_interval: {expected_interval}, but got: {monitor.sampling_interval}"
