"""
Akasha Shell Portal — thin programmatic REPL client.

AkashaShell provides a lightweight alternative to the full stdio REPL.
Useful for embedding in scripts or minimal environments.
"""

import sys
import json
import uuid

from api.router import CommandRouter
from api.env_detector import env, Colors
from api.shell.renderer import paged_render as _render_resp


class AkashaShell:
    """Thin programmatic REPL. Boots via sys.ping + auth.verify."""

    def __init__(self, gw=None, client_id: str = None):
        if gw is None:
            import api.gateway as _gw_mod
            gw = _gw_mod.gateway
        self.gw            = gw
        self.client_id     = client_id or f"cli_{env.system}_{env.machine}_{uuid.uuid4().hex[:4]}"
        self.session_token = self.client_id
        self.use_colors    = not (env.is_windows and sys.version_info < (3, 8))

    def _c(self, color: str, text: str) -> str:
        return f"{color}{text}{Colors.RESET}" if self.use_colors else text

    def boot(self):
        print(self._c(Colors.DIM,
              f"[*] {env.system.upper()} / Python {env.python_version.major}.{env.python_version.minor}"))

        ping = self.gw.dispatch({
            "jsonrpc": "2.0", "method": "sys.ping",
            "params": {"session_token": self.client_id}, "id": "boot",
        })
        if "error" in ping:
            print(self._c(Colors.FAIL, f"[!] Kernel offline: {ping['error']['message']}"))
        else:
            state = ping.get("result", {}).get("self", {}).get("state", "?")
            print(self._c(Colors.GREEN, f"[+] Kernel alive (state={state})"))

        auth = self.gw.dispatch({
            "jsonrpc": "2.0", "method": "kernel.auth.verify",
            "params": {"data": {"user_id": self.client_id, "passphrase": ""}},
            "id": "auth",
        })
        if "error" not in auth:
            self.session_token = auth["result"].get("session_token", self.client_id)
            print(self._c(Colors.GREEN, f"[+] Session: {self.session_token}"))

        self._repl()

    _NAV_ENTER = {
        "dive": "dive", "look": "dive", "d": "dive",
        "explore": "explore", "exp": "explore",
        "assoc": "assoc", "associate": "assoc",
    }
    _NAV_COLOR = {
        "dive":    Colors.CYAN,
        "explore": Colors.GREEN,
        "assoc":   "\033[35m",
    }

    def _repl(self):
        nav_mode: dict = {"active": False, "name": None}

        while True:
            try:
                if nav_mode["active"]:
                    name = nav_mode["name"]
                    col  = self._NAV_COLOR.get(name, Colors.CYAN)
                    prompt = (self._c(col, f"[{name}]") + " " +
                              self._c(Colors.CYAN, f"Akasha[{self.client_id[:10]}]> "))
                else:
                    prompt = self._c(Colors.CYAN, f"Akasha[{self.client_id[:10]}]> ")

                cmd_str = input(prompt).strip()
                if not cmd_str:
                    continue

                if cmd_str.lower() in ("exit", "quit"):
                    if nav_mode["active"]:
                        name = nav_mode["name"]
                        nav_mode["active"] = False
                        nav_mode["name"]   = None
                        print(self._c(Colors.DIM, f"  ↩ Leaving {name} mode."))
                        continue
                    print(self._c(Colors.DIM, "[*] Detaching…"))
                    break

                if cmd_str.startswith("svc "):
                    self._handle_svc(cmd_str)
                    continue

                payload = CommandRouter.build_rpc_request(cmd_str, self.session_token)
                if not payload:
                    print(self._c(Colors.FAIL, f"[!] Unknown: '{cmd_str.split()[0]}'"))
                    continue

                resp = self.gw.dispatch(payload)

                _nav_cmd = cmd_str.split()[0].lower()
                _entered = self._NAV_ENTER.get(_nav_cmd)
                if _entered and "error" not in resp:
                    nav_mode["active"] = True
                    nav_mode["name"]   = _entered

                _render_resp(resp)

            except KeyboardInterrupt:
                print(self._c(Colors.DIM, "\n[*] Interrupted."))
                break
            except EOFError:
                break
            except Exception as exc:
                print(self._c(Colors.FAIL, f"[!] Fatal: {exc}"))

    def _handle_svc(self, cmd_str: str):
        try:
            from api.service_manager import ServiceManager
            from api.shell.renderer import render_svc_list
            svc   = ServiceManager.get_instance()
            parts = cmd_str.split()
            sub   = parts[1] if len(parts) > 1 else ""

            if sub == "ls":
                session_counts = None
                try:
                    import api.gateway as _gw
                    _mgr = getattr(getattr(_gw.gateway, "kernel_client", None), "manager", None)
                    if _mgr:
                        session_counts = _mgr.count_sessions()
                except Exception:
                    pass
                render_svc_list(svc.list_services(), session_counts)
            elif sub in ("start", "stop", "restart"):
                if len(parts) < 3:
                    print(self._c(Colors.FAIL, f"  Usage: svc {sub} <name>"))
                    return
                name = parts[2]
                if sub == "start":
                    result = svc.start_by_blueprint(name)
                elif sub == "stop":
                    result = svc.stop_service(name)
                else:
                    result = svc.restart_service(name)
                if "error" in result:
                    print(self._c(Colors.FAIL, f"  [!] {result['error']}"))
                else:
                    print(self._c(Colors.GREEN, f"  ✓ {result.get('service', name)} {result.get('status', sub + 'ed')}"))
            else:
                print(self._c(Colors.DIM, "  Usage: svc ls  |  svc start <n>  |  svc stop <n>  |  svc restart <n>"))
        except ImportError:
            print(self._c(Colors.WARNING, "[!] ServiceManager unavailable."))


def run_shell(gw=None):
    AkashaShell(gw=gw).boot()
