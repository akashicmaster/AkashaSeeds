# Blue Book — Chapter 0: Building a Web GUI

> **Before this chapter:** Read **Red Book, Chapter 0** for the core CLI commands.
> This chapter builds the same write / read / record operations as a web interface,
> talking to the same server through the same JSON-RPC 2.0 protocol the CLI uses internally.
> No frameworks, no build step. A single HTML file is all you need to start.

---

By the end of this chapter you will have a working browser-based interface that can write
atoms, read them back, create structured fruit records, and display them as a sortable table —
using the same Mediterranean fruit and cheese dataset the Red Book introduces.

---

## 0-1 How the Akasha API Works

Everything in Akasha — the CLI, the web portal, and any program you write — talks to a single
endpoint through **JSON-RPC 2.0**. Understanding this protocol takes five minutes and unlocks
every operation this book covers.

### The request format

A JSON-RPC 2.0 request is a JSON object with four fields:

```json
{
  "jsonrpc": "2.0",
  "method":  "kernel.memory.write",
  "params":  {
    "session_token": "<your token here>",
    "data": { "text": "fig" }
  },
  "id": 1
}
```

| Field | Purpose |
|---|---|
| `jsonrpc` | Always the string `"2.0"` |
| `method` | The operation you want to run |
| `params.session_token` | Your session credential — explained below |
| `params.data` | Method-specific parameters |
| `id` | Any number or string you choose; the server echoes it in the response so you can match async calls |

The response is always one of two shapes:

```json
{ "jsonrpc": "2.0", "result": { ... },              "id": 1 }  // success
{ "jsonrpc": "2.0", "error":  { "code": -32602, "message": "..." }, "id": 1 }  // failure
```

There is no HTTP status code to check — even errors return HTTP 200. Always look at the
`result` or `error` field.

### The endpoint

| Server mode | URL |
|---|---|
| Default (started with `python akasha.py`) | `http://localhost:8000/api/rpc` |
| FastAPI/uvicorn (started with `--server uvicorn`) | `http://localhost:8000/rpc` or `/api/rpc` |

Both paths accept identical JSON-RPC 2.0 payloads.
Throughout this chapter the examples use `http://localhost:8000/rpc`.

### Getting a session token

Before calling any write method, you need a session token. The easiest way is a **guest session**:

```bash
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method":  "session.guest.create",
    "params":  {"session_token": "guest", "data": {}},
    "id": 1
  }'
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "binding_key": "gbk:<base64url(session_id|expires_at|nonce)>.<HMAC-SHA256>",
    "expires_at":  1751640000.0,
    "ttl":         1800
  },
  "id": 1
}
```

The `binding_key` value — the `gbk:…` string — is your session token. Pass it as
`session_token` in every subsequent request. It is valid for `ttl` seconds (default 30 minutes).
Guest sessions have read-only access to the public ontology and write access to a private guest
workspace, which is enough for everything in this chapter.

### A complete curl walkthrough

```bash
# 1. Create a guest session
TOKEN=$(curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"session.guest.create","params":{"session_token":"guest","data":{}},"id":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['binding_key'])")

echo "Token: $TOKEN"

# 2. Write an atom
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"kernel.memory.write\",\"params\":{\"session_token\":\"$TOKEN\",\"data\":{\"text\":\"fig\"}},\"id\":2}"

# 3. Peek at the ontology namespace summary
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"onto.dump\",\"params\":{\"session_token\":\"$TOKEN\",\"data\":{\"mode\":\"namespaces\"}},\"id\":3}"
```

The `onto.dump` call returns a count of atoms per namespace (`emo:`, `sys:`, `word:`, etc.).
It is a useful sanity check that the server is running and its ontology is loaded.

**CLI equivalents:** The Red Book uses shorthand commands like `w "fig"` and `r fig` in the
interactive shell. Those shorthands are translated by the CLI before dispatch; over HTTP you
always use the full method names (`kernel.memory.write`, `kernel.memory.read`, etc.) shown in
this chapter.

---

## 0-2 A Minimal HTML Page

