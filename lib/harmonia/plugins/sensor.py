"""
Sensory Receptor Plugins.
Provides background daemon sensors (e.g., biological clocks, file watchers) 
for the Harmonia platform. These sensors trigger higher-level cognitive 
engines like Contexa to initiate processing Workspaces autonomously.
"""
import time
import threading
import os
from typing import Callable, Dict, Any, Optional

class HarmoniaSensor:
    """
    Base class for sensory receptors in the Harmonia layer.
    Monitors environmental or internal events asynchronously and triggers 
    higher-level cognitive layers (e.g., Contexa) upon specific conditions.
    Each sensor runs on a dedicated daemon thread to avoid blocking the gateway.
    """
    def __init__(self, sensor_id: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Initializes the sensor.
        
        Args:
            sensor_id: A unique identifier for this sensor instance.
            callback: The function to call when an event is detected 
                      (usually ContexaEngine.on_trigger).
        """
        self.sensor_id = sensor_id
        self.callback = callback
        self.active = False
        self._thread: Optional[threading.Thread] = None

    def start(self, **kwargs):
        """Activates the sensory receptor on a dedicated daemon thread."""
        if self.active: 
            return
            
        self.active = True
        self._thread = threading.Thread(
            target=self._watch_loop, 
            kwargs=kwargs, 
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Gracefully deactivates the sensory receptor and joins the thread."""
        self.active = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _watch_loop(self, **kwargs):
        """
        The continuous monitoring loop. 
        Must be implemented by specific subclasses (e.g., InternalTimer).
        """
        pass

class InternalTimer(HarmoniaSensor):
    """
    An internal biological clock for the Akasha system.
    Pulsates within Akasha's own thread space, enabling autonomous 
    self-reflection, dreams, and maintenance without external OS schedulers.
    """
    def _watch_loop(self, interval_sec: int = 60):
        """
        Periodically triggers the callback based on the defined interval.
        Includes a granular sleep loop to ensure rapid response to 'stop' signals.
        """
        print(f"\n[Sensor] Heartbeat initialized: {self.sensor_id} (Pulse: {interval_sec}s)")
        
        while self.active:
            # Granular sleep (1 second intervals) allows for immediate graceful shutdown
            for _ in range(interval_sec):
                if not self.active: 
                    break
                time.sleep(1)
            
            if self.active:
                # Trigger the cognitive loop via the callback
                # This may initiate a new Harmonia Workspace / Transaction
                self.callback({
                    "trigger": "heartbeat", 
                    "sensor": self.sensor_id, 
                    "timestamp": time.time(),
                    "source": "internal_clock"
                })

class FileSystemWatcher(HarmoniaSensor):
    """
    Monitors a specified directory (e.g., 'assets' or 'import') for new data.
    Enables Akasha to 'notice' and absorb new historical records automatically
    as soon as they are placed in the physical environment.
    """
    def _watch_loop(self, watch_path: str = "data/import", interval_sec: int = 5):
        """
        Periodically scans the target directory for new files.
        """
        print(f"[Sensor] Watching filesystem: {watch_path}")
        
        # Initialize the known state. Handle cases where the directory doesn't exist yet.
        known_files = set(os.listdir(watch_path)) if os.path.exists(watch_path) else set()
        
        while self.active:
            if os.path.exists(watch_path):
                current_files = set(os.listdir(watch_path))
                new_files = current_files - known_files
                
                if new_files:
                    # Notify the cognitive layer of the new environmental stimuli
                    self.callback({
                        "trigger": "io_event",
                        "sensor": self.sensor_id,
                        "files": list(new_files),
                        "timestamp": time.time()
                    })
                    known_files = current_files
            
            time.sleep(interval_sec)
