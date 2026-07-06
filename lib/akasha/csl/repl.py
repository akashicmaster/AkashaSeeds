"""CSL interactive interpreter."""
import sys
from typing import Any


def run_repl(session: Any) -> None:
    """Launch the CSL interactive interpreter."""
    from .tokenizer import tokenize
    from .parser import parse
    from .validator import validate
    from .compiler import compile_script
    from .runtime import CslRuntime

    runtime = CslRuntime(session)
    print("Akasha CSL interpreter (Phase 1). Type 'exit' or Ctrl-D to quit.")

    while True:
        try:
            line = input("csl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line or line in ("exit", "quit"):
            break

        # Handle multi-line input (block syntax: line ends with :)
        if line.endswith(":"):
            block_lines = [line]
            while True:
                try:
                    cont = input("...   ")
                except (EOFError, KeyboardInterrupt):
                    break
                if not cont.strip():
                    break
                block_lines.append(cont)
            source = "\n".join(block_lines)
        else:
            source = line

        try:
            tokens = tokenize(source)
            script = parse(tokens)
            errors = validate(script)
            if errors:
                for e in errors:
                    level = e.level.upper()
                    print(f"  {level} line {e.line}: {e.error}", file=sys.stderr)
                    if e.suggestion:
                        print(f"  Suggestion: {e.suggestion}", file=sys.stderr)
                if any(e.level == "error" for e in errors):
                    continue
            calls = compile_script(script)
            results = runtime.run(calls)
            for r in results:
                if r.error:
                    print(f"  ERROR: {r.error}", file=sys.stderr)
                elif r.result is not None:
                    import json
                    print(json.dumps(r.result, ensure_ascii=False, indent=2))
                if r.assigns_to:
                    print(f"  -> ${r.assigns_to} = <{r.method} result>")
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
