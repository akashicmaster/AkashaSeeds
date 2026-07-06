"""
SQLiteBackend — SQLite implementation of AkashaBackend.

Uses WAL mode with per-thread connections and a single-threaded WriteQueue
to serialise all writes without locks.

This file is intentionally the only place in the codebase that imports
sqlite3, threading.local, or anything SQLite-specific.  All higher layers
depend on AkashaBackend only.
"""
import re
import sqlite3
import hashlib
import os
import json
import time
import threading
import functools
from datetime import datetime
from typing import Optional, List, Dict, Any

from lib.akasha.backends.base import AkashaBackend
from lib.akasha.dna import get_primal_sequence
from lib.akasha.jcl.write_queue import WriteQueue


def _queued(method):
    """Route a write method through the instance's WriteQueue."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        return self._wq.submit(lambda: method(self, *args, **kwargs))
    return wrapper


class SQLiteBackend(AkashaBackend):
    def __init__(self, db_path, is_volatile=False, sync_mode: str = "NORMAL"):
        self._db_path = os.path.abspath(db_path)
        self._local   = threading.local()   # per-thread connection storage

        # NORMAL: fast, safe against app crash, not against OS crash/SIGKILL.
        # FULL:   every WAL commit is fsynced — durable even on SIGKILL.
        # Use FULL for shared stores (nucleus.db) where sentinel durability matters.
        self._sync_mode: str = sync_mode.upper()

        if is_volatile and os.path.exists(self._db_path):
            os.remove(self._db_path)

        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        # Single-threaded write serializer — all write methods route through this.
        # Named after the db file for log clarity in multi-cortex deployments.
        self._wq = WriteQueue(name=f"core-writer:{os.path.basename(db_path)}")

        # Batch-write counter: tracks nested begin_batch() / end_batch() calls.
        # When > 0, PRAGMA synchronous=OFF is active on the WriteQueue connection
        # so commits are instant (no fsync).  Only the WriteQueue thread
        # reads/writes this counter → no locking needed.
        self._batch_depth: int = 0

        # Boot the main-thread connection so table creation proceeds normally
        _ = self.conn

        # Restrict on-disk permissions: these files hold ground-truth data and,
        # for nucleus.db, the HMAC signing secret and passphrase hashes.  Owner
        # read/write only (0600 files, 0700 dir).  Best-effort — a filesystem
        # that doesn't support chmod (some mounts) must not break boot.
        self._harden_permissions()

        self._create_tables()
        self._migrate_tables()
        self._unfold_dna()

    def _harden_permissions(self) -> None:
        """Best-effort 0600 on the DB file (and WAL/SHM sidecars) + 0700 on its dir."""
        try:
            os.chmod(os.path.dirname(self._db_path), 0o700)
        except OSError:
            pass
        for suffix in ("", "-wal", "-shm"):
            p = self._db_path + suffix
            try:
                if os.path.exists(p):
                    os.chmod(p, 0o600)
            except OSError:
                pass

    # ── Connection management ──────────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Return this thread's dedicated SQLite connection.

        Each thread gets its own connection to the same database file.
        WAL journal mode allows concurrent reads and serialises writes at the
        file level, so no Python-level lock is needed.
        """
        if not getattr(self._local, 'conn', None):
            c = sqlite3.connect(self._db_path, check_same_thread=False)
            c.row_factory = sqlite3.Row
            # WAL mode: readers and the single writer never block each other.
            # Multiple thread-local connections can read while the WriteQueue
            # thread writes — no SQLITE_BUSY on read/write overlap.
            # Durability is handled at the layer above (synchronous=FULL for
            # nucleus, filesystem sentinel files) — not by journal mode.
            c.execute("PRAGMA journal_mode=WAL")
            c.execute(f"PRAGMA synchronous={self._sync_mode}")
            # Retry for up to 5 s on SQLITE_BUSY — guards against any residual
            # overlap between WriteQueue threads writing to the same DB file
            # (e.g. IAM vault writes racing with JCL atom writes on nucleus.db).
            c.execute("PRAGMA busy_timeout=5000")
            self._local.conn = c
        return self._local.conn

    def _commit(self) -> None:
        """
        Commit the current transaction, ignoring the benign 'no transaction is
        active' state that can arise when an INSERT OR IGNORE skips all rows.
        """
        try:
            self.conn.commit()
        except sqlite3.OperationalError as exc:
            if "no transaction is active" not in str(exc):
                raise

    def begin_batch(self) -> None:
        """
        Enter batch-write mode: switch the WriteQueue thread's connection to
        synchronous=OFF so commits are instant (no fsync per write).  Each write
        still commits immediately so cross-thread reads see up-to-date data.
        Calls may be nested; the pragma is restored only when the outermost
        end_batch() is reached.  Routes through WriteQueue for correct ordering.
        """
        def _enter():
            self._batch_depth += 1
            if self._batch_depth == 1:
                self.conn.execute("PRAGMA synchronous=OFF")
        self._wq.submit(_enter)

    def end_batch(self) -> None:
        """
        Exit batch-write mode and restore the configured synchronous mode.
        Routes through WriteQueue so the pragma change is ordered after all pending writes.
        """
        def _exit():
            self._batch_depth = max(0, self._batch_depth - 1)
            if self._batch_depth == 0:
                try:
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass
                self.conn.execute(f"PRAGMA synchronous={self._sync_mode}")
        self._wq.submit(_exit)

    def set_sync_fast(self) -> None:
        """
        Set synchronous=OFF on the CALLING thread's connection.
        Used to speed up direct (non-@_queued) commits that run in the caller's
        thread (e.g. NucleusEngine.set_alias → _derive_alias_collections + _commit).
        """
        self.conn.execute("PRAGMA synchronous=OFF")

    def set_sync_normal(self) -> None:
        """Restore the configured synchronous mode on the CALLING thread's connection."""
        try:
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
        self.conn.execute(f"PRAGMA synchronous={self._sync_mode}")

    def close(self) -> None:
        """
        Drain and shut down the write queue, then checkpoint the WAL so all
        committed writes are merged into the main DB file before exit.
        Called on graceful shutdown (atexit); SIGKILL durability relies on
        synchronous=FULL ensuring each commit reaches disk before returning.
        """
        def _checkpoint():
            try:
                self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self.conn.commit()
            except Exception:
                pass
        self._wq.submit(_checkpoint)
        self._wq.shutdown()

    # ── Schema bootstrap & migration ──────────────────────────────────────────

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chunks (key TEXT PRIMARY KEY, content TEXT, created_at TEXT, meta TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS aliases (alias TEXT PRIMARY KEY, key TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS links (src TEXT, dst TEXT, rel TEXT, w REAL DEFAULT 1.0, dir TEXT DEFAULT 'forward', type TEXT DEFAULT 'atom', UNIQUE(src, dst, rel))")
        cursor.execute("CREATE TABLE IF NOT EXISTS collection_defs (name TEXT PRIMARY KEY, meta TEXT DEFAULT '{}')")

        # Computational dimension — leaf:, ns:, lang: and user-defined sets.
        # Access scopes (scope:/owner:/view:) live in chunk_access, not here.
        cursor.execute("CREATE TABLE IF NOT EXISTS collections (name TEXT, key TEXT, UNIQUE(name, key))")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_key ON collections(key)")

        # Namespace registry: pre-aggregated counts updated at write time.
        # Key is the full namespace prefix (e.g. "word", "word:en").
        # Avoids alias table scans at query time.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS namespace_counts
            (ns TEXT PRIMARY KEY, count INTEGER DEFAULT 0)
        """)
        # Backfill from existing ns: collections if table is empty.
        if cursor.execute("SELECT COUNT(*) FROM namespace_counts").fetchone()[0] == 0:
            cursor.execute("""
                INSERT OR IGNORE INTO namespace_counts (ns, count)
                SELECT REPLACE(name, 'ns:', ''), COUNT(*)
                FROM collections WHERE name LIKE 'ns:%'
                GROUP BY name
            """)

        # Access control — final security filter for every atom retrieval.
        cursor.execute("CREATE TABLE IF NOT EXISTS chunk_access (key TEXT, scope TEXT, UNIQUE(key, scope))")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_access_key   ON chunk_access(key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_access_scope ON chunk_access(scope)")

        cursor.execute("CREATE TABLE IF NOT EXISTS nucleus (category TEXT, identifier TEXT, data TEXT, PRIMARY KEY(category, identifier))")

        # DTN store-and-forward queue (see AkashaBackend.enqueue_pending_link).
        cursor.execute("CREATE TABLE IF NOT EXISTS pending_links (id INTEGER PRIMARY KEY AUTOINCREMENT, src TEXT, dst TEXT, rel TEXT, author TEXT, timestamp REAL)")

        # Deferred collection derivation queue.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_derivations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT,
                alias      TEXT,
                queued_at  REAL,
                UNIQUE(key, alias)
            )
        """)

        # Alias collision log — written whenever set_alias overwrites an existing binding.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alias_collision_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                alias    TEXT    NOT NULL,
                old_key  TEXT    NOT NULL,
                new_key  TEXT    NOT NULL,
                ts       REAL    NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_acl_ts    ON alias_collision_log(ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_acl_alias ON alias_collision_log(alias)")

        self._commit()

    def _migrate_tables(self):
        """Safely inject new columns into existing legacy tables."""
        cursor = self.conn.cursor()

        migrations = [
            ("chunks", "meta TEXT DEFAULT '{}'"),
            ("chunks", "created_at TEXT DEFAULT '1970-01-01 00:00:00'"),
            ("chunks", "author TEXT DEFAULT 'system'"),
            ("chunks", "status TEXT DEFAULT 'verified'"),
            ("links", "author TEXT DEFAULT 'system'"),
            ("links", "status TEXT DEFAULT 'verified'"),
            ("links", "updated_at REAL DEFAULT 0.0")
        ]
        for table, column_def in migrations:
            try: cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
            except sqlite3.OperationalError: pass

        try: cursor.execute("ALTER TABLE collection_defs ADD COLUMN meta TEXT DEFAULT '{}'")
        except sqlite3.OperationalError: pass

        try:
            cursor.execute("ALTER TABLE alias_collision_log ADD COLUMN resolved INTEGER NOT NULL DEFAULT 0")
            cursor.execute("ALTER TABLE alias_collision_log ADD COLUMN event TEXT NOT NULL DEFAULT 'overwrite'")
        except sqlite3.OperationalError:
            pass

        # Promote access scopes from collections → chunk_access (idempotent).
        cursor.execute("""
            INSERT OR IGNORE INTO chunk_access (key, scope)
            SELECT key, name FROM collections
            WHERE  name LIKE 'scope:%' OR name LIKE 'owner:%' OR name LIKE 'view:%'
        """)
        cursor.execute("""
            DELETE FROM collections
            WHERE  name LIKE 'scope:%' OR name LIKE 'owner:%' OR name LIKE 'view:%'
        """)

        # Drain pending_derivations queued during last session.
        pending = cursor.execute("SELECT id, key, alias FROM pending_derivations ORDER BY id").fetchall()
        for row in pending:
            pid   = row["id"]    if isinstance(row, sqlite3.Row) else row[0]
            key   = row["key"]   if isinstance(row, sqlite3.Row) else row[1]
            alias = row["alias"] if isinstance(row, sqlite3.Row) else row[2]
            self._derive_alias_collections(alias, key)
            cursor.execute("DELETE FROM pending_derivations WHERE id=?", (pid,))

        # Full alias backfill — catch-all for gaps (INSERT OR IGNORE, idempotent).
        rows = cursor.execute("SELECT alias, key FROM aliases").fetchall()
        for row in rows:
            self._derive_alias_collections(
                row["alias"] if isinstance(row, sqlite3.Row) else row[0],
                row["key"]   if isinstance(row, sqlite3.Row) else row[1],
            )
        self._commit()

    def _unfold_dna(self):
        dna = get_primal_sequence()
        for alias, text in dna.items():
            r = self.conn.execute("SELECT key FROM aliases WHERE alias=?", (alias,)).fetchone()
            if not r:
                key = hashlib.sha256(text.encode()).hexdigest()
                self.conn.execute(
                    "INSERT OR IGNORE INTO chunks (key, content, created_at, meta, author, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (key, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "{}", "system.dna", "verified")
                )
                self.conn.execute("INSERT OR IGNORE INTO aliases VALUES (?, ?)", (alias, key))
                self.conn.execute(
                    "INSERT OR IGNORE INTO chunk_access (key, scope) VALUES (?, ?)",
                    (key, "scope:sys:universal")
                )
                self._derive_alias_collections(alias, key)
        self._commit()

    # ── ISO 639-1 language code set (used by _derive_alias_collections) ────────

    _ISO_639_1 = frozenset({
        "aa","ab","ae","af","ak","am","an","ar","as","av","ay","az",
        "ba","be","bg","bh","bi","bm","bn","bo","br","bs","ca","ce",
        "ch","co","cr","cs","cu","cv","cy","da","de","dv","dz","ee",
        "el","en","eo","es","et","eu","fa","ff","fi","fj","fo","fr",
        "fy","ga","gd","gl","gn","gu","gv","ha","he","hi","ho","hr",
        "ht","hu","hy","hz","ia","id","ie","ig","ii","ik","io","is",
        "it","iu","ja","jv","ka","kg","ki","kj","kk","kl","km","kn",
        "ko","kr","ks","ku","kv","kw","ky","la","lb","lg","li","ln",
        "lo","lt","lu","lv","mg","mh","mi","mk","ml","mn","mr","ms",
        "mt","my","na","nb","nd","ne","ng","nl","nn","no","nr","nv",
        "ny","oc","oj","om","or","os","pa","pi","pl","ps","pt","qu",
        "rm","rn","ro","ru","rw","sa","sc","sd","se","sg","si","sk",
        "sl","sm","sn","so","sq","sr","ss","st","su","sv","sw","ta",
        "te","tg","th","ti","tk","tl","tn","to","tr","ts","tt","tw",
        "ty","ug","uk","ur","uz","ve","vi","vo","wa","wo","xh","yi",
        "yo","za","zh","zu",
    })

    def _derive_alias_collections(self, alias: str, key: str) -> None:
        """
        Register leaf:, ns:, and lang: collections for a namespaced alias.
        Caller owns the commit.

        'word:en:love' → leaf:love, ns:word, ns:word:en, lang:en
        """
        if ":" not in alias:
            return
        parts = alias.split(":")
        leaf = parts[-1]
        if leaf:
            self.conn.execute(
                "INSERT OR IGNORE INTO collections (name, key) VALUES (?, ?)",
                (f"leaf:{leaf}", key),
            )
        prefix = ""
        for ns in parts[:-1]:
            prefix = f"{prefix}:{ns}" if prefix else ns
            inserted = self.conn.execute(
                "INSERT OR IGNORE INTO collections (name, key) VALUES (?, ?)",
                (f"ns:{prefix}", key),
            ).rowcount
            if inserted:
                # New member in this namespace — increment the pre-aggregated counter.
                self.conn.execute(
                    "INSERT INTO namespace_counts (ns, count) VALUES (?, 1)"
                    " ON CONFLICT(ns) DO UPDATE SET count = count + 1",
                    (prefix,),
                )
            if ns in self._ISO_639_1:
                self.conn.execute(
                    "INSERT OR IGNORE INTO collections (name, key) VALUES (?, ?)",
                    (f"lang:{ns}", key),
                )

    # ── Atom CRUD ──────────────────────────────────────────────────────────────

    @_queued
    def put_chunk_raw(self, key: str, content: Optional[str], meta_str: str,
                      author: str, status: str, ts: float) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO chunks (key, content, created_at, meta, author, status) VALUES (?, ?, ?, ?, ?, ?)",
            (key, content, str(ts), meta_str, author, status)
        )
        self._commit()

    @_queued
    def update_chunk_status(self, key: str, status: str,
                            content: Optional[str] = None) -> None:
        if content is not None:
            self.conn.execute("UPDATE chunks SET status=?, content=? WHERE key=?", (status, content, key))
        else:
            self.conn.execute("UPDATE chunks SET status=? WHERE key=?", (status, key))
        self._commit()

    def get_chunk_raw(self, key: str) -> Optional[dict]:
        r = self.conn.execute(
            "SELECT content, meta, status, author FROM chunks WHERE key=?", (key,)
        ).fetchone()
        return dict(r) if r else None

    @_queued
    def drop_chunk(self, key: str) -> None:
        self.conn.execute("DELETE FROM chunks WHERE key=?", (key,))
        self.conn.execute("DELETE FROM aliases WHERE key=?", (key,))
        self.conn.execute("DELETE FROM links WHERE src=? OR dst=?", (key, key))
        self.conn.execute("DELETE FROM collections WHERE key=?", (key,))
        self.conn.execute("DELETE FROM chunk_access WHERE key=?", (key,))
        self._commit()

    @_queued
    def update_meta(self, key: str, meta_dict: dict) -> None:
        self.conn.execute("UPDATE chunks SET meta=? WHERE key=?", (json.dumps(meta_dict), key))
        self._commit()

    # ── Access Control ─────────────────────────────────────────────────────────

    @_queued
    def put_chunk_access(self, key: str, scopes: List[str]) -> None:
        for s in scopes:
            self.conn.execute(
                "INSERT OR IGNORE INTO chunk_access (key, scope) VALUES (?, ?)", (key, s)
            )
        self._commit()

    @_queued
    def remove_chunk_access(self, key: str, scope: Optional[str] = None) -> None:
        if scope:
            self.conn.execute("DELETE FROM chunk_access WHERE key=? AND scope=?", (key, scope))
        else:
            self.conn.execute("DELETE FROM chunk_access WHERE key=?", (key,))
        self._commit()

    def get_chunk_access_scopes(self, key: str) -> List[str]:
        return [r["scope"] for r in self.conn.execute(
            "SELECT scope FROM chunk_access WHERE key=?", (key,)
        ).fetchall()]

    def check_chunk_access_any(self, key: str, allowed_scopes: List[str]) -> bool:
        if not allowed_scopes:
            return False
        ph = ",".join("?" * len(allowed_scopes))
        r = self.conn.execute(
            f"SELECT 1 FROM chunk_access WHERE key=? AND scope IN ({ph}) LIMIT 1",
            [key] + allowed_scopes
        ).fetchone()
        return r is not None

    # ── Deferred Collection Derivation Queue ───────────────────────────────────

    @_queued
    def enqueue_derivation(self, key: str, alias: str) -> None:
        """
        Enqueue collection derivation for an alias to be processed by Harmonia/JCL.

        Write path (synchronous, fast):
          set_alias → put_alias + enqueue_derivation

        Index path (async, via JCL job completion or startup drain):
          drain_derivations → _derive_alias_collections (leaf:, ns:, lang:)
        """
        self.conn.execute(
            "INSERT OR IGNORE INTO pending_derivations (key, alias, queued_at) VALUES (?, ?, ?)",
            (key, alias, time.time())
        )
        self._commit()

    @_queued
    def drain_derivations(self) -> int:
        """Process all pending collection derivations in queue order."""
        rows = self.conn.execute(
            "SELECT id, key, alias FROM pending_derivations ORDER BY id"
        ).fetchall()
        count = 0
        for row in rows:
            self._derive_alias_collections(row["alias"], row["key"])
            self.conn.execute("DELETE FROM pending_derivations WHERE id=?", (row["id"],))
            count += 1
        if count:
            self._commit()
        return count

    def peek_pending_derivations(self) -> List[dict]:
        rows = self.conn.execute(
            "SELECT key, alias FROM pending_derivations ORDER BY id"
        ).fetchall()
        return [{"key": r["key"], "alias": r["alias"]} for r in rows]

    @_queued
    def derive_alias_collections(self, alias: str, key: str) -> None:
        self._derive_alias_collections(alias, key)
        self._commit()

    # ── Aliases ────────────────────────────────────────────────────────────────

    @_queued
    def put_alias(self, key: str, alias: str) -> Optional[str]:
        try:
            self.conn.execute("INSERT OR REPLACE INTO aliases VALUES (?, ?)", (alias, key))
            self._commit()
            return alias
        except sqlite3.IntegrityError:
            return None

    @_queued
    def delete_alias(self, alias: str) -> None:
        self.conn.execute("DELETE FROM aliases WHERE alias=?", (alias,))
        self._commit()

    @_queued
    def clear_ontology_data(self, preserve_keys: List[str]) -> None:
        """
        Hard-reset: delete all ontology data except the given keys (DNA atoms).
        Clears chunks, aliases, links, collections, namespace_counts, pending_links.
        Caller is responsible for re-running _unfold_dna() afterward.
        """
        ph = ",".join("?" * len(preserve_keys))
        self.conn.execute("DELETE FROM links")
        self.conn.execute("DELETE FROM pending_links")
        self.conn.execute("DELETE FROM collections")
        self.conn.execute("DELETE FROM namespace_counts")
        self.conn.execute(f"DELETE FROM chunks WHERE key NOT IN ({ph})", preserve_keys)
        self.conn.execute(f"DELETE FROM aliases WHERE key NOT IN ({ph})", preserve_keys)
        self.conn.execute(f"DELETE FROM chunk_access WHERE key NOT IN ({ph})", preserve_keys)
        self._commit()

    @_queued
    def log_alias_collision(self, alias: str, old_key: str, new_key: str,
                            event: str = "overwrite") -> None:
        try:
            self.conn.execute(
                "INSERT INTO alias_collision_log (alias, old_key, new_key, ts, event, resolved) VALUES (?, ?, ?, ?, ?, 0)",
                (alias, old_key, new_key, time.time(), event),
            )
            self._commit()
        except Exception:
            pass  # best-effort

    def get_alias_collision_log(self, since: float = 0.0, limit: int = 200,
                                unresolved_only: bool = False) -> list:
        sql = "SELECT id, alias, old_key, new_key, ts, event, resolved FROM alias_collision_log WHERE ts >= ?"
        args: list = [since]
        if unresolved_only:
            sql += " AND resolved = 0"
        sql += " ORDER BY ts DESC LIMIT ?"
        args.append(limit)
        return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    @_queued
    def resolve_alias_collision(self, alias: str) -> int:
        cur = self.conn.execute(
            "UPDATE alias_collision_log SET resolved = 1 WHERE alias = ? AND resolved = 0",
            (alias,)
        )
        self._commit()
        return cur.rowcount

    @_queued
    def clear_alias_collision_log(self) -> int:
        cur = self.conn.execute("DELETE FROM alias_collision_log")
        self._commit()
        return cur.rowcount

    def get_key_by_alias(self, alias: str) -> Optional[str]:
        # 1. Exact match
        r = self.conn.execute("SELECT key FROM aliases WHERE alias=?", (alias,)).fetchone()
        if r: return r["key"]
        # 2. Case-insensitive
        alias_lc = alias.lower()
        r = self.conn.execute("SELECT key FROM aliases WHERE LOWER(alias)=?", (alias_lc,)).fetchone()
        if r: return r["key"]
        # 3 & 4. Compound-word normalisation (spaces/hyphens ↔ compact form)
        compact = re.sub(r'[\s\-]+', '', alias_lc)
        if compact != alias_lc:
            r = self.conn.execute("SELECT key FROM aliases WHERE LOWER(alias)=?", (compact,)).fetchone()
            if r: return r["key"]
        r = self.conn.execute(
            "SELECT key FROM aliases WHERE LOWER(REPLACE(REPLACE(alias,' ',''),'-',''))=?",
            (compact,)
        ).fetchone()
        return r["key"] if r else None

    def get_aliases_by_key(self, key: str) -> List[str]:
        return [r["alias"] for r in self.conn.execute(
            "SELECT alias FROM aliases WHERE key=?", (key,)
        ).fetchall()]

    def get_aliases_by_pattern(self, pattern: str) -> List[dict]:
        # LOWER() is SQLite built-in and covers ASCII only (U+0000–U+007F).
        # Sufficient while aliases are ASCII namespace:word identifiers.
        # For Unicode aliases: compile with ICU (-DSQLITE_ENABLE_ICU) or add
        # a Python-side collation via conn.create_collation("NOCASE_UNICODE", ...).
        return [dict(r) for r in self.conn.execute(
            "SELECT alias, key FROM aliases WHERE LOWER(alias) LIKE LOWER(?)", (pattern,)
        ).fetchall()]

    # ── Links ──────────────────────────────────────────────────────────────────

    @_queued
    def remove_link_raw(self, src: str, dst: str, rel: str) -> None:
        self.conn.execute("DELETE FROM links WHERE src=? AND dst=? AND rel=?", (src, dst, rel))
        self._commit()

    @_queued
    def put_link_raw(self, src: str, dst: str, rel: str, w: float = 1.0,
                     d: str = "forward", t: str = "atom", author: str = "system",
                     status: str = "verified", ts: float = 0.0) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO links (src, dst, rel, w, dir, type, author, status, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (src, dst, rel, w, d, t, author, status, ts)
        )
        self._commit()

    def get_adjacent_links(self, src: str,
                           rel_pattern: Optional[str] = None) -> List[dict]:
        query = "SELECT dst, rel, w, dir, type, author, status FROM links WHERE src=?"
        params = [src]
        if rel_pattern:
            query += " AND rel LIKE ?"
            params.append(rel_pattern)
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def get_incoming_links(self, dst: str,
                           rel_pattern: Optional[str] = None) -> List[dict]:
        query = "SELECT src, rel, w, dir, type, author, status FROM links WHERE dst=?"
        params = [dst]
        if rel_pattern:
            query += " AND rel LIKE ?"
            params.append(rel_pattern)
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    # ── Collections ───────────────────────────────────────────────────────────

    def get_collection_members_scoped(self, collection_name: str,
                                      allowed_scopes: List[str]) -> List[str]:
        perm = [s for s in allowed_scopes if s.startswith(self._ACCESS_PREFIXES)]
        if not perm:
            return []
        placeholders = ",".join("?" * len(perm))
        query = f"""
            SELECT DISTINCT c.key
            FROM   collections c
            WHERE  c.name = ?
              AND  EXISTS (
                       SELECT 1 FROM chunk_access a
                       WHERE  a.key = c.key
                         AND  a.scope IN ({placeholders})
                   )
        """
        return [r["key"] for r in self.conn.execute(query, [collection_name] + perm).fetchall()]

    def get_collection_members_locale_ordered(
        self, collection_name: str, allowed_scopes: List[str],
        locale_codes: List[str],
    ) -> List[str]:
        perm = [s for s in allowed_scopes if s.startswith(self._ACCESS_PREFIXES)]
        if not perm:
            return []
        if not locale_codes:
            return self.get_collection_members_scoped(collection_name, allowed_scopes)

        lang_tags = [f"lang:{c}" for c in locale_codes]
        perm_ph   = ",".join("?" * len(perm))
        lang_ph   = ",".join("?" * len(lang_tags))
        neutral_rank = len(locale_codes)
        case_when = " ".join(f"WHEN ? THEN {i}" for i in range(len(lang_tags)))

        query = f"""
            SELECT DISTINCT c.key,
                COALESCE(
                    (SELECT MIN(CASE lc.name {case_when} ELSE 999 END)
                     FROM   collections lc
                     WHERE  lc.key = c.key AND lc.name LIKE 'lang:%'),
                    {neutral_rank}
                ) AS lang_rank
            FROM   collections c
            WHERE  c.name = ?
              AND  EXISTS (
                       SELECT 1 FROM chunk_access a
                       WHERE  a.key = c.key AND a.scope IN ({perm_ph})
                   )
              AND  (
                       EXISTS (
                           SELECT 1 FROM collections lc
                           WHERE  lc.key = c.key AND lc.name IN ({lang_ph})
                       )
                       OR NOT EXISTS (
                           SELECT 1 FROM collections lc
                           WHERE  lc.key = c.key AND lc.name LIKE 'lang:%'
                       )
                   )
            ORDER BY lang_rank
        """
        params = lang_tags + [collection_name] + perm + lang_tags
        return [r["key"] for r in self.conn.execute(query, params).fetchall()]

    @_queued
    def add_to_collection(self, name: str, key: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO collections (name, key) VALUES (?, ?)", (name, key))
        self._commit()

    @_queued
    def remove_from_collection(self, name: str, key: str) -> None:
        self.conn.execute("DELETE FROM collections WHERE name=? AND key=?", (name, key))
        self._commit()

    def get_distinct_collection_names(self, prefix: str = None) -> List[str]:
        if prefix:
            return [r["name"] for r in self.conn.execute(
                "SELECT DISTINCT name FROM collections WHERE name LIKE ? ORDER BY name", (prefix,)
            ).fetchall()]
        return [r["name"] for r in self.conn.execute(
            "SELECT DISTINCT name FROM collections ORDER BY name"
        ).fetchall()]

    def get_collection_members(self, name: str) -> List[str]:
        return [r["key"] for r in self.conn.execute(
            "SELECT key FROM collections WHERE name=?", (name,)
        ).fetchall()]

    def collection_exists(self, name: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM collections WHERE name=? LIMIT 1", (name,)
        ).fetchone() is not None

    def get_collections_for_key(self, key: str) -> List[str]:
        return [r["name"] for r in self.conn.execute(
            "SELECT name FROM collections WHERE key=?", (key,)
        ).fetchall()]

    def get_keys_in_any_collection(self, names: List[str]) -> List[str]:
        if not names: return []
        placeholders = ','.join(['?'] * len(names))
        return [r["key"] for r in self.conn.execute(
            f"SELECT DISTINCT key FROM collections WHERE name IN ({placeholders})", names
        ).fetchall()]

    def get_keys_in_all_collections(self, names: List[str]) -> List[str]:
        if not names: return []
        placeholders = ','.join(['?'] * len(names))
        query = f"""
            SELECT key FROM collections
            WHERE name IN ({placeholders})
            GROUP BY key
            HAVING COUNT(DISTINCT name) = ?
        """
        return [r["key"] for r in self.conn.execute(query, names + [len(names)]).fetchall()]

    @_queued
    def clear_collection(self, name: str) -> None:
        self.conn.execute("DELETE FROM collections WHERE name=?", (name,))
        self._commit()

    # ── Collection Definitions ────────────────────────────────────────────────

    @_queued
    def upsert_collection_def(self, name: str, meta: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO collection_defs (name, meta) VALUES (?, ?)",
            (name, json.dumps(meta, ensure_ascii=False))
        )
        self._commit()

    def get_collection_def(self, name: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT meta FROM collection_defs WHERE name=?", (name,)
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["meta"] or "{}")
        except Exception:
            return {}

    @_queued
    def merge_collection_def_meta(self, name: str, updates: dict) -> None:
        """Merge `updates` into the set's metadata dict (upsert).
        Runs inside the WriteQueue; re-entrance guard lets get_collection_def
        and upsert_collection_def execute directly without deadlock."""
        current = self.get_collection_def(name) or {}
        current.update(updates)
        self.upsert_collection_def(name, current)

    def list_collection_defs(self, prefix: str = None) -> List[dict]:
        rows = self.conn.execute("SELECT name, meta FROM collection_defs").fetchall()
        result = []
        for r in rows:
            if prefix and not r["name"].startswith(prefix):
                continue
            try:
                meta = json.loads(r["meta"] or "{}")
            except Exception:
                meta = {}
            result.append({"name": r["name"], "meta": meta})
        return result

    # ── Pending Links (DTN) ────────────────────────────────────────────────────

    @_queued
    def enqueue_pending_link(self, src: str, dst: str, rel: str,
                             author: str, ts: float) -> None:
        self.conn.execute(
            "INSERT INTO pending_links (src, dst, rel, author, timestamp) VALUES (?, ?, ?, ?, ?)",
            (src, dst, rel, author, ts)
        )
        self._commit()

    def get_pending_links(self) -> List[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM pending_links").fetchall()]

    @_queued
    def delete_pending_link(self, pid: int) -> None:
        self.conn.execute("DELETE FROM pending_links WHERE id=?", (pid,))
        self._commit()

    # ── Vault (Nucleus / Config) ───────────────────────────────────────────────

    @_queued
    def vault_store(self, cat: str, ident: str, data: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO nucleus VALUES (?, ?, ?)",
            (cat, ident, json.dumps(data, ensure_ascii=False))
        )
        self._commit()

    def vault_retrieve(self, cat: str, ident: str) -> Optional[Any]:
        r = self.conn.execute(
            "SELECT data FROM nucleus WHERE category = ? AND identifier = ?", (cat, ident)
        ).fetchone()
        return json.loads(r["data"]) if r else None

    def vault_scan(self, cat: str, prefix: str = None) -> List[tuple]:
        if prefix:
            rows = self.conn.execute(
                "SELECT identifier, data FROM nucleus WHERE category=? AND identifier LIKE ?",
                (cat, prefix + "%")
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT identifier, data FROM nucleus WHERE category=?", (cat,)
            ).fetchall()
        return [(r["identifier"], json.loads(r["data"])) for r in rows]

    @_queued
    def vault_delete(self, cat: str, ident: str) -> None:
        self.conn.execute("DELETE FROM nucleus WHERE category=? AND identifier=?", (cat, ident))
        self._commit()

    # ── Streaming & Export ─────────────────────────────────────────────────────

    def fetch_stream(self, limit: int = 10) -> List[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM chunks ORDER BY rowid DESC LIMIT ?", (limit,)
        ).fetchall()]

    def get_all_chunks(self) -> List[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM chunks").fetchall()]

    def get_all_links(self, rel_filter: Optional[str] = None,
                      limit: int = 5000) -> List[dict]:
        if rel_filter:
            return [dict(r) for r in self.conn.execute(
                "SELECT src, dst, rel, w FROM links WHERE rel=? ORDER BY rel, src LIMIT ?",
                (rel_filter, limit)
            ).fetchall()]
        return [dict(r) for r in self.conn.execute(
            "SELECT src, dst, rel, w FROM links ORDER BY rel, src LIMIT ?", (limit,)
        ).fetchall()]

    def get_all_keys(self) -> List[str]:
        return [r["key"] for r in self.conn.execute("SELECT key FROM chunks").fetchall()]

    def get_recent_atom_hashes(self, since: float) -> List[str]:
        return [r["key"] for r in self.conn.execute(
            "SELECT key FROM chunks WHERE CAST(created_at AS REAL) > ?", (since,)
        ).fetchall()]

    def get_recent_links(self, since: float) -> List[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT src, dst, rel, author, updated_at as timestamp FROM links WHERE updated_at > ?",
            (since,)
        ).fetchall()]

    def get_store_totals(self) -> dict:
        """Whole-store counts in one primitive (chunks/links/aliases/collections)."""
        c = self.conn
        return {
            "chunks":      c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
            "links":       c.execute("SELECT COUNT(*) FROM links").fetchone()[0],
            "aliases":     c.execute("SELECT COUNT(*) FROM aliases").fetchone()[0],
            "collections": c.execute("SELECT COUNT(DISTINCT name) FROM collections").fetchone()[0],
        }

    def get_namespace_counts(self, depth: int = 1) -> List[dict]:
        """
        Return namespace atom counts from the pre-aggregated namespace_counts table.
        depth=1 (default): top-level namespaces only (e.g. "word", "sys", "calc").
        depth=0: all namespace levels (e.g. "word", "word:en", "word:ja", …).
        O(1) primary-key read — no alias scan or string parsing at query time.
        """
        if depth == 1:
            rows = self.conn.execute(
                "SELECT ns, count FROM namespace_counts"
                " WHERE ns NOT LIKE '%:%'"
                " ORDER BY count DESC, ns ASC"
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT ns, count FROM namespace_counts ORDER BY count DESC, ns ASC"
            ).fetchall()
        return [{"ns": r["ns"], "count": r["count"]} for r in rows]

    def fetch_by_meta_field(self, field: str, value: str, author: str = None,
                            limit: int = 200) -> List[dict]:
        path = f"$.{field}"
        if author:
            rows = self.conn.execute(
                "SELECT * FROM chunks WHERE json_extract(meta,?)=? AND author=? ORDER BY rowid DESC LIMIT ?",
                (path, value, author, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM chunks WHERE json_extract(meta,?)=? ORDER BY rowid DESC LIMIT ?",
                (path, value, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_keys_by_scope(self, scope: str) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT key FROM chunk_access WHERE scope=?", (scope,)
        ).fetchall()
        return [r["key"] for r in rows]