The simplest possible web interface: one HTML file, no libraries, no build step.
Save this as `my_akasha.html` anywhere on disk and open it in a browser — but read the
CORS note in section 0-5 first to understand why you may need to serve it from the right
location.

```html
<!doctype html>
<title>Akasha — Write atoms</title>
<meta charset="utf-8">
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
  #status { font-size: 0.85rem; color: #666; margin-bottom: 1.5rem; }
  .row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
  input[type=text] { flex: 1; padding: 0.4rem 0.6rem; font-size: 1rem; border: 1px solid #ccc; border-radius: 4px; }
  button { padding: 0.4rem 1rem; font-size: 1rem; background: #2b6cb0; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
  button:disabled { background: #aaa; cursor: not-allowed; }
  #output { background: #f5f5f5; border-radius: 4px; padding: 1rem; font-family: monospace; font-size: 0.9rem; white-space: pre-wrap; min-height: 3rem; }
</style>

<h2>Akasha — Write Atoms</h2>
<p id="status">Connecting…</p>

<div class="row">
  <input id="content" type="text" placeholder="Enter text, e.g.  fig" />
  <button id="btn-write" onclick="writeAtom()" disabled>Write</button>
</div>

<div id="output">(results will appear here)</div>

<script>
  // ── Configuration ────────────────────────────────────────────────
  const BASE = "http://localhost:8000";
  let sessionToken = null;

  // ── Core helper ──────────────────────────────────────────────────
  async function rpc(method, data = {}) {
    const response = await fetch(`${BASE}/rpc`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method,
        params:  { session_token: sessionToken ?? "guest", data },
        id:      Date.now(),
      }),
    });
    return response.json();
  }

  function show(text) {
    document.getElementById("output").textContent = text;
  }

  // ── Session initialisation ───────────────────────────────────────
  async function init() {
    const resp = await rpc("session.guest.create");
    if (resp.error) {
      document.getElementById("status").textContent =
        "Could not connect: " + resp.error.message;
      return;
    }
    sessionToken = resp.result.binding_key;
    document.getElementById("status").textContent =
      "Session ready (" + sessionToken.slice(0, 24) + "…)";
    document.getElementById("btn-write").disabled = false;
  }

  // ── Write an atom ────────────────────────────────────────────────
  async function writeAtom() {
    const text = document.getElementById("content").value.trim();
    if (!text) { show("Please enter some text first."); return; }

    const resp = await rpc("kernel.memory.write", { text });
    if (resp.error) {
      show("Error: " + resp.error.message);
      return;
    }

    const key = resp.result.key;
    show(
      "Written successfully.\n\n" +
      "Full key:  " + key + "\n" +
      "Short key: " + key.slice(0, 12) + "…\n\n" +
      "Content:   " + text
    );
  }

  // ── Boot ─────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", init);
</script>
```

**What this page does, step by step:**

1. When the page loads, `init()` fires and calls `session.guest.create`. The returned
   `binding_key` is stored in `sessionToken` and will be sent with every subsequent request.

2. While `sessionToken` is still `null` (during the fetch), the Write button is disabled.
   Once the session is established, the button is enabled and the status line updates.

3. Clicking Write calls `kernel.memory.write` with `{text: "<what you typed>"}`. The server
   returns a `key` — the 64-character SHA-256 hash of the content. If you write the same
   text again you get the same key back (idempotency: identical content, identical key).

**Try it with the dataset:** Type `fig` and click Write. Note the key. Type `fig` again — the
key is identical. Type `grape` — a different key appears. This is Akasha's content-addressing
in action.

---

## 0-3 Read and Display Atoms

Extend the page with a read form. Add the following HTML after the write section and its
corresponding JavaScript functions.

### HTML to add (after the write form)

```html
<h3>Read an Atom</h3>
<div class="row">
  <input id="read-key" type="text" placeholder="Key (first 8+ chars) or alias" />
  <button id="btn-read" onclick="readAtom()" disabled>Read</button>
</div>

<div id="read-output"></div>
<div id="links-output"></div>
```

