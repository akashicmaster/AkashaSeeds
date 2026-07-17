# Publishing the archives portal on shared / rental hosting (CGI route)

**Audience:** operators who want to put the public thesaurus portal online on a
host that only offers **CGI** — no long-running httpd, no free choice of port
(typical Japanese rental servers, cPanel shared hosting, etc.).

**One-line summary:** serve `archives/` as plain static files and route the two
JSON-RPC paths (`/rpc`, `/api/rpc`) to `services/cgi/akasha.cgi`. No daemon and
no open port are required.

---

## Why plain CGI is enough

Akasha's kernel boot looks expensive, but only the **first** load of the base
ontology is. After that:

- **Warm boot is ~0.3–0.4 s per request.** The base ontology writes a filesystem
  restart sentinel (`data/central/sentinels/<pack>_<hash>.done`); every later
  boot sees it and skips the load entirely. A CGI request pays only kernel
  construction + a SQLite open.
- **Reads come from the shared, persistent nucleus.** Nothing needs to stay
  resident between requests.
- **Guest sessions are stateless.** A guest token (`gbk:…`) is HMAC-signed with
  the nucleus secret and self-verifying, so a token minted in one request
  authenticates in the next even though each request is a brand-new process.
  The whole public read flow works across independent CGI invocations:

  ```
  session.guest.create  →  thesaurus.view.atom / thesaurus.shelf.list
  ```

So a low-traffic public thesaurus runs perfectly well on plain CGI.

---

## Deploy in five steps

Assume the repo is uploaded to `~/akasha/` and your web document root is
`~/akasha/archives/` (its landing page plus the `library/`, `word/`, `field/`
sub-apps live there already).

**1. One-time initialisation + ontology preload (mandatory, interactive).**
A fresh cell must first perform the **Pact of Genesis** (create the admin
identity) — this is deliberately local-console only, so do it over SSH. Genesis
also kicks off the base-ontology load, which takes far longer than any CGI
timeout, so let it finish *before* the site is live:

```
cd ~/akasha
python akasha.py            # interactive — NOT --stdio
```

- Complete the Pact of Genesis when prompted (name the system, set an Admin ID
  and passphrase).
- **Wait for the base ontology to finish loading.** It runs in the background
  after genesis; it is done when the restart sentinel appears:

  ```
  ls data/central/sentinels/        # → base_<hash>.done  means warm
  ```

- Once the sentinel exists, exit the prompt. The cell is now initialised and
  warm; every CGI request afterwards is ~0.3–0.4 s. (Re-run this step after
  upgrading the ontology packs — a changed pack invalidates its sentinel.)

> The passphrase prompt falls back to visible input when there is no secure TTY,
> so genesis can also be scripted by piping the four answers
> (`system name`, `admin id`, `passphrase`, `passphrase again`) — keep the
> process alive until the sentinel is written before letting stdin close.

**2. Make the CGI entry executable.**

```
chmod 755 ~/akasha/services/cgi/akasha.cgi
```

**3. Install the routing config.**
Copy `services/cgi/.htaccess.example` to `archives/.htaccess` and adjust the
`RewriteRule` target to your host's CGI convention (a `/cgi-bin/` alias, or a
direct relative path to the script). It routes `POST /rpc` and `POST /api/rpc`
to the CGI entry and serves everything else statically.

**4. Set the signing secret (any networked deploy).**
Provide a strong, stable `AKASHA_SECRET` via the host environment so guest/auth
tokens verify consistently and cannot be forged:

```
python -c "import secrets; print(secrets.token_hex(32))"
# → set AKASHA_SECRET=<that value> in the host env / control panel
```

Optionally pin the distribution tier with `AKASHA_SERIES=thesaurus`.

**5. Visit the site.** The archives landing loads statically; atom lookups and
shelf listings flow through the CGI entry.

---

## What the CGI entry does

`services/cgi/akasha.cgi` is a ~20-line stdlib wrapper. It anchors `sys.path`
to the project root, asserts the CGI marker, and calls `akasha.main()`, which
takes its CGI fast-path: read the POST body → `AkashaGateway.dispatch()` (the
**same** gateway the uvicorn/httpd portals use) → print the JSON-RPC response.
Behaviour is identical to every other portal; only the transport differs.

`run_cgi` (in `api/portals/asgi.py`) accepts any `POST` and treats the body as
JSON-RPC, so `/rpc` and `/api/rpc` both work — the `.htaccess` is what confines
CGI to those two paths.

---

## Limits & notes

- **Static assets are served by your web server, not Akasha.** The archives
  portal is designed for this (it degrades gracefully if the client-side chart
  library is unavailable — see the graceful-degradation notes in the archives
  pages). `/cosmos/` and `/docs/` live outside `archives/`; symlink them into the
  doc root if you want them published too.
- **Concurrency.** Each request is its own process opening the SQLite cell in WAL
  mode: concurrent reads are fine; a burst of writes serialises. This suits a
  read-mostly public thesaurus. A high-write or high-QPS deployment wants the
  persistent uvicorn portal instead.
- **Cold start = one slow request.** If you skip the preload, the first visitor
  triggers the full ontology load and will time out. Always run step 1.
- **Not for the authenticated cockpit.** `cosmos` and other write-heavy,
  session-stateful surfaces expect a resident process; publish those with the
  uvicorn portal, not CGI.
