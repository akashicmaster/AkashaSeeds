"""
wordnet_import.py — WordNet → word:en: atom generator for Akasha ontology

Usage:
    python app/scripts/wordnet_import.py [options]

    --total N        Total words to generate (default: 30000)
    --chunk-size N   Words per output file (default: 2000)
    --min-freq F     Min Brown corpus frequency for Phase 1 (default: 2)
    --out DIR        Output directory (default: ontology/common/)
    --dry-run        Print stats only, write nothing

Output files (place in ontology/common/ for auto-load at first boot):
    word_core_01.ak     — frequency rank 1–2000
    word_core_02.ak     — frequency rank 2001–4000
    word_core_03.ak     — frequency rank 4001–6000
    word_core_04.ak     — frequency rank 6001–8000
    word_ext_01.ak      — frequency rank 8001–10000
    word_ext_02.ak      — ...
    ...                 — remaining words; JCL processes sequentially

Word sourcing (two phases):
    Phase 1 — Brown corpus frequency ranking (top ~10-15k content words)
    Phase 2 — WordNet lemma supplement for words beyond Brown coverage

Deduplication against existing ontology:
    - word:en:X already defined        → skip
    - specialist namespace atom exists → emit def + calc:associated_with link
    - not covered at all               → emit def + antonym/emotion links

WordNet definitions from Princeton University WordNet 3.1.
License: https://wordnet.princeton.edu/license-and-commercial-use
Free use with attribution. Attribution line in each output file header.
"""

import argparse
import os
import re
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)            # the application root (app/)
COMMON_DIR = os.path.join(PROJECT_ROOT, "ontology", "common")

ANTONYM_REL = "sys:antonym"

FUNCTION_WORD_BLACKLIST = {
    "be", "is", "are", "am", "was", "were", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "done", "doing",
    "will", "would", "shall", "should", "may", "might",
    "can", "could", "must", "ought",
    "i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "who", "whom", "whose", "which", "that", "this", "these", "those",
    "a", "an", "the", "any", "some", "all", "both", "each", "every",
    "no", "none", "few", "many", "much", "more", "most", "other",
    "another", "such", "what", "whatever", "whoever",
    "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after",
    "above", "below", "from", "up", "down", "out", "off", "over",
    "under", "again", "then", "once", "here", "there", "when",
    "where", "why", "how", "and", "but", "or", "nor", "so", "yet",
    "if", "because", "as", "until", "while", "although", "since",
    "though", "whether", "not", "also", "just", "even", "still",
    "than", "too", "very", "well", "back", "only",
    "get", "got", "make", "made", "go", "going", "come", "came",
    "take", "took", "give", "gave", "know", "knew", "think",
    "thought", "say", "said", "see", "saw", "look", "want", "use",
    "find", "tell", "ask", "seem", "feel", "try", "leave", "call",
    "keep", "let", "begin", "show", "hear", "play", "run", "move",
    "live", "believe", "hold", "bring", "happen", "write", "sit",
    "stand", "lose", "pay", "meet", "include", "continue", "set",
    "learn", "change", "lead", "understand", "watch", "follow",
    "stop", "create", "speak", "read", "spend", "grow", "open",
    "walk", "win", "offer", "remember", "consider", "turn", "put",
    "become", "start", "reach", "kill", "remain", "suggest", "raise",
    "pass", "sell", "send", "expect", "apply",
}

EMOTION_MAP = {
    "joy": "emo:joy", "happiness": "emo:joy", "pleasure": "emo:joy",
    "sadness": "emo:sadness", "sorrow": "emo:sadness", "grief": "emo:sadness",
    "fear": "emo:fear", "anxiety": "emo:fear", "terror": "emo:fear",
    "anger": "emo:anger", "rage": "emo:anger", "fury": "emo:anger",
    "trust": "emo:trust", "confidence": "emo:trust", "faith": "emo:trust",
    "disgust": "emo:disgust", "loathing": "emo:disgust",
    "surprise": "emo:surprise", "astonishment": "emo:surprise",
    "anticipation": "emo:anticipation", "expectation": "emo:anticipation",
    "delight": "emo:joy", "ecstasy": "emo:joy",
    "despair": "emo:sadness", "melancholy": "emo:sadness",
    "dread": "emo:fear", "panic": "emo:fear",
    "wrath": "emo:anger", "irritation": "emo:anger",
}


# ---------------------------------------------------------------------------
# Step 1: Parse existing ontology
# ---------------------------------------------------------------------------

def parse_existing_ontology(common_dir: str):
    """
    Returns:
        existing_en  : set of bare words already defined as word:en:*
        ns_atoms     : dict bare_word -> list of (ns, full_alias)
    """
    existing_en: set[str] = set()
    ns_atoms: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for fname in sorted(os.listdir(common_dir)):
        if not fname.endswith(".ak"):
            continue
        with open(os.path.join(common_dir, fname), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r'^def "([^"]+)"', line)
                if not m:
                    continue
                alias = m.group(1)
                if alias.startswith("word:en:"):
                    existing_en.add(alias[len("word:en:"):].lower())
                elif ":" in alias:
                    ns, _, rest = alias.partition(":")
                    if ns not in ("word", "ont", "series", "curations", "thesaurus"):
                        bare = rest.split(":")[0].lower()
                        ns_atoms[bare].append((ns, alias))

    return existing_en, ns_atoms


