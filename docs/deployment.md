# Deployment — environment variables

Generated from the manifests by `scripts/gen_deployment_doc.py`; do not edit by hand.

Every variable here is a **deployment fact**: a path, an address, a secret, an identity, the series, a capacity. None of them switches behaviour on or off.

- **The launcher refuses an `AKASHA_*` variable that no manifest declares.** It stops with exit 3 and one line per name: `[env] refused name=<NAME>`. That covers a variable exported in the shell and one set in `env/deployment.env`.
- `stop` still runs with an undeclared variable set, so a cell can always be halted.
- A name with `*` declares a family (one provider's budget, e.g. `AKASHA_LLM_MISTRAL_CALLS_PER_DAY`).
- The application declares its own variables under `env` in its manifest (`app/config/MANIFEST.json`); the launcher accepts them, and they are listed there, not here.

`env/deployment.env` (KEY=VALUE, `#` comments) is read at every launch. An exported variable wins over the file.

## Paths

Where the cell reads and writes.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_APP_DIR` | `<root>/app` | the application root — everything the application provides lives under it (platform-spec v1) | heart |
| `AKASHA_BASE_DIR` | `data` | the data directory the gate binds when no kernel has bound it (a process with no launcher) | heart |
| `AKASHA_DATA_DIR` | `<root>/data` | the cell's data directory | heart |
| `AKASHA_PROJECT_DIR` | `<root>` | the project root the ontology and its config are read from | heart |
| `AKASHA_SNAPSHOT_DIR` | `<pages root>/snapshots` | the portal's disk snapshot store | heart |
| `AKASHA_SOURCE_PACK_DIR` | `<app root>/assets` | where the application's source packs (corpus bundles) are read from | heart |
| `AKASHA_TLS_CERT` | — | an operator-supplied certificate (fullchain PEM); ACME manages none when set | heart |
| `AKASHA_TLS_KEY` | — | the private key for AKASHA_TLS_CERT | heart |

## Network

Where the cell listens and whom it talks to.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_ACME_DIRECTORY` | `Let's Encrypt` | the ACME directory URL | heart |
| `AKASHA_BASE_DOMAIN` | — | the public domain (host routing; the ACME fallback domain) | heart |
| `AKASHA_HOST` | `(the launcher's --host)` | the address the portal binds | heart |
| `AKASHA_HTTPS_PORT` | `443` | the HTTPS port when TLS is active | heart |
| `AKASHA_LLM_BASE_URL` | — | the generic OpenAI-compatible endpoint | heart |
| `AKASHA_OLLAMA_URL` | `http://localhost:11434` | the Ollama endpoint | heart |
| `AKASHA_PORT` | `(the launcher's --port)` | the port the portal binds | heart |
| `AKASHA_SEMCACHE_HOST` | — | the canonical public host the portal warms its cache for | heart |
| `AKASHA_SEMCACHE_ORIGIN` | — | the canonical public origin the portal warms its cache for | heart |
| `AKASHA_TLS_DOMAINS` | — | the certificate's domains (comma-separated) | heart |
| `AKASHA_TLS_EMAIL` | — | the ACME contact address | heart |
| `AKASHA_TRUST_XFF` | `1` | a trusted reverse proxy stands in front: the first X-Forwarded-For hop is the client | heart |
| `AKASHA_VISION_MODEL_URL` | `(the MobileNet release)` | where the vision model is fetched from on first use | heart |

## Secrets

Keys. Supply them out-of-band (the environment or a secrets manager); never commit them.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_ADMIN_PASS` | — | an out-of-band admin passphrase; a fresh cell self-initializes with it | heart |
| `AKASHA_GEMINI_KEY` | — | the Gemini key | heart |
| `AKASHA_LLM_API_KEY` | — | the key for the generic OpenAI-compatible endpoint | heart |
| `AKASHA_MISTRAL_KEY` | — | the Mistral key | heart |
| `AKASHA_OPENROUTER_KEY` | — | the OpenRouter key | heart |
| `AKASHA_SECRET` | `(vault)` | the token signing key; set it, identical on every host, for any networked cell | heart |
| `AKASHA_X_ACCESS_SECRET` | — | the X API access secret | heart |
| `AKASHA_X_ACCESS_TOKEN` | — | the X API access token | heart |
| `AKASHA_X_CONSUMER_KEY` | — | the X API consumer key | heart |
| `AKASHA_X_CONSUMER_SECRET` | — | the X API consumer secret | heart |

## Identity

Names the cell is given.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_ADMIN_ID` | `admin` | the admin's login id at genesis | heart |
| `AKASHA_BUILD_ID` | — | a display label for this build (a git SHA) | heart |
| `AKASHA_LLM_PROVIDER` | `mistral` | the model provider this cell speaks to | heart |
| `AKASHA_MCP_CLIENT` | `mcp:local` | the client a local (stdio) MCP server acts as | heart |
| `AKASHA_SYSTEM_NAME` | `AKASHA` | the cell's display name at genesis | heart |

## Series and host

What this deployment is: the series, the store, what the host provides.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_ALLOW_SELF_REGISTER` | — | this deployment admits self-registration (role forced to user) | heart |
| `AKASHA_BACKEND` | `(resolved by the launcher from the series and the data directory)` | the store backend | heart |
| `AKASHA_EMBED_MODEL` | — | an optional sentence-transformer for the high embedding tier | heart |
| `AKASHA_NO_WEB` | — | this host serves no web portal (CLI only) | heart |
| `AKASHA_PORTAL_GATE` | — | this deployment's portal is gated (written by the seed for its tier) | heart |
| `AKASHA_SERIES` | `seeds` | the series this cell runs | heart |
| `AKASHA_SILICA_VALUES` | `ram` | where Silica keeps values: ram or disk | heart |
| `AKASHA_SKIP_AUTOINSTALL` | — | this host installs no Python package at run time (offline / managed) | heart |
| `AKASHA_SQLITE_JOURNAL` | `WAL` | the SQLite journal mode (TRUNCATE on a synced single-file host) | heart |
| `AKASHA_TIER` | `(the series')` | the series' tier, written by the seed | heart |

## Capacity

Budgets and limits sized to the host. A `0` means unbounded where the row says so.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_ACME_RENEW_DAYS` | `30` | renew a managed certificate this many days before expiry | heart |
| `AKASHA_ADMIN_SESSION_RESERVE` | `2` | session slots held back for the admin | heart |
| `AKASHA_AUTOLEARN_LINK_MAX` | `200000` | links the structural autolearn reads | heart |
| `AKASHA_AUTOLEARN_MAX` | `40000` | atoms the boot autolearn reads | heart |
| `AKASHA_AUTOLEARN_PACE` | `100` | autolearn bake pace | heart |
| `AKASHA_A_BOT_RATE_PER_MIN` | `30` | atom pages per minute per unverified bot | heart |
| `AKASHA_BOOT_GRACE` | `300` | seconds a booting unit is not health-checked | heart |
| `AKASHA_BOOT_HARD_CEILING` | `900` | the launcher's absolute boot wait | heart |
| `AKASHA_BOOT_HEARTBEAT_STALE` | `20` | seconds before a boot heartbeat is stale | heart |
| `AKASHA_BOOT_WAIT` | `90` | seconds the launcher waits for the daemon | heart |
| `AKASHA_CENSUS_CAP` | `3000000` | atoms sys.census walks | heart |
| `AKASHA_CKPT_THRESHOLD` | `1073741824` | WAL growth in bytes, since the last fold in this process (the first check after a boot only takes the baseline), before the nucleus folds while no job is running; 0 disables | heart |
| `AKASHA_CLASS_LOG_EVERY_S` | `60` | visitor-class log interval | heart |
| `AKASHA_CLI_TTL` | `86400` | the local console's token TTL, seconds | heart |
| `AKASHA_DAEMON_OOM_SCORE_ADJ` | `-500` | the writer's oom_score_adj | heart |
| `AKASHA_DIVE_ADMIT` | `3` | concurrent dives admitted | heart |
| `AKASHA_DIVE_BUDGET` | `10` | seconds one dive may run (0: unbounded) | heart |
| `AKASHA_DIVE_QUEUE` | `10` | dives queued behind them | heart |
| `AKASHA_DIVE_WAIT_MS` | `5000` | how long a queued dive waits | heart |
| `AKASHA_GIL_SWITCH_MS` | `1.0` | the daemon's GIL switch interval, ms | heart |
| `AKASHA_GUEST_POOL_SIZE` | `128` | guest pool slots | heart |
| `AKASHA_GUEST_TTL` | `900` | guest inactivity TTL, seconds | heart |
| `AKASHA_HEARTBEAT_MEMTOP_MB` | `4096,6144` | RSS marks at which the heartbeat logs MemTop | heart |
| `AKASHA_HUMAN_TTL_S` | `1800` | how long a proven-human IP stays proven | heart |
| `AKASHA_IPC_QUEUE` | `32` | daemon IPC queue depth | heart |
| `AKASHA_IPC_WORKERS` | `6` | daemon IPC worker threads | heart |
| `AKASHA_LLM_*_CALLS_PER_DAY` | `(the provider's free tier)` | model calls per day for one provider (e.g. AKASHA_LLM_MISTRAL_CALLS_PER_DAY) | heart |
| `AKASHA_LLM_*_TOKENS_PER_DAY` | `(the provider's free tier)` | model tokens per day for one provider | heart |
| `AKASHA_LLM_*_TOKENS_PER_MONTH` | `(the provider's free tier)` | model tokens per month for one provider | heart |
| `AKASHA_LLM_CALLS_PER_DAY` | `(the provider's free tier)` | model calls per day, any provider | heart |
| `AKASHA_LLM_TOKENS_PER_DAY` | `(the provider's free tier)` | model tokens per day, any provider | heart |
| `AKASHA_LLM_TOKENS_PER_MONTH` | `(the provider's free tier)` | model tokens per month, any provider | heart |
| `AKASHA_LOG_BACKUPS` | `5` | rotated log files kept | heart |
| `AKASHA_LOG_LEVEL` | `INFO` | the log level | heart |
| `AKASHA_LOG_MAX_BYTES` | `52428800` | log file size before rotation | heart |
| `AKASHA_MANUAL_RESTART_TTL` | `120` | seconds a manual restart marker holds the guard off | heart |
| `AKASHA_MAX_LEAVES` | `(the series')` | the client limit | heart |
| `AKASHA_MEMTOP_MB` | `2500` | RSS at which the loader logs one MemTop | heart |
| `AKASHA_MEM_PRESSURE_BATCH` | `8` | sessions reaped per pressure tick | heart |
| `AKASHA_MEM_PRESSURE_MB` | `0` | reap idle owning sessions below this MemAvailable (0: never) | heart |
| `AKASHA_PORTAL_GRACEFUL_S` | `3` | the portal's graceful shutdown, seconds | heart |
| `AKASHA_PORTAL_OOM_SCORE_ADJ` | `500` | the portal's oom_score_adj | heart |
| `AKASHA_PULSE_KEEP_DAYS` | `2` | days of raw pulse kept before aggregation | heart |
| `AKASHA_RDNS_TIMEOUT` | `2` | crawler reverse-DNS timeout, seconds | heart |
| `AKASHA_REFERENCE_PAGE_TTL_S` | `1800` | portal reference-page cache TTL | heart |
| `AKASHA_RESPAWN_SETTLE` | `3` | seconds between a unit's death and its respawn | heart |
| `AKASHA_ROBOTS_CRAWL_DELAY` | `10` | robots.txt Crawl-delay | heart |
| `AKASHA_RPC_RATE_PER_MIN` | `120` | RPCs per minute per IP | heart |
| `AKASHA_SEARCH_BUDGET_S` | `10` | seconds one semantic search may run | heart |
| `AKASHA_SEARCH_CANDIDATES` | `500` | semantic search candidates | heart |
| `AKASHA_SEMCACHE_BUDGET_MB` | `512` | the semantic cache budget | heart |
| `AKASHA_SEMCACHE_STAGE_RENDERS_PER_MIN` | `60` | demand-staging renders per minute | heart |
| `AKASHA_SEMCACHE_WARM_INTERVAL_S` | `900` | portal warm pass interval | heart |
| `AKASHA_SEMCACHE_WARM_PACE_S` | `1.0` | portal warm pace, seconds per page | heart |
| `AKASHA_SESSION_TTL` | `1800` | owning-session inactivity TTL, seconds | heart |
| `AKASHA_SILICA_CACHE_FRAC` | `0.02` | Silica's value cache as a fraction of RAM | heart |
| `AKASHA_SILICA_CACHE_MB` | — | Silica's value cache, MB | heart |
| `AKASHA_SNAPSHOT_RETRY` | `30` | Retry-After on a warming snapshot | heart |
| `AKASHA_SNAPSHOT_TTL_DAYS` | `7` | snapshot TTL, days | heart |
| `AKASHA_SOURCE_BOOTSTRAP_MAX_S` | `0` | seconds a corpus bootstrap may run (0: unbounded) | heart |
| `AKASHA_SSR_MAX_CONCURRENCY` | `1` | concurrent server-side renders | heart |
| `AKASHA_SSR_TIMEOUT` | `6` | server-side render fetch timeout, seconds | heart |
| `AKASHA_THREAD_GUARD_INTERVAL` | `60` | thread-census guard interval, seconds | heart |
| `AKASHA_WATCHDOG_INTERVAL` | `60` | daemon watchdog round, seconds | heart |
| `AKASHA_WATCHDOG_SILENT_K` | `3` | silent rounds before the watchdog reaps | heart |
| `AKASHA_WORKER_FOOTPRINT_MB` | `1500` | a portal worker's expected RSS | heart |
| `AKASHA_WQ_YIELD_INTERVAL_MS` | `15` | WriteQueue yield interval, ms | heart |
| `AKASHA_WQ_YIELD_MS` | `8` | WriteQueue yield to readers, ms | heart |

## Set by the platform

The launcher sets these on its own child processes. An operator does not set them.

| variable | default | means | declared by |
|---|---|---|---|
| `AKASHA_DAEMON_ARGV` | — | the writer's argv, carried to the watchdog so it can revive it | heart |
| `AKASHA_EMBEDDED` | — | set by the launcher on an embedded (single-process) host | heart |
| `AKASHA_HANDSHAKE_BUILD` | — | the code fingerprint a launcher and daemon compare | heart |
| `AKASHA_SERVE_ONLY` | — | set by the launcher on a portal process: it never writes | heart |
| `AKASHA_SPAWNED_BY` | `launcher` | which process spawned this writer | heart |
