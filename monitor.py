import json
import psutil
import threading
import time
from typing import Dict, List, Any

class ProcessMonitor:
    """
    Monitors a list of system processes and tracks their runtime status, CPU, memory, and other stats.
    """
    def __init__(self, config_path: str):
        """
        Initialize the monitor with configuration from a JSON file.
        """
        self.config = self.load_config(config_path)
        self.sampling_interval = self.config.get("sampling_interval", 5)
        self.processes_to_monitor = [p.lower() for p in self.config.get("processes", [])]
        self.status: Dict[str, Any] = {}  # Current status of monitored processes
        self.running = False  # Control flag for the monitoring loop
        self.lock = threading.Lock()  # Ensure thread-safe access to shared data

    def load_config(self, path: str) -> Dict:
        """
        Load configuration from a JSON file.
        """
        with open(path, 'r') as f:
            return json.load(f)

    def sample(self):
        """
        Sampling loop that periodically collects status for the monitored processes.
        """
        while self.running:
            new_status = {}

            # Iterate over all running processes and gather info
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'num_threads', 'create_time']):
                try:
                    name = proc.info['name'].lower() if proc.info['name'] else ''
                    if name in self.processes_to_monitor:
                        # Collect metrics for the monitored process
                        mem_mb = proc.info['memory_info'].rss / (1024 * 1024)  # Convert memory to MB
                        lifetime = time.time() - proc.info['create_time']
                        new_status[name] = {
                            'running': True,
                            'cpu_percent': proc.cpu_percent(interval=0.1),
                            'memory_mb': mem_mb,
                            'num_threads': proc.info['num_threads'],
                            'lifetime_sec': int(lifetime)
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Skip processes that disappear or can't be accessed
                    continue

            # Mark monitored processes not found in this iteration as "not running"
            for proc in self.processes_to_monitor:
                if proc not in new_status:
                    new_status[proc] = {
                        'running': False,
                        'cpu_percent': 0,
                        'memory_mb': 0,
                        'num_threads': 0,
                        'lifetime_sec': 0
                    }

            # Update shared status dictionary safely
            with self.lock:
                self.status = new_status

            # Wait before next sampling
            time.sleep(self.sampling_interval)

    def get_status(self) -> Dict[str, Any]:
        """
        Get a snapshot of the current monitored processes status.
        """
        with self.lock:
            return self.status.copy()  # Return a copy to prevent external modification

    def start(self):
        """
        Start the monitoring in a background thread.
        """
        self.running = True
        # Launch sampling loop in a daemon thread so it exits with the main program
        threading.Thread(target=self.sample, daemon=True).start()

    def stop(self):
        """
        Stop the monitoring loop.
        """
        self.running = False  # Set flag to exit loop in sample()
