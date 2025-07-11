import json
import psutil
import threading
import time
from typing import Dict, List, Any

class ProcessMonitor:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.sampling_interval = self.config.get("sampling_interval", 5)
        self.processes_to_monitor = [p.lower() for p in self.config.get("processes", [])]
        self.status: Dict[str, Any] = {}
        self.running = False
        self.lock = threading.Lock()

    def load_config(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)

    def sample(self):
        while self.running:
            new_status = {}

            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'num_threads', 'create_time']):
                try:
                    name = proc.info['name'].lower() if proc.info['name'] else ''
                    if name in self.processes_to_monitor:
                        mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                        lifetime = time.time() - proc.info['create_time']
                        new_status[name] = {
                            'running': True,
                            'cpu_percent': proc.cpu_percent(interval=0.1),
                            'memory_mb': mem_mb,
                            'num_threads': proc.info['num_threads'],
                            'lifetime_sec': int(lifetime)
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Mark processes not found as not running
            for proc in self.processes_to_monitor:
                if proc not in new_status:
                    new_status[proc] = {
                        'running': False,
                        'cpu_percent': 0,
                        'memory_mb': 0,
                        'num_threads': 0,
                        'lifetime_sec': 0
                    }

            with self.lock:
                self.status = new_status

            time.sleep(self.sampling_interval)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return self.status.copy()

    def start(self):
        self.running = True
        threading.Thread(target=self.sample, daemon=True).start()


    def stop(self):
        self.running = False
