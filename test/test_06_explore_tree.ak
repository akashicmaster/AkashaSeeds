# =============================================================================
# AKASHA Test Suite 06 — Navigation: exp / tree / look / assoc / ln.ls
# =============================================================================
# Builds an AI/ML knowledge graph large enough for tree and exp to be meaningful.
# HOW TO RUN:  run test/test_06_explore_tree.ak
#
# VERIFY (interactively after job is DONE):
#   tree t06:hub:ai 3            → 3-level AI hierarchy
#   exp  ns=t06                  → BFS neighbourhood of all t06 atoms
#   look t06:node:ml             → ML atom with signposts
#   ln.ls t06:hub:ai             → outgoing sys:contains links
#   tree t06:node:ml 2           → ML sub-tree (deep_learning, rl)
# =============================================================================

# ── 1. Create an AI/ML knowledge graph ────────────────────────────────────────
def "t06:hub:ai"

w "Machine Learning — a subfield of AI focused on learning patterns from data."
al $0 "t06:node:ml"

w "Deep Learning — ML using multi-layer neural networks for feature extraction."
al $0 "t06:node:deep_learning"

w "Reinforcement Learning — ML where an agent learns via reward signals."
al $0 "t06:node:rl"

w "Natural Language Processing — AI applied to understanding and generating human language."
al $0 "t06:node:nlp"

w "Computer Vision — AI for interpreting and understanding visual information."
al $0 "t06:node:cv"

w "Transformer — a neural architecture based on self-attention, foundational for LLMs."
al $0 "t06:node:transformer"

w "Convolutional Neural Network — a deep learning architecture for grid-like data such as images."
al $0 "t06:node:cnn"

w "Large Language Model — a transformer-based model trained on vast text corpora."
al $0 "t06:node:llm"

# ── 2. Build hierarchy ────────────────────────────────────────────────────────
ln t06:hub:ai             t06:node:ml             sys:contains
ln t06:hub:ai             t06:node:nlp            sys:contains
ln t06:hub:ai             t06:node:cv             sys:contains

ln t06:node:ml            t06:node:deep_learning  sys:contains
ln t06:node:ml            t06:node:rl             sys:contains

ln t06:node:deep_learning t06:node:transformer    sys:contains
ln t06:node:deep_learning t06:node:cnn            sys:contains

ln t06:node:transformer   t06:node:llm            sys:contains
ln t06:node:nlp           t06:node:transformer    sys:uses

# ── 3. Cross-domain associations ──────────────────────────────────────────────
ln t06:node:cv  t06:node:cnn sys:uses
ln t06:node:nlp t06:node:llm sys:associated_with

# ── 4. Metadata ───────────────────────────────────────────────────────────────
meta t06:hub:ai   domain "artificial_intelligence"
meta t06:node:ml  domain "machine_learning"
meta t06:node:llm example "GPT-4, Claude, Gemini"

# ── 5. In-script navigation calls (results captured in job log) ───────────────
tree t06:hub:ai 3
# Shows 3-level hierarchy rooted at t06:hub:ai.

exp ns=t06
# BFS neighbourhood of all t06:* atoms.

look t06:node:ml
# Dive view of Machine Learning node with its signposts.

assoc t06:node:llm
# Gap detection: lists semantic axes where t06:node:llm could have more links.

# ── 6. Set ────────────────────────────────────────────────────────────────────
s.add test:06:explore t06:hub:ai
s.add test:06:explore t06:node:ml
s.add test:06:explore t06:node:llm
s.add test:06:explore t06:node:transformer
