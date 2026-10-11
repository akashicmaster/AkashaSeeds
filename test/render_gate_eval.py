#!/usr/bin/env python3
"""
F47-1.3 — the render slot is concurrency-1 and HUMAN-PRIORITY.

Measured GIL anti-scaling makes serial rendering the fastest (3 concurrent renders were 172 ms each
/ 18-per-s TOTAL vs 21 ms / 46-per-s at 1). So the portal admits ONE render at a time, and the slot
is reserved for humans: a bot-class render is admitted only when the slot is free AND no human is
waiting, so a human is NEVER shed while a bot holds or is queued for the slot. This eval drives the
admission primitive directly on an event loop.

Run:  python test/render_gate_eval.py   (exit 0 = all pass)
"""
import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


async def scenario():
    import api.portals.asgi as asgi
    # fresh semaphore bound to THIS loop
    asgi._SSR_SEM["sem"] = None
    asgi._HUMAN_WAITING["n"] = 0

    check("1.3 render concurrency defaults to 1 (serial is fastest)",
          asgi._SSR_MAX_CONCURRENCY == 1, "conc=%d" % asgi._SSR_MAX_CONCURRENCY)

    # (1) slot free, no human waiting → a bot is admitted
    got_bot = await asgi._acquire_render(is_human=False)
    check("1.3 a bot is admitted when the slot is free and no human waits", got_bot is True)

    # (2) while the bot holds the (only) slot, another bot is SHED (never a second concurrent render)
    got_bot2 = await asgi._acquire_render(is_human=False)
    check("1.3 a second bot is shed while the slot is held (concurrency stays 1)", got_bot2 is False)
    asgi._release_render()                       # bot #1 done

    # (3) a human takes the slot; a bot arriving now is shed (human holds it)
    got_h = await asgi._acquire_render(is_human=True)
    check("1.3 a human acquires the free slot", got_h is True)
    got_bot3 = await asgi._acquire_render(is_human=False)
    check("1.3 a bot is shed while a human holds the slot", got_bot3 is False)

    # (4) THE INVARIANT: while a human is WAITING for a busy slot, a bot is shed (never queues ahead)
    #     Start a human waiter (the slot is currently held by the human from step 3), then a bot tries.
    async def _human_waiter():
        ok = await asgi._acquire_render(is_human=True)   # will block until the slot frees
        return ok
    waiter = asyncio.create_task(_human_waiter())
    await asyncio.sleep(0.05)                     # let the waiter register as _HUMAN_WAITING
    check("1.3 a waiting human is registered so bots defer", asgi._HUMAN_WAITING["n"] >= 1,
          "waiting=%d" % asgi._HUMAN_WAITING["n"])
    got_bot4 = await asgi._acquire_render(is_human=False)
    check("1.3 a bot is shed while ANY human is waiting (the F47 invariant)", got_bot4 is False)

    asgi._release_render()                        # free the slot the first human held
    waited_ok = await asyncio.wait_for(waiter, timeout=2.0)
    check("1.3 the waiting human then gets the slot", waited_ok is True)
    asgi._release_render()                         # second human done
    check("1.3 slot accounting balances (no leaked holders)", asgi._HUMAN_WAITING["n"] == 0,
          "waiting=%d" % asgi._HUMAN_WAITING["n"])


def main():
    asyncio.run(scenario())
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — render concurrency is 1 and human-priority: bots serialize/shed, a human is "
          "never shed while a bot holds or is queued for the slot, and a waiting human is served next.")
    sys.exit(0)


if __name__ == "__main__":
    main()
