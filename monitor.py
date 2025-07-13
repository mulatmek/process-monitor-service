import json
import psutil
import threading
import time
from typing import Dict, Any
from logger import logger

class ProcessMonitor:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.sampling_interval = self.config.get("sampling_interval", 5)
        self.processes_to_monitor = [p.lower() for p in self.config.get("processes", [])]
        self.status: Dict[str, Any] = {}
        self.running = False
        self.lock = threading.Lock()
        logger.info(f"Initialized ProcessMonitor with sampling_interval={self.sampling_interval} "
                     f"and processes_to_monitor={self.processes_to_monitor}")

    def load_config(self, path: str) -> Dict:
        logger.info(f"Loading configuration from {path}")
        with open(path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded config: {config}")
        return config

    def sample(self):
        while self.running:
            new_status = {}

            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'num_threads', 'create_time']):
                try:
                    name = proc.info['name'].lower() if proc.info['name'] else ''
                    if name in self.processes_to_monitor:
                        mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                        lifetime = time.time() - proc.info['create_time']
                        cpu = proc.cpu_percent(interval=0.1)
                        new_status[name] = {
                            'running': True,
                            'cpu_percent': cpu,
                            'memory_mb': mem_mb,
                            'num_threads': proc.info['num_threads'],
                            'lifetime_sec': int(lifetime)
                        }
                        logger.debug(f"Process '{name}' is running: CPU={cpu:.2f}%, MEM={mem_mb:.2f}MB, "
                                     f"Threads={proc.info['num_threads']}, Lifetime={int(lifetime)}s")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.debug(f"Skipping process: {e}")
                    continue

            for proc in self.processes_to_monitor:
                if proc not in new_status:
                    new_status[proc] = {
                        'running': False,
                        'cpu_percent': 0,
                        'memory_mb': 0,
                        'num_threads': 0,
                        'lifetime_sec': 0
                    }
                    logger.info(f"Process '{proc}' not found — marked as not running.")

            with self.lock:
                self.status = new_status

            time.sleep(self.sampling_interval)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return self.status.copy()

    def start(self):
        self.running = True
        logger.info("Starting process monitor...")
        threading.Thread(target=self.sample, daemon=True).start()

    def stop(self):
        logger.info("Stopping process monitor...")
        self.running = False