# ---------------------------------------------------------------------------
# Step 2: Build candidate word list (Brown + WordNet supplement)
# ---------------------------------------------------------------------------

def _is_valid_word(w: str) -> bool:
    return bool(re.match(r"^[a-z]{4,30}$", w)) and w not in FUNCTION_WORD_BLACKLIST


def phase1_brown(min_freq: int) -> list[tuple[str, int]]:
    """Brown corpus frequency-ranked content words."""
    from nltk.corpus import brown
    from nltk.probability import FreqDist

    print("[wordnet_import] Phase 1: Brown corpus frequency ranking...", flush=True)
    keep_tags = {"NOUN", "VERB", "ADJ", "ADV"}
    fd = FreqDist()
    for word, tag in brown.tagged_words(tagset="universal"):
        if tag in keep_tags:
            w = word.lower()
            if _is_valid_word(w):
                fd[w] += 1

    result = [(w, f) for w, f in fd.most_common() if f >= min_freq]
    print(f"  Brown candidates: {len(result)}", flush=True)
    return result


def phase2_wordnet_supplement(already_seen: set[str], target_count: int) -> list[tuple[str, int]]:
    """
    WordNet lemmas not already in Brown (or existing ontology).
    Priority = synset offset (lower = more common in WordNet ordering).
    Returns list of (word, priority) where priority is a synthetic rank.
    """
    from nltk.corpus import wordnet as wn

    print(f"[wordnet_import] Phase 2: WordNet supplement for {target_count} more words...", flush=True)

    # Collect all WordNet lemmas with their minimum synset offset as proxy for frequency
    lemma_priority: dict[str, int] = {}
    for syn in wn.all_synsets():
        for lemma in syn.lemmas():
            w = lemma.name().lower().replace("_", " ")
            # Only single-word lemmas
            if " " in w:
                continue
            w = w.replace("-", "")
            if not _is_valid_word(w):
                continue
            if w in already_seen:
                continue
            # Lower offset = earlier in WordNet = conventionally more common
            if w not in lemma_priority or syn.offset() < lemma_priority[w]:
                lemma_priority[w] = syn.offset()

    # Sort by offset ascending (lower offset → higher priority)
    sorted_lemmas = sorted(lemma_priority.items(), key=lambda x: x[1])
    result = [(w, 0) for w, _ in sorted_lemmas[:target_count]]
    print(f"  WordNet supplement candidates: {len(result)}", flush=True)
    return result


def build_candidate_list(total_n: int, min_freq: int, existing_en: set[str]) -> list[tuple[str, int]]:
    """Build frequency-ranked candidate list up to total_n words."""
    brown_words = phase1_brown(min_freq)

    # Remove words already in ontology
    brown_filtered = [(w, f) for w, f in brown_words if w not in existing_en]

    if len(brown_filtered) >= total_n:
        return brown_filtered[:total_n]

    # Need more: supplement with WordNet
    already_seen = existing_en | {w for w, _ in brown_filtered}
    supplement_needed = total_n - len(brown_filtered)
    wn_supplement = phase2_wordnet_supplement(already_seen, supplement_needed)
    return brown_filtered + wn_supplement


# ---------------------------------------------------------------------------
# Step 3: WordNet lookup
# ---------------------------------------------------------------------------

def wordnet_lookup(word: str) -> tuple[str | None, list[str]]:
    """Returns (definition, antonym_bare_list) using the most common synset."""
    from nltk.corpus import wordnet as wn

    synsets = wn.synsets(word)
    if not synsets:
        return None, []

    syn = synsets[0]
    defn = syn.definition()
    if not defn:
        return None, []

    defn = defn[0].upper() + defn[1:]
    if not defn.endswith("."):
        defn += "."

    antonyms = []
    for lemma in syn.lemmas():
        for ant in lemma.antonyms():
            ant_name = ant.name().replace("_", " ")
            if " " not in ant_name and _is_valid_word(ant_name):
                antonyms.append(ant_name)

    return defn, antonyms


# ---------------------------------------------------------------------------
# Step 4: Emit .ak content for a single word
# ---------------------------------------------------------------------------

def emit_word(fh, word: str, defn: str, antonyms: list[str],
              spec_atoms: list[tuple[str, str]] | None):
    fh.write(f'def "word:en:{word}" "{defn}"\n')

    if spec_atoms:
        for ns, full_alias in spec_atoms:
            bare_target = full_alias.split(":")[-1].split(".")[-1]
            fh.write(f"ln {word} {bare_target} calc:associated_with\n")

    for ant in antonyms:
        fh.write(f"ln {word} {ant} {ANTONYM_REL}\n")
        fh.write(f"ln {ant} {word} {ANTONYM_REL}\n")

    emo = EMOTION_MAP.get(word)
    if emo:
        fh.write(f"ln {word} {emo} calc:has_emotion\n")

    fh.write("\n")


