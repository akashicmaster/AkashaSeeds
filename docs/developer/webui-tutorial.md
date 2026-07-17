# Building a Web UI for AKASHA — Tutorial

**Example application:** Note UI (`/note`)  
**Audience:** Developers adding a new browser-based front end to AKASHA  
**Version:** 1.1 — kernel series `seeds`

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Design First: The Concept Model as UI Specification](#2-design-first-the-concept-model-as-ui-specification)
3. [How the Web Layer Works](#3-how-the-web-layer-works)
4. [Step 1 — Create the HTML File](#4-step-1--create-the-html-file)
5. [Step 2 — Implement Authentication](#5-step-2--implement-authentication)
6. [Step 3 — Call the Kernel](#6-step-3--call-the-kernel)
7. [Step 4 — Build the UI](#7-step-4--build-the-ui)
8. [Step 5 — Verify in the Browser](#8-step-5--verify-in-the-browser)
9. [Adding Custom API Endpoints](#9-adding-custom-api-endpoints)
10. [Complete Minimal Template](#10-complete-minimal-template)

---

## 1. Prerequisites

- AKASHA is running (`python akasha.py`)
- At least one user has been created via genesis rite or `user.add`
- Basic knowledge of HTML and JavaScript `fetch`
- Recommended: read `docs/cop-tutorial-note.md` (concept-oriented design)

---

## 2. Design First: The Concept Model as UI Specification

### 2.1 The Web UI is a Projection

The web UI is not the application. **The concept model is the application.** The web UI is a *rendering projection* of the concept model onto a browser surface.

This distinction matters in practice. There are two fundamentally different kinds of "UI change":

| Change type | Example | Scope |
|---|---|---|
| Presentation change | Rename "Append" button to "Add Entry" | HTML/CSS only |
| Behavioural change | "User should add content without opening a note first" | Concept model operator — session state design |

In a visual-first workflow these look identical at first glance — both feel like "a UI change." In concept-first design, a behavioural change is immediately identified as a design change at the operator level, and its scope and cost are understood before any code is written.

### 2.2 Design the Concept Model Before Writing HTML

Before creating `services/static/<name>/index.html`, answer these five questions:

1. **Entities** — what objects does the user manage? → root atoms and sub-atoms
2. **Operations** — what actions does the user take? → `op_*` methods
3. **Order** — what is the sequence relationship? → `sys:next` linked list
4. **Containment** — what holds what? → `sys:contains` links
5. **Focus** — what is the user currently working on? → session context key

Once these five questions are answered, the complete list of JSON-RPC methods is known. The HTML becomes a *form layer over that method list* — no more, no less. The UI never contains application logic; it only reflects concept model state.

See `docs/cop-tutorial-note.md §§1.1–1.5` for a full walkthrough of this design process with NoteConcept, and `docs/cop-tutorial-note.md Part 4` for the general theory of concept-oriented UI/UX design.

### 2.3 Handling UX Feedback Without Code Patches

When UX feedback arrives — "users are confused about X", "they want to do Y before Z" — the correct workflow is:

1. **Identify** which concept model element the feedback addresses: an operation, a relationship, or session state.
2. **Modify** the concept model: add a new `op_*` method, or change parameters of an existing one.
3. **Update IAM routing** — add the new method to `_METHOD_TO_ACTION` in `kernel.py`.
4. **Update the HTML** to call the new or modified operator.

Only step 4 touches the HTML. Steps 1–3 happen at the concept model level, where design intent is explicit, reviewable, and testable independently of any rendering surface.

Contrast this with patching code in a visual-first design: UX feedback simultaneously changes HTML structure, CSS, JavaScript logic, and possibly route handlers. The changes are interleaved and difficult to review. In concept-first design, each layer changes independently.

**Concrete example — adding "quick add" (no open required):**

Without concept-first design, "quick add" feels like a UI hack (detect if note is open, fall back to last note, etc.). With concept-first design, the correct question is: *does the concept model support inserting content without an explicit `op_open` call?* If not, add an `op_quick_add` that auto-selects the most recent note. The HTML then calls `note.quick_add` — one line. The behaviour contract lives in the concept model.

### 2.4 Example: Note UI and Presentation UI as Projections

The Note UI (`/note`) projects `NoteConcept`:

| UI affordance | Concept model element |
|---|---|
| "New Note" button | `note.new` operator |
| Sidebar note list | `note.ls` → array of root atoms |
| Click to open | `note.open` → sets `active_note_root` session key |
| Text area + Add | `note.add` operator |
| Section heading | `note.section` operator |
| TOC panel | `note.toc` → traverses `sys:contains` links |
| Sequential read view | `note.read` → walks `sys:next` timeline |
| Delete with confirm | `note.rm` operator |

A Presentation UI (`/presentation`) would project `PresentationConcept` in exactly the same pattern:

| UI affordance | Concept model element |
|---|---|
| "New Deck" button | `pres.new` operator |
| Slide navigator strip | `pres.ls` → frame atoms in `sys:next` order |
| Click to open deck | `pres.open` → sets `active_presentation_root` |
| "Add Slide" button | `pres.frame.add` operator |
| Layout zone palette | `pres.region.add` → region atoms with `sys:contains` |
| Content element | `pres.node.add` → node atoms |

Both UIs follow the same design process; the concept model differs, not the methodology.

The **rendering-agnostic principle** means the same `PresentationConcept` model could also drive a mobile card list or a CLI outline renderer. See `docs/concept-extensions.md §5` for the Presentation model's full operator reference.

### 2.5 The Full Analysis Pipeline in a UI

AKASHA supports a pipeline of concept models:

```
FieldNote / Survey   →   Aggregation   →   Synthesis   →   Presentation
(raw observations)       (quant layer)     (qual layer)    (output surface)
```

A web UI that displays analysis results is a **Presentation projection of the pipeline's output**. Nodes in a PresentationConcept frame can hold atom IDs from Aggregation (measures) or Synthesis (claims). The UI renders those atoms by fetching their content via `rpc` — it never owns the data, it only projects it.

This means a UX change like "show the supporting evidence for each claim" maps cleanly to `synth.trace` in `SynthesisConcept` — not to a new SQL query or a new REST endpoint. The pipeline is already there; the UI just exposes a new path through it.

---

## 3. How the Web Layer Works

The HTTP portal (port 8000) serves:

| Path | File | Description |
|---|---|---|
| `/` | `services/static/index.html` | Cosmos 3D graph |
| `/note` | `services/static/note/index.html` | Note UI |
| `/<name>` | `services/static/<name>/index.html` | any new app |
| `/api/rpc` | kernel (POST) | JSON-RPC 2.0 gateway |

`BaseWebHandler.translate_path()` maps `/<name>` directly to `services/static/<name>/index.html` without a redirect. No routing configuration is needed — file placement is sufficient.

All kernel communication goes through `POST /api/rpc` using standard JSON-RPC 2.0 envelopes.

---

## 4. Step 1 — Create the HTML File

Create the directory and the file:

```
services/static/note/index.html
```

That is the only file required. The app is immediately available at `http://host:8000/note` once the portal is running.

---

## 5. Step 2 — Implement Authentication

Every app must implement a two-phase login flow. Copy this pattern exactly.

### Login form (HTML)

```html
<div id="login-overlay">
    <input type="text"     id="inp-user" placeholder="IDENTITY" autocomplete="off">
    <input type="password" id="inp-pass" placeholder="PASSPHRASE" autocomplete="off">
    <button onclick="login()">UNLOCK</button>
    <div id="login-msg"></div>
</div>
<div id="app" style="display:none">
    <!-- main UI here -->
</div>
```

**Rules:**
- No `value=` default on the username field.
- The `#app` div starts hidden and is shown only after successful authentication.

### Login function (JavaScript)

```javascript
const API = '/api/rpc';
let sessionToken = '';
let currentUser  = '';

async function login() {
    const user  = document.getElementById('inp-user').value.trim();
    const pass  = document.getElementById('inp-pass').value;
    const msgEl = document.getElementById('login-msg');

    if (!user || !pass) { msgEl.textContent = 'Enter identity and passphrase.'; return; }
    msgEl.textContent = 'Verifying…';

    try {
        // kernel.auth.verify is pre-auth: no session_token needed
        const resp = await fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method:  'kernel.auth.verify',
                params:  { data: { user_id: user, passphrase: pass } },
                id:      'auth'
            })
        });
        const raw = await resp.json();
        if (raw.error) throw new Error(raw.error.message);

        const res = raw.result;
        if (res.status === 'authenticated') {
            sessionToken = res.session_token;   // save for all subsequent calls
            currentUser  = res.user_id;
            document.getElementById('login-overlay').style.display = 'none';
            document.getElementById('app').style.display = 'flex';
            onLoggedIn();
        } else {
            msgEl.textContent = 'Access Denied.';
        }
    } catch (e) {
        msgEl.textContent = `Error: ${e.message}`;
    }
}
```

`onLoggedIn()` is where you initialize the UI after successful authentication (load data, render initial state, etc.).

---

## 6. Step 3 — Call the Kernel

Define a single `rpc()` helper. All kernel calls go through this function.

```javascript
async function rpc(method, data = {}) {
    const body = {
        jsonrpc: '2.0',
        method,
        params:  { session_token: sessionToken, data },
        id:      Date.now()
    };
    const resp = await fetch(API, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body)
    });
    const res = await resp.json();
    if (res.error) throw new Error(res.error.message || JSON.stringify(res.error));
    return res.result;
}
```

**Note method examples:**

```javascript
// List existing notes (newest first)
const { notes } = await rpc('note.ls');
// notes is an array of { note_id, title, created_at }

// Open (mount) an existing note into the session
await rpc('note.open', { note_id: notes[0].note_id });

// Create a new note
const res = await rpc('note.new', { title: 'My Note' });
// res.note_id is now the session's active note

// Add a content chunk to the active note
await rpc('note.add', { text: 'First paragraph.' });

// Add a section heading
await rpc('note.section', { title: 'Chapter One', role: 'chapter' });

// Read the note as sequential content
const seq = await rpc('note.read', {});
// seq is an array of { id, role, content, category } objects

// Get the table of contents
const toc = await rpc('note.toc', {});
// toc is an array of { title, role, depth, id } objects

// Delete the active note
await rpc('note.rm', {});
```

For a full list of available methods see `docs/api-spec.md §10`.

---

## 7. Step 4 — Build the UI

> **Principle**: the UI reflects concept model state — it does not manage state itself. Every UI element maps to exactly one operator call or one piece of returned data. If you find yourself writing conditional logic in JavaScript to reconcile UI state, that logic belongs in the concept model.

### 7.1 Listing and opening notes

Call `note.ls` immediately after login to populate a sidebar list. Each item's `onclick` calls `note.open` to mount the selected note.

```javascript
async function loadNotesList() {
    const { notes } = await rpc('note.ls');
    const el = document.getElementById('notes-list');
    el.innerHTML = notes.map(n => {
        const date = n.created_at
            ? new Date(n.created_at * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
            : '';
        return `<div class="note-item" onclick="openNote('${escHtml(n.note_id)}')">
            <span>${escHtml(n.title)}</span>
            <span>${escHtml(date)}</span>
        </div>`;
    }).join('');
}

async function openNote(noteId) {
    const res = await rpc('note.open', { note_id: noteId });
    // res = { status: 'opened', note_id: '...', title: '...' }
    document.getElementById('note-title').textContent = res.title;
    await refreshNote();
}
```

### 7.2 Rendering sequential content with scroll anchors

Assign an `id` attribute to each rendered element using the atom's `id` field. This enables TOC-driven scrolling.

```javascript
function renderSequential(items) {
    const el = document.getElementById('note-display');
    el.innerHTML = items.map(item => {
        const role = item.role || 'chunk';
        const text = escHtml(item.content || '');
        const domId = `nd-${escHtml(item.id || '')}`;

        if (role === 'chapter')
            return `<div class="nd-chapter" id="${domId}">${text}</div>`;
        if (role === 'section')
            return `<div class="nd-section"  id="${domId}">${text}</div>`;
        if (role === 'paragraph')
            return `<div class="nd-paragraph" id="${domId}">[${escHtml(item.category || 'MEMO')}]</div>`;
        return `<div class="nd-chunk" id="${domId}">${text}</div>`;
    }).join('');
}
```

### 7.3 Rendering a clickable TOC

Each TOC entry stores the corresponding DOM element id. The `onclick` handler scrolls the content panel to the element using `scrollIntoView`.

```javascript
function renderToc(items) {
    const el = document.getElementById('toc-list');
    el.innerHTML = items.map(item => {
        const indent = '&nbsp;'.repeat(item.depth * 4);
        const domId  = `nd-${escHtml(item.id || '')}`;
        return `<div class="toc-item toc-${item.role}"
                     onclick="scrollToSection('${domId}')">
            ${indent}${escHtml(item.title)}
        </div>`;
    }).join('');
}

function scrollToSection(domId) {
    const el = document.getElementById(domId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

Add `scroll-margin-top` CSS to the content items so they land below any fixed headers:

```css
.nd-chapter, .nd-section, .nd-paragraph, .nd-chunk {
    scroll-margin-top: 20px;
}
```

### 7.4 Two-step delete confirmation

Never delete on a single click. Use a confirmation modal to avoid accidental data loss.

```html
<!-- Hidden by default; shown via JS -->
<div id="confirm-modal" style="display:none">
    <p>Delete note <strong id="confirm-title"></strong>?</p>
    <button onclick="deleteNote()">Delete</button>
    <button onclick="closeConfirm()">Cancel</button>
</div>
```

```javascript
function confirmDelete() {
    document.getElementById('confirm-title').textContent = `"${activeNoteTitle}"`;
    document.getElementById('confirm-modal').style.display = 'flex';
}

function closeConfirm() {
    document.getElementById('confirm-modal').style.display = 'none';
}

async function deleteNote() {
    closeConfirm();
    await rpc('note.rm', {});
    // reset UI state
    activeNoteId = null;
    document.getElementById('note-display').innerHTML = '';
    await loadNotesList();
}
```

### 7.5 Always escape HTML

```javascript
function escHtml(s) {
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
```

Never insert user-supplied content into the DOM without `escHtml()`.

---

## 8. Step 5 — Verify in the Browser

1. Start AKASHA: `python akasha.py`
2. Open `http://localhost:8000/note` (or the Codespace forwarded URL)
3. Log in with a registered user
4. Confirm the login overlay disappears and the main UI appears
5. Open the browser console — there should be no authentication errors

Common mistakes:

| Symptom | Cause |
|---|---|
| `Identity 'guest' is unknown` | Calling a non-pre-auth method without `session_token`, or using old `auth.login` method |
| `Authentication failed` | Wrong passphrase, or `session_token` not included in `params` |
| `Method not found` | Typo in method name; check `docs/api-spec.md §10` |
| Login form pre-fills a username | `value="..."` left on the username input — remove it |
| `note.ls` returns empty list | No notes created yet for this user, or wrong user logged in |
| `note.open` returns -32002 | The note_id doesn't exist or belongs to a different user |

---

## 9. Adding Custom API Endpoints

If your app needs endpoints beyond `/api/rpc` (e.g. composite queries that aggregate multiple kernel calls), create a routes file:

```
services/routes/<name>.py
```

```python
from api.gateway import gateway

def my_aggregate_handler(req_data: dict) -> dict:
    # session_token is validated upstream by the HTTP layer
    session_token = req_data.get("session_token", "")

    r1 = gateway.dispatch({
        "jsonrpc": "2.0", "method": "note.read",
        "params":  {"session_token": session_token, "data": {}},
        "id": "r1"
    })
    r2 = gateway.dispatch({
        "jsonrpc": "2.0", "method": "note.toc",
        "params":  {"session_token": session_token, "data": {}},
        "id": "r2"
    })
    return {
        "content": r1.get("result", []),
        "toc":     r2.get("result", []),
    }

ROUTES = {
    "/api/<name>/read-all": ("POST", my_aggregate_handler),
}
```

Launch the sub-service on a separate port:

```bash
python -m services.app_server --app <name> --port 8082
```

`app_server.py` auto-discovers the routes file. If `services/routes/<name>.py` does not exist, the service starts with `/api/rpc` and static files only — no routes file is ever required.

From the browser, call your custom endpoint like a normal `fetch`:

```javascript
const resp = await fetch('/api/<name>/read-all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken })
});
```

---

## 10. Complete Minimal Template

A working app skeleton with login, note listing, and note creation:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Akasha App</title>
    <style>
        body { font-family: monospace; background: #050505; color: #ddd; margin: 0; height: 100vh; display: flex; flex-direction: column; }
        #login-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.95);
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px;
        }
        input { background: #111; border: 1px solid #00ffcc; color: #00ffcc; padding: 10px; font-family: inherit; width: 220px; text-align: center; }
        button { background: transparent; border: 1px solid #00ffcc; color: #00ffcc; padding: 8px 22px; cursor: pointer; font-family: inherit; }
        #app { display: none; flex: 1; }
        #err { color: #f55; font-size: 0.85rem; }
    </style>
</head>
<body>

<div id="login-overlay">
    <div style="font-size:2rem;letter-spacing:4px;color:#00ffcc">MY APP</div>
    <input type="text"     id="inp-user" placeholder="IDENTITY"   autocomplete="off">
    <input type="password" id="inp-pass" placeholder="PASSPHRASE" autocomplete="off">
    <button onclick="login()">UNLOCK</button>
    <div id="err"></div>
</div>

<div id="app">
    <p>Logged in as <strong id="auth-label"></strong></p>
    <input type="text" id="new-title" placeholder="Note title">
    <button onclick="createNote()">New Note</button>
    <ul id="notes-list"></ul>
    <pre id="output"></pre>
</div>

<script>
    const API = '/api/rpc';
    let sessionToken = '';

    async function rpc(method, data = {}) {
        const res = await fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method,
                params: { session_token: sessionToken, data }, id: Date.now() })
        });
        const json = await res.json();
        if (json.error) throw new Error(json.error.message);
        return json.result;
    }

    async function login() {
        const user = document.getElementById('inp-user').value.trim();
        const pass = document.getElementById('inp-pass').value;
        const err  = document.getElementById('err');
        if (!user || !pass) { err.textContent = 'Enter identity and passphrase.'; return; }
        try {
            const resp = await fetch(API, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0', method: 'kernel.auth.verify',
                    params: { data: { user_id: user, passphrase: pass } }, id: 'auth'
                })
            });
            const raw = await resp.json();
            if (raw.error) throw new Error(raw.error.message);
            if (raw.result.status === 'authenticated') {
                sessionToken = raw.result.session_token;
                document.getElementById('auth-label').textContent = raw.result.user_id;
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('app').style.display = 'block';
                await loadNotes();
            }
        } catch (e) { err.textContent = `Error: ${e.message}`; }
    }

    async function loadNotes() {
        const { notes } = await rpc('note.ls');
        const ul = document.getElementById('notes-list');
        ul.innerHTML = notes.map(n =>
            `<li><a href="#" onclick="openNote('${escHtml(n.note_id)}');return false">${escHtml(n.title)}</a></li>`
        ).join('');
    }

    async function openNote(noteId) {
        const res = await rpc('note.open', { note_id: noteId });
        const seq = await rpc('note.read');
        document.getElementById('output').textContent =
            seq.map(s => `[${s.role}] ${s.content || ''}`).join('\n');
    }

    async function createNote() {
        const title = document.getElementById('new-title').value.trim();
        if (!title) return;
        await rpc('note.new', { title });
        document.getElementById('new-title').value = '';
        await loadNotes();
    }

    function escHtml(s) {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    document.getElementById('inp-pass').addEventListener('keypress', e => {
        if (e.key === 'Enter') login();
    });
</script>
</body>
</html>
```

Save as `services/static/<name>/index.html` and access at `http://host:8000/<name>`.

---

## 11. Service Namespace Isolation

### The Problem

Session context is **user-scoped, not service-scoped.** If two UI services both use
`note.new` / `note.read`, they share the same `active_note_root` pointer. Whichever
service ran last overwrites the other's active document — the user opens Loom and sees
the document they were editing in the Note app.

### The Solution

When your service reuses an existing concept class, use a **prefixed RPC method name**
and the kernel will instantiate the concept under an isolated namespace:

| Service | RPC prefix | Session context key |
|---|---|---|
| Note app (standalone) | `note.*` | `active_note_root` |
| Loom writing atelier | `loom.note.*` | `loom:active_note_root` |

In practice:

```javascript
// ❌ Wrong — shares context with the Note app
await rpc('note.new', { title: 'My Loom Doc' });
await rpc('note.list', {});

// ✅ Correct — isolated context for this service
await rpc('loom.note.new', { title: 'My Loom Doc' });
await rpc('loom.note.list', {});
```

### When This Applies

You need a namespace only when your service **reuses an existing concept class** that is
already used by another service. If you build a brand-new concept class (e.g.
`MyConcept` with its own `CONTEXT_KEY_ACTIVE`), no namespace is needed — the context
key is already unique.

To add a new namespaced service:
1. Choose a short lowercase identifier (e.g. `"myservice"`)
2. Add `myservice.note.*` (or whichever concept) to the kernel permission map
3. Add kernel dispatch that calls `NoteConcept(session, namespace="myservice")`
4. Use `myservice.note.*` in your client code

See `docs/scope-dimension-model.md §9` and `docs/concept-model-spec.md §12` for the
full specification.

---

*See `docs/api-spec.md §10.9` for the complete Notes method reference.*  
*See `docs/concept-extensions.md` for Aggregation, Synthesis, and Presentation concept model references.*  
*See `docs/cop-tutorial-note.md Part 4` for the general theory of concept-oriented UI/UX design.*
