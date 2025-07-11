from server import monitor

def test_add_process_api(client):
    response = client.post("/add_process", json={"name": "pytest"})
    assert response.status_code == 200
    assert "added" in response.json()["message"].lower()
    assert "pytest" in monitor.processes_to_monitor

def test_add_existing_process_api(client):
    with monitor.lock:
        monitor.processes_to_monitor.append("pytest")

    response = client.post("/add_process", json={"name": "pytest"})
    assert response.status_code == 200
    assert "already" in response.json()["message"].lower()

def test_delete_process_api(client):
    with monitor.lock:
        monitor.processes_to_monitor.append("pytest")
        monitor.status["pytest"] = {}

    response = client.request("DELETE", "/delete_process", json={"name": "pytest"})
    assert response.status_code == 200
    assert "removed" in response.json()["message"].lower()
    assert "pytest" not in monitor.processes_to_monitor

def test_delete_non_existent_process_api(client):
    response = client.request("DELETE", "/delete_process", json={"name": "nonexistent"})
    assert response.status_code == 200
    assert "not being monitored" in response.json()["message"].lower()


def test_dashboard_rendering(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Process Monitor Dashboard" in response.text