Enable the read button in `init()` by adding:

```javascript
document.getElementById("btn-read").disabled = false;
```

### JavaScript to add

```javascript
// ── Read an atom and list its links ─────────────────────────────
async function readAtom() {
  const id = document.getElementById("read-key").value.trim();
  if (!id) { return; }

  // First call: read the atom content
  const readResp = await rpc("kernel.memory.read", { id });
  const readOut  = document.getElementById("read-output");

  if (readResp.error) {
    readOut.textContent = "Not found: " + readResp.error.message;
    document.getElementById("links-output").textContent = "";
    return;
  }

  const atom = readResp.result;
  // atom.key, atom.content, atom.aliases (array of strings)
  readOut.innerHTML =
    "<strong>Key:</strong> "     + atom.key.slice(0, 12) + "…<br>" +
    "<strong>Aliases:</strong> " + (atom.aliases ?? []).join(", ") + "<br>" +
    "<strong>Content:</strong> " + escapeHtml(atom.content);

  // Second call: list links attached to this atom
  const linksResp = await rpc("link.list", { id: atom.key });
  const linksOut  = document.getElementById("links-output");

  if (linksResp.error || !linksResp.result?.links?.length) {
    linksOut.textContent = "No links.";
    return;
  }

  const rows = linksResp.result.links.map(lk =>
    `<tr>
       <td>${lk.direction === "out" ? "→" : "←"}</td>
       <td><code>${lk.rel}</code></td>
       <td>${escapeHtml(lk.preview)}</td>
     </tr>`
  ).join("");

  linksOut.innerHTML =
    "<table style='border-collapse:collapse;margin-top:0.5rem'>" +
    "<thead><tr><th>Dir</th><th>Relation</th><th>Neighbour</th></tr></thead>" +
    "<tbody>" + rows + "</tbody></table>";
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
```

**What the responses look like:**

`kernel.memory.read` returns:
```json
{
  "key":     "3a9fc2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
  "content": "fig",
  "aliases": ["fig"],
  "meta":    {}
}
```

`link.list` returns:
```json
{
  "key": "3a9fc2…",
  "links": [
    {
      "direction": "out",
      "rel":       "sys:is_a",
      "key":       "b4c5d6…",
      "preview":   "fruit"
    },
    {
      "direction": "in",
      "rel":       "emo:evokes",
      "key":       "c5d6e7…",
      "preview":   "sweetness"
    }
  ]
}
```

Each link has a `direction` (`"out"` = this atom points to the neighbour;
`"in"` = the neighbour points to this atom), a `rel` describing the relationship type,
and a `preview` of the neighbour's content.

**Try it with the dataset:** If you have not yet assigned aliases, the ontology atoms such as
`emo:joy` and `sys:is_a` are already accessible by alias from the start. Type `emo:joy` in
the read field and click Read to see the built-in emotional vocabulary node and its links.

---

## 0-4 Create Records and Display a Table

A **record** in Akasha is an atom with named attributes stored as typed links.
There is no schema to declare — you name the attributes inline when you write the record.
The `rec.new` method creates the atom and wires all the attribute links in one call.

This section adds a form for creating fruit records and a live table showing all records
created so far.

### rec.new — creating a record

The request to create one fruit entry:

```json
{
  "jsonrpc": "2.0",
  "method":  "rec.new",
  "params":  {
    "session_token": "<your token>",
    "data": {
      "type":      "fruit",
      "content":   "fig — a sun-dried Mediterranean fruit",
      "sweetness": "0.88",
      "acidity":   "0.18"
    }
  },
  "id": 10
}
```

`type` becomes the record category (used to look up all records of this kind).
`content` is the human-readable label stored in the atom's text.
Every other field — `sweetness`, `acidity`, or any name you choose — becomes a typed attribute
link pointing to a content-addressed value atom. No two records with the same `sweetness`
value share an atom by accident; value atoms are deduplicated by content.

The response:
```json
{
  "result": {
    "key":     "a1b2c3…",
    "type":    "fruit",
    "content": "fig — a sun-dried Mediterranean fruit"
  }
}
```

