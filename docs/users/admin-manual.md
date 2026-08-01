# AKASHA Administrator Manual

**Version 1.2 — June 2026**

> This document is for system administrators only.  
> Commands described here are not visible in the standard `help` output and are not available to regular users.

---

## Table of Contents

1. [Permission Architecture](#1-permission-architecture)
2. [Initial Setup — Genesis Rite](#2-initial-setup--genesis-rite)
3. [su — Privileged Identity Switch](#3-su--privileged-identity-switch)
4. [User Management](#4-user-management)
5. [Group Management](#5-group-management)
6. [Security Considerations](#6-security-considerations)
7. [Service Management](#7-service-management)
8. [Troubleshooting](#8-troubleshooting)
9. [Ontology Management (admin / librarian)](#9-ontology-management-admin--librarian)

---

## 1. Permission Architecture

### 1.1 Role Hierarchy

AKASHA uses a five-level role hierarchy. Roles are strictly ordered — a higher role always subsumes the capabilities of all roles below it.

```
root (su root mode)
  └── ADMIN
        └── LIBRARIAN
              └── GROUP_ADMIN
                    └── USER
                          └── GUEST (unauthenticated)
```

> **root** is not a persistent role. It is a temporary elevated state activated via `su root` within an ADMIN session. It exists only for the duration of that shell session.

---

### 1.2 Capability Table

| Capability | root | ADMIN | LIBRARIAN | GROUP_ADMIN | USER | GUEST |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Read personal atoms | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Read collective scope | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Read group scope (own) | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Read all scopes (bypass) | ✓ | — | — | — | — | — |
| Write personal atoms | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Write to collective scope | ✓ | ✓ | ✓ | — | — | — |
| Write to group scope | ✓ | ✓ | — | ✓ | — | — |
| Delete own atoms | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Delete any atom | ✓ | ✓ | — | — | — | — |
| Run JCL jobs | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| View all users' jobs | ✓ | ✓ | — | — | — | — |
| Cancel any user's job | ✓ | ✓ | — | — | — | — |
| Manage groups (all) | ✓ | ✓ | — | — | — | — |
| Manage own group | ✓ | ✓ | — | ✓ | — | — |
| User CRUD (`user.*`) | ✓ | ✓ | — | — | — | — |
| Impersonate a client (`su <id>`) | ✓ | ✓ | — | — | — | — |
| Unrestricted scope bypass (`su root`) | ✓ | ✓ | — | — | — | — |
| Librarian privilege injection (`su librarian`) | ✓ | ✓ | — | — | — | — |
| Reload / reset ontology (`onto.reload` / `onto.reset`) | ✓ | ✓ | ✓ | — | — | — |
| Bulk scope delete (`onto.scope.drop`) | ✓ | ✓ | ✓ | — | — | — |
| Genesis redo (`onto.genesis.redo`) | ✓ | ✓ | — | — | — | — |
| Submit / cancel JCL jobs (`job.submit` / `job.cancel`) | ✓ | ✓ | ✓ | — | — | — |

---

### 1.3 Scope Access Table

Scopes are physical namespaces in the database. Atoms outside a client's granted scopes are **completely invisible** during graph traversal — they do not appear in search results, BFS expansion, or link lists.

| Scope identifier | Content | Who can read | Who can write |
|---|---|---|---|
| `scope:sys:universal` | Collective public ontology | All roles | ADMIN, LIBRARIAN |
| `scope:sys:dna` | Innate kernel DNA atoms | ADMIN+ only | System only |
| `scope:sys:admin` | System administration atoms | ADMIN+ only | ADMIN+ only |
| `owner:user_<id>` / `view:user_<id>` | Private atoms of user `<id>` | `<id>` and ADMIN | `<id>` only |
| `scope:group_<g>` / `view:group_<g>` | Shared atoms of group `<g>` | Group members | GROUP_ADMIN, ADMIN |
| `view:public` | Public read atoms | All roles | ADMIN+ only |

**root mode** (`su root`) adds `scope:sys:root` to the active scope list, which is recognized by the scope engine as a wildcard that bypasses all restrictions. This grants visibility of every atom in the database regardless of its scope tags.

---

### 1.4 Role Notes

#### ADMIN
The system administrator. Created during genesis. Can perform all operations including user management, group management, JCL oversight, and scope bypass via `su`. Only ADMIN can use `su`, create users, or delete other users' atoms.

#### LIBRARIAN
The collective knowledge curator. Can write to `scope:sys:universal` (the shared ontology commons). LIBRARIANs have access to all public knowledge but cannot read private atoms of other users, even with explicit permission. Typically assigned to automated curation processes or trusted editors.

#### GROUP_ADMIN
Manages one specific group. Can add and remove members of their own group, and grant/revoke group-level librarian status within that group. Has full read/write access to their group's shared scope. **Cannot** read private atoms of group members. **Cannot** see or manage other groups. **Cannot** use `user.*` commands.

#### USER
Standard researcher or contributor. Has full access to their own private scope and can read all collective and group scopes they belong to. All atoms written by default land in the user's private scope.

#### GUEST
Unauthenticated read-only observer. Can read atoms in `scope:sys:universal` and `view:public`. Cannot create atoms, run jobs, or authenticate into a session.

---

## 2. Initial Setup — Genesis Rite

The genesis rite is a one-time initialization ceremony that creates the system administrator account and binds the AKASHA instance to a name.

### Running Genesis

Start AKASHA without a pre-initialized nucleus. The system detects an uninitialized state and launches the genesis prompt:

```
python akasha.py

[+] Akasha online.
[ Genesis Rite ]

  No consciousness has been established.
  You are the first. Speak your true name.

  Name this system: MyAkasha
  Your identity (Admin ID): admin

  About to seal the pact:
    This system will be named  →  MyAkasha
    You will be known as       →  admin
  Is this correct? [yes/no]: yes

  Set passphrase:                  ••••••••••
  Confirm:                         ••••••••••

[ MyAkasha online. Welcome, admin. ]
akasha/admin $
```

> The **`Is this correct? [yes/no]`** confirmation is required — a bare Enter (or anything
> other than `yes`/`y`) re-asks the names rather than proceeding, so a first-time install
> can't sail past on a stray keypress before you've chosen the names.

After genesis:
- The admin account (`admin` in this example) is registered in the IAM database with role `ADMIN`.
- A canonical alias `admin` is also registered with the same passphrase, for use by automation and `run_single_shot`.
- The passphrase hash is stored in `data/central/nucleus.db` under both the IAM layer and the legacy `system` vault for backward compatibility.
- Subsequent logins require the passphrase.

### Migrating an Existing Installation

If you upgrade from a pre-persistence version, AKASHA automatically migrates on first boot:

1. Reads `("system", "admin_name")` and `("system", "passphrase_hash")` from nucleus.
2. Creates IAM records for both `<admin_name>` and `admin` with the existing passphrase hash.
3. All subsequent operations use the IAM layer exclusively.

No manual migration step is required.

---

## 3. su — Privileged Identity Switch

The `su` command allows an ADMIN to temporarily adopt a different identity or enter unrestricted root mode. It is hidden from `help` and inaccessible to non-ADMIN roles.

### Syntax

```
su <target>        Enter su mode for <target>
su exit            Return to normal admin identity
su                 Same as su exit
```

`<target>` is one of:
- `root` — unrestricted access mode (all scope restrictions lifted)
- `<client_id>` — impersonate a registered client

**A passphrase is required every time su is invoked** (except `su exit`).

---

### 3.1 su root — Root Mode

```
akasha/admin $ su root
Password: ••••••••••

  [SU] Root mode active — all scope restrictions lifted.

[root@akasha] #
```

In root mode:
- **All atoms are visible**, including private atoms of all users, system atoms, and DNA-level atoms.
- `ls` shows all atoms in the database, not just the admin's.
- Writes are still authored under the real admin's client ID (not `__root__`).
- The prompt changes to `[root@akasha] #` (red) as a visual warning.

Return to normal mode:

```
[root@akasha] # su exit
  [SU] Returned to normal mode.

akasha/admin $
```

> **Use root mode sparingly.** It is intended for emergency diagnostics, scope audits, and atom recovery — not for routine administration.

---

### 3.2 su librarian — Librarian Mode

Injects the LIBRARIAN role and `scope:sys:collective` into the current ADMIN session **without changing the authoring identity**. Atoms written in this mode are still attributed to the admin's real `client_id`, but the kernel treats the session as having full collective-scope write access.

Use this to perform ontology curations and reload operations without needing a separate LIBRARIAN account.

```
akasha/admin $ su librarian
Password: ••••••••••

  [SU] Librarian mode active — collective-scope write enabled.
  [SU] Writes are still attributed to: admin

akasha/admin(su:librarian) $
```

In librarian mode:
- **Write to `scope:sys:universal`** is permitted (collective ontology commons).
- `onto.reload`, `onto.reset`, `onto.pack.enable`, `onto.scope.drop` are all accessible.
- `job.submit` and `job.cancel` are available.
- The real admin identity (`admin`) is preserved — no authorship change.
- The prompt shows `akasha/admin(su:librarian) $` (yellow).

Return to normal:

```
akasha/admin(su:librarian) $ su exit
  [SU] Returned to normal mode.

akasha/admin $
```

> **Note:** `su librarian` is distinct from creating a dedicated LIBRARIAN user. It is a temporary privilege injection for admin-driven curation work. For automated or long-running curation, create a dedicated `librarian`-role account instead.

---

### 3.3 su \<client_id\> — Client Impersonation

Impersonation switches the effective client identity to that of another registered user, adopting their scopes and authorship for all subsequent commands.

```
akasha/admin $ su alice
Password: ••••••••••

  [SU] Impersonating: alice

akasha/admin(su:alice) $
```

In impersonation mode:
- All commands execute as `alice` — reads, writes, and links are scoped to alice's IAM scopes.
- Atoms written in this mode are authored as `alice`.
- The prompt shows `akasha/<real_id>(su:<target>) $` (yellow).
- `ls` shows alice's atoms only.

Return to normal:

```
akasha/admin(su:alice) $ su exit
  [SU] Returned to normal mode.

akasha/admin $
```

> **Use impersonation for debugging only.** Any writes during impersonation will be permanently attributed to the impersonated user.

---

### 3.4 Prompt Reference

| State | Prompt | Color |
|---|---|---|
| Normal ADMIN | `akasha/admin $` | Cyan |
| su root | `[root@akasha] #` | Red |
| su librarian | `akasha/admin(su:librarian) $` | Yellow |
| su \<user\> | `akasha/admin(su:alice) $` | Yellow |

---

## 4. User Management

All `user.*` commands require ADMIN role. They are hidden from the standard `help` output.

Passphrases are always entered interactively (never echoed to the terminal). The shell prompts twice for confirmation on `user.add` and `user.passwd`.

---

### `user.ls` — List All Users

Displays all registered users with their role, display name, and creation date. Passphrase hashes are never shown.

```
akasha/admin $ user.ls

  id                   role           display_name         created_at
  ─────────────────────────────────────────────────────────────────────
  admin                admin          admin                2026-05-26
  alice                user           Alice Tanaka         2026-05-26
  admin                admin          admin                2026-05-26
  lab_curator          librarian      Lab Curator          2026-05-27
  team_bob             group_admin    Bob Nakamura         2026-05-27
```

---

### `user.add <id> [role]` — Create a User

Creates a new user account. Role defaults to `user` if omitted. Valid roles: `user`, `librarian`, `group_admin`, `admin`.

The shell prompts for an initial passphrase (entered twice for confirmation).

```
akasha/admin $ user.add alice user
New passphrase: ••••••••••
Confirm passphrase: ••••••••••
{"status": "created", "client_id": "alice", "role": "user"}
```

```
akasha/admin $ user.add lab_curator librarian
New passphrase: ••••••••••
Confirm passphrase: ••••••••••
{"status": "created", "client_id": "lab_curator", "role": "librarian"}
```

After creation, the user can log in from any portal using their client ID and passphrase.

---

### `user.rm <id>` — Remove a User

Soft-deletes a user. Their atoms remain in the database but they can no longer authenticate. You cannot remove yourself.

```
akasha/admin $ user.rm old_account
{"status": "removed", "client_id": "old_account"}
```

> Atoms authored by a removed user remain in the graph. Use `su root` to locate and manage them if needed.

---

### `user.mod <id> <role>` — Change Role

Promotes or demotes a user's role. Valid roles: `user`, `librarian`, `group_admin`, `admin`.

```
akasha/admin $ user.mod alice librarian
{"status": "updated", "client_id": "alice", "role": "librarian"}

akasha/admin $ user.mod lab_curator user
{"status": "updated", "client_id": "lab_curator", "role": "user"}
```

> Promoting a user to `admin` grants full administrative access. Do this deliberately.

---

### `user.id <id>` — Show User Details

Displays full information for a single user, including groups and passphrase status.

```
akasha/admin $ user.id alice

────────────────────────────────────────────────
  id:           alice
  role:         user
  display:      Alice Tanaka
  created:      2026-05-26T09:14:32+00:00
  created_by:   admin
  passphrase:   yes
  groups:       dig2026, history_lab
```

The `passphrase` field shows `yes` if a hash is stored, or a warning if not. A user without a passphrase cannot log in interactively.

---

### `user.passwd <id>` — Change Passphrase

Updates the passphrase for any user. Prompts for the new passphrase twice.

```
akasha/admin $ user.passwd alice
New passphrase: ••••••••••
Confirm passphrase: ••••••••••
{"status": "passphrase_updated", "client_id": "alice"}
```

> This does not invalidate existing sessions. The new passphrase takes effect at the next login.

---

## 5. Group Management

Groups are named collections of users sharing a dedicated scope. The ADMIN creates groups and assigns a GROUP_ADMIN; the GROUP_ADMIN then manages membership day-to-day.

Group management commands are hidden from `help`.

---

### `grp.ls [group_id]` — List Groups or Members

Without an argument, lists all groups with their admin and member count.

```
akasha/admin $ grp.ls

  dig2026  admin: team_bob
    · team_bob
    · alice
    · carol [lib]

  history_lab  admin: prof_kim
    · prof_kim
    · alice
```

With a group ID, shows that group's members in detail.

```
akasha/admin $ grp.ls dig2026

  dig2026  admin: team_bob
    · team_bob
    · alice
    · carol [lib]
```

`[lib]` indicates the member holds group-librarian status within that group.

---

### `grp.new <group_id> <admin_id>` — Create a Group

Creates a new group and designates its GROUP_ADMIN. The GROUP_ADMIN must be a registered user.

```
akasha/admin $ grp.new dig2026 team_bob
{"status": "created", "group_id": "dig2026", "admin": "team_bob"}
```

This automatically:
1. Creates the group record in the IAM database.
2. Adds `team_bob` as the first (and only) member.
3. Grants `team_bob` the GROUP_ADMIN role if they don't already hold a higher role.

---

### `grp.add <group_id> <member_id>` — Add a Member

Adds a registered user to a group. Can be executed by the group's GROUP_ADMIN or any ADMIN.

```
akasha/admin $ grp.add dig2026 alice
{"status": "added", "group_id": "dig2026", "member": "alice"}
```

Once added, the user gains read access to `scope:group_dig2026` atoms.

---

### `grp.rm <group_id> <member_id>` — Remove a Member

Removes a user from a group. The GROUP_ADMIN cannot be removed (use `grp.del` to dissolve the group entirely). Can be executed by the group's GROUP_ADMIN or any ADMIN.

```
akasha/admin $ grp.rm dig2026 alice
{"status": "removed", "group_id": "dig2026", "member": "alice"}
```

After removal, the user loses access to group-scoped atoms. Their personal atoms are unaffected.

---

### `grp.lib <group_id> grant|revoke <member_id>` — Group Librarian Rights

Grants or revokes group-level librarian status for a group member. A group librarian can write atoms to the group scope; ordinary group members are read-only within the group scope.

```
akasha/admin $ grp.lib dig2026 grant carol
{"status": "librarian_granted", "group_id": "dig2026", "member": "carol"}

akasha/admin $ grp.lib dig2026 revoke carol
{"status": "librarian_revoked", "group_id": "dig2026", "member": "carol"}
```

> Group librarian status is scoped to the group — it does not affect the user's role in other groups or in the collective scope.

---

### `grp.del <group_id>` — Delete a Group

Dissolves a group entirely. Removes all membership records and the group's IAM entry. Requires ADMIN role.

```
akasha/admin $ grp.del old_project
{"status": "deleted", "group_id": "old_project"}
```

> Atoms that were written to the group scope remain in the database but become invisible to former members (they no longer hold the required scope tag). Use `su root` to locate orphaned group-scoped atoms if needed.

---

## 6. Security Considerations

### Passphrase Storage

Passphrases are stored in `data/central/nucleus.db` as **PBKDF2-SHA256 (200,000 iterations) over a per-user random salt**, and verified with a constant-time compare (`hmac.compare_digest`). The plaintext passphrase is never persisted anywhere in the system. The client computes a SHA-256 "presented hash" in the shell process before the RPC call (so the raw passphrase never traverses the kernel dispatcher); the server derives and stores the salted PBKDF2 of that presented hash.

> The per-user salt plus 200k PBKDF2 iterations resist offline brute-force even if the nucleus file is exfiltrated. Legacy unsalted records are upgraded transparently to the salted PBKDF2 form on the user's next login.

### IAM Persistence

All user and group records live in the `nucleus` table of `data/central/nucleus.db` under `category="iam"`. The database uses SQLite with `check_same_thread=False`. For multi-process deployments, ensure only one writer process accesses this file at a time.

### Hardcoded Identities

AKASHA retains two permanent system-process identities that are not stored in the database:

| Identity | Role | Purpose |
|---|---|---|
| `system.jataka` | ADMIN | Jataka spatiotemporal engine internal calls |
| `system.librarian` | LIBRARIAN | Automated collective-scope curation |

These identities cannot be modified or removed via `user.*` commands. They do not have passphrases and cannot authenticate interactively.

### su Security Model

- `su` requires the calling ADMIN's own passphrase on every invocation.
- `su exit` requires no passphrase (returning to normal is always safe).
- The su state is stored in the session context (in-memory), not persisted to disk. It is automatically cleared when the session ends.
- Writes made during `su <client_id>` are permanently attributed to the impersonated user — there is no audit trail distinguishing them from that user's own writes.
- `su root` bypasses all scope checks at the database read level. Do not run `su root` in an environment with untrusted users present.

### JCL and Privilege

JCL jobs run under the session token of the user who submitted them. The JCL allowlist (`lib/akasha/jcl/validator.py`) explicitly excludes `sys.su`, `user.*`, and `grp.*` methods — batch jobs cannot escalate privileges.

---

## 7. Service Management

AKASHA runs one or more background services alongside the interactive shell. Admins can inspect, stop, and restart services from within the REPL using the `svc` family of commands.

### Access Control

| Command | USER | ADMIN / su root |
|---|:---:|:---:|
| `svc ls` | ✓ | ✓ |
| `svc stop <name>` | ✗ | ✓ |
| `svc restart <name>` | ✗ | ✓ |

### `svc ls` — List Services

Shows all registered services with status, engine type, address or PID, and uptime. Available to all authenticated users.

```
akasha/admin $ svc ls

  name                   status   engine        address / pid          uptime
  ─────────────────────────────────────────────────────────────────────────────
  svc:cell               Active   cell-daemon   PID=4120               930s
  svc:web-portal         Active   httpd         PID=4310               928s
  svc:cosmos_visualizer  Active   uvicorn       PID=12345              120s
  job:onto-load          Done     job           —                      —
```

**The registry.** All services are **OS subprocesses** (`substrate: process`) managed by the one
Harmonia **Supervisor**, recorded in the persistent run-dir (`data/central/run/*`). There is no
in-process "thread" service — the web portal (httpd or uvicorn) runs as its own subprocess, so it
survives a CLI disconnect and is respawnable from a saved recipe. `svc ls` is a **cross-process**
view: any session (even a fresh CLI) sees every unit, because the truth is on disk, not in one
process's memory. `job:*` rows (e.g. `job:onto-load`) are in-process work, shown for visibility.

**Engine column:** `httpd` / `uvicorn` — the web portal subprocess; `cell-daemon` — the writer
root (`svc:cell`); `job` — an in-process job. Non-operators see a redacted `svc ls` (no recipe,
pid, or log path); an operator/admin sees the full descriptor.

### `svc stop <name>` — Stop a Service

Sends SIGTERM over the run-dir and waits its per-unit grace before SIGKILL. This works
**cross-process** (a pid + a signal — no spawn authority needed), so a thin CLI client can stop the
detached daemon or portal it never launched itself. The writer root `svc:cell` gets a generous
grace so it can checkpoint before exit.

```
akasha/admin $ svc stop cosmos_visualizer
  ✓ svc:cosmos_visualizer stopped
```

### `svc restart <name>` — Restart a Service

Relaunches the named service **from its persisted recipe (P1)**. The request is routed to the Cell
daemon (the sole respawn authority, P3), which stops the old process and spawns a new one from the
saved `argv`/`env`/`cwd` — so restart works from **any** session, not only the one that started it,
and after a crash the health tick brings an `on-failure`/`always` service back on its own.

```
akasha/admin $ svc restart web-portal
  Restarting web-portal…
  ✓ svc:web-portal restarted (PID 5561)
```

### Registered Services at Boot

| Name | Engine | Description |
|---|---|---|
| `svc:cell` | cell-daemon | The Cell daemon — owns the engine + the single nucleus writer (root) |
| `svc:web-portal` | httpd / uvicorn | Main JSON-RPC web gateway (`/api/rpc`), a serve-only subprocess |
| `svc:cosmos_visualizer` | subprocess | Graph visualization UI (if launched) |
| `svc:app:<operator>:<name>` | (varies) | Operator-added service programs (see the cookbook) |

> Operator-added services (dropped into `services/*` and registered with
> `supervisor.Supervisor.record_running(spec=…)`) are visible in `svc ls` exactly like the built-in
> ones. Start/stop/restart require admin locally; on a server deployment an admin can delegate
> `svc_operate` over a `svc:app:<operator>:*` selector with the `grant` command.

### Web Service Authentication

All HTTP endpoints require a valid `session_token`. The `/api/rpc` endpoint whitelists only `sys.ping`, `sys.status`, `kernel.auth.status`, `kernel.auth.verify`, and `kernel.genesis_rite` for unauthenticated access (the initial handshake). All other methods — including custom endpoints registered on sub-services — require a session token or the kernel returns `-32001 Authentication failed`.

Custom sub-service endpoints (e.g. `/api/cosmos/sync`) validate the presence of `session_token` at the HTTP handler layer before invoking the handler function. Missing or invalid tokens return HTTP 401.

---

## 8. Troubleshooting

### User cannot log in after `user.add`

Check that the passphrase was set during creation. Use `user.id <id>` and verify `passphrase: yes`. If it shows a warning, set the passphrase with `user.passwd <id>`.

### `su <id>` reports "unknown identity"

The target client ID must be registered via `user.add` before impersonation. Use `user.ls` to see registered users.

### Genesis admin not appearing in `user.ls`

The admin account is registered in IAM during genesis. If you upgraded from a pre-persistence version, the migration runs automatically on first boot. If the admin still does not appear, verify that `data/central/nucleus.db` exists and contains a `("system", "admin_name")` entry.

### Group member cannot see group-scoped atoms

Confirm the user is in the group with `grp.ls <group_id>`. If they are, verify their session is fresh (scopes are resolved at session start — a running session may need to be restarted after a group membership change).

### Passphrase prompt does not appear for `user.add`

Passphrase prompting is implemented in the stdio portal only. When calling `user.add` via the HTTP or MCP portal, provide `passphrase_hash` (SHA-256 hex) directly in the request body.

### The Cell daemon — the CLI is a client, the backend owns the jobs

`python akasha.py` no longer runs the engine inside your terminal. It starts (or reconnects to)
a persistent **Cell daemon** — a detached backend process that owns the engine, the write queue,
and every job (including the ontology load) — and attaches your CLI to it as a thin **client**
over a local socket. This is the intended topology: the backend is the server, the shell is a
client, exactly as the web portal (httpd) has always been a detached process.

The practical consequence: **closing the CLI never stops the daemon's work.** The first boot of a
large deployment (e.g. the thesaurus tier) imports the full ontology — including the
canon-normalize pass over ~120 K entries, which can run for many minutes — and that runs in the
daemon. You can start it, watch progress, disconnect your SSH session, and reconnect later to a
load that kept running the whole time:

```
python akasha.py            # spawns the Cell daemon if needed, attaches your CLI, do genesis
                            # …watch the load, then just close the terminal / drop SSH…
python akasha.py            # reconnects to the SAME daemon — the load never stopped
python akasha.py stop       # cleanly stop the daemon (finishes the in-flight write, checkpoints)
```

Watch load progress at any time with **`onto.status`** (packs · atoms; shows `Load COMPLETE`
when every bundled pack is in) and **`job.ls`** (per-step `N/N` for the running canon-normalize
job).

**Trust / security.** The local socket is created `0600`, owned by your user — only a process of
the **same UID** can connect, which is why the local CLI keeps its no-passphrase-for-genesis
convenience (the OS user boundary is the gate, exactly what `TRUST_LOCAL` means for the console).
A network client cannot reach the socket, so it can never obtain local trust. Design and full
rationale: `docs/for-llm/backend-daemon-local-ipc-spec.md`.

**Stopping.** `python akasha.py stop` sends the daemon a graceful `SIGTERM` and gives it a
generous grace window to finish the in-flight write and checkpoint the WAL before any forceful
kill — SIGKILLing the writer mid-checkpoint is exactly the crash this design avoids. `systemctl
stop` / `kill <pid>` do the same (the daemon routes `SIGTERM` through the graceful path).
`SIGHUP` (SSH hangup) is ignored, so a disconnect can never abort the daemon.

**Escape hatch.** To run the old in-process behaviour (engine inside the CLI, no daemon), use
`python akasha.py --embedded` or set `AKASHA_EMBEDDED=1`. `--stdio` (self-contained CLI, no web
portal) is also embedded.

**Relocating data.** `AKASHA_DATA_DIR` points the daemon and clients at a different cell
directory (default `<install>/data`). The daemon inherits it when the CLI spawns it.

> Do **not** run `--embedded` against the same `data/` while a Cell daemon is running — the
> nucleus is a single-writer store. Stop the daemon first (`python akasha.py stop`). The normal
> client path already prevents this: it routes every write through the one daemon.

### Concept model commands return `-32601 Method not found`

The Concept Model Plugin Registry failed to discover the class. Check:

1. The file is in `lib/akasha/concepts/` and does not start with `_`.
2. The class defines both `CONCEPT_PREFIX` (str) and `CONCEPT_METHODS` (dict) at the class level.
3. There are no import-time errors in the file — check kernel startup logs for `ConceptRegistry init failed` or per-file tracebacks.
4. The method name in the request matches `"{CONCEPT_PREFIX}.{suffix}"` exactly (case-sensitive).

### Concept model commands return `-32001 Permission denied`

IAM routing is missing for that method. Add the method name to `_METHOD_TO_ACTION` in
`lib/akasha/kernel.py` with the appropriate action string (`"read"`, `"write"`, or `"drop"`).
Restart the kernel after editing.

### Concept model discovery log

At kernel startup, the registry logs one INFO entry per discovered class and one DEBUG
entry per registered method (logger name `Akasha.ConceptRegistry`):

```
INFO  Akasha.ConceptRegistry  ConceptRegistry: registered NoteConcept (prefix=note)
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.new     → NoteConcept.op_new
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.add     → NoteConcept.op_add_chunk
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.list    → NoteConcept.op_list_chunks
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.edit    → NoteConcept.op_edit_chunk
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.move    → NoteConcept.op_move_chunk
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.undo    → NoteConcept.op_undo_edit
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.redo    → NoteConcept.op_redo_edit
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.restore → NoteConcept.op_restore_original
DEBUG Akasha.ConceptRegistry  ConceptRegistry: note.rename  → NoteConcept.op_rename
…
```

If a concept model's class is absent from the INFO log, the class was not discovered.
Enable debug logging (`LOG_LEVEL=DEBUG`) to see per-method registration and any
import-time warnings.

---

## 9. Ontology Management (admin / librarian)

These commands manage the lifecycle of the collective ontology stored in the nucleus. All require LIBRARIAN role or higher; `onto.genesis.redo` requires ADMIN.

Use `su librarian` (§3.2) to activate librarian mode within an admin session before running any of these commands.

---

### `onto.reload confirm=RELOAD` — Soft Reload

Clears all ontology load sentinels and re-triggers the boot load sequence. Ontology files in `ontology/common/` and `ontology/acquired/` are reprocessed. Existing atoms that hash-match loaded content are silently unified (idempotent). New atoms are inserted; nothing is deleted.

```
akasha/admin(su:librarian) $ onto.reload confirm=RELOAD
  [ont] ⚠  This will clear all ontology sentinels and re-run the full boot load.
  [ont] Proceeding...
  [ont] ✓ Reload triggered.
```

**When to use:** after placing new `.ak` files in `ontology/acquired/`, or after fixing a malformed ontology file that caused a sentinel to be skipped.

#### Updating an existing deployment (overwrite-install)

A running Cell keeps its ontology **load sentinels** in the persistent nucleus. Each pack's
sentinel is keyed by a **manifest hash of `basename:size:mtime`** over its files, so:

- an **ordinary restart** with untouched files → same hash → the load is skipped instantly;
- **overwrite-extracting a newer seed → then restarting** → a zip extract stamps every file
  with a fresh mtime, so every pack's hash changes → the boot **re-imports the whole ontology
  automatically**, reflecting the new seed's diff. **You do _not_ have to run a migration
  command** — a restart is the trigger.

The one gotcha is that the trigger is a **boot**: if you overwrite the files but the old
server process is still running (you only re-logged in), the graph still reflects the *older*
load until you restart. Symptoms of a not-yet-reloaded process — an empty concept-hierarchy
pane (its apex atom, e.g. `emo:emotion`, is a newer file), `cur.ls` returning `0 items`, or a
bundled pack missing from `onto.pack.list`.

**So the normal update is: overwrite-extract → restart the server → wait for the background
load.** `onto.reload confirm=RELOAD` (admin, librarian mode) is the **fallback** for when you
want to reload *without* a restart, edited files in place without changing their mtime, or
want to force a full re-run — it clears the sentinels and re-triggers the same background load.
Either way the re-import is content-addressed and **additive**: existing atoms are re-written
idempotently (no data loss, no user atoms touched); it does not purge atoms deleted upstream
(wipe `data/central`, or `onto.reset`, for a clean slate).

**Watching progress (the load is background, so it is observable, not a blind wait):**

```
akasha/admin $ onto.status
  ◐ Load IN PROGRESS   6/29 packs · relations … · curations … · atoms 41,208
    pending: world, tech, nutrition, drinks_c, …
  …
  ● Load COMPLETE   29/29 packs · relations ✓ · curations ✓     ← when done
```

Re-run `onto.status` to watch `atoms` climb and packs flip to `●`; `relations ✓` means all
atoms + links are in (the signal the portal and learn daemons gate on), `curations ✓` means
`cur.ls` is populated. `job.ls` shows the underlying background load jobs.

**Exiting before it finishes is safe.** The load is a background daemon writing each pack's
sentinel **only on completion**, through the single crash-stop write queue. If the process
exits (or is killed) mid-load, nothing is half-committed — the unfinished packs simply have no
sentinel and **re-load on the next boot**; completed packs are skipped. There is no corruption
and no manual cleanup: start the server again and the load resumes where it left off. (The load
only makes progress while the loader process is alive, so if you exit early, restart to let it
finish — then confirm with `onto.status`.)

> Static, pre-published assets do **not** need any reload: the archives Exhibition Room reads
> its exhibits from bundled `/curation/exports/*.json`, so it renders the moment the new
> archives are served — the load only repopulates the *graph* side (`cur.ls`, `narrate`, the
> concept-hierarchy panes, and newer `nar:` / `geo:` links).

---

### `onto.reset confirm=RESET` — Hard Reset

**Destructive.** Wipes all nucleus ontology data (atoms, links, aliases, sets whose `scope` tag is `scope:sys:universal`) except the DNA-layer atoms (`scope:sys:dna`). Then triggers a full reload from disk.

```
akasha/admin(su:librarian) $ onto.reset confirm=RESET
  [ont] ⚠  DESTRUCTIVE: this wipes all nucleus ontology data (DNA preserved).
  [ont] Confirm? Type RESET to proceed: RESET
  [ont] ✓ Reset complete. Reload triggered.
```

**When to use:** when the ontology is in an irrecoverably inconsistent state (e.g. after a failed partial import that left half-registered atoms). User personal atoms and IAM records are not affected.

---

### `onto.scope.drop <scope> confirm=DROP:<scope>` — Bulk Scope Delete *(librarian)*

Deletes all nucleus atoms carrying the specified scope tag. The confirmation string must include the scope name to prevent casual use.

```
akasha/admin(su:librarian) $ onto.scope.drop scope=acquired:botany confirm=DROP:acquired:botany
  [ont] ⚠  This will delete all atoms in scope: acquired:botany
  [ont] Keys found: 847
  [ont] Deleted 847 atoms.
```

**When to use:** to remove an acquired ontology pack that was loaded into the wrong scope, or to cleanly retire a discontinued topic area. After deletion, run `onto.reload` to confirm the remaining ontology is consistent.

> **Caution:** any links pointing to deleted atoms become dangling references. Run `onto.dump mode=links` before and after to verify no structural damage.

---

### `onto.genesis.redo confirm=GENESIS` — Genesis Anchor Reset *(admin only)*

Removes the two genesis anchor atoms (`sys:genesis:anchor` and `sys:genesis:complete`) from the nucleus. This allows `genesis_rite()` to run again on the next startup — useful for renaming the Akasha instance or correcting a genesis configuration error.

```
akasha/admin $ onto.genesis.redo confirm=GENESIS
  [gen] ⚠  This removes sys:genesis:anchor and sys:genesis:complete.
  [gen] ⚠  On next restart, the genesis ceremony will run again.
  [gen] All other atoms, users, and ontology data are preserved.
  [gen] Proceeding...
  [gen] ✓ Genesis anchors removed. Restart to re-run the genesis rite.
```

**What is preserved:** all user accounts, personal atoms, group data, acquired ontology, and all nucleus ontology atoms. Only the two genesis anchor records are removed.

**What to expect on restart:** the genesis prompt asks for a new Akasha instance name and admin credentials. Providing the same credentials re-links the existing admin account.

> **Use case:** renaming an Akasha installation from the initial name chosen during genesis. There is no other way to change the instance name without rebuilding from scratch.

---

*AKASHA Administrator Manual — Version 1.2 — June 2026*  
*© 2026 Akasha Protocol Project*
