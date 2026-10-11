"""
Operator secrets store — a chmod-0600 KEY=VALUE file under the runtime data dir that the daemon loads
into the environment at boot. So an operator sets an API key ONCE (via the `llm.key` CLI command) and
it persists across restarts, without ever touching Linux `export`.

- NEVER in the repo or a distributable seed (it lives under `data/`, which is gitignored, and is
  written 0600). Keys are still env-only at runtime — this file is just where the env is seeded from.
- A real environment variable ALWAYS wins over the file (so a systemd `Environment=` / a shell export
  still overrides). The file only fills in what the env has not already set.
"""
import os

_HEADER = "# Akasha operator secrets — API keys. chmod 0600, NOT in the repo/seed. Env vars override.\n"


def _path(base_dir: str) -> str:
    d = os.path.join(base_dir, "central")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, "secrets.env")


def read_all(base_dir: str) -> dict:
    """The stored {VAR: value}. Missing/unreadable file → {}."""
    out = {}
    try:
        with open(_path(base_dir), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip():
                    out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def load_into_env(base_dir: str) -> int:
    """Seed os.environ from the file — but only for vars NOT already set (a real env var wins).
    Returns how many were loaded. Best-effort; a missing file is a no-op."""
    n = 0
    for k, v in read_all(base_dir).items():
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n


def _write_all(base_dir: str, data: dict) -> None:
    p = _path(base_dir)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(_HEADER)
        for k, v in data.items():
            fh.write(f"{k}={v}\n")
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    os.replace(tmp, p)
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def set_var(base_dir: str, var: str, value: str) -> bool:
    """Upsert VAR=value in the file (0600) AND os.environ (LIVE — takes effect without a restart)."""
    data = read_all(base_dir)
    data[var] = value
    _write_all(base_dir, data)
    os.environ[var] = value
    return True


def remove_var(base_dir: str, var: str) -> bool:
    """Delete VAR from the file and os.environ. Returns whether it was present."""
    data = read_all(base_dir)
    if var not in data:
        os.environ.pop(var, None)
        return False
    del data[var]
    _write_all(base_dir, data)
    os.environ.pop(var, None)
    return True
