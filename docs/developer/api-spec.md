# AKASHA JSON-RPC 2.0 API Specification

**Version:** 2.0.0  
**Last updated:** 2026-05-27  
**Status:** Active

> **Related:** [Scope Dimension Model](scope-dimension-model.md) — full
> specification of the four scope dimensions, storage architecture, node
> character model, and write pattern.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Transport Layer](#2-transport-layer)
3. [Request and Response Envelope](#3-request-and-response-envelope)
4. [Authentication](#4-authentication)
5. [Error Codes](#5-error-codes)
6. [Context References (id Parameters)](#6-context-references-id-parameters)
7. [IAM — Roles, Capabilities, and Scopes](#7-iam--roles-capabilities-and-scopes)
8. [Ontology Architecture](#8-ontology-architecture)
9. [Harmonia Workspace and Rollback Model](#9-harmonia-workspace-and-rollback-model)
10. [Method Reference](#10-method-reference)
    - [10.1 System Handshake](#101-system-handshake)
    - [10.2 Authentication](#102-authentication)
    - [10.3 Memory (Atoms)](#103-memory-atoms)
    - [10.4 Links](#104-links)
    - [10.5 Metadata](#105-metadata)
    - [10.6 Aliases](#106-aliases)
    - [10.7 Ontology Inspection](#107-ontology-inspection)
    - [10.8 Exploration](#108-exploration)
    - [10.9 Sets](#109-sets)
    - [10.10 Notes](#1010-notes)
    - [10.11 JCL — Job Control](#1011-jcl--job-control)
    - [10.12 Contexa](#1012-contexa--the-client-sessions-input-side)
    - [10.13 Jataka](#1013-jataka--the-client-sessions-output-side)
    - [10.14 Session](#1014-session)
    - [10.15 Associate](#1015-associate)
    - [10.16 Scope State](#1016-scope-state)
    - [10.17 Log](#1017-log)
    - [10.18 Whiteboard](#1018-whiteboard)
    - [10.19 Cross-Concept Intersection](#1019-cross-concept-intersection)
    - [10.20 Cockpit](#1020-cockpit) *(→ concept-model-spec.md §10.1)*
    - [10.21 Survey](#1021-survey) *(→ concept-model-spec.md §10.3)*
    - [10.22 Delegation & Donation Sets](#1022-delegation--donation-sets)
11. [JCL Security Blocklist](#11-jcl-security-blocklist)
12. [MCP Portal](#12-mcp-portal)
13. [Group Management API](#13-group-management-api)
14. [CLI Shorthand Reference](#14-cli-shorthand-reference)
15. [Web Application Development](#15-web-application-development)
    - [15.1 Architecture Overview](#151-architecture-overview)
    - [15.2 Adding a New Frontend-Only Application](#152-adding-a-new-frontend-only-application)
    - [15.3 Authentication Flow](#153-authentication-flow)
    - [15.4 Request Envelope](#154-request-envelope)
    - [15.5 Adding a Sub-Service with Custom Endpoints](#155-adding-a-sub-service-with-custom-endpoints)
    - [15.6 File Structure Reference](#156-file-structure-reference)
    - [15.7 Security Requirements](#157-security-requirements)

---

## 1. Overview

AKASHA is a local-first semantic memory substrate. Knowledge is stored as **atoms** — hashed content nodes — connected by typed, weighted **links**. The result is a living knowledge graph (the *cortex*) that can be explored, annotated, and extended programmatically.

All operations are exposed through a single JSON-RPC 2.0 interface. The same method names work identically across every transport (stdio REPL, HTTP server, MCP). The kernel never raises exceptions to callers; every response is a well-formed JSON-RPC object with either a `result` or an `error` field.

Key architectural concepts:

- **Atom** — the fundamental unit of memory. A SHA-256-keyed content node with optional metadata and scope labels.
- **Link** — a directed, typed, weighted edge between two atoms. Relation types follow a `namespace:name` convention (e.g., `sys:is_a`, `emo:joy`).
- **Scope** — a string tag attached to atoms that controls visibility (e.g., `view:user_alice`, `scope:sys:universal`).
- **Session** — a per-client anchor node that tracks context (last-written atom, active note, focus position).
- **Cortex** — the local SQLite-backed graph database for each client cell.

---

## 2. Transport Layer

### 2.1 stdio — Interactive REPL

Start the interactive shell with:

```bash
python akasha.py
```

The REPL accepts shorthand CLI commands (see [Section 14](#14-cli-shorthand-reference)) or raw JSON-RPC payloads. A background HTTP portal is also launched automatically unless `--stdio` is passed.

Options:

| Flag | Default | Description |
|---|---|---|
| `--stdio` | — | CLI only; skip web portal |
| `--server uvicorn` | `httpd` | Use FastAPI/uvicorn instead of stdlib httpd |
| `--host ADDR` | `127.0.0.1` | Bind address for the web portal |
| `--port N` | auto (8000+) | Port for the web portal |

Single-shot headless execution (exits after the command):

```bash
python akasha.py ping
python akasha.py w "The cat sat on the mat"
```

### 2.2 HTTP — REST/RPC via POST

**Endpoint:** `POST /rpc`  
**Content-Type:** `application/json`

Start in HTTP-only server mode:

```bash
python akasha.py --server uvicorn --host 0.0.0.0 --port 8080
```

Additional HTTP routes:

| Route | Method | Description |
|---|---|---|
| `GET /health` | GET | Liveness check (wraps `sys.ping`) |
| `POST /rpc` | POST | JSON-RPC 2.0 endpoint |
| `GET /docs` | GET | Swagger UI (uvicorn mode) |
| `GET /openapi.json` | GET | OpenAPI schema (uvicorn mode) |

The stdlib `httpd` engine accepts JSON-RPC at `POST /api/rpc`.

CORS headers (`Access-Control-Allow-Origin: *`) are set on all responses.

### 2.3 MCP — Model Context Protocol

The MCP portal (`api/portals/mcp.py`) exposes a subset of kernel operations as MCP tools for AI assistant integration (e.g., Claude Desktop). Transport wiring is pending the `mcp-python-sdk`. See [Section 12](#12-mcp-portal) for the full tool definitions.

---

## 3. Request and Response Envelope

### 3.1 Request

Every request must follow the JSON-RPC 2.0 envelope:

```json
{
  "jsonrpc": "2.0",
  "method": "kernel.memory.write",
  "params": {
    "session_token": "<client_id>",
    "data": {
      "text": "Hello, Akasha."
    }
  },
  "id": "req-001"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `jsonrpc` | string | Yes | Must be `"2.0"` |
| `method` | string | Yes | Dot-separated method name |
| `params.session_token` | string | Yes (post-auth) | Your `client_id` / session token |
| `params.data` | object | Yes | Method-specific parameters |
| `id` | string or number | Yes | Request correlation ID (any value; UUID recommended) |

### 3.2 Success Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "key": "a3f9...",
    "status": "written"
  },
  "id": "req-001"
}
```

### 3.3 Error Response

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "write requires 'text'"
  },
  "id": "req-001"
}
```

---

## 4. Authentication

### 4.1 Flow

```
Client                              Kernel
  |                                   |
  |-- kernel.auth.status -----------> |
  |<- {initialized, akasha_name} ---- |
  |                                   |
  |-- kernel.genesis_rite ----------> |  (first boot only)
  |<- {status: "bound"} ------------ |
  |                                   |
  |-- kernel.auth.verify -----------> |
  |<- {session_token, role} --------- |
  |                                   |
  |-- kernel.memory.write ----------> |  (session_token in every request)
  |<- {key, status} ----------------- |
```

### 4.2 Pre-authentication Methods

The following methods are accessible without a valid `session_token`:

- `sys.ping`
- `sys.status`
- `kernel.auth.status`
- `kernel.auth.verify`

`kernel.genesis_rite` is **local/internal-only** — it is not reachable over the network and cannot be used as a network pre-auth call.

#### Transport trust

Trust level is set by the **portal** that received the request, never by the client:

| Level | Set by | Meaning |
|---|---|---|
| `TRUST_NETWORK` | ASGI / web / CGI portals (default) | Safe default. A bare `client_id` is only ever an anonymous GUEST. |
| `TRUST_LOCAL` | Physical stdio console | OS process boundary is the gate; a bare `client_id` may be asserted. |
| `TRUST_INTERNAL` | Kernel-originated callers (JCL worker, boot loader) | A bare `client_id` may be asserted. |

Only `TRUST_LOCAL` and `TRUST_INTERNAL` may assert a bare `client_id`. Over `TRUST_NETWORK` a bare id is never an identity — it resolves to an anonymous GUEST.

### 4.3 Session Token

After `kernel.auth.verify` succeeds, the returned `session_token` is a **signed, expiring `akt:` credential** (HMAC-SHA256 over `client_id|role|expires|epoch|nonce`) that must be passed as `params.session_token` in every subsequent request. It is a credential, **not** your username and **not** equal to your `user_id`. It carries a TTL and expires; it is also revoked when the passphrase or role changes (a per-user token-epoch bump invalidates all outstanding tokens) or when `sys.session.close` is called.

### 4.4 First-boot Ceremony

On a fresh installation, `kernel.auth.status` returns `{"initialized": false}`. Call `kernel.genesis_rite` once to register the administrator identity. After that, passphrase verification is mandatory.

**Python example:**

```python
import requests

BASE = "http://localhost:8000/rpc"

def rpc(method, data=None, token="guest"):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": {"session_token": token, "data": data or {}},
        "id": "1"
    }
    return requests.post(BASE, json=payload).json()

# Check initialisation state
status = rpc("kernel.auth.status")
print(status["result"])  # {"initialized": false, "akasha_name": "AKASHA"}

# First-boot ceremony (run once)
rpc("kernel.genesis_rite", {
    "akasha_name": "MyAkasha",
    "user_name": "alice",
    "passphrase": "s3cr3t"
})

# Authenticate
auth = rpc("kernel.auth.verify", {"user_id": "alice", "passphrase": "s3cr3t"})
token = auth["result"]["session_token"]  # opaque signed credential, e.g. "akt:9f2c1a7e...c83"
role  = auth["result"]["role"]           # "admin"
```

**curl example:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","method":"kernel.auth.verify",
    "params":{"session_token":"guest","data":{"user_id":"alice","passphrase":"s3cr3t"}},
    "id":"auth-1"
  }'
```

---

## 5. Error Codes

| Code | Constant | Meaning |
|---|---|---|
| -32700 | Parse error | Body is not valid JSON |
| -32600 | Invalid request | JSON-RPC envelope malformed (missing `jsonrpc`, `method`, etc.) |
| -32601 | Method not found | The method string is not recognised by the kernel |
| -32602 | Invalid params | Required field missing or wrong type in `data` |
| -32001 | Permission denied | IAM check failed: wrong role, insufficient capability, or quota exceeded |
| -32002 | Resource not found | Atom key, alias, or job ID does not exist (or is out of scope) |
| -32003 | Permission denied | Caller lacks the required role or scope for this specific operation |
| -32000 | Internal kernel error | Unhandled exception in the cognitive engine |

When an error object is returned, `result` is absent. The `error.data` field may contain additional context in some cases.

---

## 6. Context References (id Parameters)

Any parameter named `id` (atom key) in a method's `data` block supports **context references** — symbolic shortcuts resolved at dispatch time against the active session state and graph.

| Syntax | Resolves to |
|---|---|
| `$it` | The atom last explicitly written by the client (`session.last_written_id`) |
| `$0` | The most recent user-authored atom in session history |
| `$1`, `$2`, `$N` | Older history entries (0 = newest) |
| `$0:5` | Returns a list of the first 5 history keys (slice syntax) |
| `set:name` | Expands to the full list of member keys in the named set |
| `alias_name` | Resolved via the alias registry (e.g., `"Philosophy"`, `"emo:joy"`) |
| `@here` | Atom pinned to the current GPS position (Jataka spatial context) |
| `@now` | Atom pinned to the current temporal anchor |
| `@2026` | Year-era anchor (`chrono:year:2026`) |
| `alias.child` | All atoms linked outward from the resolved alias |
| `alias.parent` | All atoms linked inward to the resolved alias |
| `~emo:sadness` | Closest-match tensor search (semantic gravity; planned) |
| 64-char hex | Direct key lookup; bypasses the resolver |

Context references are resolved by `lib/akasha/resolver.py:ContextResolver`. They respect the caller's IAM scopes: atoms out of scope are silently excluded from list results.

---

## 7. IAM — Roles, Capabilities, and Scopes

### 7.1 Roles

| Role | Value | Description |
|---|---|---|
| `ADMIN` | `"admin"` | Full system access including DNA memory and all sessions |
| `LIBRARIAN` | `"librarian"` | Collective knowledge editor; cannot access other users' private atoms |
| `GROUP_ADMIN` | `"group_admin"` | Manages one group; can write group shared knowledge |
| `USER` | `"user"` | Standard authenticated client; private scope + assigned group scopes |
| `GUEST` | `"guest"` | Unauthenticated; read-only access to public collective knowledge |

### 7.2 Capabilities

| Capability | Granted to | Governs |
|---|---|---|
| `READ` | All | `explore`, `read`, `link.list`, `dive.*`, `sys.history` |
| `WRITE` | USER and above | `write`, `define`, `link.create`, `meta.set`, `note.*`, `alias` |
| `DELETE` | USER and above | `drop`, `set.clear`, `set.rm` |
| `COLLECTIVE_WRITE` | LIBRARIAN, ADMIN | Writing to `scope:sys:universal` |
| `GROUP_MANAGE` | GROUP_ADMIN, ADMIN | Adding/removing members, granting group librarian rights |
| `SIMULATE` | USER and above | `jataka.dream`, `link.reinforce` |
| `SYNC_PULL` / `SYNC_PUSH` | LIBRARIAN, ADMIN | Network synchronisation |
| `FEDERATE` | LIBRARIAN, ADMIN | Knowledge verification and merge |
| `DELEGATE` | ADMIN | Issuing tokens; cancelling others' JCL jobs |
| `iam.manage` | ADMIN | All user management: `user.add`, `user.ls`, `user.mod`, `user.passwd`, `user.rm` |
| `TELEMETRY` | ADMIN | Swarm intelligence telemetry |

### 7.3 Scope Taxonomy

> **Full specification:** [`docs/scope-dimension-model.md`](scope-dimension-model.md)

Scope tags are `namespace:value` strings attached to atoms. They belong to one
of four distinct dimensions. **Mixing dimensions in a single SQL query is a
security invariant violation.**

| Dimension | Prefixes | Storage | Evaluated by |
|---|---|---|---|
| **Dim-1 — Access control** | `scope:`, `owner:`, `view:` | `chunk_access` table | `check_chunk_access_any()` |
| **Dim-2 — Capability flags** | `role:`, `write:`, `manage:` | Session only | `authorize()` |
| **Dim-3 — Locale preference** | `lang:XX` (session) | `session.locale` | `list_leaf(locale_codes=...)` |
| **Calc-Dim — Semantic dimensions** | `leaf:`, `ns:`, `lang:XX` (atom), user sets | `collections` table | set-theory queries |

**Dim-1 access scopes (quick reference):**

| Scope tag | Who can read |
|---|---|
| `scope:sys:universal` | Everyone |
| `scope:sys:dna` | ADMIN only |
| `view:public` | Everyone (including GUEST) |
| `owner:user_<id>` | ADMIN + `<id>` |
| `view:user_<id>` | ADMIN + `<id>` |
| `scope:group_<g>` / `view:group_<g>` | Group members + GROUP_ADMIN + ADMIN |
| `view:admin_override` | ADMIN |

Every authenticated session's scope list is computed once at session creation by
`IdentityManager.get_allowed_scopes()` and cached in `session.active_scopes`.
Locale preference (`lang:en` etc.) lives separately in `session.locale` and is
**never** included in access-control SQL queries.

### 7.4 Quota Limits

| Role | Max explore depth | Max nodes |
|---|---|---|
| GUEST | 2 | 50 |
| USER | 10 | 1 000 |
| GROUP_ADMIN | 15 | 2 000 |
| LIBRARIAN | 20 | 5 000 |
| ADMIN | 99 | 9 999 |

Exceeding the depth quota raises error `-32001` with the message `"Quota exceeded: depth N > M"`.

---

## 8. Ontology Architecture

AKASHA's knowledge base has two tiers of foundational knowledge that are loaded automatically at startup.

### 8.1 Innate DNA (Tier 1)

Defined in `lib/akasha/dna.py:get_primal_sequence()`. These atoms are bootstrapped into `scope:sys:universal` before any user session exists. They encode the kernel's "birth state" — the minimum cognitive framework needed to reason about any domain:

| Namespace | Content |
|---|---|
| `sys:` | Topology relations: `sys:is_a`, `sys:part_of`, `sys:associated_with`, `sys:requires`, `sys:causes`, `sys:mapped_to`, `sys:mapped_from` |
| `log:` | Fuzzy logic operators: `log:not`, `log:and`, `log:or`, `log:implies`, `log:iff` |
| `geo:` | Spatiotemporal axes: `geo:at` (GPS pin), `geo:ref` (affine reference) |
| `chrono:` | `chrono:period` (temporal era pin) |
| `nar:` | `nar:perspective` (cognitive narrative filter) |
| `emo:` | 8 primary Plutchik/Keltner emotions + 7 compound emotions (awe, nostalgia, love, guilt, curiosity, despair, contempt) |
| `frame:` | Epistemological frames: dialectics (thesis/antithesis/synthesis), systems (feedback loop) |

DNA atoms are tagged `scope:sys:dna` in addition to `scope:sys:universal`. Only ADMIN can read the `scope:sys:dna` tag directly; however, all users can access the content through `scope:sys:universal`.

### 8.2 Acquired Ontology Files (Tier 2)

Ontology ships as `.ak` files organised into per-namespace **package directories** under `ontology/<ns>/` (e.g. `ontology/base1–3/` (the base packs), `ontology/art/`, `ontology/film/`), each with a `PACK.json` manifest. `ontology/REGISTRY.json` (version 2) lists every package and its `autoload` flag (`base1`, `base2`, `base3`, `nutrition`, `recipe`, and `curation` autoload at startup). The obsolete flat JSON `.ak` format loaded by `bootstrap_ontology()` is no longer used.

An `.ak` file is a flat sequence of loader commands, not JSON. The full command vocabulary is:

| Command | Purpose |
|---|---|
| `def "id" "description"` | Define an atom |
| `ln src dst rel` | Create a typed link |
| `al atom_id alias` | Register an alias |
| `set.add name="..." id="..."` | Add an atom to a named collection |
| `# comment` | Comment — ignored by the loader |

```
def "emo:joy" "Primary Emotion: Happiness, expansion, and presence."
def "emo:sadness" "Primary Emotion: Melancholy, contraction, and memory."
ln emo:joy emo:sadness log:not
al emo:joy joy
```

An `.ak` file is loaded via the shell command `run <file>`, which submits a JCL job to apply the steps. All bootstrapped concepts are pinned to `scope:sys:universal` and `view:public`. Atoms are content-addressed, so reloading a file that overlaps existing content is idempotent — duplicates are silently unified and existing aliases are never overwritten.

---

## 9. Harmonia Workspace and Rollback Model

**Harmonia** (`lib/harmonia/engine.py:HarmoniaEngine`) is the transactional motor cortex. Every operation that produces new atoms — whether triggered by Contexa NLP mapping, a Jataka dream cycle, or a JCL job — runs inside a Harmonia *workspace*.

### 9.1 Workspace Lifecycle

```
begin_workspace(cortex, label)
  → tx_id = "ws:<label>:<timestamp>"
  → writes sys:workspace_info atom to cortex

execute_with_evidence(cortex, tx_id, executor, data)
  → writes sys:action_evidence atom (audit trail)
  → runs the plugin function
  → each output is stored as a "pending" atom tagged with tx_id
  → the atom key is added to the tx_id set in the DB

commit_workspace(cortex, tx_id)
  → for each pending atom in set tx_id:
      - sets status = "active", removes tx_id binding
      - overwrites the chunk with status = "verified"
  → workspace is marked "committed"

rollback_workspace(cortex, tx_id)
  → for each pending atom in set tx_id:
      - physically deletes the chunk from the DB
  → workspace is marked "rolled_back"
  → evidence atoms (sys:action_evidence, sys:workspace_info) are retained
```

### 9.2 JCL Integration

JCL jobs (see [Section 10.11](#1011-jcl--job-control)) run each job as a single Harmonia workspace. If any step fails:

1. The workspace is rolled back — no orphaned atoms remain.
2. A `sys:jcl_failure_log` atom is written permanently so `job.log` can surface it.
3. Evidence atoms from completed steps survive rollback (audit trail is preserved).

### 9.3 Plugin Registry

Plugins are registered with `harmonia.register_plugin(name, callable)`. At boot, the kernel registers:

| Plugin name | Purpose |
|---|---|
| `nlp.extract` | Multi-locale SpaCy-based trait extraction (`lib/harmonia/plugins/nlp.py`). Auto-installs SpaCy via Symbiosis on first use. Degrades gracefully to regex (T1) or CJK bigrams (T0) when no model is available. |

---

## 10. Method Reference

### 10.1 System Handshake

---

#### `sys.ping`

Consciousness liveness check. No authentication required.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "sys.ping",
  "params": {"session_token": "guest", "data": {}},
  "id": "1"
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "kernel_online",
    "series": "seeds",
    "timestamp": 1716600000.123
  },
  "id": "1"
}
```

When called with a valid authenticated `session_token`, the full `ConsciousnessEngine.ping()` state is returned (includes active context, session metadata).

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"sys.ping","params":{"session_token":"guest","data":{}},"id":"1"}'
```

---

#### `sys.status`

Returns kernel subsystem availability. No authentication required.

**Response schema:**

```json
{
  "result": {
    "status": "online",
    "series": "seeds",
    "harmonia": true,
    "contexa": true,
    "active_sessions": 2,
    "timestamp": 1716600000.0
  }
}
```

---

#### `sys.cogito`

Full self-awareness pulse for the authenticated session. Returns rich session state from `ConsciousnessEngine.cogito()`.

**Requires:** Authentication.

**Python:**

```python
resp = rpc("sys.cogito", token=token)
print(resp["result"])
```

---

### 10.2 Authentication

---

#### `kernel.genesis_rite`

First-boot ceremony. Must be called exactly once to register the system administrator. After this call, passphrase authentication is enforced for all subsequent sessions.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `akasha_name` | string | No | Name for this AKASHA instance (default: `"AKASHA"`) |
| `user_name` | string | Yes | Administrator identity (client_id) |
| `passphrase` | string | Yes | Administrator passphrase. The client presents a SHA-256 hash; the server stores a **per-user-salted PBKDF2 derivation** of it and compares with `hmac.compare_digest`. |

**Response:**

```json
{
  "result": {
    "status": "bound",
    "akasha_name": "MyAkasha",
    "admin_name": "alice"
  }
}
```

**Errors:**

| Code | Condition |
|---|---|
| -32602 | `user_name` or `passphrase` missing |

---

#### `kernel.auth.status`

Returns initialisation state. No authentication required. The response contains only `initialized` and `akasha_name`; the administrator username is a login identifier and is withheld pre-authentication.

**Response:**

```json
{
  "result": {
    "initialized": true,
    "akasha_name": "MyAkasha"
  }
}
```

---

#### `kernel.auth.verify`

Verify credentials and obtain a session token.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `user_id` | string | Yes |
| `passphrase` | string | Yes |

**Response:**

```json
{
  "result": {
    "status": "authenticated",
    "user_id": "alice",
    "session_token": "akt:9f2c1a7e...c83",
    "role": "admin"
  }
}
```

**Errors:**

| Code | Condition |
|---|---|
| -32001 | Invalid credentials or unknown user |
| -32602 | `user_id` or `passphrase` missing |

**Python:**

```python
auth = rpc("kernel.auth.verify", {"user_id": "alice", "passphrase": "s3cr3t"})
token = auth["result"]["session_token"]
```

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"kernel.auth.verify",
       "params":{"session_token":"guest","data":{"user_id":"alice","passphrase":"s3cr3t"}},
       "id":"auth"}'
```

---

### 10.3 Memory (Atoms)

---

#### `kernel.memory.write`

Write a new atom (memory node) to the cortex.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Content to store |
| `meta` | object | No | Arbitrary metadata dict attached to the atom |
| `public` | boolean | No | If `true`, adds `view:public` scope (default: false) |
| `scope` | string | No | Write destination. `"universal"` routes the atom to the shared nucleus DB (visible to all users). Requires `LIBRARIAN` or `ADMIN` role. Omit for private writes to the local cell. |
| `alias` | string | No | Alias to register for the atom when `scope="universal"`. Ignored for private writes. |

**Two write modes:**

| Mode | `scope` value | Destination | Visibility | Required role |
|---|---|---|---|---|
| **Private** | omitted | Local cell DB | Owner only | USER and above |
| **Universal** | `"universal"` | Nucleus DB | All users | LIBRARIAN, ADMIN |

**Response:**

```json
{
  "result": {
    "key": "a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "status": "written"
  }
}
```

The returned `key` is a 64-character hexadecimal SHA-256 digest of the content. Akasha also sets `session.last_written_id` to this key, making it immediately accessible as `$it`.

After writing, the text is asynchronously processed by the unified post-write Weaver pipeline: protoword links are woven and NLP word decomposition is queued as a `sys.weaver.decompose` JCL job (non-fatal; the write succeeds regardless).

**Errors:**

| Code | Condition |
|---|---|
| -32602 | `text` is empty or missing |

**Python:**

```python
resp = rpc("kernel.memory.write", {"text": "The basilica of San Vitale dates from 547 AD."}, token=token)
key = resp["result"]["key"]
```

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"kernel.memory.write\",
       \"params\":{\"session_token\":\"alice\",\"data\":{\"text\":\"The basilica of San Vitale dates from 547 AD.\"}},
       \"id\":\"w1\"}"
```

---

#### `kernel.memory.define`

Create a named **concept hub** — a special atom that serves as a named anchor for semantic clustering. Automatically assigns the `name` as an alias to the new atom.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Human-readable name (becomes the alias) |
| `description` | string | No | Optional description text |

**Response:**

```json
{
  "result": {
    "key": "b4c5...",
    "alias": "Byzantine Architecture",
    "status": "defined"
  }
}
```

The hub atom's content is formatted as `[Byzantine_Architecture]\n<description>` and tagged `type: hub`.

**Python:**

```python
resp = rpc("kernel.memory.define",
           {"name": "Byzantine Architecture", "description": "Architectural tradition 330–1453 AD"},
           token=token)
hub_alias = resp["result"]["alias"]
```

---

#### `kernel.memory.read`

Read an atom by key, alias, or context reference.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | No | Key, alias, or `$`-reference. Defaults to `$it` (last written). |

**Response:**

```json
{
  "result": {
    "key": "a3f9...",
    "content": "The basilica of San Vitale dates from 547 AD.",
    "meta": {"type": "hub", "name": "Byzantine Architecture"},
    "aliases": ["Byzantine Architecture", "byz-arch"]
  }
}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | Atom not found or out of caller's scope |
| -32602 | No `id` and no active session context |

**Python:**

```python
# By alias
resp = rpc("kernel.memory.read", {"id": "Byzantine Architecture"}, token=token)

# By $-reference
resp = rpc("kernel.memory.read", {"id": "$it"}, token=token)

# By direct key
resp = rpc("kernel.memory.read", {"id": "a3f9b2c1..."}, token=token)
```

---

#### `kernel.memory.drop`

Delete an atom and all its associated aliases, links, and collection memberships.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `id` | string | Yes |

**Response:**

```json
{
  "result": {"status": "dropped", "key": "a3f9..."}
}
```

**Errors:**

| Code | Condition |
|---|---|
| -32001 | Atom is out of the caller's write scope |
| -32002 | Atom not found |

---

### 10.4 Links

---

#### `kernel.memory.link`

Create a directed, typed, weighted link between two atoms.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `src` | string | Yes | Source atom (key, alias, or `$`-ref) |
| `dst` | string | Yes | Destination atom (key, alias, or `$`-ref) |
| `rel` | string | Yes | Relation type. If no namespace prefix (`:`) is present, `@` is prepended automatically. |
| `w` | number | No | Link weight `0.0`–`1.0` (default: `1.0`) |

**Response:**

```json
{
  "result": {
    "status": "linked",
    "src": "a3f9...",
    "dst": "b4c5...",
    "rel": "sys:is_a",
    "w": 1.0
  }
}
```

**Python:**

```python
rpc("kernel.memory.link", {
    "src": "$it",
    "dst": "Byzantine Architecture",
    "rel": "sys:is_a",
    "w": 0.95
}, token=token)
```

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"kernel.memory.link",
       "params":{"session_token":"alice",
                 "data":{"src":"$it","dst":"Byzantine Architecture","rel":"sys:is_a","w":0.95}},
       "id":"ln1"}'
```

---

#### `link.list`

List all links (inbound and outbound) for an atom.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | No | Target atom. Defaults to `$it`. |

**Response:**

```json
{
  "result": {
    "key": "a3f9...",
    "links": [
      {
        "direction": "out",
        "rel": "sys:is_a",
        "key": "b4c5...",
        "preview": "Byzantine Architecture..."
      },
      {
        "direction": "in",
        "rel": "sys:associated_with",
        "key": "c5d6...",
        "preview": "Ravenna mosaics..."
      }
    ]
  }
}
```

Each entry in `links`:

| Field | Type | Description |
|---|---|---|
| `direction` | `"out"` or `"in"` | Whether the link points away from or toward the focal atom |
| `rel` | string | Relation type |
| `key` | string | The other atom's key |
| `preview` | string | First 60 characters of the other atom's content |

---

#### `link.reinforce`

Increase the weight of an existing link by a delta.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `src` | string | Yes | Source atom |
| `dst` | string | Yes | Destination atom |
| `rel` | string | Yes | Relation type |
| `delta` | number | No | Weight increment (default: `0.1`) |

**Response:**

```json
{
  "result": {
    "status": "reinforced",
    "src": "a3f9...",
    "dst": "b4c5...",
    "rel": "sys:is_a",
    "w": 1.1
  }
}
```

---

### 10.5 Metadata

---

#### `meta.set`

Set or update a single metadata key on an existing atom.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `id` | string | Yes |
| `key` | string | Yes |
| `value` | any | Yes |

**Response:**

```json
{
  "result": {"status": "meta_updated", "key": "a3f9..."}
}
```

**Python:**

```python
rpc("meta.set", {"id": "$it", "key": "source", "value": "UNESCO World Heritage"}, token=token)
```

---

### 10.6 Aliases

---

#### `kernel.identity.alias`

Assign a human-readable alias to an atom. An atom may have multiple aliases; an alias points to exactly one key.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `id` | string | Yes |
| `name` | string | Yes |

**Response:**

```json
{
  "result": {"status": "alias_set", "alias": "San Vitale", "key": "a3f9..."}
}
```

---

#### `kernel.identity.alias.list`

Return all aliases registered in the cortex.

**Params (`data`):** _(none)_

**Response:**

```json
{
  "result": {
    "aliases": [
      {"alias": "Byzantine Architecture", "key": "b4c5..."},
      {"alias": "San Vitale", "key": "a3f9..."}
    ]
  }
}
```

---

#### `kernel.identity.alias.find`

Search aliases by SQL `LIKE` pattern.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `pattern` | string | Yes | SQL LIKE pattern (e.g., `"emo:%"`, `"%arch%"`) |

**Response:**

```json
{
  "result": {
    "aliases": [
      {"alias": "emo:awe", "key": "c5d6..."},
      {"alias": "emo:joy", "key": "d6e7..."}
    ]
  }
}
```

**Python:**

```python
resp = rpc("kernel.identity.alias.find", {"pattern": "emo:%"}, token=token)
for a in resp["result"]["aliases"]:
    print(a["alias"], "→", a["key"][:12])
```

---

### 10.7 Ontology Inspection

Commands for inspecting the live ontology graph and diagnosing alias collisions.
Typically used during ontology development and after loading new files.

---

#### `onto.dump`

Multi-angle dump of ontology data. Supports six modes selectable via the `mode`
parameter. All modes support `sort` and `limit`; additional parameters apply
per mode.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `mode` | string | No | `atoms` (default) \| `links` \| `antonyms` \| `aliases` \| `sets` \| `namespaces` |
| `ns` | string | No | Namespace prefix filter, e.g. `"word:en"`. Applied in `atoms` and `aliases` modes. |
| `rel` | string | No | Relation type filter for `links` mode, e.g. `"sys:antonym"`. |
| `collection` | string | No | Collection name for `sets` mode, e.g. `"ontology.narrative_typology"`. |
| `sort` | string | No | `alpha` (default) \| `count` \| `recent` |
| `limit` | integer | No | Max items returned. Default 500, max 5000. |
| `pattern` | string | No | SQL `LIKE` pattern for `aliases` mode. Overrides `ns`. |

**Mode details:**

| Mode | Returns | Typical use |
|---|---|---|
| `atoms` | One entry per distinct atom: primary alias + content preview | Verify all terms loaded |
| `links` | All semantic links: src / rel / dst / weight | Check link integrity |
| `antonyms` | Shortcut: links where `rel=sys:antonym` | Audit antonym pair symmetry |
| `aliases` | All registered aliases with their keys | Find namespace collisions |
| `sets` | Members of a named collection | Inspect hub membership |
| `namespaces` | Atom count per namespace prefix | Check namespace balance |

**Response (example — `atoms` mode):**

```json
{
  "result": {
    "mode": "atoms",
    "count": 42,
    "items": [
      {"alias": "word:en:courage", "key": "a3f7c2...", "preview": "Word: courage. The ability to do something that..."},
      {"alias": "word:en:fear",    "key": "b8c1d5...", "preview": "Word: fear. An unpleasant emotion caused by..."}
    ]
  }
}
```

**Response (example — `namespaces` mode):**

```json
{
  "result": {
    "mode": "namespaces",
    "count": 12,
    "items": [
      {"ns": "word", "count": 823},
      {"ns": "sys",  "count": 79},
      {"ns": "nar",  "count": 42}
    ]
  }
}
```

**Python:**

```python
# Dump all English vocabulary atoms
resp = rpc("onto.dump", {"mode": "atoms", "ns": "word:en", "limit": 100}, token=token)
for item in resp["result"]["items"]:
    print(item["alias"], "—", item["preview"][:60])

# Check antonym pairs
resp = rpc("onto.dump", {"mode": "antonyms"}, token=token)
for link in resp["result"]["items"]:
    print(f"{link['src']} ↔ {link['dst']}")

# Namespace overview
resp = rpc("onto.dump", {"mode": "namespaces"}, token=token)
for ns in resp["result"]["items"]:
    print(f"  {ns['ns']:20s} {ns['count']:4d} atoms")
```

---

#### `onto.report`

Returns the alias collision log accumulated since the last call with `clear=true`
(or since server start). Printed automatically at login when the log is non-empty.

Two collision event types:

| Event | Meaning | Action |
|---|---|---|
| `overwrite` | Canonical alias (`word:en:X`) rebound to a different atom | **Bug** — remove duplicate definition from later-loading file |
| `leaf_skipped` | Bare alias (`X`) already claimed; new registration skipped | **Normal** — first-registered wins; no action needed |

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `since` | number | No | If provided, return only entries recorded after this epoch timestamp |
| `limit` | integer | No | Maximum number of entries to return |
| `clear` | boolean | No | If `true`, return the log and immediately clear it (default: `false`) |

**Response:**

```json
{
  "result": {
    "overwrites": 1,
    "leaf_skips": 2,
    "entries": [
      {"event": "overwrite",    "alias": "word:en:comedy", "winner": "a3f7c2...", "loser": "88ca29..."},
      {"event": "leaf_skipped", "alias": "comedy",         "winner": "88ca29...", "loser": "a3f7c2..."},
      {"event": "leaf_skipped", "alias": "rival",          "winner": "c5d8e1...", "loser": "f2a091..."}
    ]
  }
}
```

**Python:**

```python
resp = rpc("onto.report", {"clear": True}, token=token)
r = resp["result"]
print(f"Overwrites: {r['overwrites']}  Leaf skips: {r['leaf_skips']}")
for e in r["entries"]:
    if e["event"] == "overwrite":
        print(f"  ⚠ OVERWRITE '{e['alias']}'  {e['loser'][:8]}→{e['winner'][:8]}")
```

---

### 10.8 Exploration

---

#### `explore`

Breadth-first graph traversal from a focal atom.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Starting atom |
| `depth` | integer | No | BFS depth (default: 2, role-capped) |
| `rel` | string | No | Filter traversal to links matching this relation pattern (SQL LIKE) |

**Response:**

```json
{
  "result": {
    "focus": "a3f9...",
    "nodes": [
      {"key": "a3f9...", "content": "The basilica...", "depth": 0},
      {"key": "b4c5...", "content": "Byzantine Architecture...", "depth": 1}
    ],
    "count": 2
  }
}
```

**Python:**

```python
resp = rpc("explore", {"id": "Byzantine Architecture", "depth": 3}, token=token)
for node in resp["result"]["nodes"]:
    print(f"  depth={node['depth']} {node['key'][:12]} — {node['content'][:50]}")
```

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"explore",
       "params":{"session_token":"alice","data":{"id":"Byzantine Architecture","depth":3}},
       "id":"exp1"}'
```

---

#### `sys.tree`

Render a hierarchical link-tree from a root node, following outgoing links recursively.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | No | Root atom. Defaults to `$it`. |
| `depth` | integer | No | Max recursion depth (default: 3, max: 8) |

**Response:**

```json
{
  "result": {
    "root": "b4c5...",
    "max_depth": 3,
    "tree": {
      "key": "b4c5...",
      "preview": "Byzantine Architecture",
      "depth": 0,
      "children": [
        {
          "key": "a3f9...",
          "preview": "The basilica of San Vitale...",
          "depth": 1,
          "rel": "sys:is_a",
          "children": []
        }
      ]
    }
  }
}
```

Each `node` in the tree:

| Field | Type |
|---|---|
| `key` | string |
| `preview` | string (first 70 chars of content) |
| `depth` | integer |
| `rel` | string (relation label on the edge to this node; absent on root) |
| `children` | array of nodes |

---

#### `dive.look`

Focused single-atom view: returns the atom's content, N-D Cosmos coordinates, and a rich list of signpost links for navigation.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | No | Atom to focus on. Defaults to the session's current focus. |
| `time` | string | No | Temporal filter tag attached to the response as `active_time` metadata (display hint for UI; does not filter graph content). |

**Response:**

```json
{
  "result": {
    "type": "atom",
    "focus": {
      "key": "a3f9...",
      "alias": "San Vitale",
      "content": "The basilica of San Vitale dates from 547 AD.",
      "meta": "{\"type\": \"hub\"}",
      "cosmos_nd": [0.5, 0.2, 0.8, 0.1, 0, "#a0c4ff"]
    },
    "signposts": [
      {
        "index": 0,
        "key": "b4c5...",
        "alias": "Byzantine Architecture",
        "rel": "sys:is_a",
        "direction": "out",
        "w": 1.0,
        "type": "explicit",
        "preview": "Byzantine Architecture...",
        "branches_ahead": 3,
        "cosmos_nd": [0.4, 0.3, 0.9, 0.2, 1, "#00ffcc"]
      }
    ]
  }
}
```

**`focus` fields:**

| Field | Type | Description |
|---|---|---|
| `key` | string | 64-char SHA-256 hex key |
| `alias` | string \| null | Primary alias if any |
| `content` | string | Full atom content |
| `meta` | string | JSON-encoded metadata |
| `cosmos_nd` | array | 6-element vector `[x, y, z, T, layer, color]` for the Cosmos Viewer. **X/Y/Z are the real semantic position** — a projection of the atom's self-owned `semantic_vector` (near in space ⇒ near in meaning; when a learned model exists it projects onto that model's principal SVD axes, else a distance-preserving random projection). `T` is reserved for the chrono axis (0 until the time layer feeds it), `layer` is the BFS depth from the focus, `color` is the emotion/sense aura hex. |

**Signpost fields:**

| Field | Type | Description |
|---|---|---|
| `index` | integer | Position in the signpost list |
| `key` | string | Neighbor atom key |
| `alias` | string \| null | Neighbor's primary alias |
| `rel` | string | Link relation type |
| `direction` | `"out"` \| `"in"` | Link direction relative to the focal atom |
| `w` | number | Link weight `0.0`–`1.0` |
| `type` | `"explicit"` \| `"magnetic"` | Whether the link was user-defined or inferred |
| `preview` | string | First ~30 chars of neighbor content |
| `branches_ahead` | integer | Number of further links on the neighbor atom |
| `cosmos_nd` | array | 6-element `[x, y, z, T, layer, color]` vector for the neighbor (see focus `cosmos_nd`). |

> **Cosmos graph payload.** `dive.look` also returns a `cosmos` object (`{nodes, links, axis}`)
> for the 3-D viewer. Each node carries the real semantic position (`x`/`y`/`z`, scaled to
> force-graph units — a front-end can seed layout from them so proximity means similarity), a
> degree-based size (`val`), and the emotion/sense aura `color`. See
> `docs/developer/cosmos-frontend-requirements.md`.

The signpost list is assembled by `ConsciousnessEngine.generate_view()`. It merges explicit links from the local cell DB with cross-store atoms (nucleus, group spaces) that the caller's IAM scopes allow.

Calling `dive.look` updates `session.focus` to the resolved atom. When a collection name is passed as `id`, a **collection view** is returned (`type: "collection"`) listing all members as signposts.

---

#### `dive.out`

Zoom out to a macro-level view centered on the current (or specified) atom. Returns a broader neighbourhood summary.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `id` | string | No |

---

### 10.9 Sets

Sets are named collections of atom keys. They serve dual purpose: as user-facing grouping tools and as the underlying mechanism for IAM scope resolution.

---

#### `set.add`

Add an atom to a named set.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `name` | string | Yes |
| `id` | string | Yes |

**Response:**

```json
{"result": {"status": "added", "set": "my_reading_list", "key": "a3f9..."}}
```

---

#### `set.rm`

Remove an atom from a set.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `name` | string | Yes |
| `id` | string | Yes |

**Response:**

```json
{"result": {"status": "removed", "set": "my_reading_list", "key": "a3f9..."}}
```

---

#### `set.ls`

List all members of a set (scoped to the caller's visible atoms).

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `name` | string | Yes |

**Response:**

```json
{
  "result": {
    "set": "my_reading_list",
    "members": [
      {"key": "a3f9...", "content": "The basilica...", "meta": {}}
    ],
    "count": 1
  }
}
```

---

#### `set.clear`

Remove all members from a set (does not delete the atoms themselves).

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `name` | string | Yes |

**Response:**

```json
{"result": {"status": "cleared", "set": "my_reading_list"}}
```

---

#### `set.op`

Perform a set-algebra operation, storing the result in a new named set.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `op` | string | Yes | `"union"`, `"isect"` (intersection), or `"diff"` (difference) |
| `result` | string | Yes | Name of the output set |
| `a` | string | Yes | First operand set name |
| `b` | string | Yes | Second operand set name |

**Response:**

```json
{
  "result": {
    "result_set": "overlap",
    "members": [{"key": "a3f9...", "content": "..."}]
  }
}
```

**Python:**

```python
# Find atoms in both "ravenna_sites" AND "byzantine_art"
rpc("set.op", {"op": "isect", "result": "overlap", "a": "ravenna_sites", "b": "byzantine_art"}, token=token)
```

---

### 10.10 Notes

Notes are hierarchical document structures built on top of atoms. `note.new` creates a root atom (stored in session as `active_note_root`); subsequent calls build the document's dual topology — a horizontal timeline of chunks and a vertical hierarchy of sections, chapters, and paragraphs.

The editing layer (M1) adds non-destructive revision, reordering, undo/redo, and rename. It operates on a **two-namespace design**:

- **Input layer** (`sys:top/next`): the immutable write-order timeline — never touched after creation.
- **Edit layer** (`edit:top/next`, `note:current`): reorderable display layer; absent means fall back to input order. `note:current` resolves an anchor's current content version.

All edits are recorded in `note:edit_journal` (a JSON atom) that drives undo/redo as a cursor over a history list.

---

#### `note.new`

Create a new note/document.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `title` | string | Yes |

**Response:**

```json
{"result": {"status": "initialized", "note_id": "e7f8..."}}
```

The new note is set as the session's `active_note_root`.

---

#### `note.add`

Append a paragraph atom to the active note.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `text` | string | Yes |

**Response:**

```json
{"result": {"node_id": "f8a9...", "status": "added"}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. Call `note.new` first. |

**Python:**

```python
rpc("note.new", {"title": "Field Notes — Ravenna 2026"}, token=token)
rpc("note.add", {"text": "Morning visit to San Vitale. Mosaics in excellent condition."}, token=token)
rpc("note.add", {"text": "Afternoon: Galla Placidia mausoleum. Notable sarcophagi."}, token=token)
```

---

#### `note.section`

Add a section (or chapter) to the active note. Creates a container atom in the hierarchy and appends it to the timeline.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Section heading text |
| `role` | string | No | Structural role label (default: `"section"`; use `"chapter"` for top-level chapters) |

**Response:**

```json
{"result": {"node_id": "a1b2...", "title": "Morning Observations", "role": "section", "status": "added"}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. Call `note.new` first. |

---

#### `note.paragraph`

Add a paragraph container to the active note. The paragraph becomes the `active_container_id` in session; subsequent `note.add` calls deposit chunks inside it.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `category` | string | No | Paragraph category label (default: `"body"`) |

**Response:**

```json
{"result": {"node_id": "b2c3...", "category": "body", "status": "added"}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |

---

#### `note.toc`

Return the table of contents for the active note — all section/chapter/paragraph container atoms with their titles and hierarchy depth.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"toc": [
  {"node_id": "a1b2...", "title": "Morning Observations", "role": "section", "depth": 1},
  {"node_id": "c3d4...", "title": "Afternoon", "role": "section", "depth": 1}
]}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |

---

#### `note.read`

Read the active note as sequential text — all content chunks in timeline order.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": [
  {"id": "f8a9...", "role": "chunk", "content": "Morning visit to San Vitale. Mosaics in excellent condition.", "category": "body"},
  {"id": "g9b0...", "role": "chunk", "content": "Afternoon: Galla Placidia mausoleum. Notable sarcophagi.", "category": "body"}
]}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |

---

#### `note.rm`

Delete the active note (root atom) and clear `active_note_root` from session. Child atoms remain in the graph; only the root and its direct index links are removed.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"status": "deleted", "note_id": "e7f8..."}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |
| -32003 | Insufficient privileges to delete this atom. |

**Python (full lifecycle example):**

```python
rpc("note.new",     {"title": "Field Notes — Ravenna 2026"}, token=token)
rpc("note.section", {"title": "Morning", "role": "section"}, token=token)
rpc("note.paragraph", {"category": "body"},                  token=token)  # note.para is CLI shorthand only
rpc("note.add",     {"text": "San Vitale. Mosaics intact."}, token=token)
rpc("note.section", {"title": "Afternoon"},                  token=token)
rpc("note.add",     {"text": "Galla Placidia mausoleum."},   token=token)
toc = rpc("note.toc",  {}, token=token)
txt = rpc("note.read", {}, token=token)
rpc("note.rm", {}, token=token)
```

---

#### `note.list`

List all content chunks in the active note, in current display order (edit layer if active, otherwise input order). Returns a head preview of each chunk.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"chunks": [
  {"id": "a1b2...", "version": "c3d4...", "head": "San Vitale. Mosaics intact.", "role": "chunk", "order": 0},
  {"id": "e5f6...", "version": "e5f6...", "head": "Galla Placidia mausoleum.", "role": "chunk", "order": 1}
], "count": 2}}
```

`id` is the stable anchor id (never changes). `version` is the current content atom (changes on edit). `head` is the first line, truncated to 80 characters.

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |

---

#### `note.edit`

Replace the content of a chunk with a new version. The original content atom is preserved as history via `note:revises`. Supports undo.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `chunk_id` | string | Yes | Anchor id of the chunk to edit |
| `text` | string | Yes | New content text |

**Response:**

```json
{"result": {"status": "edited", "chunk_id": "a1b2...", "version": "f7g8..."}}
```

`version` is the newly created content atom. The anchor `chunk_id` is unchanged.

**Errors:**

| Code | Condition |
|---|---|
| -32002 | No active note. |
| -32003 | Chunk not accessible under current IAM scopes. |

---

#### `note.move`

Reorder a chunk to a new position. The input-order timeline (`sys:top/next`) is never modified; only the edit-layer order (`edit:top/next`) is updated. Supports undo.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `chunk_id` | string | Yes | Anchor id to move |
| `after` | string | No | Anchor id to insert after. Omit or `null` to move to the top. |

**Response:**

```json
{"result": {"status": "moved", "chunk_id": "a1b2...", "after": "e5f6...", "order": ["e5f6...", "a1b2..."]}}
```

---

#### `note.undo`

Undo the last edit or reorder. Steps the journal cursor back one position and re-materialises the previous state.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"status": "undone", "cursor": 2}}
```

Returns `{"status": "nothing_to_undo"}` if already at the beginning of history.

---

#### `note.redo`

Redo the last undone edit or reorder.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"status": "redone", "cursor": 3}}
```

Returns `{"status": "nothing_to_redo"}` if already at the latest state.

---

#### `note.restore`

Discard all edit-layer overrides and return to the original input order with original content. History atoms are preserved (the `note:revises` chain is intact). The restore operation itself is undo-able.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"status": "restored_to_original"}}
```

---

#### `note.rename`

Set a mutable display name for the active note. Because root atoms are content-addressed and immutable, the display name is stored as a separate `note:title` pointer atom, which this method updates atomically.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `title` | string | Yes |

**Response:**

```json
{"result": {"status": "renamed", "note_id": "e7f8...", "title": "Field Notes — Ravenna 2026 (revised)"}}
```

**Python (editing lifecycle example):**

```python
rpc("note.new", {"title": "Field Notes"}, token=token)
rpc("note.add", {"text": "Morning: San Vitale."}, token=token)
rpc("note.add", {"text": "Afternoon: Galla Placidia."}, token=token)

chunks = rpc("note.list", {}, token=token)["chunks"]
chunk_id = chunks[0]["id"]

# Edit a chunk
rpc("note.edit", {"chunk_id": chunk_id, "text": "Morning: San Vitale. Apse mosaics in fine condition."}, token=token)

# Move second chunk to top
rpc("note.move", {"chunk_id": chunks[1]["id"], "after": None}, token=token)

# Undo the move
rpc("note.undo", {}, token=token)

# Rename the note
rpc("note.rename", {"title": "Ravenna 2026 — Final"}, token=token)
```

---

### 10.11 JCL — Job Control

JCL (Job Control Language) allows clients to submit multi-step batch jobs that execute asynchronously under Harmonia transactional guarantees. Jobs run on a **single background worker that schedules by priority at step granularity** (the mainframe-initiator model): priority changes the order in which ready steps run, it never introduces parallelism.

---

#### `job.submit`

Submit a batch job with one or more sequential steps.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `steps` | array | Yes | List of step objects (see below) |
| `label` | string | No | Human-readable job name |

Each **step** object:

| Field | Type | Required | Description |
|---|---|---|---|
| `method` | string | Yes | Kernel method to invoke (must not be blocked by the JCL step validator, a blocklist) |
| `params` | object | No | `data` dict passed to the method |
| `cmd` | string | No | Original CLI command (audit trail only) |

**Response (immediate):**

```json
{
  "result": {
    "job_id": "job:4a7f3c2b1e09",
    "status": "PENDING",
    "step_count": 3,
    "label": "import-ravenna"
  }
}
```

The call returns immediately. The job runs in the background. Poll with `job.stat`.

**Errors:**

| Code | Condition |
|---|---|
| -32001 | A step's method is blocked by the JCL step validator (a blocklist); JCL subsystem unavailable |
| -32602 | `steps` is empty or malformed |

**Python:**

```python
job = rpc("job.submit", {
    "label": "import-ravenna",
    "steps": [
        {"method": "kernel.memory.write", "params": {"text": "Ravenna — capital of Western Roman Empire 402–476 AD"}},
        {"method": "kernel.memory.define", "params": {"name": "Ravenna", "description": "Italian city, UNESCO World Heritage"}},
        {"method": "kernel.memory.link",   "params": {"src": "$it", "dst": "Byzantine Architecture", "rel": "sys:associated_with"}}
    ]
}, token=token)
job_id = job["result"]["job_id"]
```

**curl:**

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","method":"job.submit",
    "params":{"session_token":"alice","data":{
      "label":"import-ravenna",
      "steps":[
        {"method":"kernel.memory.write","params":{"text":"Ravenna — capital of Western Roman Empire"}},
        {"method":"kernel.memory.define","params":{"name":"Ravenna"}}
      ]
    }},
    "id":"job1"
  }'
```

---

#### `job.ls`

List jobs. Non-ADMIN callers see only their own jobs.

**Params (`data`):** _(none)_

**Response:**

```json
{
  "result": {
    "jobs": [
      {
        "job_id": "job:4a7f3c2b1e09",
        "label": "import-ravenna",
        "status": "DONE",
        "step_done": 3,
        "step_count": 3,
        "error": null
      }
    ],
    "count": 1
  }
}
```

Job status values: `PENDING`, `RUNNING`, `DONE`, `FAILED`, `CANCELLED`.

---

#### `job.stat`

Detailed status for a single job. Non-ADMIN callers can only inspect their own jobs.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `job_id` | string | Yes |

**Response:**

```json
{
  "result": {
    "job_id": "job:4a7f3c2b1e09",
    "label": "import-ravenna",
    "owner": "alice",
    "status": "DONE",
    "step_done": 3,
    "step_count": 3,
    "tx_id": "ws:jcl:import-ravenna:1716600123000",
    "elapsed_sec": 0.42,
    "error": null
  }
}
```

---

#### `job.cancel`

Cancel a PENDING job. Once a job transitions to RUNNING it cannot be cancelled.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `job_id` | string | Yes |

**Response:**

```json
{"result": {"job_id": "job:4a7f3c2b1e09", "status": "CANCELLED"}}
```

**Errors:**

| Code | Condition |
|---|---|
| -32001 | Job is already RUNNING/DONE/FAILED, or not owned by caller |
| -32002 | Job not found |

---

#### `job.log`

Return Harmonia evidence atoms produced during a job's execution. Useful for debugging failed jobs.

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `job_id` | string | Yes |

**Response:**

```json
{
  "result": {
    "job_id": "job:4a7f3c2b1e09",
    "tx_id": "ws:jcl:import-ravenna:1716600123000",
    "evidence": [
      {
        "key": "f0a1...",
        "type": "sys:action_evidence",
        "executor": "nlp.extract",
        "content": "Action Trace: nlp.extract within ws:..."
      }
    ],
    "count": 1
  }
}
```

Evidence atom types:

| Type | Description |
|---|---|
| `sys:workspace_info` | Workspace open record |
| `sys:action_evidence` | Per-step execution trace |
| `sys:jcl_failure_log` | Permanent failure record (survives rollback) |

---

#### `sys.monitor`

Queue and worker health snapshot. Non-ADMIN callers see only their own jobs in `recent`.

**Params (`data`):** _(none)_

**Response:**

```json
{
  "result": {
    "queue_depth": 0,
    "total_jobs": 5,
    "by_status": {"DONE": 4, "FAILED": 1},
    "recent": [
      {"job_id": "job:4a7f...", "label": "import-ravenna", "status": "DONE", "step_done": 3, "step_count": 3}
    ]
  }
}
```

---

### 10.12 Contexa — the client session's INPUT side

Contexa is the client session's **input side on the I/O pipe** (`lib/harmonia/pipeline.py`);
Jataka (§10.13) is the output side, and Consciousness is the substrate both flow *through*
(auto-weave on input, `generate_view` on output — never a pipe endpoint). Contexa reads the
external world into the cortex: web fetch, and collected survey responses with macro
context-binding.

---

#### `contexa.fetch`

Fetch external content from Wikipedia or a URL and integrate it as atoms (`ContexaWebSource`).
Written atoms carry the `provenance=external` guardrail (trust score + provenance scopes).

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | Wikipedia search query or direct URL (`url=` accepted) |

**Response:** the provider result dict plus `atom_key`/`written`. Triggers the same Weaver/NLP
post-write pipeline as any write.

**Errors:** `-32001` ContexaEngine unavailable · `-32602` `query`/`url` missing.

---

#### `contexa.ingest`

Read collected survey responses (a CSV/JSON file, or an inline upload) into the survey graph
**with Contexa macro-binding** (`ResponseIngestSink`): each response is linked `ctx:answers` →
its question and `ctx:from` → its respondent, and added to the per-question set — the
dialogue/context layer over the survey model's structural tri-links. The input half of the
survey round-trip. Write capability; disk reads (`path=`) are admin/librarian and honour the
`io.allow` list; inline uploads (`text=`) are open to any WRITE client.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `survey` | string | Yes* | Survey root id (`survey_id=` accepted; falls back to the active survey) |
| `path` \| `text` | string | Yes | A permitted file path, or an inline upload payload |
| `format` | string | with `text=` | `csv` / `json` (required for inline) |
| `respondent_col` | string | No | Column identifying the respondent (default: first column) |
| `map` | string | No | Column→question mapping `col:qid[,col:qid]` (qid = question id, alias, or 1-indexed position); else columns map to questions in order |

**Response:** `{kind:"survey_ingest", survey, respondents, responses, errors, mapped_questions}`.

**Errors:** `-32602` missing survey/source or no mappable question column · `-32001` disk read denied (allow-list).

---

### 10.13 Jataka — the client session's OUTPUT side

Jataka is the client session's **output side on the I/O pipe**: it presents a graph selection
back out, read *through* the Consciousness substrate (`generate_view` / `cosmos_nd`). `dream`
is the kernel's asynchronous affinity-gap incubation.

---

#### `jataka.present`

Render a selection as a presentation, returned inline (READ-level; no graph write).

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `as` | string | No | `table` (default) \| `scatter` \| `narrative` |
| `survey` \| `set` \| `focus` | string | Yes | The selection to present (which one depends on `as`) |
| `format` | string | No | For `as=table`: also serialise to `csv`/`json`/`md` |

- **`table`** (`survey=`\|`set=`) — per-(question,answer) counts / listed rows.
- **`scatter`** (`survey=`\|`set=`) — 2-D points positioned by `cosmos_nd` (the real semantic position).
- **`narrative`** (`focus=`\|`survey=`) — prose from `generate_view`. **LLM-optional**: with no
  LLM a deterministic structural template is emitted (never empty); an injected narrator lifts it.

**Response:** `{kind:"present", format, …}` (`rows`/`columns` for table, `points` for scatter, `text` for narrative).

---

#### `jataka.dream`  (alias: `dream`)

Asynchronous affinity-gap incubation ("sleep on it") — deliberately unlike the fast explorers
(`assoc` fills 1-hop high-confidence gaps; `sim`/`node.sim` rank what is already near). It
searches for atoms **near in meaning but far in the explicit graph** and stages them as
*tentative* links a **human** confirms. Runs as a LOW-priority background JCL job.

**Params (`data`):** `id` (focus atom); optional `boldness` (0 conservative … 1 bold single
signal; default 0.2), `reach` (gap weight; default 0.5), `again=yes` (re-dream a completed
focus), `threshold`/`limit`/`scan`.

**Flow:**

1. `dream id=<atom>` submits a background job → `{status:"dreaming", job_id, elapsed_s}`.
2. `dream id=<atom>` again for the same focus polls: still running → `dreaming`; done →
   `{status:"ready", focus, candidates:[{dst, alias, score, rel, preview}], count}`. Candidates
   are staged as `tent:calc:hidden_affinity` links — the job **never** writes a real edge.
3. `dream.confirm dst=<atom> [src=<focus>]` promotes one staged bridge to a real
   `calc:hidden_affinity` link. `dream.forget [dst=|all=yes] [src=]` drops the rest. Human
   approval is mandatory by design (no agent auto-approval). If JCL is unavailable, `dream`
   falls back to a synchronous run.

IAM: `dream` requires the `SIMULATE` capability and always inherits the session's `active_scopes`.

**Errors:** `-32002` focus not found / access denied · `-32602` `dream.confirm` needs `dst`.

---

### 10.14 Session

---

#### `sys.history`

Return the 10 most recent user-authored atoms (excluding internal `sys:` nodes).

**Params (`data`):** _(none)_

**Response:**

```json
{
  "result": {
    "history": [
      {"key": "a3f9...", "preview": "The basilica of San Vitale dates from 547 AD."},
      {"key": "b4c5...", "preview": "Byzantine Architecture"}
    ]
  }
}
```

---

#### `sys.ls`

List the last N user-authored atoms.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | No | Number of atoms to return (default: 10, max: 100) |

**Response:**

```json
{
  "result": {
    "atoms": [
      {"idx": 0, "key": "a3f9...", "preview": "The basilica..."},
      {"idx": 1, "key": "b4c5...", "preview": "Byzantine Architecture..."}
    ],
    "count": 2
  }
}
```

---

#### `sys.session.close`

Terminate the caller's session, releasing all in-memory state.

**Params (`data`):** _(none)_

**Response:**

```json
{"result": {"status": "session_closed", "client_id": "alice"}}
```

---

### 10.15 Associate

`kernel.associate` traverses the **meaning network** — `calc:*`, `emo:*`, `word:*` links — and returns a projection of the semantic field surrounding the focal atom. It is the meaning-layer complement to `explore`'s structure-layer BFS.

---

#### `kernel.associate`

**Params (`data`):**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `id` | string | No | `$it` | Focal atom. Supports all context references. |
| `axis` | string | No | `null` (all) | Filter by semantic axis (see Axis Filter table). |
| `scope` | integer | No | `2` | Traversal depth. Role-capped identical to `explore`. |
| `format` | string | No | `"raw"` | `"raw"` or `"cosmos"` (Cosmos Viewer ready). |

**Axis filter values:**

| `axis` | Matched rel prefixes |
|---|---|
| `emotion` | `emo:` |
| `color` | `word:color:`, `calc:color` |
| `sense` | `word:sense:`, `calc:sense` |
| `time` | `chrono:`, `calc:time` |
| `context` | `calc:context`, `calc:associated_with` |
| `story` | `polti:`, `story:` |
| omitted | all of the above |

**Response (format=raw):**

```json
{
  "result": {
    "focal":  {"key": "<hex>", "content": "<full text>", "preview": "<50 chars>"},
    "axis":   "emotion | all",
    "scope":  2,
    "associations": [
      {"key": "<hex>", "rel": "emo:sadness", "depth": 1, "preview": "<60 chars>", "type": "emotion"}
    ],
    "resonance": [
      {"key": "<hex>", "via": "<tag key>", "rel": "<rel>", "preview": "<60 chars>", "weight": 1.0}
    ],
    "unwritten": {"status": "pending | unavailable", "job_id": "<id | null>", "voids": []}
  }
}
```

**Response (format=cosmos):**

```json
{
  "result": {
    "focal": {"key": "...", "preview": "..."},
    "axis":  "emotion",
    "nodes": [
      {"id": "<key>", "name": "<preview>", "group": "focus | association | resonance", "val": 20, "color": "#ffffff"}
    ],
    "links": [
      {"source": "<key>", "target": "<key>", "rel": "<rel>", "type": "association | resonance"}
    ],
    "unwritten": {"status": "pending", "job_id": "<id>"}
  }
}
```

**Node color convention:**

| Group | Color | Meaning |
|---|---|---|
| `focus` | `#ffffff` | Focal atom |
| `association` | `#00ffcc` | Semantic link traversal |
| `resonance` | `#ff9900` | Shared-tag resonance |
| `void` | `#333333` | UnwrittenVoid (future) |

**UnwrittenVoid detection:**

An async JCL job (`associate.unwritten`) is submitted automatically. It detects which semantic axes are absent from the focal atom. Retrieve results via `job.log <job_id>` once the job completes.

**Errors:**

| Code | Condition |
|---|---|
| -32602 | Missing `id` and no last-written atom in session. |
| -32002 | Atom not found or access denied. |

**CLI examples:**

```
associate $it
associate $it axis=emotion
associate $it axis=color format=cosmos
associate note.chunk1 axis=story scope=3
```

---

### 10.16 Scope State

`sys.scope.*` manages the **session-level scope state** — persistent context keys that are automatically inherited by `kernel.associate` and `explore` when the caller omits the corresponding parameter. This allows slider-based UIs (e.g. the Cosmos Viewer) to synchronise traversal parameters with the kernel without resending them on every call.

#### Session context keys

| Key | Type | Default | Description |
|---|---|---|---|
| `active_axis` | string \| null | `null` | Semantic axis filter inherited by `kernel.associate` |
| `active_scope` | integer \| null | `null` | Traversal depth inherited by `kernel.associate` and `explore` |
| `active_time` | string \| null | `null` | Temporal filter tag returned in `dive.look` response metadata |

#### Parameter inheritance rules

| Method | Parameter | Falls back to | Ultimate default |
|---|---|---|---|
| `kernel.associate` | `axis` | `active_axis` | `null` (all axes) |
| `kernel.associate` | `scope` | `active_scope` | `2` |
| `explore` | `depth` | `active_scope` | `2` |
| `dive.look` | *(response only)* | `active_time` attached as `meta.active_time` | `null` |

---

#### `sys.scope.set`

Set one or more session scope keys. Omitted keys are left unchanged.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `axis` | string \| null | No | Set `active_axis`. Pass `null` to clear. |
| `scope` | integer \| null | No | Set `active_scope`. Pass `null` to clear. |
| `time` | string \| null | No | Set `active_time`. Pass `null` to clear. |

**Result:**

```json
{
  "status": "scope_updated",
  "active_axis": "emotion",
  "active_scope": 3,
  "active_time": null
}
```

---

#### `sys.scope.get`

Return the current session scope state.

**Params:** none

**Result:**

```json
{
  "active_axis": "emotion",
  "active_scope": 3,
  "active_time": null
}
```

---

#### `sys.scope.reset`

Clear all session scope keys back to `null`.

**Params:** none

**Result:**

```json
{
  "status": "scope_reset",
  "active_axis": null,
  "active_scope": null,
  "active_time": null
}
```

---

#### Cosmos Viewer integration

The Cosmos Viewer sends a `sys.scope.set` call whenever the user moves a slider, then fires `kernel.associate` without repeating the axis/scope arguments:

```javascript
// Slider onChange
async function onAxisChange(axis) {
  await rpc("sys.scope.set", { axis });
}

async function onScopeChange(depth) {
  await rpc("sys.scope.set", { scope: depth });
}

// Associate button — no axis/scope needed; session state is inherited
async function onAssociate(nodeId) {
  return rpc("kernel.associate", { id: nodeId });
}
```

---

#### CLI shortcuts

```
scope              # alias for: scope get
scope get          # sys.scope.get
scope reset        # sys.scope.reset
scope axis=emotion scope=3   # sys.scope.set {axis: "emotion", scope: 3}
scope time=2026    # sys.scope.set {time: "2026"}
scope axis=null    # sys.scope.set {axis: null}  — clear axis filter
```

The `scope` command uses key=value token parsing instead of positional arguments. Multiple key=value pairs may be combined in a single call.

---

### 10.17 Log

`log.*` records the **process of exploration** — which atoms were visited, under what scope conditions, and when. Unlike `note.*` (which records written content), LogConcept records the act of traversal itself.

Implemented in `lib/akasha/concepts/log.py` as a `BaseConcept` subclass (does **not** inherit `NoteConcept`).

#### Session context keys

| Key | Description |
|---|---|
| `active_log_root` | Root atom of the currently active Log |
| `active_log_container` | Current container in the Log hierarchy (updated on each checkpoint) |

#### `log.new`

Create a new Log and set it as active.

**Params (`data`):** `name: str`

**Result:**
```json
{"log_id": "<hex>", "name": "Cosmos Exploration 2026-05-26", "status": "created"}
```

---

#### `log.checkpoint`

Record the current session state as a checkpoint. Automatically captures `session.focus`, `active_axis`, `active_scope`, `active_time` (whiteboard-local when a board is active), and timestamp.

**Params (`data`):** `note?: str` (optional annotation)

**Result:**
```json
{
  "checkpoint_id": "<hex>",
  "focal": "<key>",
  "axis": "emotion",
  "scope": 2,
  "time": null,
  "note": "Noticed strong resonance here",
  "status": "recorded"
}
```

**Checkpoint atom meta structure:**
```json
{
  "type": "log_checkpoint",
  "role": "checkpoint",
  "focal_key": "<hex>",
  "focal_alias": "<alias | null>",
  "active_axis": "emotion",
  "active_scope": 2,
  "active_time": null,
  "whiteboard": "<wb_name | null>",
  "note": "<optional text>",
  "created_at": 1716600000.0
}
```

---

#### `log.annotate`

Add a text annotation to the most recent checkpoint.

**Params (`data`):** `text: str`

**Result:**
```json
{"annotation_id": "<hex>", "checkpoint_id": "<hex>", "status": "annotated"}
```

---

#### `log.replay`

Replay the Log — restore each checkpoint's focal atom and scope state sequentially into the session.

**Params:** none

**Result:**
```json
{
  "checkpoints": [
    {"index": 0, "focal": "<key>", "alias": "Atlantis", "axis": "emotion", "scope": 2, "note": "...", "restored": true}
  ],
  "count": 5,
  "status": "replayed"
}
```

---

#### `log.read`

Read the Log as a sequential list of checkpoints (timeline order).

**Params:** none

**Result:**
```json
{
  "log_id": "<hex>",
  "name": "Cosmos Exploration 2026-05-26",
  "checkpoints": [...],
  "count": 5
}
```

---

#### `log.rm`

Delete the active Log and clear session context keys.

**Params:** none

**Result:** `{"status": "deleted", "log_id": "<hex>"}`

---

#### Set namespace

| Set | Members |
|---|---|
| `set:log:<root_id>` | All checkpoint and annotation atoms |
| `set:log:<root_id>:checkpoints` | Checkpoint atoms only |
| `set:concept:<root_id>` | Concept-word atoms (`"log"`, `"checkpoint"`) |

---

### 10.18 Whiteboard

A Whiteboard is a **named meaning session** — a surface onto which Concept Models are pinned to define their intersection. When active, scope state and traversal context are scoped to that board.

Implemented in `lib/akasha/concepts/whiteboard.py`. **No cortex atoms are created** — all state lives in session context keys.

#### Session context keys

| Key | Description |
|---|---|
| `active_whiteboard` | Name of the currently active Whiteboard |
| `wb_names` | List of all known whiteboard names |
| `wb:<name>:pinned` | Ordered list of pinned concept model names |
| `wb:<name>:scope_axis` | Whiteboard-local `active_axis` |
| `wb:<name>:scope_scope` | Whiteboard-local `active_scope` |
| `wb:<name>:scope_time` | Whiteboard-local `active_time` |

#### Whiteboard × sys.scope integration

When a whiteboard is active, `sys.scope.set/get/reset` operate on the board's local scope keys (`wb:<name>:scope_*`) instead of the session-global keys. Switching boards via `wb.focus` restores the target board's scope state automatically.

```
wb.focus "Story Exploration"
scope axis=emotion scope=3   # → stored in wb:"Story Exploration":scope_axis/scope_scope

wb.focus "Molecule Search"
scope axis=context scope=2   # → stored in wb:"Molecule Search":scope_axis/scope_scope

wb.focus "Story Exploration"
scope get                    # → {"axis": "emotion", "scope": 3, "time": null}
```

#### `wb.new`

Create a new Whiteboard and make it active.

**Params (`data`):** `name: str`

**Result:** `{"name": "Story Exploration", "pinned": [], "status": "created", "active": true}`

---

#### `wb.pin`

Pin a Concept Model to the active Whiteboard.

**Params (`data`):** `concept: str` — valid values: `note`, `log` (extensible)

**Result:** `{"whiteboard": "Story Exploration", "pinned": ["note"], "status": "pinned"}`

---

#### `wb.unpin`

Remove a Concept Model from the active Whiteboard.

**Params (`data`):** `concept: str`

**Result:** `{"whiteboard": "Story Exploration", "pinned": ["log", "cosmos"], "status": "unpinned"}`

---

#### `wb.focus`

Switch the active Whiteboard. All scope state reads/writes immediately route to this board's local keys.

**Params (`data`):** `name: str`

**Result:**
```json
{
  "active_whiteboard": "Molecule Search",
  "pinned": ["log", "molecule"],
  "scope": {"axis": null, "scope": 2, "time": null},
  "status": "focused"
}
```

---

#### `wb.ls`

List all Whiteboards in this session.

**Params:** none

**Result:**
```json
{
  "whiteboards": [
    {"name": "Story Exploration", "pinned": ["note", "log", "cosmos"], "active": true},
    {"name": "Molecule Search",   "pinned": ["log", "molecule"],       "active": false}
  ],
  "count": 2
}
```

---

#### `wb.show`

Show the current state of the active Whiteboard.

**Params:** none

**Result:**
```json
{
  "name": "Story Exploration",
  "pinned": ["note", "log", "cosmos"],
  "scope": {"axis": "emotion", "scope": 3, "time": null},
  "active_note": "<note_root_id | null>",
  "active_log":  "<log_root_id  | null>",
  "active_focus": "<focal_key   | null>"
}
```

---

#### `wb.rm`

Remove a Whiteboard from this session. Clears all `wb:<name>:*` context keys.

**Params (`data`):** `name: str`

**Result:** `{"status": "deleted", "name": "Story Exploration"}`

---

#### Whiteboard × kernel.associate

When a Whiteboard is active, `kernel.associate` appends a `whiteboard_context` field:

```json
{
  "focal": {...},
  "whiteboard_context": {
    "name": "Story Exploration",
    "pinned": ["note", "log", "cosmos"]
  },
  "associations": [...],
  "resonance": [...]
}
```

The Cosmos Viewer uses `whiteboard_context.pinned` to apply the correct node colour scheme per concept.

---

### 10.19 Cross-Concept Intersection

`sys.cross.*` computes the **set intersection** of atoms across multiple active Concept Models. `WhiteboardConcept` uses `sys.cross.query` internally; direct use is available for scripting and JCL jobs.

Concept names are resolved to their active collection set names via session context:
- `"note"` → `set:note:<active_note_root>`
- `"log"` → `set:log:<active_log_root>`

#### `sys.cross.query`

Return atoms present across the specified concept sets, weighted by coverage ratio.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `concepts` | array of strings | Yes | Concept model names to intersect |
| `id` | string | No | Focal atom for context. Defaults to `$it`. |
| `format` | string | No | `"raw"` (default) or `"cosmos"` |

**Result (`format=raw`):**
```json
{
  "focal": "<key | null>",
  "concepts": ["note", "log", "cosmos"],
  "intersection": [
    {
      "key": "<hex>",
      "preview": "<60 chars>",
      "present_in": ["note", "log"],
      "weight": 0.6667
    }
  ],
  "count": 12
}
```

`weight` is `len(present_in) / len(concepts)` — atoms present in all concepts have weight `1.0`.

---

#### `sys.cross.axes`

Return the semantic axes available across the specified concept sets, with a recommendation.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `concepts` | array of strings | Yes | Concept model names |

**Result:**
```json
{
  "concepts": ["note", "log"],
  "available_axes": ["emotion", "time", "story", "context"],
  "recommended": "time"
}
```

`recommended` is the axis with the highest cross-concept coverage (present in the most distinct concept sets).

---

### 10.20 Cockpit

> **Full API reference:** [`docs/concept-model/concept-model-spec.md §10.1`](../concept-model/concept-model-spec.md#101-cockpit)

The Cockpit concept model (`lib/akasha/concepts/cockpit.py`) is registered automatically
via the Concept Model Plugin Registry — no manual kernel dispatch is required.

| Method | Required params | Description |
|---|---|---|
| `cockpit.new` | `name` (str) | Commission a new cockpit deck |
| `cockpit.ls` | — | List all cockpits owned by this user |
| `cockpit.open` | `cockpit_id` (str) | Mount an existing cockpit as active |
| `cockpit.lock` | `target` (str) | Set the focal point (session only) |
| `cockpit.tune` | `axis`? (str), `scope`? (int) | Adjust dimensional lens filters |
| `cockpit.beacon` | `note` (str) | Drop a beacon at current focal point |
| `cockpit.wake` | — | Read the chronological beacon trail |
| `cockpit.status` | — | Read instrument panel state |
| `cockpit.rm` | — | Decommission the active cockpit |

**CLI aliases:** `cp.new`, `cp.ls`, `cp.open`, `cp.lock`, `cp.tune`, `cp.beacon`, `cp.wake`, `cp.status`, `cp.rm`

---

### 10.21 Survey

> **Full API reference:** [`docs/concept-model/concept-model-spec.md §10.3`](../concept-model/concept-model-spec.md#103-survey)

The Survey concept model (`lib/akasha/concepts/survey.py`) is registered automatically
via the Concept Model Plugin Registry — no manual kernel dispatch is required.

| Method | Required params | Description |
|---|---|---|
| `survey.new` | `title` (str) | Create a new survey root |
| `survey.open` | `survey_id` (str) | Mount an existing survey |
| `survey.ls` | — | List all accessible surveys |
| `survey.q.add` | `text` (str) | Add a question to the active survey |
| `survey.opt.add` | `question_id`, `label` (str) | Add an answer option to a question |
| `survey.res.add` | `respondent_id` (str) | Register a respondent |
| `survey.ans` | `question_id`, `respondent_atom`, `answer` | Record a tri-linked response |
| `survey.list` | — | Structural inventory of active survey |
| `survey.rm` | — | Delete the active survey root |

---

### 10.22 Delegation & Donation Sets

Delegation sets (`dont:*`) are named collections used to bundle atoms and transfer them to a shared space — either the nucleus (universal scope) or a group knowledge space. They serve both as a donation mechanism and as a provenance record: both origin and destination retain the set record with metadata about date, source, and destination.

**Donation modes:**

| Mode | `open` value | Effect |
|---|---|---|
| **Copy** (default) | `false` | Atom is physically copied to the target DB. Originals are unchanged. Group members can collaborate on the copy independently. |
| **Open** | `true` | Original atom's scope is extended to include the target scope. No copy is made. |

Copy mode is preferred for group donations because it prevents group collaboration from modifying the original.

---

#### `dont.create`

Create or update a named delegation set with provenance metadata.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Set name. The `dont:` prefix is added automatically if omitted. |
| `description` | string | No | Human-readable description of the set's purpose |

**Response:**

```json
{
  "result": {
    "set": "dont:love_vocab",
    "status": "created",
    "meta": {
      "type": "donation_set",
      "created_by": "alice",
      "created_at": 1748304000.0,
      "description": "Vocabulary atoms for the emotion cluster",
      "donations": []
    }
  }
}
```

---

#### `dont.add`

Add atoms to an existing delegation set.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Set name (with or without `dont:` prefix) |
| `targets` | string or array | Yes | Space-separated atom keys/aliases, or a JSON array. Supports `$`-references. |

**Response:**

```json
{
  "result": {
    "set": "dont:love_vocab",
    "added": 3,
    "keys": ["a3f9...", "b4c5...", "c5d6..."]
  }
}
```

---

#### `dont.send`

Donate all atoms in a delegation set to a shared space.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Delegation set name |
| `to` | string | Yes | Destination: `"universal"` or `"group:<id>"` |
| `open` | boolean | No | If `true`, extends scope instead of copying (default: `false`) |

**Destination `"universal"`:** requires `LIBRARIAN` or `ADMIN` role. Atoms are written to the nucleus DB.

**Destination `"group:<id>"`:** requires membership in the group (`scope:group_<id>` in caller's scopes).

**Response:**

```json
{
  "result": {
    "status": "donated",
    "set": "dont:love_vocab",
    "to": "group:history_lab",
    "mode": "copy",
    "donated": 3,
    "skipped": 0,
    "donated_at": 1748304000.0
  }
}
```

After `dont.send`, both the origin set and the destination set record a provenance entry:

**Origin metadata** (`donations[]` array, appended):
```json
{
  "target": "group:history_lab",
  "donated_at": 1748304000.0,
  "atom_count": 3,
  "mode": "copy"
}
```

**Destination metadata** (receipt record in target DB):
```json
{
  "type": "donation_receipt",
  "source_cell": "alice",
  "source_set": "dont:love_vocab",
  "donated_at": 1748304000.0,
  "atom_count": 3,
  "mode": "copy"
}
```

**Errors:**

| Code | Condition |
|---|---|
| -32602 | `name` or `to` missing |
| -32002 | Set is empty, not found, or group space not loaded |
| -32003 | Destination requires `librarian` role or group membership |

---

#### `dont.open`

Convenience shorthand: `dont.send` with `open=true`. Extends the original atom's scope to include the destination instead of copying.

**Params (`data`):** identical to `dont.send` (the `open` flag is forced to `true`).

---

#### `dont.ls`

List delegation sets and their donation history.

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | No | If provided, returns detail for a single set (including member count). If omitted, lists all sets. |

**Response (no `name` — list all):**

```json
{
  "result": {
    "donation_sets": [
      {"name": "dont:love_vocab", "description": "Vocabulary atoms...", "atom_count": 3}
    ]
  }
}
```

**Response (with `name` — single set detail):**

```json
{
  "result": {
    "set": "dont:love_vocab",
    "atom_count": 3,
    "meta": {
      "type": "donation_set",
      "created_by": "alice",
      "created_at": 1748304000.0,
      "description": "Vocabulary atoms for the emotion cluster",
      "donations": [
        {"target": "group:history_lab", "donated_at": 1748304000.0, "atom_count": 3, "mode": "copy"}
      ]
    }
  }
}
```

---

**Python workflow example:**

```python
# 1. Create a delegation set
rpc("dont.create", {"name": "emotion_vocab", "description": "Core emotion vocabulary"}, token=token)

# 2. Add atoms (by alias or $-reference)
rpc("dont.add", {"name": "emotion_vocab", "targets": "emo:love emo:joy emo:sadness"}, token=token)

# 3. Donate to the group space
rpc("dont.send", {"name": "emotion_vocab", "to": "group:history_lab"}, token=token)

# 4. Inspect provenance
rpc("dont.ls", {"name": "emotion_vocab"}, token=token)
```

---

## 11. JCL Security Blocklist

`job.submit` validates every step's `method` against a hard-coded **blocklist** (`validate_steps`, defined in `lib/akasha/jcl/validator.py`). Submitting a step whose method matches the blocklist returns error `-32001`. Everything not on the blocklist is permitted.

**Blocked methods (may not run inside a JCL step):**

| Category | Methods |
|---|---|
| Job control | `job.*` (prevents recursion and job introspection/cancellation from inside a job) |
| Privilege escalation | `sys.su` |
| User & group management | `user.*`, `grp.*` |
| Session | `session.*` |
| Authentication | `auth.*`, `kernel.auth.*` |
| First-boot ceremony | `kernel.genesis_rite` |
| Destructive ontology | `onto.reset`, `onto.genesis.redo`, `onto.scope.drop` |

**Everything else is permitted** — including `rec.*`, `table.*`, `lens*`, `quadrant.*`, weave operations, and any future concept models. A blocklist is used deliberately: with an allowlist, every newly added concept model would silently become un-runnable inside a job until someone remembered to register it; a blocklist keeps new models runnable by default while still barring the sensitive control-plane methods.

Each step runs as a normal `kernel.dispatch()` call under the submitter's own `session_token`, and is re-authenticated as the job owner (the blocklist is defense-in-depth on top of that). Scope isolation is therefore enforced naturally: a USER can only write to their private scope from a JCL step, exactly as they would in an interactive session.

---

## 12. MCP Portal

The MCP portal (`api/portals/mcp.py`) exposes five kernel operations as MCP tools. Full transport wiring (stdio/SSE) requires `mcp-python-sdk` and is pending; the portal class (`AkashaMCPPortal`) is instantiable today for local integrations.

### Tool Definitions

```json
[
  {
    "name": "akasha_write",
    "description": "Write a new atom (memory node) to the Akasha semantic mesh.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "text": {"type": "string", "description": "Content to store as a new atom"}
      },
      "required": ["text"]
    }
  },
  {
    "name": "akasha_read",
    "description": "Read an atom by ID, alias, or $-reference.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "description": "Atom key (64-char hex), alias name, or $-reference ($0, $it, etc.)"
        }
      },
      "required": ["id"]
    }
  },
  {
    "name": "akasha_explore",
    "description": "BFS graph exploration from a focal node up to given depth.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "id":    {"type": "string"},
        "depth": {"type": "integer", "default": 2, "minimum": 1, "maximum": 10}
      },
      "required": ["id"]
    }
  },
  {
    "name": "akasha_fetch",
    "description": "Fetch external context from Wikipedia or a URL and integrate it.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Search query or URL"}
      },
      "required": ["query"]
    }
  },
  {
    "name": "akasha_ping",
    "description": "Check Akasha kernel liveness.",
    "inputSchema": {"type": "object", "properties": {}}
  }
]
```

### MCP → JSON-RPC Mapping

| MCP Tool | Kernel Method |
|---|---|
| `akasha_write` | `kernel.memory.write` |
| `akasha_read` | `kernel.memory.read` |
| `akasha_explore` | `explore` |
| `akasha_fetch` | `contexa.fetch` |
| `akasha_ping` | `sys.ping` |

### Programmatic Use (Python)

```python
from api.gateway import create_gateway
from api.portals.mcp import AkashaMCPPortal

gw = create_gateway(series="seeds", base_dir="data")
mcp = AkashaMCPPortal(gw, client_id="claude")

# List available tools
tools = mcp.list_tools()

# Execute a tool call
result = mcp.handle_tool_call("akasha_write", {"text": "Theodoric the Great ruled 493–526 AD."})
print(result)  # {"key": "...", "status": "written"}
```

---

## 13. Group Management API

Groups provide shared knowledge spaces for collaborative research teams. Each group has its own dedicated SQLite database (`data/groups/{group_id}/g_space.db`) managed by a `GroupEngine` instance. Group atoms are isolated from the nucleus and from other groups.

### 13.1 Group Concepts

- Each group has a unique string identifier (e.g., `"architects"`, `"history_lab"`).
- Group knowledge lives in a **separate per-group DB** (`data/groups/{group_id}/g_space.db`), not in the nucleus or any user's local cell.
- Atoms in a group space are tagged `scope:group_<id>`.
- Only group participants can read group atoms; `GROUP_ADMIN` and group-level LIBRARIANs can write.
- A `GROUP_ADMIN` cannot read private atoms of individual group members.
- The kernel loads all group DBs for a user's groups automatically at session creation (`AkashaSession.group_engines` dict).

### 13.2 Group Management Methods (`grp.*`)

| Method | Required Role | Description |
|---|---|---|
| `grp.new` | ADMIN | Create a group and assign its administrator |
| `grp.ls` | GROUP_ADMIN, ADMIN | List current members of a group |
| `grp.add` | GROUP_ADMIN, ADMIN | Add a user to a group |
| `grp.rm` | GROUP_ADMIN, ADMIN | Remove a member (cannot remove the GROUP_ADMIN) |
| `grp.lib` | GROUP_ADMIN, ADMIN | Grant or revoke group-level LIBRARIAN rights |
| `grp.del` | ADMIN | Delete a group |

#### `grp.new`

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `group_id` | string | Yes |
| `admin_id` | string | Yes |

**Response:** `{"status": "created", "group_id": "history_lab", "admin": "alice"}`

---

#### `grp.ls`

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `group_id` | string | Yes |

**Response:** `{"group_id": "history_lab", "members": [...], "count": 3}`

---

#### `grp.add`

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `group_id` | string | Yes |
| `member_id` | string | Yes |

**Response:** `{"status": "added", "group_id": "history_lab", "member": "bob"}`

---

#### `grp.rm`

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `group_id` | string | Yes |
| `member_id` | string | Yes |

**Response:** `{"status": "removed", "group_id": "history_lab", "member": "bob"}`

---

#### `grp.lib`

**Params (`data`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `group_id` | string | Yes | Target group |
| `action` | string | Yes | `"grant"` or `"revoke"` |
| `member_id` | string | Yes | Target user |

**Response:** `{"status": "librarian_granted", "group_id": "history_lab", "member": "carol"}`

---

#### `grp.del`

**Params (`data`):**

| Field | Type | Required |
|---|---|---|
| `group_id` | string | Yes |

**Response:** `{"status": "deleted", "group_id": "history_lab"}`

---

### 13.3 Scope Effects

When a user is added to a group, their scope list automatically includes:

```
scope:group_<id>     — read access to group atoms
view:group_<id>      — explicit read grant
```

A group-level LIBRARIAN additionally receives `write:group_<id>` (Dim-2 capability flag), granting write access to the group space without elevating them to the global LIBRARIAN role.

### 13.4 Group Knowledge Spaces

Writing atoms to a group space is done via the **Delegation & Donation Sets** API (see §10.21). A user collects atoms into a named delegation set and then sends them to `"group:<id>"`. The `GroupEngine` copies (or scope-extends) the atoms into the group DB and records provenance metadata on both sides.

**Direct group writes** (atoms created directly in the group space) are possible for users holding `write:group_<id>` via the standard `kernel.memory.write` method — add a `scope` field of `"group:<id>"` *(planned; currently use the donation API)*.

### 13.5 Python Example

```python
iam = kernel_dispatcher.iam

# Create a group with alice as its admin
iam.create_group("history_lab", "alice")

# Add bob as a member
iam.add_group_member("history_lab", requester_id="alice", new_member_id="bob")

# Grant bob group-level librarian rights
iam.grant_group_librarian("history_lab", requester_id="alice", target_id="bob")
```

---

## 14. CLI Shorthand Reference

The interactive REPL translates shorthand commands to JSON-RPC 2.0 payloads via `api/router.py:CommandRouter`. Every shorthand is equivalent to its full method name.

| Shorthand | Method | Arguments |
|---|---|---|
| `w <text>` | `kernel.memory.write` | `text` |
| `def <name>` | `kernel.memory.define` | `name` |
| `r <id>` | `kernel.memory.read` | `id` |
| `rm <id>` | `kernel.memory.drop` | `id` |
| `ln <src> <dst> <rel>` | `kernel.memory.link` | `src`, `dst`, `rel` |
| `ln.ls [id]` | `link.list` | `id` |
| `ln.+ <src> <dst> <rel>` | `link.reinforce` | `src`, `dst`, `rel` |
| `meta <id> <key> <value>` | `meta.set` | `id`, `key`, `value` |
| `al <id> <name>` | `kernel.identity.alias` | `id`, `name` |
| `al.ls` | `kernel.identity.alias.list` | — |
| `al.find <pattern>` | `kernel.identity.alias.find` | `pattern` |
| `onto.dump [mode] [ns=..] [rel=..] [collection=..] [sort=..] [limit=..]` | `onto.dump` | `mode`, `ns`, `rel`, `collection`, `sort`, `limit` |
| `onto.report [clear=true]` | `onto.report` | `clear` |
| `exp <id> [depth]` | `explore` | `id`, `depth` |
| `tree [id] [depth]` | `network.tree` | `id`, `depth` |
| `look [id]` | `dive.look` | `id` |
| `d [id]` | `dive.look` | `id` (alias for `look`) |
| `out [id]` | `dive.out` | `id` |
| `s.add <name> <id>` | `set.add` | `name`, `id` |
| `s.rm <name> <id>` | `set.rm` | `name`, `id` |
| `s.ls <name>` | `set.ls` | `name` |
| `s.clear <name>` | `set.clear` | `name` |
| `s.op <op> <result> <a> <b>` | `set.op` | `op`, `result`, `a`, `b` |
| `n.new <title>` | `note.new` | `title` |
| `n.ls` | `note.ls` | — |
| `n.open <note_id>` | `note.open` | `note_id` |
| `n.add <text>` | `note.add` | `text` |
| `n.sec <title>` | `note.section` | `title` |
| `n.chap <title> [role]` | `note.section` | `title`, `role` |
| `n.para [category]` | `note.paragraph` | `category` |
| `n.toc` | `note.toc` | — |
| `n.read` | `note.read` | — |
| `n.rm` | `note.rm` | — |
| `n.list` | `note.list` | — |
| `n.edit <chunk_id> <text>` | `note.edit` | `chunk_id`, `text` |
| `n.move <chunk_id> [after]` | `note.move` | `chunk_id`, `after` |
| `n.undo` | `note.undo` | — |
| `n.redo` | `note.redo` | — |
| `n.restore` | `note.restore` | — |
| `n.rename <title>` | `note.rename` | `title` |
| `cp.new <name>` | `cockpit.new` | `name` |
| `cp.ls` | `cockpit.ls` | — |
| `cp.open <cockpit_id>` | `cockpit.open` | `cockpit_id` |
| `cp.lock <target>` | `cockpit.lock` | `target` |
| `cp.tune <axis> <scope>` | `cockpit.tune` | `axis`, `scope` |
| `cp.beacon <note>` | `cockpit.beacon` | `note` |
| `cp.wake` | `cockpit.wake` | — |
| `cp.status` | `cockpit.status` | — |
| `cp.rm` | `cockpit.rm` | — |
| `job.ls` | `job.ls` | — |
| `job.st <job_id>` | `job.stat` | `job_id` |
| `job.can <job_id>` | `job.cancel` | `job_id` |
| `job.log <job_id>` | `job.log` | `job_id` |
| `mon` | `sys.monitor` | — |
| `associate <id> [axis=X] [scope=N] [format=F]` | `kernel.associate` | `id`, `axis`, `scope`, `format` |
| `assoc <id> [axis=X] [scope=N] [format=F]` | `kernel.associate` | `id`, `axis`, `scope`, `format` |
| `scope` / `scope get` | `sys.scope.get` | — |
| `scope reset` | `sys.scope.reset` | — |
| `scope [key=val ...]` | `sys.scope.set` | `axis`, `scope`, `time` (key=value pairs) |
| `log.new <name>` | `log.new` | `name` |
| `log.cp [note]` | `log.checkpoint` | `note` (optional) |
| `log.ann <text>` | `log.annotate` | `text` |
| `log.replay` | `log.replay` | — |
| `log.read` | `log.read` | — |
| `log.rm` | `log.rm` | — |
| `wb.new <name>` | `wb.new` | `name` |
| `wb.pin <concept>` | `wb.pin` | `concept` |
| `wb.unpin <concept>` | `wb.unpin` | `concept` |
| `wb.focus <name>` | `wb.focus` | `name` |
| `wb.ls` | `wb.ls` | — |
| `wb.show` | `wb.show` | — |
| `wb.rm <name>` | `wb.rm` | `name` |
| `cross <c1> <c2> [...]` | `sys.cross.query` | `concepts` (space-separated) |
| `cross.axes <c1> <c2> [...]` | `sys.cross.axes` | `concepts` (space-separated) |
| `dream` | `jataka.dream` | — |
| `fetch <query>` | `contexa.fetch` | `query` |
| `ping` | `sys.ping` | — |
| `cog` | `sys.cogito` | — |
| `hist` | `sys.history` | — |
| `ls [limit]` | `sys.ls` | `limit` |
| `grp.new <group_id> <admin_id>` | `grp.new` | `group_id`, `admin_id` |
| `grp.ls <group_id>` | `grp.ls` | `group_id` |
| `grp.add <group_id> <member_id>` | `grp.add` | `group_id`, `member_id` |
| `grp.rm <group_id> <member_id>` | `grp.rm` | `group_id`, `member_id` |
| `grp.lib <group_id> <grant\|revoke> <member_id>` | `grp.lib` | `group_id`, `action`, `member_id` |
| `grp.del <group_id>` | `grp.del` | `group_id` |
| `dont.create <name> [desc]` | `dont.create` | `name`, `description` |
| `dont.add <name> <targets...>` | `dont.add` | `name`, `targets` (space-separated) |
| `dont.send <name> <to>` | `dont.send` | `name`, `to` |
| `dont.open <name> <to>` | `dont.open` | `name`, `to` |
| `dont.ls [name]` | `dont.ls` | `name` (optional) |

Arguments are parsed with `shlex.split`. The last declared argument in a command absorbs all remaining tokens, so `w This is a full sentence.` works as expected.

---

---

## 15. Web Application Development

### 15.1 Architecture Overview

AKASHA's HTTP portal (`http_portal`, default port 8000) serves both the JSON-RPC API and static web application files from a single process. Sub-applications are plain HTML/JS single-page apps stored under `services/static/` and accessed via path-based routing.

```
http://host:8000/          →  services/static/index.html        (Cosmos 3D)
http://host:8000/note      →  services/static/note/index.html   (Note UI)
http://host:8000/<name>    →  services/static/<name>/index.html (any app)
```

`BaseWebHandler.translate_path()` maps directory paths directly to their `index.html` without issuing a redirect, which ensures correct routing through reverse-proxy and port-forwarding environments (e.g. GitHub Codespaces).

All kernel access from the browser goes through `POST /api/rpc` with standard JSON-RPC 2.0 payloads.

---

### 15.2 Adding a New Frontend-Only Application

Place a single HTML file in `services/static/<name>/index.html`. No other configuration is required.

```
services/static/
  <name>/
    index.html    ← entire app lives here
```

The app is immediately accessible at `http://host:8000/<name>`.

Additional static assets (CSS, JS, images) can be placed in the same subdirectory and referenced with relative paths.

---

### 15.3 Authentication Flow

Every web app must implement the two-phase auth flow. The browser never handles passphrases directly — the kernel performs all credential verification.

**Phase 1 — Login (pre-auth, no session token required)**

```javascript
const resp = await fetch('/api/rpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        jsonrpc: '2.0',
        method:  'kernel.auth.verify',
        params:  { data: { user_id: user, passphrase: pass } },
        id:      'auth'
    })
});
const { result, error } = await resp.json();
if (error) { /* show error */ return; }
// result.status === 'authenticated'
const sessionToken = result.session_token;   // store this
const currentUser  = result.user_id;
```

**Phase 2 — All subsequent calls (session token required)**

```javascript
async function rpc(method, data = {}) {
    const res = await fetch('/api/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0', method,
            params:  { session_token: sessionToken, data },
            id:      Date.now()
        })
    });
    const json = await res.json();
    if (json.error) throw new Error(json.error.message);
    return json.result;
}
```

**Rules:**
- `session_token` is the opaque signed `akt:` credential returned by `kernel.auth.verify` — not your `user_id`.
- Every call except pre-auth methods must include `session_token` in `params`.
- Never hardcode a default username or pass `client_id` — both are legacy patterns that bypass the IAM layer.
- The login form must have no `value=` default on the username field.

---

### 15.4 Request Envelope

All RPC calls from the browser use the standard envelope defined in §3. The `data` object contains the method-specific parameters.

```json
{
  "jsonrpc": "2.0",
  "method":  "kernel.memory.write",
  "params":  {
    "session_token": "<token>",
    "data": { "text": "Hello, Akasha." }
  },
  "id": 1748304000000
}
```

The `id` field can be any unique value; using `Date.now()` is conventional for browser clients.

---

### 15.5 Adding a Sub-Service with Custom Endpoints

If an application requires API endpoints beyond `/api/rpc`, use the sub-service launcher.

**Step 1 — Create the route handler file**

```
services/routes/<name>.py
```

```python
# services/routes/<name>.py
from api.gateway import gateway

def my_handler(req_data: dict) -> dict:
    # session_token is pre-validated by the HTTP layer
    session_token = req_data.get("session_token", "")
    result = gateway.dispatch({
        "jsonrpc": "2.0",
        "method":  "some.kernel.method",
        "params":  {"session_token": session_token, "data": {}},
        "id":      "req",
    })
    return result.get("result", result)

ROUTES = {
    "/api/<name>/action": ("POST", my_handler),
}
```

`ROUTES` is a dict mapping URL path → `(HTTP_METHOD, handler_function)`. Only `"POST"` handlers are supported for custom endpoints (they receive a validated `session_token`).

**Step 2 — Launch with app_server.py**

```bash
python -m services.app_server --app <name> --port 8081
```

`app_server.py` auto-discovers `services/routes/<name>.py` and registers its routes. If the file does not exist, the service starts with `/api/rpc` and static files only.

Via `svc` commands (admin only):
```
svc restart <name>
```

The sub-service runs on a separate port as a subprocess managed by `ServiceManager`.

---

### 15.6 File Structure Reference

```
services/
  app_server.py          ← universal sub-service launcher
  http_gateway.py        ← BaseWebService / BaseWebHandler
  routes/
    cosmos.py            ← custom routes for Cosmos (example)
    <name>.py            ← optional; omit if /api/rpc is sufficient
  static/
    index.html           ← Cosmos 3D UI (served at /)
    note/
      index.html         ← Note UI (served at /note)
    <name>/
      index.html         ← any new app (served at /<name>)
```

---

### 15.7 Security Requirements

- **No hardcoded credentials.** Never embed `value="admin"` or any default identity in login forms.
- **session_token in every call.** All methods except the pre-auth whitelist (§4.2) require a valid `session_token`. Calls without one return `-32001 Authentication failed`.
- **Custom endpoints are authenticated.** `_execute_custom_handler` rejects requests missing `session_token` with HTTP 401 before the handler function is invoked.
- **No `client_id` in params.** The `client_id` field is a legacy pattern. The kernel derives identity exclusively from `session_token`.
- **XSS prevention.** Always escape user-supplied content before inserting into the DOM. Use `escHtml()` or equivalent for all dynamic text rendering.

---

*This document is generated from the AkashicTree source at `/home/user/AkashicTree`. Refer to `lib/akasha/kernel.py` for the authoritative method dispatcher and `lib/akasha/identity.py` for the IAM layer.*
