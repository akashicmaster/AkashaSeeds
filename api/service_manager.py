"""
Akasha Service Manager (Somatic Organ Control).
Manages external sensory organs and web services (e.g., Cosmos Visualizer, Note UI)
directly from the Cognitive Shell or API Gateway.

[PROCESS ORCHESTRATION]
Provides resilient, OS-independent process creation, graceful termination, 
and real-time health monitoring of spawned service instances.

[RESOURCE MANAGEMENT]
Ensures proper log file handler delegation and strictly prevents zombie 
processes when shutting down or detaching services.
"""

import os
import sys
import subprocess
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Harmonia.ServiceManager")

class ServiceManager:
    """
    Singleton Orchestrator for Akasha's background web services.
    Manages the lifecycle of ASGI/WSGI endpoints spun up as subprocesses.
    """
    _instance: Optional['ServiceManager'] = None
    
    @classmethod
    def get_instance(cls) -> 'ServiceManager':
        if cls._instance is None:
            cls._instance = ServiceManager()
        return cls._instance

    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        self._thread_services: Dict[str, Dict[str, Any]] = {}
        self._blueprints: Dict[str, Any] = {}   # name → spawn callable for restart/start
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.log_dir = os.path.join(self.root_dir, "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def start_service(self, engine: str, service_name: str, host: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Spawns a new background service process, binding it to the specified engine (e.g., uvicorn).
        Pipes all standard output/errors safely to a dedicated log file.
        """
        # 1. Prevent duplicate invocations
        if service_name in self.services:
            p = self.services[service_name]['process']
            if p.poll() is None:
                return {"error": f"Service '{service_name}' is already active (PID: {p.pid})."}
        
        log_file_path = os.path.join(self.log_dir, f"{service_name}.log")
        
        # We must intentionally leave this file handle open for the child process to write to.
        # It will be closed by the OS when the child process terminates.
        try:
            out_file = open(log_file_path, "a")
        except IOError as e:
            return {"error": f"Failed to initialize log stream for '{service_name}': {e}"}
        
        # 2. Construct the subprocess command vector
        cmd = [sys.executable, "-m", f"services.{service_name}", "--engine", engine]
        if host:
            cmd.extend(["--host", str(host)])
        if port:
            cmd.extend(["--port", str(port)])
            
        # 3. Environment isolation (Ensure unbuffered output for real-time logging)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        # 4. Sprout the subprocess
        try:
            p = subprocess.Popen(
                cmd, 
                stdout=out_file, 
                stderr=subprocess.STDOUT, 
                cwd=self.root_dir, 
                env=env
            )
            
            # Register to internal registry
            self.services[service_name] = {
                "process": p,
                "engine": engine,
                "log_file": log_file_path,
                "out_fd": out_file,  # Keep reference to close it gracefully later
                "start_time": time.time()
            }
            logger.info(f"[ServiceManager] Service '{service_name}' sprouted on PID {p.pid}.")
            return {"status": "started", "pid": p.pid, "log": f"logs/{service_name}.log"}
            
        except Exception as e:
            # Clean up file descriptor on failure
            out_file.close()
            logger.error(f"[ServiceManager] Failed to sprout service '{service_name}': {e}")
            return {"error": f"Failed to start service: {str(e)}"}
            
    def register_process_service(self, name: str, proc: subprocess.Popen, out_fd,
                                 engine: str = "uvicorn", host: str = "", port: int = 0,
                                 spawn_fn=None) -> None:
        """Register an already-launched subprocess with lifecycle management.

        spawn_fn, if provided, is stored as a blueprint so the service can be
        restarted or started from scratch via svc restart / svc start.
        """
        self.services[name] = {
            "process":    proc,
            "engine":     engine,
            "log_file":   getattr(out_fd, "name", ""),
            "out_fd":     out_fd,
            "start_time": time.time(),
            "host":       host,
            "port":       port,
        }
        if spawn_fn is not None:
            self._blueprints[name] = spawn_fn
        logger.info(f"[ServiceManager] Registered process service '{name}' PID {proc.pid}.")

    def register_thread_service(self, name: str, instance, restart_fn, host: str = "0.0.0.0", port: int = 0):
        """Register a thread-based service (e.g. HTTP portal) for lifecycle management."""
        self._thread_services[name] = {
            "instance":    instance,
            "restart_fn":  restart_fn,
            "host":        host,
            "port":        port,
            "start_time":  time.time(),
        }

    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Stop and restart a service (works for both subprocess and thread-based services)."""
        if service_name in self._thread_services:
            info = self._thread_services[service_name]
            try:
                info["instance"].stop()
            except Exception:
                pass
            del self._thread_services[service_name]
            try:
                info["restart_fn"]()
                return {"status": "restarted", "service": service_name}
            except Exception as e:
                return {"error": f"Restart failed: {e}"}

        if service_name in self.services:
            engine = self.services[service_name].get("engine", "httpd")
            stop_result = self.stop_service(service_name)
            if "error" in stop_result:
                return stop_result
            time.sleep(0.5)
            if service_name in self._blueprints:
                result = self._blueprints[service_name]()
                if isinstance(result, dict) and "error" in result:
                    return result
                return {"status": "restarted", "service": service_name}
            return self.start_service(engine, service_name)

        return {"error": f"Service '{service_name}' not found."}

    def start_by_blueprint(self, service_name: str) -> Dict[str, Any]:
        """Start a service from its stored blueprint (for svc start after svc stop)."""
        if service_name in self.services:
            p = self.services[service_name].get("process")
            if p and p.poll() is None:
                return {"error": f"'{service_name}' is already running (PID {p.pid})."}
        if service_name not in self._blueprints:
            return {"error": f"No blueprint for '{service_name}'. Restart akasha.py to re-register."}
        result = self._blueprints[service_name]()
        if isinstance(result, dict) and "error" in result:
            return result
        return {"status": "started", "service": service_name}

    def stop_all(self) -> None:
        """Terminate all registered services. Intended for atexit cleanup."""
        for name in list(self.services.keys()):
            try:
                self.stop_service(name)
            except Exception:
                pass
        for name in list(self._thread_services.keys()):
            try:
                self.stop_service(name)
            except Exception:
                pass

    def stop_service(self, service_name: str) -> Dict[str, str]:
        """
        Gracefully terminates a running service. Uses SIGTERM followed by SIGKILL
        if the service resists shutdown, strictly preventing zombie processes.
        """
        if service_name in self._thread_services:
            info = self._thread_services[service_name]
            try:
                info["instance"].stop()
            except Exception:
                pass
            del self._thread_services[service_name]
            return {"status": "stopped", "service": service_name}

        if service_name not in self.services:
            return {"error": f"Service '{service_name}' is not currently running."}
            
        service_info = self.services[service_name]
        p: subprocess.Popen = service_info['process']
        out_fd = service_info.get('out_fd')
        
        if p.poll() is None:
            # Attempt graceful termination
            p.terminate()
            try:
                p.wait(timeout=5)  # Wait up to 5 seconds for clean shutdown
                status = "stopped"
            except subprocess.TimeoutExpired:
                # Force kill if process is hung
                p.kill()
                p.wait()
                status = "killed_forcefully"
                logger.warning(f"[ServiceManager] Service '{service_name}' resisted termination and was forcefully killed.")
        else:
            status = "already_dead"
            
        # Clean up file descriptors
        if out_fd and not out_fd.closed:
            try:
                out_fd.close()
            except Exception:
                pass
                
        # Remove from internal registry
        del self.services[service_name]
        logger.info(f"[ServiceManager] Service '{service_name}' has been {status}.")
        return {"status": status, "service": service_name}
            
    def list_services(self) -> List[Dict[str, Any]]:
        """
        Audits all registered services, checking their real-time health (alive/dead)
        and computing uptimes. Automatically scrubs dead services from the registry.
        """
        res = []
        dead_services = []
        
        for name, info in list(self.services.items()):
            p: subprocess.Popen = info['process']
            is_alive = p.poll() is None
            
            if is_alive:
                uptime = int(time.time() - info['start_time'])
                res.append({
                    "name":       name,
                    "engine":     info['engine'],
                    "pid":        p.pid,
                    "host":       info.get("host", ""),
                    "port":       info.get("port", 0),
                    "uptime_sec": uptime,
                    "status":     "Active",
                })
            else:
                res.append({
                    "name":   name,
                    "engine": info['engine'],
                    "pid":    p.pid,
                    "host":   info.get("host", ""),
                    "port":   info.get("port", 0),
                    "status": "Dead (Check logs)",
                })
                # Mark for cleanup
                dead_services.append(name)
                
        # Automatically scrub the registry of processes that died unexpectedly
        for dead_name in dead_services:
            out_fd = self.services[dead_name].get('out_fd')
            if out_fd and not out_fd.closed:
                try:
                    out_fd.close()
                except Exception:
                    pass
            del self.services[dead_name]

        # Thread-based services (e.g. HTTP portal running as a daemon thread)
        for name, info in list(self._thread_services.items()):
            instance = info["instance"]
            is_alive = getattr(instance, '_httpd', None) is not None
            uptime = int(time.time() - info["start_time"])
            res.append({
                "name":       name,
                "engine":     "thread",
                "host":       info.get("host", "?"),
                "port":       info.get("port", 0) or getattr(instance, "port", 0),
                "uptime_sec": uptime,
                "status":     "Active" if is_alive else "Dead",
                "pid":        None,
            })

        return res
