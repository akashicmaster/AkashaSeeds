# =============================================================================
# AKASHA Test Suite 05 — Notes, Logs & System history
# =============================================================================
# HOW TO RUN:  run test/test_05_notes_sys.ak
# VERIFY (interactively after job is DONE):
#   r t05:note:root             → note root atom content
#   ln.ls t05:note:root         → outgoing links to paragraphs and principle
#   ls 10                       → recent atoms including note paragraphs
#   hist                        → recent atom stream
#   al.find t05:%               → t05 aliases
#   log.ls                      → should include "t05: Akasha Memory Model" log
# =============================================================================

# ── 1. Create a structured note ────────────────────────────────────────────────
n.new "t05: The AKASHA Memory Model"
al $0 "t05:note:root"

n.add "AKASHA is a local-first semantic knowledge substrate. Every piece of information is stored as an Atom — an addressable node in the memory mesh."
n.add "Atoms are connected by typed Links. Each link carries a relation label (rel) and an optional weight (w) representing confidence or strength."
n.add "The memory is organised into Scopes. Your private atoms live in your personal scope. Collective knowledge lives in scope:sys:universal."
n.add "JCL (Job Control Layer) allows batch operations to run asynchronously under Harmonia orchestration, with full rollback support."

# ── 2. Write a standalone atom referencing the note ──────────────────────────
w "AKASHA design principle: the shell never touches the database; only the kernel does."
al $0 "t05:principle:kernel_boundary"
ln t05:note:root t05:principle:kernel_boundary sys:associated_with

# ── 3. Build a small temporal chain to test $0 reference ─────────────────────
w "Temporal test atom: first in sequence."
al $0 "t05:seq:first"

w "Temporal test atom: second in sequence."
al $0 "t05:seq:second"
ln t05:seq:first $0 @followed_by

w "Temporal test atom: third in sequence."
al $0 "t05:seq:third"
ln t05:seq:second $0 @followed_by

# ── 4. Read back to confirm round-trip ───────────────────────────────────────
r t05:seq:first
r t05:seq:second

# ── 5. Test hist — recent atom stream ────────────────────────────────────────
hist
# Result captured in job log; shows atoms written most recently.

# ── 6. Test exploration log ──────────────────────────────────────────────────
log.new "t05: Akasha Memory Model"
log.cp  "Wrote 4-chunk note on the memory model"
log.cp  "Built temporal chain to test $0 resolution"
log.ann "Both seq:first and seq:second readable via alias"
log.read
# VERIFY: log.ls should list this log after the job completes.

# ── 7. Add to test set ────────────────────────────────────────────────────────
s.add test:05:notes t05:note:root
s.add test:05:notes t05:principle:kernel_boundary
s.add test:05:notes t05:seq:first
s.add test:05:notes t05:seq:second
s.add test:05:notes t05:seq:third
