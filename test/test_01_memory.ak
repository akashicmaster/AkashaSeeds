# =============================================================================
# AKASHA Test Suite 01 — Memory: write / define / read / drop / alias / meta
# =============================================================================
# HOW TO RUN:  run test/test_01_memory.ak
# VERIFY (interactively after job is DONE):
#   ls 15                         → see t01:* atoms
#   r t01:atom:a                  → content of atom A
#   al.find t01:%                 → all t01 aliases (temp should be absent — dropped)
#   al.ls                         → full alias list; t01:atom:gone should be absent
#   s.ls test:01:memory           → 3 members (apple/banana/cherry)
# =============================================================================

# ── 1. Write plain atoms ──────────────────────────────────────────────────────
w "Memory test atom A: the quick brown fox jumps over the lazy dog."
al $0 "t01:atom:a"

w "Memory test atom B: in the beginning was the word, and the word was data."
al $0 "t01:atom:b"

w "Memory test atom C: all models are wrong, but some are useful."
al $0 "t01:atom:c"

# ── 2. Define a conceptual hub ────────────────────────────────────────────────
def "t01:hub:memory_test"

# ── 3. Set metadata on an atom ────────────────────────────────────────────────
meta t01:atom:a category "test"
meta t01:atom:a suite "01_memory"

# ── 4. Add atoms to a set for verification ───────────────────────────────────
s.add test:01:memory t01:atom:a
s.add test:01:memory t01:atom:b
s.add test:01:memory t01:atom:c

# ── 5. Read back to confirm round-trip ───────────────────────────────────────
r t01:atom:a
r t01:atom:b

# ── 6. Link hub to atoms ──────────────────────────────────────────────────────
ln t01:hub:memory_test t01:atom:a sys:contains
ln t01:hub:memory_test t01:atom:b sys:contains
ln t01:hub:memory_test t01:atom:c sys:contains

# ── 7. Write and immediately drop a throwaway atom ───────────────────────────
# rm drops the atom by resolved key; $0 resolves to the last write's key.
w "Throwaway atom — will be dropped in the next step."
al $0 "t01:atom:temp"
rm t01:atom:temp

# ── 8. Test al.rm — remove an alias binding without deleting the atom ─────────
w "Alias removal test: this atom will have its alias stripped."
al $0 "t01:atom:gone"
al.rm "t01:atom:gone"
# Atom still exists in DB; alias t01:atom:gone no longer resolves it.
# VERIFY: al.find t01:% should not show "t01:atom:gone"
