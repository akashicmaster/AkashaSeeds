"""
Harmonia Logger & Telemetry Hub (Pro Edition).

Handles physical file logging for system diagnostics and provides
hooks for 'Semantic Logging' (storing system events as Akasha Atoms).

[SEMANTIC OBSERVABILITY]
Errors and critical events are not just written to dead files; they can be 
"atomized" into the Cortex memory mesh. This allows the Jataka engine to 
"dream" about past operational history, identifying systemic failures or 
recurring anomalies autonomously.

[CGI-SAFE CONSOLE & IAM BOUNDARIES]
Console outputs strictly route to stderr to prevent JSON-RPC HTTP corruption.
Atomized logs are securely bound to 'scope:sys:admin' to prevent unauthorized 
clients from reading internal system traces.
"""

import logging
import os
import sys
from typing import Optional, Any

# Optional import for immersive terminal output
try:
    from lib.akasha.symbiosis import Colors
except ImportError:
    class Colors:
        CYAN = GREEN = WARNING = FAIL = ENDC = DIM = BOLD = ''

class ColorFormatter(logging.Formatter):
    """Dynamically colorizes console output based on the log level severity."""
    FORMATS = {
        logging.DEBUG: f"{Colors.DIM}%(asctime)s [DEBUG] %(name)s: %(message)s{Colors.ENDC}",
        logging.INFO: f"{Colors.CYAN}%(asctime)s [INFO] %(name)s: %(message)s{Colors.ENDC}",
        logging.WARNING: f"{Colors.WARNING}%(asctime)s [WARN] %(name)s: %(message)s{Colors.ENDC}",
        logging.ERROR: f"{Colors.FAIL}%(asctime)s [ERROR] %(name)s: %(message)s{Colors.ENDC}",
        logging.CRITICAL: f"{Colors.FAIL}{Colors.BOLD}%(asctime)s [CRIT] %(name)s: %(message)s{Colors.ENDC}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_harmonia_logger(cell_id: str, cell_root: str, master_log_path: str) -> logging.Logger:
    """
    Initializes and returns a multi-channel logger for a specific Cell.
    Acts as the physical 'Job Ledger' for Harmonia, recording operational history
    for system diagnostics and catastrophic recovery.
    
    Args:
        cell_id: The unique identifier for the cell/user.
        cell_root: The root directory for the cell's storage.
        master_log_path: The file path for the system-wide master log.
    """
    logger = logging.getLogger(f"Harmonia.{cell_id}")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to prevent duplicate entries during re-initialization
    if logger.hasHandlers():
        logger.handlers.clear()

    # Standardized telemetry format for physical file parsing and aggregation
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # 1. Master System Log (Physical Survival Record)
    try:
        os.makedirs(os.path.dirname(master_log_path), exist_ok=True)
        master_handler = logging.FileHandler(master_log_path, encoding='utf-8')
        master_handler.setFormatter(file_formatter)
        master_handler.setLevel(logging.INFO)
        logger.addHandler(master_handler)
    except Exception as e:
        print(f"{Colors.WARNING}[Warning] Failed to mount Master Log: {e}{Colors.ENDC}", file=sys.stderr)

    # 2. Cell Activity Log (Physical Audit Record)
    cell_log_path = os.path.join(cell_root, "logs", "activity.log")
    try:
        os.makedirs(os.path.dirname(cell_log_path), exist_ok=True)
        cell_handler = logging.FileHandler(cell_log_path, encoding='utf-8')
        cell_handler.setFormatter(file_formatter)
        cell_handler.setLevel(logging.DEBUG)
        logger.addHandler(cell_handler)
    except Exception as e:
        print(f"{Colors.WARNING}[Warning] Failed to mount Cell Log for {cell_id}: {e}{Colors.ENDC}", file=sys.stderr)

    # 3. Console Output (Real-time Observability - CGI Safe)
    # Strictly bound to sys.stderr to protect stdout data streams (e.g., CGI JSON-RPC)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(ColorFormatter())
    
    # Hide DEBUG from console by default to keep the terminal clean, 
    # but write it to the physical file handlers above.
    console_handler.setLevel(logging.INFO) 
    logger.addHandler(console_handler)

    return logger

class SemanticLogWrapper:
    """
    [PRO EDITION UPGRADE] 
    A wrapper that bridges physical logging and Akasha Memory (Atoms).
    Allows critical log events to be stored persistently in the Cortex as 
    Atoms with 'sys:log_event' metadata. 
    
    Safeguards: Atomized logs are strictly bound to admin-level scopes to 
    prevent internal logic or stack traces from leaking to standard users.
    """
    def __init__(self, logger: logging.Logger, cortex: Optional[Any] = None):
        self.logger = logger
        self.cortex = cortex # Instance of Akasha Engine / Cortex

    def info(self, msg: str, atomize: bool = False):
        """Logs an INFO message. Optionally stores it in semantic memory."""
        self.logger.info(msg)
        if atomize and self.cortex:
            self._write_to_memory("INFO", msg)

    def error(self, msg: str, atomize: bool = True):
        """Logs an ERROR message. Stored in semantic memory by default for diagnosis."""
        self.logger.error(msg)
        if atomize and self.cortex:
            self._write_to_memory("ERROR", msg)

    def debug(self, msg: str):
        """Logs a DEBUG message (physical logs only to prevent DB bloat)."""
        self.logger.debug(msg)

    def warning(self, msg: str, atomize: bool = False):
        """Logs a WARNING message. Optionally stores it in semantic memory."""
        self.logger.warning(msg)
        if atomize and self.cortex:
            self._write_to_memory("WARNING", msg)

    def _write_to_memory(self, level: str, msg: str):
        """
        Injects a log message into the Cortex as an Atom.
        Enforces strict admin-only visibility.
        """
        try:
            # Metadata allows queries like 'Find all recent system errors'
            meta = {
                "role": "sys:log_event", # Prevents asynchronous NLP Weaver from processing it
                "level": level, 
                "origin": "harmonia"
            }
            # Failsafe: ensure logging never crashes the main operational flow.
            # Assigned strictly to 'scope:sys:admin' for ultimate privacy and security.
            admin_scopes = ["scope:sys:admin", "view:admin"]
            
            self.cortex.put_chunk(
                content=f"System Log [{level}]: {msg}", 
                meta=meta, 
                author="system.harmonia",
                scopes=admin_scopes
            )
        except Exception as e:
            # Absolute fallback: If DB fails, log the failure to physical stderr
            print(f"{Colors.FAIL}[Critical Logging Failure] Could not atomize log: {e}{Colors.ENDC}", file=sys.stderr)
