"""
Shared fixtures for the platform's evals — the platform's suite reads nothing of an application.

  world_genesis(kernel)   the commons (`world:default` + its clock) through the platform's WorldAxis,
                          synchronously — what the writer's boot does on its own thread
  fixture_app(name)       the absolute path of a fixture application root under test/fixtures/,
                          for `AKASHA_APP_DIR` (set it BEFORE the first platform import)
  pack_cell(files)        a fixture project (one pack `p_fx` holding `files`, an empty application
                          root) and a cell on it whose packs the REAL loader has loaded:
                          (kernel, cli, project_root). `cli(line, token)` runs a console line
                          through the console's router. Call before any other platform import.
"""
import hashlib
import json
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def fixture_app(name: str) -> str:
    return os.path.join(HERE, "fixtures", name)


def world_genesis(kernel) -> dict:
    from lib.akasha.api.concepts import WorldAxis
    from lib.akasha.jcl.workspace_context import system_context
    with system_context():
        return WorldAxis(kernel.manager.get_session("system.librarian")).genesis()


def pack_cell(files: dict, series: str = "seeds", load: bool = True):
    root = tempfile.mkdtemp(prefix="pack_cell_")
    ont = os.path.join(root, "ontology")
    pdir = os.path.join(ont, "p_fx")
    os.makedirs(pdir)
    with open(os.path.join(pdir, "PACK.json"), "w") as fh:
        json.dump({"label": "p_fx"}, fh)
    with open(os.path.join(ont, "REGISTRY.json"), "w") as fh:
        json.dump({"version": 2, "packages": [{"name": "p_fx", "autoload": True}]}, fh)
    os.makedirs(os.path.join(root, "config", "ontology"))
    with open(os.path.join(root, "config", "ontology", "packs.json"), "w") as fh:
        json.dump({"load_all": True}, fh)
    for name, text in files.items():
        with open(os.path.join(pdir, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    os.environ["AKASHA_PROJECT_DIR"] = root
    os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    from api.router import CommandRouter
    cls = type("FixturePackCell", (KernelDispatcher,), {"_boot_load_ontology": lambda self: None})
    k = cls(series=series, base_dir=os.path.join(root, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw-123456").hexdigest()}},
                "id": "g"}, "local")
    k._boot_daemons_started = True
    if load:
        L.boot_load_ontology(k)

    def cli(line, token="admin"):
        r = k.dispatch(CommandRouter.build_rpc_request(line, token), "local")
        return r.get("result") if "result" in r else {"error": (r.get("error") or {}).get("message")}
    return k, cli, root
