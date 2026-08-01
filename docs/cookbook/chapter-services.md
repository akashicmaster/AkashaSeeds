# Chapter: Adding a Service Program

By the end of this chapter, you will be able to add your own long-running program to Akasha so
that it is started, listed, restarted, and kept alive by the same machinery that runs Akasha's own
web portal — on any distribution (seeds, thesaurus, server, enterprise). The mechanism is
identical everywhere; only *who is allowed to operate it* differs by distribution, and that is
covered at the end.

> **How to read the Cookbook**
> This chapter is self-contained. While working through the examples you will not need to consult
> other documentation. Advanced references are listed once at the end — never inline.

---

## What Is a Service Program?

Akasha runs two kinds of long-lived work:

- **Jobs** — work that runs *inside* Akasha (for example, loading the ontology). You do not manage
  these directly; they appear in listings for visibility.
- **Services** — separate operating-system programs that Akasha starts and supervises (for example,
  the web portal). **A service program is one of these.** It is your own program — a small web app,
  a dashboard, a background worker — that you want Akasha to run and keep running.

The component that manages services is the **Supervisor**. It lives inside the **Cell daemon** — the
persistent background process that owns Akasha's memory. When you add a service, the Supervisor:

1. **starts** it as its own OS process,
2. **records** it in a durable registry so any Akasha session can see it,
3. **restarts** it from a saved recipe if it dies (when you ask it to), and
4. **stops** it cleanly (before the daemon itself) when Akasha shuts down.

Everything a service needs to be (re)started — the exact command, working directory, and
environment — is saved as a small, safe **recipe**. Because the recipe is saved (not held only in
memory), *any* Akasha session can restart your service, and it comes back automatically after a
crash. You never have to hunt for a process id or write a startup script.

---

## The One Rule You Must Follow: `serve_only`

Akasha has **exactly one** writer to its memory — the Cell daemon. This is a hard design rule that
keeps your data safe and consistent.

Therefore: **a service program must not open its own Akasha memory to write.** A service that only
needs to *read* Akasha, or does not touch Akasha at all, is called **`serve_only`** and is always
allowed. A service that needs to *write* must send its writes **through the daemon** (over Akasha's
normal request interface), never by opening a second writer.

If you try to register a writer service while the daemon is running, Akasha **refuses to start it**
— on purpose. This is not an error in your code; it is the single-writer rule protecting your data.
Keep your services `serve_only` and route any writes through the daemon.

---

## Step 1 — Put Your Program Where Akasha Can Launch It

A service is launched as a Python module: `python -m services.<yourapp>`. For safety, Akasha will
**only** ever launch modules under the `services/` folder (or a short built-in allow-list). This is
what stops a corrupted or tampered recipe from ever running an arbitrary program on your machine.

So the simplest, no-configuration path is:

- Put your program at **`services/yourapp.py`** (or `services/yourapp/__main__.py`).

That's it — `services/*` is pre-approved, so your program is launchable and restartable out of the
box, with no change to Akasha itself.

Here is a complete, runnable example. Save it as `services/hello_service.py` (it ships with Akasha,
so you can try it immediately):

```python
"""hello_service — the minimal Akasha service program."""
import argparse, http.server, signal, threading

def _run(host, port):
    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b'{"service":"hello","status":"ok"}'
            self.send_response(200 if self.path in ("/healthz", "/") else 404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *a): pass
    httpd = http.server.HTTPServer((host, port), _H)
    def _term(_s, _f): threading.Thread(target=httpd.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, _term)   # stop cleanly when Akasha asks it to
    signal.signal(signal.SIGINT, _term)
    print(f"[hello_service] serving on {host}:{port}", flush=True)
    httpd.serve_forever(poll_interval=0.5)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--engine", default="")     # accepted and ignored
    a = ap.parse_args()
    _run(a.host, a.port)

if __name__ == "__main__":
    main()
```

Two things to notice, both of which matter to the Supervisor:

- It **handles `SIGTERM`** and shuts down cleanly. This is the signal Akasha sends when it stops your
  service. A program that ignores it would eventually be force-killed; one that handles it stops
  gracefully every time.
- It exposes **`/healthz`**. This is optional, but it lets Akasha check that your service is not just
  *running* but actually *answering* — and restart it if it hangs (see Step 4).

You can run it by hand exactly the way Akasha will:

```
python -m services.hello_service --port 8899
```

Open `http://127.0.0.1:8899/healthz` and you'll see `{"service":"hello","status":"ok"}`.

---

## Step 2 — Register It With the Supervisor

To have Akasha manage your service, you build a **recipe** and **register** it. This is done in the
code that launches your service (typically where your app decides to bring its background program
up). The pattern is always the same:

```python
import os, sys
from lib.harmonia import supervisor as sv

root     = os.getcwd()
port     = 8899
base_dir = os.path.join(root, "data")   # or wherever Akasha's data lives

# 1. Build a validated, saveable recipe. Akasha checks it here: the command must launch an
#    allow-listed services.* module, and env_add may hold only ordinary settings (no secrets).
recipe = sv.build_process_spec(
    argv=[sys.executable, "-m", "services.hello_service", "--port", str(port)],
    cwd=root,
    env_add={"PYTHONUNBUFFERED": "1"},   # ordinary settings ONLY — never passwords/tokens
    log=os.path.join(root, "logs", "hello_service.log"),
    base_dir=base_dir,
)

# 2. Start it and register it with the Supervisor — the one service registry. `spec=recipe`
#    is what makes it restartable by anyone (any Akasha session, and the daemon after a crash).
import subprocess
proc = subprocess.Popen(recipe["argv"], cwd=root, start_new_session=True)

sup = sv.Supervisor(base_dir)
sup.record_running(
    "svc:app:me:hello", proc.pid,
    engine="hello", host="127.0.0.1", port=port,
    proc=proc,                   # this-process handle (so THIS process can stop it at exit)
    spec=recipe,                 # the saveable respawn recipe (this is the important part)
    deps=["svc:cell"],           # start after the daemon; stop before it
    trust="local",               # "local" = this machine only; "network" = reachable off-box
    serve_only=True,             # MANDATORY unless your service IS the writer (it isn't)
    restart="on-failure",        # never | on-failure | always
    health={"kind": "http", "target": f"http://127.0.0.1:{port}/healthz", "expect": 200},
)
```

