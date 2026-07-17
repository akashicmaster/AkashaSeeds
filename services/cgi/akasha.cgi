#!/usr/bin/env python3
"""
Akasha CGI entry — JSON-RPC endpoint for restricted / shared hosting.

Some rental servers do not let you launch a long-running httpd or bind an
arbitrary port; they only offer CGI. This script is the RPC route for those
environments. It forwards a POST JSON-RPC body to the very same gateway every
other portal uses (api.gateway → kernel), so behaviour is identical to the
uvicorn/httpd portals — only the transport differs.

Why plain CGI is enough here (no daemon, no open port):
  • On a warm cell (base ontology already loaded, its filesystem sentinel
    present) the kernel boot is ~0.3–0.4 s per request. Reads come from the
    shared, persistent nucleus; nothing needs to stay resident.
  • Guest tokens (gbk:) are self-verifying — HMAC-signed with the nucleus
    secret — so a token minted in one request authenticates in the next,
    even though each request is a fresh process. The public thesaurus read
    flow (session.guest.create → thesaurus.view.atom / shelf.list) therefore
    works statelessly.

Deployment (see docs/developer/cgi-deployment.md for the full guide):
  1. Upload the repository somewhere under your account.
  2. ONE-TIME preload so the first visitor does not pay the ontology-load
     cost (which would exceed a CGI timeout):
         python akasha.py --stdio ping
     Run it once over SSH; it loads the base ontology and writes the restart
     sentinel. All later CGI requests are warm.
  3. Make this file executable:  chmod 755 services/cgi/akasha.cgi
  4. Route /rpc and /api/rpc (POST) to this script and serve the archives/
     static files directly — see services/cgi/.htaccess.example.

Environment (optional):
  AKASHA_SERIES   pin the distribution tier (e.g. "thesaurus"); default "seeds".
  AKASHA_SECRET   REQUIRED for any networked/multi-host deploy — the HMAC key
                  that signs guest/auth tokens. Set it in the host env so it is
                  stable across requests and hosts (see the Security Model in
                  CLAUDE.md). Without it, a per-cell key is generated on disk.
"""
import os
import sys

# Anchor to the project root (this file lives at <root>/services/cgi/akasha.cgi)
# regardless of the web server's working directory.
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))
if _root not in sys.path:
    sys.path.insert(0, _root)

# The web server sets REQUEST_METHOD (and usually GATEWAY_INTERFACE) for CGI;
# assert the marker so akasha.py takes its CGI fast-path even on hosts that omit
# GATEWAY_INTERFACE. akasha.py reads this at import time, so set it BEFORE import.
os.environ.setdefault("GATEWAY_INTERFACE", "CGI/1.1")

import akasha  # noqa: E402  (env must be set first)

akasha.main()
