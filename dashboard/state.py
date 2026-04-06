import threading

class AppState:
    """
    Mantém o estado global da medição atual para permitir
    integração segura entre a thread síncrona do Dash e 
    a thread assíncrona do Bleak/Bluetooth.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.ble_status = "Disconnected"  # "Disconnected", "Listening...", "Connected"
        self.live_weight = 0.0
        self.is_stable = False
        self.impedance = None
        self.scan_error = None
        self.metrics_calculated = None
        self.device_name = None
        
    def reset(self):
        with self._lock:
            self.live_weight = 0.0
            self.is_stable = False
            self.impedance = None
            self.scan_error = None
            self.metrics_calculated = None
            self.device_name = None
            self.ble_status = "Disconnected"
        
    def update_weight(self, weight, stable=False):
        with self._lock:
            self.live_weight = weight
            self.is_stable = stable
            
    def update_impedance(self, imp):
        with self._lock:
            self.impedance = imp
            
    def set_status(self, status, device_name=None):
        with self._lock:
            self.ble_status = status
            if device_name:
                self.device_name = device_name
            
    def set_scan_error(self, err):
        with self._lock:
            self.scan_error = err

    def set_metrics(self, metrics):
        with self._lock:
            self.metrics_calculated = metrics
            
    def get_snapshot(self):
        with self._lock:
            return {
                "status": self.ble_status,
                "weight": self.live_weight,
                "is_stable": self.is_stable,
                "impedance": self.impedance,
                "scan_error": self.scan_error,
                "device_name": self.device_name,
                "metrics": self.metrics_calculated
            }

app_state = AppState()
