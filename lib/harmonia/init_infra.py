"""
Harmonia Environment Bootstrap (Pro Edition).

Provisions the minimal physical infrastructure required for the Akasha Matrix.
This script acts as the 'Physiology' setup before the 'Psychology' (Memory) awakens.

[ARCHITECTURAL ALIGNMENT]
Following the 'Minimalist Physical Infrastructure' policy:
1. Physical directories are allocated exclusively for SQLite DBs, explicit 
   user assets, and essential diagnostic logs.
2. All simulation data (Dreams), extracted vectors, and intermediate NLP tokens 
   are processed and stored strictly within the Akasha Cortex as 'Workspaces' 
   (Pending Atoms/Collections).
"""

import os
import sys

# -----------------------------------------------------------------------------
# Robust Path Resolution: Ensure project root is mapped before importing local libs
# -----------------------------------------------------------------------------
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(_script_dir, '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from lib.harmonia.infra import HarmoniaInfra

# Optional import for immersive terminal output
try:
    from lib.akasha.symbiosis import Colors
except ImportError:
    class Colors:
        CYAN = GREEN = WARNING = FAIL = ENDC = DIM = BOLD = ''


def setup_harmonia_environment() -> bool:
    """
    Initializes physical paths and performs physiological sanity checks on the environment.
    Ensures that the root architecture and the 'admin' cell isolation zones are ready.
    """
    infra = HarmoniaInfra(root_path=project_root)
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}[Harmonia] Initiating Physical Infrastructure Setup...{Colors.ENDC}")
    
    # 1. System-level Provisioning
    # Creates: data/central, data/cells, env, ontology, series, assets, etc.
    success = infra.setup_system()
    if not success:
        print(f"{Colors.FAIL}  [!] FAILED to provision global system directories.{Colors.ENDC}")
        return False
        
    print(f"{Colors.GREEN}  -> System core directories: [READY]{Colors.ENDC}")
    
    # 2. Administrative Cell Provisioning
    # Creates: data/cells/admin/l_cortex, etc.
    # The 'admin' cell acts as the primary physical anchor for global operations.
    cell_id = "admin"
    try:
        cell_root = infra.setup_cell(cell_id)
        print(f"{Colors.GREEN}  -> Admin cell ('{cell_id}') space: [READY]{Colors.ENDC}")
        print(f"{Colors.DIM}     Path: {cell_root}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}  [!] FAILED to provision admin cell: {e}{Colors.ENDC}")
        return False

    # 3. Telemetry & Log Path Verification
    # While intermediate files are minimized, system-level 'Master Logs' are 
    # essential for diagnosing boot failures or DB corruption.
    master_log_dir = infra.logs_dir
    if os.access(master_log_dir, os.W_OK):
        print(f"{Colors.GREEN}  -> Master Telemetry Path: {master_log_dir} [WRITABLE]{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}  -> [WARNING] Master Telemetry Path is not writable: {master_log_dir}{Colors.ENDC}")
        print(f"{Colors.DIM}     System will attempt to log to current working directory.{Colors.ENDC}")

    # 4. Neural Models Verification
    models_dir = infra.models_dir
    if os.path.exists(models_dir):
        print(f"{Colors.GREEN}  -> Neural Engine Path: {models_dir} [READY]{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}  -> [WARNING] Neural Engine Path missing. Bootloader will self-repair.{Colors.ENDC}")

    # 5. Global Ontology Sync Check
    if os.path.exists(infra.ontology_dir):
        print(f"{Colors.GREEN}  -> Global Ontology Repository: {infra.ontology_dir} [FOUND]{Colors.ENDC}")
    else:
        print(f"{Colors.DIM}  -> [INFO] Global Ontology will be initialized upon first boot.{Colors.ENDC}")

    print(f"\n{Colors.CYAN}[Harmonia] Pre-flight check completed. Physical body is stable.{Colors.ENDC}")
    print(f"{Colors.BOLD}The system is ready to invoke the Akasha Core.{Colors.ENDC}")
    return True

if __name__ == "__main__":
    try:
        if setup_harmonia_environment():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}[CRITICAL] Setup failed due to an unexpected physiological error: {e}{Colors.ENDC}")
        sys.exit(1)
