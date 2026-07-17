"""
Akasha Symbiosis Module (Environment & Dependency Manager - Pro Edition).

Acts as the peripheral nervous system of Akasha. 
1. `EnvironmentDetector (env)`: Profiles host hardware and capabilities.
2. `Colors`: Provides cinematic, environment-aware terminal styling.
3. `Symbiosis`: Handles graceful degradation and autonomic assimilation 
   (installation) of heavy modules in restricted environments.
"""

import importlib
import sys
import subprocess
import os
import platform

class Colors:
    """
    Cinematic terminal coloring.
    Automatically disables colors if running in a restricted or legacy environment.
    """
    _is_dumb = os.environ.get("TERM", "") == "dumb" or not sys.stdout.isatty()
    
    if _is_dumb:
        CYAN = GREEN = WARNING = FAIL = ENDC = DIM = BOLD = ''
    else:
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        DIM = '\033[2m'
        BOLD = '\033[1m'


class EnvironmentDetector:
    """Profiles the local machine to orchestrate the 'Struggle Algorithm'."""
    
    def __init__(self):
        self.os_name = platform.system()
        self.arch = platform.machine()
        self.python_version = platform.python_version()

    def print_environment_info(self):
        """Prints a cinematic overview of the host machine."""
        print(f" {Colors.CYAN}[System]{Colors.ENDC} OS: {self.os_name} | Arch: {self.arch} | Python: {self.python_version}")
        
    def secure_input(self, prompt: str) -> str:
        """
        Safe input handling to prevent terminal freezes and gracefully 
        handle EOF/KeyboardInterrupts during pre-flight checks.
        """
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            print() # Print newline
            return "n" # Default to 'no' on interruption

    def get_ml_engine_status(self) -> str:
        """
        Executes the Struggle Algorithm's reconnaissance phase.
        Determines the deepest level of Neural computation available.
        """
        try:
            import tflite_runtime
            return "ready_tflite"
        except ImportError:
            pass
            
        try:
            import tensorflow
            return "ready_tf"
        except ImportError:
            pass
            
        if '64' in platform.architecture()[0]:
            return "installable"
            
        return "impossible"

# Expose a singleton instance for system-wide environmental checks
env = EnvironmentDetector()


class Symbiosis:
    """
    Akasha's Dependency & Ecosystem Manager.
    Handles graceful degradation, missing dependencies, and automatic assimilation (installation).
    Includes timeout safeguards against infinite build loops in compiler-less environments.
    Crucial for safely loading heavy data-science modules (e.g., scikit-learn for TensorEngine)
    while maintaining Local-First mobile compatibility.
    """
    @staticmethod
    def require(module_name: str, package_name: str = None, scope: str = "[System]", feature: str = "Unknown Feature", ask: bool = True):
        package_name = package_name or module_name
        
        try:
            return importlib.import_module(module_name)
        except ImportError:
            print(f"\n{Colors.WARNING}{scope} Warning: Missing dependency for '{feature}'{Colors.ENDC}")
            print(f"{Colors.DIM}    Required package: '{package_name}' (import: '{module_name}'){Colors.ENDC}")
            
            is_interactive = sys.stdin and sys.stdin.isatty()
            
            if ask and is_interactive:
                try:
                    ans = input(f"    Would you like Akasha to install '{package_name}' automatically? (y/N): ").strip().lower()
                    if ans == 'y':
                        print(f"    {Colors.CYAN}[+] Assimilating {package_name} into ecosystem...{Colors.ENDC}")
                        
                        # timeout=90 to prevent infinite hangs during impossible source builds (e.g. Rust/C extensions on iOS)
                        try:
                            # --prefer-binary — prefer a wheel, but let a capable host build
                            # from source when no wheel exists for this Python. The 90 s
                            # timeout below bounds the build, so a compiler-less env still
                            # fails fast and degrades. (env_detector's core path stays
                            # wheels-only by design; this optional installer favours
                            # "install if at all possible".)
                            _cmd = [sys.executable, "-m", "pip", "install", package_name, "--prefer-binary"]
                            _r = subprocess.run(_cmd, timeout=90,
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            # PEP 668 (externally-managed): retry allowing the system-site install.
                            if _r.returncode != 0 and b"externally-managed" in (_r.stderr or b""):
                                _r = subprocess.run(_cmd + ["--break-system-packages"], timeout=90,
                                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            if _r.returncode != 0:
                                raise subprocess.CalledProcessError(_r.returncode, "pip install")
                        except subprocess.TimeoutExpired:
                            print(f"\n    {Colors.FAIL}[-] Assimilation timed out (process took too long).{Colors.ENDC}")
                            print(f"    {Colors.DIM}[-] This usually happens when compiling C/Rust extensions in restricted environments.{Colors.ENDC}")
                            raise subprocess.CalledProcessError(1, "pip install (timeout)")

                        print(f"    {Colors.GREEN}[+] Integration successful. Loading module...{Colors.ENDC}")
                        
                        importlib.invalidate_caches()
                        return importlib.import_module(module_name)
                    else:
                        print(f"    {Colors.DIM}[!] Proceeding with degraded functionality.{Colors.ENDC}")
                        return None
                        
                except subprocess.CalledProcessError:
                    print(f"    {Colors.FAIL}[-] Integration failed (network, compiler missing, timeout, or incompatible environment).{Colors.ENDC}")
                    fallback_ans = input(f"    Continue with degraded functionality (fallback)? (Y/n): ").strip().lower()
                    if fallback_ans == 'n':
                        print(f"    {Colors.DIM}[!] Terminating process by user request.{Colors.ENDC}")
                        sys.exit(1)
                    else:
                        print(f"    {Colors.DIM}[!] Proceeding with degraded functionality.{Colors.ENDC}")
                        return None
                except Exception as e:
                    print(f"    {Colors.FAIL}[-] Unexpected error: {e}{Colors.ENDC}")
                    return None
            else:
                if not is_interactive and ask:
                    print(f"    {Colors.DIM}(Auto-install skipped: Non-interactive environment detected.){Colors.ENDC}")
                print(f"    {Colors.WARNING}[!] Proceeding with degraded functionality (fallback).{Colors.ENDC}")
                print(f"    {Colors.DIM}Please install manually later: pip install {package_name}{Colors.ENDC}")
                return None
