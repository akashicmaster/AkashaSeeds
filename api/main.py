#!/usr/bin/env python3
"""
Legacy entry-point shim.
Delegates to the canonical akasha.py entry point so that invocations via
`python api/main.py` continue to work unchanged.
"""
import sys
import os

# Ensure the project root is on sys.path when invoked as `python api/main.py`
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from akasha import main

if __name__ == "__main__":
    main()