### rec.table — reading records as a table

Once one or more fruit records exist, this call retrieves them all with their attributes:

```json
{
  "method": "rec.table",
  "data":   { "in_set": "rec:fruit" }
}
```

The response is structured for direct table rendering:

```json
{
  "result": {
    "_view":   "table",
    "title":   "rec:fruit",
    "columns": ["content", "sweetness", "acidity"],
    "rows": [
      { "content": "fig — a sun-dried Mediterranean fruit", "sweetness": "0.88", "acidity": "0.18" },
      { "content": "grape",                                 "sweetness": "0.82", "acidity": "0.35" }
    ],
    "count": 2
  }
}
```

`columns` is the ordered list of discovered attribute names.
`rows` is an array of plain objects where each key is a column name and each value is the
stored string. Attributes are discovered from the actual links present in the set — if you
add a `region` field to one record later, it appears as a column automatically on the next call.

### Complete page for this section

Save this as `fruit_records.html` in `archives/` (or see section 0-5 for why that matters).

```html
<!doctype html>
<title>Akasha — Fruit Records</title>
<meta charset="utf-8">
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  #status { font-size: 0.85rem; color: #666; margin-bottom: 1.5rem; }
  label { display: block; font-size: 0.85rem; margin-bottom: 0.2rem; }
  .field { margin-bottom: 0.75rem; }
  input[type=text], input[type=number] {
    width: 100%; box-sizing: border-box;
    padding: 0.35rem 0.5rem; font-size: 1rem;
    border: 1px solid #ccc; border-radius: 4px;
  }
  .row { display: flex; gap: 0.5rem; }
  .row .field { flex: 1; }
  button {
    margin-top: 0.5rem; padding: 0.4rem 1.2rem; font-size: 1rem;
    background: #2b6cb0; color: #fff; border: none; border-radius: 4px; cursor: pointer;
  }
  button.secondary { background: #4a5568; }
  button:disabled  { background: #aaa; cursor: not-allowed; }
  #msg { margin-top: 0.5rem; font-size: 0.9rem; color: #2b6cb0; }
  #table-wrap { margin-top: 2rem; overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; }
  th { background: #f0f4f8; font-weight: 600; }
  tr:hover td { background: #fafafa; }
  #empty { color: #999; font-style: italic; margin-top: 1rem; }
</style>

<h2>Akasha — Fruit Records</h2>
<p id="status">Connecting…</p>

<h3>Add a Fruit</h3>

<div class="field">
  <label for="fruit-name">Name / description</label>
  <input id="fruit-name" type="text" placeholder="e.g.  fig — a sun-dried Mediterranean fruit" />
</div>

<div class="row">
  <div class="field">
    <label for="sweetness">Sweetness (0–1)</label>
    <input id="sweetness" type="number" min="0" max="1" step="0.01" placeholder="0.88" />
  </div>
  <div class="field">
    <label for="acidity">Acidity (0–1)</label>
    <input id="acidity" type="number" min="0" max="1" step="0.01" placeholder="0.18" />
  </div>
</div>

<button id="btn-add" onclick="addFruit()" disabled>Add Fruit</button>
<button class="secondary" onclick="loadTable()" style="margin-left:0.5rem">Refresh Table</button>
<div id="msg"></div>

<div id="table-wrap">
  <div id="empty">No fruit records yet. Add one above.</div>
</div>

<script>
  const BASE = "http://localhost:8000";
  let sessionToken = null;

  // ── RPC helper ──────────────────────────────────────────────────
  async function rpc(method, data = {}) {
    const response = await fetch(`${BASE}/rpc`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method,
        params:  { session_token: sessionToken ?? "guest", data },
        id:      Date.now(),
      }),
    });
    return response.json();
  }

  function setMsg(text, isError = false) {
    const el = document.getElementById("msg");
    el.textContent = text;
    el.style.color = isError ? "#c53030" : "#2b6cb0";
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  // ── Session initialisation ──────────────────────────────────────
  async function init() {
    const resp = await rpc("session.guest.create");
    if (resp.error) {
      document.getElementById("status").textContent =
        "Connection failed: " + resp.error.message;
      return;
    }
    sessionToken = resp.result.binding_key;
    document.getElementById("status").textContent =
      "Session ready (" + sessionToken.slice(0, 24) + "…)";
    document.getElementById("btn-add").disabled = false;
    await loadTable();
  }

  // ── Add a fruit record ──────────────────────────────────────────
  async function addFruit() {
    const content   = document.getElementById("fruit-name").value.trim();
    const sweetness = document.getElementById("sweetness").value;
    const acidity   = document.getElementById("acidity").value;

    if (!content) { setMsg("Please enter a name.", true); return; }

    const data = { type: "fruit", content };
    if (sweetness !== "") data.sweetness = sweetness;
    if (acidity   !== "") data.acidity   = acidity;

    const resp = await rpc("rec.new", data);
    if (resp.error) {
      setMsg("Error: " + resp.error.message, true);
      return;
    }

    setMsg("Added: " + resp.result.key.slice(0, 12) + "…");
    document.getElementById("fruit-name").value = "";
    document.getElementById("sweetness").value  = "";
    document.getElementById("acidity").value    = "";
    await loadTable();
  }

  // ── Load and render the fruit table ────────────────────────────
  async function loadTable() {
    const resp = await rpc("rec.table", { in_set: "rec:fruit" });
    const wrap = document.getElementById("table-wrap");

    if (resp.error) {
      // A "resource not found" error just means no records exist yet.
      wrap.innerHTML = '<div id="empty">No fruit records yet. Add one above.</div>';
      return;
    }

    const { columns, rows, count } = resp.result;

    if (!rows || rows.length === 0) {
      wrap.innerHTML = '<div id="empty">No fruit records yet. Add one above.</div>';
      return;
    }

    // Build <thead> from the columns array
    const headCells = columns.map(c =>
      `<th>${escapeHtml(c)}</th>`
    ).join("");

    // Build <tbody> — one <tr> per record
    const bodyRows = rows.map(row => {
      const cells = columns.map(col =>
        `<td>${escapeHtml(row[col] ?? "")}</td>`
      ).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    wrap.innerHTML =
      `<p style="font-size:0.85rem;color:#666">${count} record${count !== 1 ? "s" : ""}</p>` +
      `<table>` +
      `  <thead><tr>${headCells}</tr></thead>` +
      `  <tbody>${bodyRows}</tbody>` +
      `</table>`;
  }

  document.addEventListener("DOMContentLoaded", init);
</script>
```

