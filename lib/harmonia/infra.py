"""
Harmonia Infrastructure Provisioning Manager (Pro Edition).

Handles the automated setup of physical directory structures with a strict 
minimalist approach. Avoids disk-based intermediate files in favor of pure 
semantic memory mapping (Akasha Atoms and Workspaces) to maximize SSD 
lifespan and edge-device portability.

[PHYSICAL SYNC & ALIGNMENT]
Maintains parity with the entrypoint requirements defined in `main.py` and 
`akasha.py`, ensuring seamless auto-provisioning of AI models (env/models), 
DTN capsules (data/export), and identity cells.
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger("Harmonia.Infra")

class HarmoniaInfra:
    """
    Provisions only the indispensable physical "skeleton" of the Akasha system.
    Physical storage of intermediate files or simulation logs is bypassed;
    they are processed entirely as transactional "Workspaces" within the Cortex.
    """
    def __init__(self, root_path: str = "."):
        """
        Initializes the infrastructure map relative to the specified root path.
        """
        self.root_path = os.path.abspath(root_path)
        
        # 1. Data Persistence Directories
        self.data_dir = os.path.join(self.root_path, "data")
        self.central_dir = os.path.join(self.data_dir, "central")
        self.cells_dir = os.path.join(self.data_dir, "cells")
        self.import_dir = os.path.join(self.data_dir, "import")  # FileSystemWatcher staging
        self.export_dir = os.path.join(self.data_dir, "export")  # Memory dumps / Capsules
        
        # 2. Ecosystem Resources
        self.logs_dir = os.path.join(self.root_path, "logs")
        self.env_dir = os.path.join(self.root_path, "env")
        self.models_dir = os.path.join(self.env_dir, "models")   # TFLite/Tensor embedding models
        self.assets_dir = os.path.join(self.root_path, "assets") # Static UI assets
        
        # 3. Knowledge & Context Boundaries
        self.ontology_dir = os.path.join(self.root_path, "ontology")
        self.series_root = os.path.join(self.root_path, "series")

    def setup_system(self) -> bool:
        """
        Builds the minimal physical directories essential for Akasha's global operation.
        Automatically invoked during the boot sequence.
        """
        essential_dirs: List[str] = [
            self.central_dir, 
            self.cells_dir, 
            self.import_dir,
            self.export_dir,
            self.logs_dir,
            self.env_dir,
            self.models_dir,
            self.assets_dir,
            self.ontology_dir,
            self.series_root
        ]
        
        try:
            for d in essential_dirs:
                os.makedirs(d, exist_ok=True)
                self._ensure_gitkeep(d)
            logger.debug("[Harmonia.Infra] Global physical infrastructure verified/provisioned.")
            return True
        except PermissionError as e:
            logger.critical(f"[Harmonia.Infra] Permission denied while provisioning infrastructure: {e}")
            return False
        except Exception as e:
            logger.error(f"[Harmonia.Infra] Unexpected error during infrastructure setup: {e}", exc_info=True)
            return False

    def setup_cell(self, client_id: str) -> str:
        """
        Creates the physical isolation directories for a specific identity cell (user).
        Subdirectories are kept to a bare minimum, relying on Cortex for complex topologies.
        """
        if not client_id:
            raise ValueError("client_id must be provided to provision a cell.")
            
        cell_root = os.path.join(self.cells_dir, client_id)
        
        # Secure spatial isolation only for the physical DB and original binary assets
        sub_dirs: List[str] = [
            "l_cortex",   # Local SQLite Database storage
            "assets",     # Explicitly provided binaries/images by the user
            "exports",    # Final DTN capsule outputs specific to this user
            "logs"        # Private diagnostic logs
        ]
        
        try:
            for sd in sub_dirs:
                path = os.path.join(cell_root, sd)
                os.makedirs(path, exist_ok=True)
                self._ensure_gitkeep(path)
            
            logger.debug(f"[Harmonia.Infra] Identity Cell provisioned for '{client_id}'.")
            return cell_root
        except Exception as e:
            logger.error(f"[Harmonia.Infra] Failed to provision Cell for '{client_id}': {e}")
            raise

    def setup_series(self, series_name: str) -> str:
        """
        Creates template directories for a specific series (knowledge domain mapping).
        """
        if not series_name:
            raise ValueError("series_name must be provided to provision a series.")
            
        series_dir = os.path.join(self.series_root, series_name)
        sub_dirs: List[str] = ["ontology", "docs", "apps"]
        
        try:
            for sd in sub_dirs:
                path = os.path.join(series_dir, sd)
                os.makedirs(path, exist_ok=True)
                self._ensure_gitkeep(path)
                
            logger.debug(f"[Harmonia.Infra] Series template provisioned for '{series_name}'.")
            return series_dir
        except Exception as e:
            logger.error(f"[Harmonia.Infra] Failed to provision Series '{series_name}': {e}")
            raise

    def _ensure_gitkeep(self, directory: str):
        """Creates an empty .gitkeep file to anchor the directory structure in version control."""
        gitkeep = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep):
            try:
                with open(gitkeep, "w") as f:
                    f.write("")
            except Exception:
                pass # Fail silently if permission is restricted, as gitkeep is non-critical

    def get_db_path(self, client_id: Optional[str] = None) -> str:
        """
        Resolves the absolute file path for the target database.
        
        Args:
            client_id: If provided, resolves the local Cortex DB path for that specific user.
                       If None, resolves the global central Nucleus DB path.
        """
        if client_id:
            # Ensure the directory exists before returning the path
            cell_db_dir = os.path.join(self.cells_dir, client_id, "l_cortex")
            os.makedirs(cell_db_dir, exist_ok=True)
            return os.path.join(cell_db_dir, "l_cortex.db")
            
        # Ensure central directory exists
        os.makedirs(self.central_dir, exist_ok=True)
        return os.path.join(self.central_dir, "nucleus.db")