`Supervisor` is the single registry — there is no separate service manager. Everything you need
to know about your service lives in one place: the saved recipe (how to (re)start it), the health
check (how to tell it's really up), and the policy (when to bring it back).

You do **not** have to write secrets into the recipe. If your service needs a real secret at
runtime, the daemon passes its own environment through when it restarts your service, so the secret
is *inherited*, never saved to disk. In fact, Akasha **refuses** to save any environment key that
looks like a credential (anything with `SECRET`, `TOKEN`, `PASSWORD`, and so on in its name). This
keeps the saved recipe safe to read.

### Name your service `app:<you>:<name>`

Notice the id `"app:me:hello"` (Akasha stores it as `svc:app:me:hello`). Always give your own
services a name of the shape **`app:<operator>:<name>`**, where `<operator>` is you (or your app's
account). The built-in platform services keep plain names like `web-portal`. This shape matters on
multi-user server deployments: it lets an administrator later hand *you* the right to operate *your*
`app:me:*` services and nothing else. Adopt it now and nothing needs renaming later.

---

## Step 3 — Operate It From the CLI

Once registered, your service is a first-class citizen. From the Akasha prompt:

```
akasha> svc ls
  name                    status   engine   address / pid          uptime
  ────────────────────────────────────────────────────────────────────────
  svc:cell                Active   cell-daemon   PID=4120            930s
  svc:web-portal          Active   uvicorn       PID=4310            928s
  svc:app:me:hello        Active   hello         PID=5561            42s
  job:onto-load (29/29 …) Done     job           —                  —
```

- `svc ls` — list everything Akasha is running. This is a **cross-session** view: even a fresh CLI,
  or a different terminal, sees your service, because the registry is saved on disk (not held in one
  process's memory).
- `svc restart app:me:hello` — restart your service. This works from **any** session, because it is
  rebuilt from the saved recipe by the daemon.
- `svc stop app:me:hello` — stop your service.
- `svc start app:me:hello` — start it again.

Start, stop, and restart require administrator rights on this machine (the local operator). Listing
is open to any signed-in user.

---

## Step 4 — Keep It Alive Automatically (optional)

If you registered with `restart="on-failure"` (or `"always"`), the daemon watches your service and
brings it back on its own:

- If the process **dies**, it is restarted from the saved recipe.
- If you gave it a **health check** and the process is running but no longer *answering*, it is
  restarted too. A health check is declared as plain data on the service, so Akasha can check it
  without importing your code:

  - `{"kind": "pid"}` — just "is the process alive" (the default).
  - `{"kind": "tcp", "target": "127.0.0.1:8899"}` — "is it accepting connections".
  - `{"kind": "http", "target": "http://127.0.0.1:8899/healthz", "expect": 200}` — "does it answer".

This is why the example exposes `/healthz`: with the `http` check, a service that hangs (still
"running" but not responding) is noticed and restarted, not left stuck.

You do not run anything to enable this — the daemon checks on a slow, background schedule while it is
otherwise idle, so watching your service never competes with real work.

---

## What Stays the Same Everywhere (and What Changes)

Everything above — the recipe, the `services/` rule, the `serve_only` rule, `svc ls/start/stop/
restart`, the health check — is **identical** on every Akasha distribution:

| Distribution | Who operates services | What is different |
|---|---|---|
| **seeds** (single user) | you, on your own machine | nothing |
| **thesaurus** (a library/organisation) | the administrator | more services; some reachable over the network |
| **server / enterprise** (future) | the administrator **plus delegated operators** | an admin can hand you operation of just *your* `app:you:*` services, without making you an admin |

The last row is why you name your services `app:<you>:<name>`: on a shared server, an administrator
can grant one person the right to start/stop/restart exactly their own services — a scoped
permission, not full administrator access — and the single-writer rule still holds, because a
delegated operator can only run `serve_only` services, never a second writer. You do not need to do
anything for that today; adopting the name shape now is all that is required to be ready for it.

---

## Common Questions

**My writer service is "refused admission" — why?**
Because Akasha has exactly one memory writer (the daemon). Set `serve_only=True` and route any
writes through the daemon's request interface. This is the single-writer rule protecting your data,
not a bug.

**`svc restart` says the service is unknown.**
Check the name. Your services are addressed as `app:<operator>:<name>` (Akasha stores them as
`svc:app:...`); `svc restart app:me:hello` and `svc restart svc:app:me:hello` are both accepted.

**Can a service write to Akasha at all?**
Yes — by sending normal requests to the daemon, exactly as the CLI and web portal do. It just may not
open its *own* second writer.

**Where do my service's logs go?**
To the `log` path in your recipe (e.g. `logs/hello_service.log`). `svc ls` shows the process id; the
log file has its output.

---

## References (advanced)

- Service extension & delegation contract: `docs/for-llm/service-extension-and-delegation-spec.md`
- The Supervisor plane and unit registry: `docs/for-llm/transport-daemon-units-spec.md`
- Respawn recipe and its safety gate: `docs/for-llm/supervisor-deferred-premises.md`
- Per-client permissions (delegation) model: `docs/for-llm/capability-delegation-iam-spec.md`
