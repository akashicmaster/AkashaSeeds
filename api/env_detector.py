"""
Akasha Symbiosis & Environment Detection Module.
Analyzes the execution environment (OS, Terminal, IDEs, Python version, Locale) 
to determine system capabilities and manage external dependencies.

[THE STRUGGLE ALGORITHM]
Degradation is the absolute last resort.
The system attempts to keep options open (e.g., offering or suggesting installation)
unless physically impossible due to hardware or OS restrictions (e.g., 32-bit limits).

[SYMBIOTIC DEPENDENCY INJECTION]
Provides `Symbiosis.require()` to dynamically load optional modules. If a module
is missing, it consults the Struggle Algorithm to determine if the ecosystem
can adapt, falling back gracefully without crashing the core Soma.
"""

import sys
import os
import getpass
import platform
import locale
import importlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Harmonia.Symbiosis")

# Tracks packages whose pip install already failed this process lifetime;
# prevents re-attempting on every ensure() call (e.g. repeated spacy loads).
_install_failed: set = set()

# Terminal Color Codes
class Colors:
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    BLUE    = '\033[94m'
    WARNING = '\033[93m'
    FAIL    = '\033[91m'
    HEADER  = '\033[95m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    ENDC    = '\033[0m'
    RESET   = '\033[0m'   # alias


class EnvironmentDetector:
    """
    Profiles the host machine's physical and OS-level capabilities.
    Determines locale, architecture, and terminal interactivity to ensure
    Akasha can survive and render output effectively.
    """
    def __init__(self):
        # Basic OS and Architecture Info
        self.os_type = os.name
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.python_version = sys.version_info
        
        self.is_windows = (self.os_type == 'nt')
        self.is_mac = (self.system == 'darwin')
        self.is_linux = (self.system == 'linux')
        
        # Determine 32-bit vs 64-bit for ML Engine compatibility
        self.is_64bit = "64" in platform.architecture()[0]
        
        self.default_locales = self._detect_locales()
        self.is_restricted_console = self._detect_restricted_env()
        self._capability_cache: Dict[str, bool] = {}

    def _detect_locales(self) -> List[str]:
        """Safely probes OS environment variables to determine preferred languages."""
        locales = []
        for env_var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(env_var)
            if val:
                for part in val.split(':'):
                    lang = part.split('.')[0].split('@')[0]
                    if lang and lang not in locales and lang != 'C':
                        locales.append(lang)
        try:
            default_locale, _ = locale.getdefaultlocale()
            if default_locale and default_locale not in locales and default_locale != 'C':
                locales.append(default_locale)
        except Exception:
            pass
            
        if 'en_US' not in locales:
            locales.append('en_US')
        return locales

    def _detect_restricted_env(self) -> bool:
        """
        Refined detection: Do not degrade capable terminals like Codespaces or VS Code.
        Degrade ONLY when the environment is fundamentally incapable of hiding input 
        or handling complex TTY commands.
        """
        # 1. Non-interactive pipes/redirections always degrade
        if not sys.stdin.isatty(): 
            return True
        
        # 2. Notebooks (Jupyter/Colab) cannot handle getpass elegantly
        if "IPYTHONENABLE" in os.environ or "JPY_PARENT_PID" in os.environ:
            return True
            
        # 3. Known restricted iOS Python environments (e.g., Pyto, Pythonista)
        if sys.platform == 'ios' or 'pyto' in sys.modules or 'pythonista' in sys.modules:
            return True
            
        # 4. Windows background GUI consoles without proper TTY footprints
        if self.is_windows:
            if 'PROMPT' not in os.environ and 'PSModulePath' not in os.environ and 'WT_SESSION' not in os.environ:
                return True
                
        # Codespaces, VS Code, Gitpod, etc., are fully capable and will reach here (False).
        return False

    def secure_input(self, prompt: str) -> str:
        """
        Safe wrapper for getpass to prevent deadlocks in restricted TTYs (like iOS or IDEs).
        Degrades to standard visible input if terminal lacks secure capabilities.
        """
        if self.is_restricted_console:
            return input(f"{prompt} (Visible) > ").strip()
        else:
            try:
                return getpass.getpass(prompt).strip()
            except (getpass.GetPassWarning, EOFError, Exception):
                return input(f"{prompt} (Visible) > ").strip()

    # =========================================================================
    # The Struggle Algorithm (Capability Profiling)
    # =========================================================================
    
    def is_library_available(self, lib_name: str) -> bool:
        """Caches module import checks to prevent redundant disk I/O."""
        if lib_name in self._capability_cache:
            return self._capability_cache[lib_name]
        try:
            importlib.import_module(lib_name)
            self._capability_cache[lib_name] = True
            return True
        except ImportError:
            self._capability_cache[lib_name] = False
            return False

    def get_ml_engine_status(self) -> str:
        """
        Evaluates the ML capability of the environment.
        Returns:
            "ready_tflite": Optimal lightweight inference available.
            "ready_tf": Full TensorFlow available (heavy, but works).
            "installable": Missing libraries, but hardware supports it.
            "impossible": Hardware/OS limits prohibit ML (forced degradation).
        """
        if self.is_library_available('ai_edge_litert'):
            return "ready_litert"
        if self.is_library_available('tflite_runtime'):
            return "ready_tflite"
        if self.is_library_available('tensorflow'):
            return "ready_tf"
            
        # If it's a 32-bit system, modern TF/TFLite binaries usually don't exist.
        if not self.is_64bit:
            return "impossible"
            
        # Hardware supports it. The ecosystem struggles to survive.
        return "installable"

    def get_nlp_status(self, lang_code: Optional[str] = None) -> str:
        """Evaluates NLP library status with the Struggle Algorithm."""
        ml_status = self.get_ml_engine_status()
        if ml_status == "impossible":
            return "impossible"
            
        if not lang_code:
            lang_code = self.get_primary_locale()
            
        has_spacy = self.is_library_available('spacy')
        
        if lang_code.startswith('ja'):
            has_fugashi = self.is_library_available('fugashi')
            has_ipadic = self.is_library_available('ipadic')
            if has_spacy and has_fugashi and has_ipadic:
                return "ready"
        elif lang_code.startswith('en'):
            if has_spacy:
                return "ready"
                
        return "installable"

    # =========================================================================
    # Getters and Output
    # =========================================================================

    def get_primary_locale(self, user_locales: Optional[List[str]] = None) -> str:
        locales = user_locales if user_locales else self.default_locales
        return locales[0] if locales else "en_US"

    def get_environment_status(self, user_locales: Optional[List[str]] = None) -> Dict[str, Any]:
        active_locales = user_locales if user_locales else self.default_locales
        primary = self.get_primary_locale(user_locales)
        
        ml_stat = self.get_ml_engine_status()
        if ml_stat in ["ready_litert", "ready_tflite", "ready_tf"]:
            ml_disp = "Active (" + ml_stat.split('_')[1].upper() + ")"
        elif ml_stat == "installable": 
            ml_disp = "Missing (Installable)"
        else: 
            ml_disp = "Impossible (Hardware Limits)"
        
        nlp_stat = self.get_nlp_status(primary)
        if nlp_stat == "ready": 
            nlp_disp = "Active"
        elif nlp_stat == "installable": 
            nlp_disp = "Missing (Installable)"
        else: 
            nlp_disp = "Impossible (Hardware Limits)"
        
        return {
            "os": f"{self.system.capitalize()} ({self.machine})",
            "python": f"{self.python_version.major}.{self.python_version.minor}",
            "locales": active_locales,
            "terminal_mode": "Restricted (Degraded Mode)" if self.is_restricted_console else "Native (Full Features)",
            "ml_engine": ml_disp,
            "nlp_support": nlp_disp
        }

    def print_environment_info(self):
        stat = self.get_environment_status()
        print(f"{Colors.DIM}[Environment]{Colors.ENDC} OS: {stat['os']} | Python: {stat['python']}")
        print(f"{Colors.DIM}[Locale]     {Colors.ENDC} {' -> '.join(stat['locales'])} (System Default)")
        print(f"{Colors.DIM}[Terminal]   {Colors.ENDC} Mode: {stat['terminal_mode']}")
        print(f"{Colors.DIM}[Engines]    {Colors.ENDC} ML: {stat['ml_engine']} | NLP: {stat['nlp_support']}")

# Global somatic environment detector
env = EnvironmentDetector()


class Symbiosis:
    """
    Dynamic Dependency Injection and Environment Adaptation.
    Handles the safe loading of third-party modules. If a module is missing, 
    it consults the EnvironmentDetector to provide context-aware feedback 
    before gracefully degrading capabilities.
    """
    
    @classmethod
    def require(cls, module_name: str, package_name: Optional[str] = None,
                scope: str = "[System]", feature: str = "Feature", ask: bool = True) -> Optional[Any]:
        """
        Attempts to import a dynamic dependency.
        If missing, uses the Struggle Algorithm to determine the appropriate response.

        Args:
            module_name (str): The Python module to import (e.g., 'fastapi', 'spacy').
            package_name (str, optional): The pip package name if different from module_name.
            scope (str): The system boundary requesting the module (for logging).
            feature (str): Human-readable feature relying on this module.
            ask (bool): If True, warns the user visibly in the terminal.

        Returns:
            The loaded module, or None if the dependency is missing/impossible to load.
        """
        try:
            return importlib.import_module(module_name)
        except ImportError:
            pkg_name = package_name or module_name

            # The Struggle: Assess if it's even worth trying to survive
            if env.is_64bit is False and "tensorflow" in pkg_name.lower():
                if ask:
                    print(f"{Colors.FAIL}{scope} Hardware Limit: Cannot enable '{feature}'. 32-bit OS detected.{Colors.ENDC}")
                return None

            if ask:
                print(f"{Colors.WARNING}{scope} Missing Capability: '{feature}' is offline.{Colors.ENDC}")
                print(f"{Colors.DIM}  -> To enable, run: pip install {pkg_name}{Colors.ENDC}")

            return None

    # ── Internal helper ───────────────────────────────────────────────────────

    @classmethod
    def _pip_install(cls, package_name: str, module_name: str,
                     scope: str, timeout: int) -> Optional[Any]:
        """
        Install *package_name* via pip (subprocess) with a spinner and stderr
        log suppression, then import and return *module_name*.
        Returns None silently on any failure — callers decide what to report.
        """
        import subprocess
        import threading
        import time
        import itertools
        import logging as _log_mod

        # Suppress Harmonia stderr handlers so the spinner isn't interrupted
        _harmonia_log = _log_mod.getLogger("Harmonia")
        _suppressed: list = [
            h for h in list(_harmonia_log.handlers)
            if isinstance(h, _log_mod.StreamHandler) and getattr(h, "stream", None) is sys.stderr
        ]
        for h in _suppressed:
            _harmonia_log.removeHandler(h)

        _done = [False]
        _frames = itertools.cycle(r'|/-\\')

        def _spin():
            while not _done[0]:
                sys.stdout.write(f"\r  {next(_frames)}  {scope} Installing '{package_name}'… ")
                sys.stdout.flush()
                time.sleep(0.13)

        spin_t = threading.Thread(target=_spin, daemon=True)
        spin_t.start()

        ok = False
        _err_detail = ""
        try:
            # --only-binary=:all: — never build from source. In a compiler-less env
            # (Codespaces, iPadOS/Pyto, locked-down containers) a source build for a
            # C-extension package hangs or fails slowly; this makes it "wheel or
            # nothing" so we degrade fast to the self-owned floor. Pure-Python and
            # manylinux-wheel packages still install normally.
            _base_cmd = [sys.executable, "-m", "pip", "install", "--quiet",
                         "--disable-pip-version-check", "--only-binary=:all:", package_name]
            res = subprocess.run(
                _base_cmd, timeout=timeout,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            ok = res.returncode == 0
            _stderr = res.stderr.decode("utf-8", errors="replace")

            # PEP 668: a modern distro Python (Debian 12+, Ubuntu 23.04+, and newer
            # Python builds) marks the system environment "externally managed" and
            # refuses system-site installs. Akasha's optional deps are meant to
            # self-provision, and running the seed is the operator's opt-in, so
            # retry with --break-system-packages. Guarded on the exact error, so a
            # non-PEP-668 pip is never handed the flag.
            if not ok and ("externally-managed" in _stderr or "PEP 668" in _stderr):
                res = subprocess.run(
                    _base_cmd + ["--break-system-packages"], timeout=timeout,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                ok = res.returncode == 0
                _stderr = res.stderr.decode("utf-8", errors="replace")

            if not ok:
                lines = _stderr.strip().splitlines()
                _err_detail = lines[-1] if lines else "(no output)"
        except subprocess.TimeoutExpired:
            _err_detail = f"timed out after {timeout}s"
        except Exception as exc:
            _err_detail = str(exc)
        finally:
            _done[0] = True
            spin_t.join(timeout=1.0)
            sys.stdout.write("\r" + " " * 64 + "\r")
            sys.stdout.flush()
            for h in _suppressed:
                _harmonia_log.addHandler(h)

        if ok:
            try:
                importlib.invalidate_caches()
                return importlib.import_module(module_name)
            except ImportError:
                _err_detail = "installed but not importable"

        if _err_detail:
            logger.warning(f"{scope} pip install '{package_name}': {_err_detail}")
        return None

    # ── Public auto-install API ───────────────────────────────────────────────

    @classmethod
    def ensure(cls, module_name: str, package_name: Optional[str] = None,
               scope: str = "[System]", feature: str = "Feature",
               timeout: int = 120) -> Optional[Any]:
        """
        Like require(), but automatically attempts pip install when the module is absent.

        Runs pip as a child process with a spinner and a hard timeout (default 120 s,
        matching the original "at most 2-3 minutes" design contract).
        During the install window stderr log handlers are silenced so only the
        spinner line is visible (original behaviour on all platforms inc. iPadOS/Pyto).
        """
        try:
            return importlib.import_module(module_name)
        except ImportError:
            pass

        pkg = package_name or module_name
        if pkg in _install_failed:
            return None

        # Honour the operator's opt-out: never attempt a network/pip install when
        # AKASHA_SKIP_AUTOINSTALL is set (restricted / non-interactive / offline).
        # Degrade silently — the caller always has a self-owned floor. This keeps the
        # install-attempt latency and spinner noise out of environments that can't or
        # won't install, without changing that degradation was already correct.
        if os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
            return None

        result = cls._pip_install(pkg, module_name, scope, timeout)
        if result is not None:
            print(f"  [+] {scope} '{pkg}' ready.", flush=True)
            return result

        _install_failed.add(pkg)
        print(f"  [!] {scope} '{feature}' unavailable — could not install '{pkg}'.",
              flush=True)
        return None

    @classmethod
    def ensure_one_of(cls, candidates: list, scope: str = "[System]",
                      feature: str = "Feature", timeout: int = 120) -> Optional[Any]:
        """
        Ensure at least one of the given (module_name, package_name) candidates
        is importable — trying each in order until one succeeds.

        First checks whether any candidate is already importable (no install
        needed).  If none are present, attempts pip install for each candidate
        in sequence, returning the first that succeeds.

        Useful for packages that ship under different names across platforms or
        Python versions (e.g. tflite-runtime → tensorflow-cpu → tensorflow).
        """
        # Fast path: already installed
        for module_name, _ in candidates:
            try:
                return importlib.import_module(module_name)
            except ImportError:
                pass

        # Try installing each candidate in priority order
        for module_name, package_name in candidates:
            if package_name in _install_failed:
                continue
            result = cls._pip_install(package_name, module_name, scope, timeout)
            if result is not None:
                print(f"  [+] {scope} '{package_name}' ready.", flush=True)
                return result
            _install_failed.add(package_name)

        print(f"  [!] {scope} '{feature}' unavailable — no compatible variant found.",
              flush=True)
        return None