**Try it with the dataset:** Enter these five entries one by one:

| Name / description | Sweetness | Acidity |
|---|---|---|
| `fig` | `0.88` | `0.18` |
| `grape` | `0.82` | `0.35` |
| `date` | `0.95` | `0.05` |
| `lemon` | `0.08` | `0.95` |
| `orange` | `0.72` | `0.52` |

After each addition the table refreshes automatically. Notice:

- `columns` in the response always lists the attributes in the order they were first encountered
  across the records in the set. If you later add a `region` field to a new record, it appears
  as a new column on the next table call with no schema change required.
- Adding the same content twice returns the same atom key. The record is written once;
  subsequent identical writes are silent upserts.

### Adding cheese records (same table, different type)

The `rec.*` model has no schema — you can store cheeses the same way with different attributes:

```javascript
await rpc("rec.new", {
  type:    "cheese",
  content: "Brie",
  origin:  "France",
  texture: "soft",
  age_months: "4",
});
```

The cheese records land in their own set (`set:rec:cheese`) and do not interfere with the
fruit table. To display them, call `rec.table` with `{ in_set: "rec:cheese" }`.

---

## 0-5 Wiring to a Live Server

### Starting the server

To use a web interface, start Akasha with the ASGI web server:

```bash
python akasha.py --server uvicorn
```

The server prints the port it binds to (default 8000). The RPC endpoint is then at
`http://localhost:8000/rpc`.

