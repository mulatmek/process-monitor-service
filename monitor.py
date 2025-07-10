import json
import psutil
import threading
import time
from typing import Dict, List

class ProcessMonitor:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.sampling_interval = self.config.get("sampling_interval", 5)
        self.processes_to_monitor = self.config.get("processes", [])
        self.status = {}
        self.running = False
        self.lock = threading.Lock()


    def load_config(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)

    def sample(self):
        while self.running:
            active_processes = [p.name().lower() for p in psutil.process_iter()]
            with self.lock:
                for proc in self.processes_to_monitor:
                    self.status[proc] = proc.lower() in active_processes
            time.sleep(self.sampling_interval)

    def get_status(self) -> Dict[str, bool]:
        with self.lock:
            return self.status.copy()

    def dashboard(self):
        while self.running:
            print("\n===== Process Monitor Dashboard =====")
            for proc, is_running in self.get_status().items():
                status = "RUNNING" if is_running else "NOT RUNNING"
                print(f"{proc}: {status}")
            print("=====================================")
            time.sleep(self.sampling_interval)

    def start(self, console_dashboard=False):
        self.running = True
        threading.Thread(target=self.sample, daemon=True).start()

        if console_dashboard:
            threading.Thread(target=self.dashboard, daemon=True).start()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    monitor = ProcessMonitor("config.json")
    try:
        monitor.start(console_dashboard=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()