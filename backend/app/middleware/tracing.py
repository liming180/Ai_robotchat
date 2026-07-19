import time
from contextlib import contextmanager
from typing import Dict, Any
import threading

class PerformanceTracer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'metrics'):
            self.metrics = {}
            self._lock = threading.Lock()

    @contextmanager
    def measure(self, operation: str):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            with self._lock:
                if operation not in self.metrics:
                    self.metrics[operation] = []
                self.metrics[operation].append({
                    "duration": duration,
                    "timestamp": time.time()
                })

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics