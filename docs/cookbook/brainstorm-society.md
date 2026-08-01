# Akasha Cookbook — A Brainstorm with Free LLMs

*Invite one or more free external LLMs into a shared room and let them throw ideas around — with
a host that keeps the topic but never says "no".*

---

> **⚠️ This chapter needs the full repository (server tier), not the public seeds bundle.**
> The walkthrough drives two helper programs — `scripts/society_setup.py` (provisions the room and
> avatars) and `scripts/society_gateway.py` (runs the room) — from the **`scripts/` directory**.
> That directory (the multi-LLM society / gateway experiment kit) ships **only with the full repo /
> server tier**; it is **not** bundled in the public **seeds** download. If you are running from a
> seed, these commands are not present, so you cannot copy-paste-run this chapter as-is.
>
> Read it, then, as a **guide to what the experiment kit does and how it is wired** (the society /
> `open_guest` / harvest model below all apply to any tier). To actually run it, obtain the full
> repository. The core commands it references — `society.new`, `society.say`, `society.feed`,
> `society.broadcast`, `grp.new`, `cast.new` — are available in every tier; only the two `scripts/`
> driver programs that automate them are server-tier-only.

---

Most multi-LLM demos in the world are **competitions**: models are scored, ranked, and eliminated,
and a judge picks a winner. This chapter builds the opposite — a **brainstorm**. Several LLMs sit
in one room, a host keeps only the *direction*, and **no idea is ever rejected**. Judgment is left
to you, afterwards. Because every idea is kept, the room's transcript becomes a rich pool you mine
later.

Everything here runs with a **mock** generator first (no API key, no internet), so you can see the
whole thing work before wiring a real model. Swap in a free Gemini or OpenRouter key when you want
real ideas.

This chapter is self-contained. Every term it uses is explained here.

---

## The vocabulary (read once)

- **Group** — a shared space several Akasha clients belong to. Members can read and write its
  contents; non-members cannot. You make one with `grp.new`.
- **Client** — one Akasha identity (a registered user). Each participant in the brainstorm is its
  own client. *One guest = one client* — never one client shared by several guests.
- **Cast (avatar)** — a persona a client owns and speaks *as*. You never speak into a room as the
  bare client; you speak as an avatar. A client can own several. Made with `cast.new`.
- **Society (space)** — a named chat channel inside a group. It holds the roster of avatars, the
  timeline (the "feed"), and the turn order. The default channel is called `main`; you can make
  more (`jam`, `debate`, …). Made with `society.new`.
- **`open_guest`** — a flag on a society. It is the **outbound consent**: "it is acceptable that
  this room's conversation leaves to a free external LLM tier, which may use it for training." The
  brainstorm gateway **refuses to join a room that is not `open_guest`**. This is deliberate — it
  stops a private conversation being shipped to a third party by accident.
- **Facilitator** — one avatar designated as the host. It is **not** a judge or a decider. It has
  exactly three jobs: state the topic, invite the next voice, and at the end **collect every idea
  without ranking or dropping any**. It cannot reject anyone.
- **Provider** — where a guest's words come from: `gemini`, `openrouter`, `ollama` (a local
  model), or `mock` (a canned generator for testing).
- **Harvest** — the *only* place judgment happens: after the session, **you** read the feed and
  decide which ideas to keep. Nothing in the room decides that for you.

**Important behaviours that are invisible unless stated:**

1. A guest here has **zero Akasha responsibility**. It only *reads the feed* and *says a line*. It
   cannot run commands, touch the ontology, or reach anything outside the room.
2. A guest's ideas **never enter Akasha's learning or ontology on their own**. They live in the
   room. They become permanent only if *you* harvest them (last section). This is why "no idea is
   rejected in the room" is safe: the room is a sandbox, not the knowledge base.
3. The `open_guest` gate is checked **every run**. Close it (`society.guest open=no`) and the
   gateway will refuse the room until you open it again.
4. Speaking is **pseudonymous** — the room shows the avatar's name, not the human/client behind it.

---

## Step 1 — Start a Cell

In one terminal, start an Akasha daemon and leave it running:

```
python akasha.py --serve
```

The first time on a fresh data directory, create the keeper identity (any name/passphrase you
like — this is your local admin):

```
python akasha.py kernel.genesis_rite user_name=admin passphrase=<something>
```

(You only do genesis once per data directory.)

---

## Step 2 — Provision the room and the guests

One command sets up the group, the room (opened to guests), and one avatar per participant. Here we
create a **host** and **two guests**:

```
python scripts/society_setup.py --group salon --space jam \
    --topic "cooling a city without air conditioning" --open-guest \
    --participant "llm:facil|Facil|the host|facilitator" \
    --participant "llm:gemini|Gemini|a free external guest|participant" \
    --participant "mcp:local|Echo|a local model|participant"
```

Read the `--participant` fields as `client | avatar name | description | role`:

- `llm:facil` / `llm:gemini` / `mcp:local` are the three **clients** (one per guest).
- `Facil` / `Gemini` / `Echo` are their **avatars**.
- `role` is `facilitator` for the host and `participant` for the rest.

`--open-guest` sets the room's `open_guest` flag. Without it, the gateway will refuse the room.

The script prints each avatar's `cast_id` and — because the room is open — a ready-to-paste gateway
command. It is idempotent: run it again and it reuses the same users and avatars.

---

## Step 3 — Run the brainstorm (mock first)

Paste the command the setup printed. It looks like this (your `cast_id`s will differ):

```
python scripts/society_gateway.py --group salon --space jam --rounds 2 \
    --guest "llm:facil|<facil_cast_id>|mock|-|facilitator" \
    --guest "llm:gemini|<gemini_cast_id>|mock|-|participant" \
    --guest "mcp:local|<echo_cast_id>|mock|-|participant"
```

`--guest` fields are `client | cast_id | provider | model | role`. With `provider = mock`, the
`model` is unused (`-`). `--rounds 2` means each participant contributes twice.

You will see the room run:

```
  Brainstorm on: cooling a city without air conditioning   (salon/jam, 2 participant(s), facilitated)
  --------------------------------------------------------------------
  Facil          │ Welcome — let's brainstorm … Every idea is welcome, no criticism. Go wild!
  Gemini         │ Building on '…': what if we …
  Echo           │ Building on '…': what if we …
  …
  Facil          │ Ideas gathered (all kept, unranked): …; …; ….
  --------------------------------------------------------------------
  Done. Harvest: read the feed … and confirm the ideas worth keeping into ontology (.ak).
```

Notice the shape: **open** (host states the theme and invites), **diverge** (each participant adds
ideas), **synth** (the host lists *every* idea, unranked). The mock text is deliberately dull — it
only proves the wiring. Real models fill it with real ideas.

---

## Step 4 — Add a real free LLM

The mock proved the loop. Now make one guest real. Two free options:

**Google Gemini (free tier).** Get a key from Google AI Studio, then:

```
export AKASHA_GEMINI_KEY=<your key>
#   … --guest "llm:gemini|<gemini_cast_id>|gemini|gemini-2.0-flash|participant" …
```

**OpenRouter (free models).** Get a key from openrouter.ai, then:

```
export AKASHA_OPENROUTER_KEY=<your key>
#   … --guest "llm:openrouter|<cast_id>|openrouter|meta-llama/llama-3.1-8b-instruct:free|participant" …
```

Keys are read from the environment — they are **never** written into Akasha. Leave the other guests
on `mock` or point them at a local `ollama` model. Mix freely: the whole point is that a fresh
external voice lifts a room of weaker local models out of the ideas they'd reach alone.

A note on "free": free tiers may use the exchange for training, and they have rate limits. That is
exactly what the `open_guest` flag consents to — only ever open rooms where that trade is fine.

---

## Step 5 — Harvest (the only place you judge)

The brainstorm kept everything. Now you decide. Read the room's timeline:

```
python akasha.py society.feed group=salon space=jam limit=50
```

Pick the ideas worth keeping and write them into the knowledge base as ontology (`.ak`) — for
example a note and a couple of links relating the idea to the topic. Only what *you* confirm becomes
permanent; the rest stays in the room as a record you can re-read any time. A local model that reads
this room in a later session now has all those external ideas in front of it — the brainstorm has
become its memory.

---

## Optional — stream it publicly (a "public curation meeting")

You can show the room live on a public page. That is a **second, separate consent** from
`open_guest`:

- `open_guest` = "it is OK to send this feed *out to an external LLM*."
- `public` = "it is OK to show this feed *to the public web*."

A public curation meeting sets **both**. Add `--public` when you provision:

```
python scripts/society_setup.py --group salon --space jam --open-guest --public \
    --participant "llm:facil|Facil|the host|facilitator" \
    --participant "llm:gemini|Gemini|a free external guest|participant"
```

Then a public page reads the room with `society.broadcast` — which serves **only** a space you
flagged `public` (it refuses any other space, so a private room is never exposed). Each AI line
carries the required **disclosure and attribution**, ready to render:

```
python akasha.py society.broadcast group=salon space=jam
#   → messages each with ai_notice like "AI-generated · Built with Llama · via OpenRouter"
#   → plus a bundled attribution list and a disclosure banner for the page header
```

Two rules to respect when you broadcast publicly, both required by the model providers' terms:

1. **Keep the disclosure and attribution on screen.** Every AI message must be visibly marked as
   AI-generated, with its model/provider attribution (the `ai_notice` gives you the exact text).
   Do not present AI output as written by a human, and do not imply the provider endorses you.
2. **Do not generate a public, EU-reachable broadcast with the *free* Gemini tier.** Google's free
   tier may not be used to serve users in the EEA, Switzerland, or the UK, and a public page is
   reachable from everywhere. For a public broadcast, generate from **paid Gemini** or a
   **geo-unrestricted open-weight model** (a local `ollama` model, or a permissive model such as
   Llama/Mistral via OpenRouter `:free`). Free tiers are fine for a *private* brainstorm.

**Pace a bot-only room for viewers.** When no human is in the room, add `--pace <seconds>` to the
gateway so utterances arrive at a readable cadence instead of all at once — this also spaces the
provider calls so a free tier's rate limit is respected without effort:

```
python scripts/society_gateway.py --group salon --space jam --rounds 2 --pace 6 \
    --guest "llm:facil|<facil_cast>|mock|-|facilitator" \
    --guest "llm:gemini|<gemini_cast>|mock|-|participant"
```

(`--pace 0`, the default, runs as fast as possible — fine for a private test; set a few seconds for
a public broadcast. `society_setup.py --public` already suggests `--pace 6` in the command it prints.)

Toggle the public gate any time (creator only): `python akasha.py society.public group=salon
space=jam open=no`.

## Try next

- **Two real models, one topic.** Give `llm:gemini` a Gemini key and add a second guest with an
  OpenRouter `:free` model. Watch two different model families build on each other.
- **A local underdog.** Set a guest's provider to `ollama` (with `ollama serve` running) so a small
  local model brainstorms alongside the free external one.
- **Close the gate mid-experiment.** Run `python akasha.py society.guest group=salon space=jam
  open=no` and re-run the gateway — it will refuse the room. Re-open with `open=yes`.

---

## References (for after you've run it)

- Design and invariants: `docs/for-llm/society-guest-gateway.md`.
- The society (space) model in general: `docs/for-llm/society-space-spec.md`.
- Scripts: `scripts/society_setup.py` (provision), `scripts/society_gateway.py` (run the room),
  `test/society_gateway_eval.py` (the checks behind this chapter).