FILE_HEADER = """\
# {filename}
# WordNet definitions: Princeton University WordNet 3.1
# License: https://wordnet.princeton.edu/license-and-commercial-use
# Place in ontology/common/ — loads at first-install boot only (sentinel-guarded).
#
# Words: {word_range}
# Generated by wordnet_import

"""


# ---------------------------------------------------------------------------
# Step 5: Main generation
# ---------------------------------------------------------------------------

def generate(total_n: int, chunk_size: int,
             min_freq: int, out_dir: str, dry_run: bool):
    os.makedirs(out_dir, exist_ok=True)

    print("[wordnet_import] Scanning existing ontology...", flush=True)
    existing_en, ns_atoms = parse_existing_ontology(COMMON_DIR)
    print(f"  word:en: already defined: {len(existing_en)}")
    print(f"  bare words with specialist namespace atoms: {len(ns_atoms)}")

    candidates = build_candidate_list(total_n, min_freq, existing_en)
    print(f"\n[wordnet_import] Total candidates to process: {len(candidates)}")

    CORE_CHUNKS = 4  # word_core_01..04 (frequency top ~8000)

    if dry_run:
        crosslink = sum(1 for w, _ in candidates if w in ns_atoms)
        newdef = len(candidates) - crosslink
        print(f"  → cross-link candidates: {crosslink}")
        print(f"  → new def candidates:    {newdef}")
        num_core = CORE_CHUNKS
        num_ext = max(0, (len(candidates) - CORE_CHUNKS * chunk_size + chunk_size - 1) // chunk_size)
        print(f"  → core files ({chunk_size} words each): word_core_01.ak .. word_core_{num_core:02d}.ak")
        print(f"  → extended files ({chunk_size} words each): word_ext_01.ak .. word_ext_{num_ext:02d}.ak")
        return

    # Classify all candidates
    words: list[tuple[str, str, list[str], list[tuple[str, str]] | None]] = []
    skipped = 0
    for word, _ in candidates:
        defn, antonyms = wordnet_lookup(word)
        if not defn:
            skipped += 1
            continue
        spec = ns_atoms.get(word) or None
        words.append((word, defn, antonyms, spec))

    print(f"  Skipped (no WordNet entry): {skipped}")
    print(f"  Words to write: {len(words)}")

    # Split uniformly: first CORE_CHUNKS files → word_core_NN.ak, rest → word_ext_NN.ak
    all_chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
    core_chunks = all_chunks[:CORE_CHUNKS]
    ext_chunks  = all_chunks[CORE_CHUNKS:]

    written_files = []
    offset = 0

    # --- word_core_NN.ak ---
    for idx, chunk in enumerate(core_chunks, start=1):
        fname = f"word_core_{idx:02d}.ak"
        fpath = os.path.join(out_dir, fname)
        chunk_range = f"{offset + 1} – {offset + len(chunk)}"
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(FILE_HEADER.format(filename=fname, word_range=chunk_range))
            for word, defn, antonyms, spec in chunk:
                emit_word(fh, word, defn, antonyms, spec)
        written_files.append((fname, len(chunk)))
        offset += len(chunk)

    # --- word_ext_NN.ak ---
    for idx, chunk in enumerate(ext_chunks, start=1):
        fname = f"word_ext_{idx:02d}.ak"
        fpath = os.path.join(out_dir, fname)
        chunk_range = f"{offset + 1} – {offset + len(chunk)}"
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(FILE_HEADER.format(filename=fname, word_range=chunk_range))
            for word, defn, antonyms, spec in chunk:
                emit_word(fh, word, defn, antonyms, spec)
        written_files.append((fname, len(chunk)))
        offset += len(chunk)

    # --- Summary ---
    print(f"\n[wordnet_import] Files written to {out_dir}/")
    for fname, count in written_files:
        print(f"  {fname:25s}  {count:5d} words")

    total_written = sum(c for _, c in written_files)
    print(f"\n  Total: {total_written} words across {len(written_files)} files")
    print(f"\nNext step: copy files to ontology/common/ and run onto.reload")
    print("  (or place there before first-install boot — sentinel prevents duplicate load)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--total",      type=int, default=30000,
                    help="Total words to generate (default: 30000)")
    ap.add_argument("--chunk-size", type=int, default=2000,
                    help="Words per output file (default: 2000); first 4 files are word_core_NN.ak, rest word_ext_NN.ak")
    ap.add_argument("--min-freq",   type=int, default=2,
                    help="Min Brown corpus frequency (default: 2)")
    ap.add_argument("--out", default=os.path.join(PROJECT_ROOT, "out"),
                    help="Output directory (default: out/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print stats only, write no files")
    args = ap.parse_args()

    import nltk
    for corpus in ("wordnet", "brown", "omw-1.4", "universal_tagset"):
        try:
            nltk.data.find(f"corpora/{corpus}")
        except LookupError:
            print(f"[wordnet_import] Downloading: {corpus}")
            nltk.download(corpus, quiet=True)

    generate(args.total, args.chunk_size,
             args.min_freq, args.out, args.dry_run)


if __name__ == "__main__":
    main()
