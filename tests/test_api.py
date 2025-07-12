from server import monitor

def test_add_process_api(client):
    response = client.post("/add_process", json={"name": "pytest"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "added" in response.json()["message"].lower(), f"Expected 'added' in response message, got {response.json()['message']}"
    assert "pytest" in monitor.processes_to_monitor, "'pytest' should be in processes_to_monitor after adding"

def test_add_existing_process_api(client):
    with monitor.lock:
        monitor.processes_to_monitor.append("pytest")

    response = client.post("/add_process", json={"name": "pytest"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "already" in response.json()["message"].lower(), f"Expected 'already' in response message, got {response.json()['message']}"

def test_delete_process_api(client):
    with monitor.lock:
        monitor.processes_to_monitor.append("pytest")
        monitor.status["pytest"] = {}

    response = client.request("DELETE", "/delete_process", json={"name": "pytest"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "removed" in response.json()["message"].lower(), f"Expected 'removed' in response message, got {response.json()['message']}"
    assert "pytest" not in monitor.processes_to_monitor, "'pytest' should not be in processes_to_monitor after deletion"

def test_delete_non_existent_process_api(client):
    response = client.request("DELETE", "/delete_process", json={"name": "nonexistent"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "not being monitored" in response.json()["message"].lower(), \
        f"Expected 'not being monitored' in response message, got {response.json()['message']}"

def test_dashboard_rendering(client):
    response = client.get("/dashboard")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Process Monitor Dashboard" in response.text, "Expected 'Process Monitor Dashboard' in response content"