Without `--server uvicorn`, Akasha starts in CLI-only mode with a lightweight stdlib HTTP
server (`/api/rpc`). That endpoint works for curl and Python scripts, but does not serve
static files and does not send CORS headers — which brings us to the next point.

### CORS — why it matters for browser pages

Browsers enforce the **Same-Origin Policy**: a script running on page origin A cannot make
network requests to origin B unless origin B explicitly permits it via a
`Access-Control-Allow-Origin` response header.

This causes a practical problem when you open an HTML file directly from disk:

```
file:///home/you/my_akasha.html    ← page origin: file://
http://localhost:8000/rpc          ← request target: http://localhost:8000
```

These are different origins. The browser will block the `fetch()` call with a CORS error.
No amount of JavaScript can work around this — it is enforced by the browser itself.

The uvicorn/FastAPI server (`--server uvicorn`) sends `Access-Control-Allow-Origin: *` on all
responses, which tells the browser to allow requests from any origin including `file://`.
The stdlib httpd server does not set this header.

**Option 1 — Use `--server uvicorn` and open from `file://` or any origin.**

This is the simplest approach during development. Just start with `--server uvicorn` and
open your HTML file from disk as usual. The `*` CORS policy allows it.

**Option 2 — Serve your HTML from the Akasha server itself (same origin, no CORS at all).**

Place your HTML file inside the `archives/` directory:

```
AkashicTree/
  archives/
    index.html          ← the built-in portal
    fruit_records.html  ← your file goes here
```

Then start with:

```bash
python akasha.py --server uvicorn
```

Your page is now at `http://localhost:8000/fruit_records.html` — the same origin as
`http://localhost:8000/rpc`. No CORS header is needed at all because both the page and the
API are on `localhost:8000`. This is how the production web portal works.

In your HTML, you can simplify the `BASE` constant to an empty string or a relative path:

```javascript
const BASE = "";   // relative to current origin

async function rpc(method, data = {}) {
  const response = await fetch("/rpc", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ... }),
  });
  return response.json();
}
```

A relative URL like `/rpc` automatically resolves to the same host and port the page was
served from — so the code works regardless of which port Akasha started on.

### The archives portal as a reference

The `archives/` directory already contains a production-level frontend built entirely on
the same `/rpc` endpoint. It implements the public thesaurus reader, the Cosmos graph viewer,
and the admin console — all using `fetch()` calls in plain JavaScript, with no frameworks or
build pipeline beyond what ships with the HTML files themselves.

If you want to understand how a more complete interface handles authentication state,
error display, and progressive enhancement, reading `archives/index.html` and the companion
scripts is the most direct reference available.

---

## What You Have Built

Over this chapter you have:

- Understood the JSON-RPC 2.0 envelope and how every Akasha operation is a `method` + `data` call
- Established a guest session from a browser page and stored the `binding_key` for reuse
- Written atoms from a form and read them back with their link neighbourhood
- Created structured `rec:fruit` records with named numeric attributes and displayed them
  as a live-updating HTML table
- Understood why CORS matters and how to avoid it by serving your page from `archives/`

### Quick reference: method names used in this chapter

| CLI shorthand (Red Book) | HTTP JSON-RPC method | Key `data` fields |
|---|---|---|
| `w "text"` | `kernel.memory.write` | `text` |
| `r <key>` | `kernel.memory.read` | `id` |
| `al $it name` | `kernel.identity.alias` | `id`, `name` |
| `ln src dst rel` | `kernel.memory.link` | `src`, `dst`, `rel` |
| `ln.ls <key>` | `link.list` | `id` |
| `rec.new type=fruit …` | `rec.new` | `type`, `content`, plus any attributes |
| `rec.ls type=fruit` | `rec.ls` | `type` or `in_set` |
| `rec.table in_set=rec:fruit` | `rec.table` | `in_set` or `type` |
| `onto.dump mode=namespaces` | `onto.dump` | `mode` |

The `session.guest.create` method has no CLI equivalent — guest sessions are initiated
from client code, not from the interactive shell.

---

*Next: Blue Book Chapter 1 — Authentication, User Sessions, and Scoped Writes*
