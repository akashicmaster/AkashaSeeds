"""
akasha-managed Let's Encrypt — TLS layer B (RFC 8555 ACME, http-01).

Obtains and renews a trusted certificate with **no operator scripting**: no
certbot, no nginx, no cron. `python akasha.py` calls `ensure_certificate()` on
boot; if the cert is missing or near expiry and one or more domains are
configured, it runs the ACME http-01 flow, writing `fullchain.pem` + `privkey.pem`
into `<data>/tls/` — exactly where TLS layer A (services/tls.py) serves from. The
http-01 challenge tokens are written into the same `<data>/tls/acme-challenge/`
directory the port-80 responder serves, so the two layers compose directly.

Configuration (env):
  AKASHA_TLS_DOMAINS  — comma-separated hostnames for the cert's SANs (required
                        to enable ACME). Falls back to AKASHA_BASE_DOMAIN.
  AKASHA_TLS_EMAIL    — ACME account contact (recommended; expiry notices).
  AKASHA_ACME_STAGING — "1" uses Let's Encrypt STAGING (untrusted certs, high
                        rate limits) — verify the flow on the VPS with this FIRST,
                        then unset for a real cert.
  AKASHA_ACME_DIRECTORY — override the ACME directory URL entirely.
  AKASHA_ACME_RENEW_DAYS — renew when fewer than N days remain (default 30).

Running the flow constitutes agreement to the ACME provider's Terms of Service
(termsOfServiceAgreed=true), the same as `certbot` with an email.

Dependency: `cryptography` (auto-installed via Symbiosis if absent). If it cannot
be loaded the function degrades to a no-op and the portal serves plain HTTP.

NOTE: the live ACME handshake talks to Let's Encrypt over the network and cannot
be exercised in a restricted CI sandbox — verify on the target VPS with
AKASHA_ACME_STAGING=1 first. All *local* crypto (account key, JWK thumbprint,
key-authorization, CSR SANs, cert-expiry decision) is unit-tested.
"""
import os
import json
import time
import base64
import hashlib
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("Harmonia.ACME")

LETSENCRYPT_PROD = "https://acme-v02.api.letsencrypt.org/directory"
LETSENCRYPT_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"

_UA = "akasha-acme/1.0"


# ── small helpers ─────────────────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    """base64url without padding (JOSE)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _domains_from_env() -> list:
    raw = os.environ.get("AKASHA_TLS_DOMAINS", "").strip()
    if not raw:
        raw = os.environ.get("AKASHA_BASE_DOMAIN", "").strip()
    seen, out = set(), []
    for d in raw.split(","):
        d = d.strip().lower()
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _directory_url() -> str:
    override = os.environ.get("AKASHA_ACME_DIRECTORY", "").strip()
    if override:
        return override
    if os.environ.get("AKASHA_ACME_STAGING", "").strip() in ("1", "true", "yes"):
        return LETSENCRYPT_STAGING
    return LETSENCRYPT_PROD


def _renew_days() -> int:
    v = os.environ.get("AKASHA_ACME_RENEW_DAYS", "").strip()
    return int(v) if v.isdigit() else 30


def cert_days_remaining(certfile: str):
    """Days until *certfile* expires, or None if unreadable/unparseable."""
    try:
        from cryptography import x509
        with open(certfile, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        try:
            not_after = cert.not_valid_after_utc          # cryptography >= 42
            now = _utcnow_aware()
        except AttributeError:
            not_after = cert.not_valid_after               # naive UTC (older)
            now = _utcnow_naive()
        return (not_after - now).days
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        # Includes a broken native cryptography binding (pyo3 panic == BaseException):
        # degrade to "can't tell" rather than crashing the boot sequence.
        return None


def _utcnow_aware():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _utcnow_naive():
    from datetime import datetime
    return datetime.utcnow()


def needs_issue(certfile: str, renew_days: int) -> bool:
    """True if there is no cert or it expires within *renew_days*."""
    if not os.path.isfile(certfile):
        return True
    days = cert_days_remaining(certfile)
    if days is None:
        return True
    return days < renew_days


# ── ACME account key (ES256) ──────────────────────────────────────────────────

class _Account:
    """An ACME account keypair (ECDSA P-256 / ES256) persisted as PEM."""

    def __init__(self, key):
        self._key = key

    @classmethod
    def load_or_create(cls, path: str):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        if os.path.isfile(path):
            with open(path, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            key = ec.generate_private_key(ec.SECP256R1())
            pem = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
            _write_private(path, pem)
        return cls(key)

    def jwk(self) -> dict:
        """Public JWK for an EC P-256 key (keys sorted for thumbprint use)."""
        nums = self._key.public_key().public_numbers()
        x = nums.x.to_bytes(32, "big")
        y = nums.y.to_bytes(32, "big")
        # RFC 7638 requires exactly these members, lexicographically ordered.
        return {"crv": "P-256", "kty": "EC", "x": _b64(x), "y": _b64(y)}

    def thumbprint(self) -> str:
        jwk = self.jwk()
        canon = json.dumps(jwk, separators=(",", ":"), sort_keys=True).encode()
        return _b64(hashlib.sha256(canon).digest())

    def key_authorization(self, token: str) -> str:
        return f"{token}.{self.thumbprint()}"

    def sign(self, message: bytes) -> bytes:
        """ES256 JWS signature: raw R||S (64 bytes), not DER."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        der = self._key.sign(message, ec.ECDSA(hashes.SHA256()))
        r, s = utils.decode_dss_signature(der)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def _write_private(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# ── CSR ────────────────────────────────────────────────────────────────────────

def _make_domain_key_and_csr(domains: list):
    """Return (private_key_pem_bytes, csr_der_bytes) for the SAN list."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    builder = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domains[0])])
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(d) for d in domains]),
        critical=False,
    )
    csr = builder.sign(key, hashes.SHA256())
    return key_pem, csr.public_bytes(serialization.Encoding.DER)


# ── ACME transport ─────────────────────────────────────────────────────────────

class _AcmeClient:
    def __init__(self, directory_url: str, account: _Account):
        self.directory_url = directory_url
        self.account = account
        self.dir = {}
        self.nonce = None
        self.kid = None

    def _raw(self, url, data=None, headers=None):
        req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
        req.add_header("User-Agent", _UA)
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            body = resp.read()
            self.nonce = resp.headers.get("Replay-Nonce", self.nonce)
            return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            body = e.read()
            self.nonce = e.headers.get("Replay-Nonce", self.nonce)
            return e.code, dict(e.headers), body

    def bootstrap(self):
        status, _, body = self._raw(self.directory_url)
        if status != 200:
            raise RuntimeError(f"ACME directory fetch failed: {status}")
        self.dir = json.loads(body)
        self._new_nonce()

    def _new_nonce(self):
        url = self.dir.get("newNonce")
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", _UA)
        resp = urllib.request.urlopen(req, timeout=30)
        self.nonce = resp.headers.get("Replay-Nonce")

    def _signed(self, url, payload, _retry=True):
        """POST a JWS. payload=None → POST-as-GET (empty payload).

        Retries once on a stale-nonce rejection (badNonce): the server hands back
        a fresh Replay-Nonce and expects the request re-signed with it — a normal
        part of the protocol, not an error."""
        protected = {"alg": "ES256", "nonce": self.nonce, "url": url}
        if self.kid:
            protected["kid"] = self.kid
        else:
            protected["jwk"] = self.account.jwk()
        protected_b64 = _b64(json.dumps(protected, separators=(",", ":")).encode())
        payload_b64 = "" if payload is None else _b64(
            json.dumps(payload, separators=(",", ":")).encode())
        signature = _b64(self.account.sign(f"{protected_b64}.{payload_b64}".encode()))
        body = json.dumps({
            "protected": protected_b64, "payload": payload_b64, "signature": signature,
        }).encode()
        status, headers, resp = self._raw(
            url, data=body, headers={"Content-Type": "application/jose+json"})
        if status == 400 and _retry and b"badNonce" in resp:
            # self.nonce was refreshed from the error's Replay-Nonce header in _raw.
            return self._signed(url, payload, _retry=False)
        return status, headers, resp

    def register_account(self, email: str):
        payload = {"termsOfServiceAgreed": True}
        if email:
            payload["contact"] = [f"mailto:{email}"]
        status, headers, body = self._signed(self.dir["newAccount"], payload)
        if status not in (200, 201):
            raise RuntimeError(f"newAccount failed: {status} {body[:200]!r}")
        self.kid = headers.get("Location")
        return self.kid

    def new_order(self, domains):
        payload = {"identifiers": [{"type": "dns", "value": d} for d in domains]}
        status, headers, body = self._signed(self.dir["newOrder"], payload)
        if status not in (200, 201):
            raise RuntimeError(f"newOrder failed: {status} {body[:200]!r}")
        order = json.loads(body)
        order["_url"] = headers.get("Location")
        return order

    def fetch(self, url):
        status, _, body = self._signed(url, None)
        return status, json.loads(body) if body else {}

    def solve_http01(self, authz_url, challenge_dir):
        _, authz = self.fetch(authz_url)
        domain = authz["identifier"]["value"]
        chal = next(c for c in authz["challenges"] if c["type"] == "http-01")
        token = chal["token"]
        keyauth = self.account.key_authorization(token)
        # Write the token file the port-80 responder serves.
        os.makedirs(challenge_dir, exist_ok=True)
        token_path = os.path.join(challenge_dir, token)
        with open(token_path, "w") as f:
            f.write(keyauth)
        # Tell ACME to validate.
        status, _, body = self._signed(chal["url"], {})
        if status >= 400:
            raise RuntimeError(f"challenge trigger failed for {domain}: {status} {body[:200]!r}")
        # Poll the authorization to completion.
        for _ in range(30):
            _, authz = self.fetch(authz_url)
            st = authz.get("status")
            if st == "valid":
                _safe_unlink(token_path)
                return True
            if st in ("invalid", "revoked", "deactivated", "expired"):
                _safe_unlink(token_path)
                raise RuntimeError(f"authorization {st} for {domain}: {authz}")
            time.sleep(2)
        _safe_unlink(token_path)
        raise RuntimeError(f"authorization timed out for {domain}")

    def finalize(self, order, csr_der):
        status, _, body = self._signed(order["finalize"], {"csr": _b64(csr_der)})
        if status >= 400:
            raise RuntimeError(f"finalize failed: {status} {body[:200]!r}")
        # Poll the order until the certificate URL appears.
        order_url = order["_url"]
        for _ in range(30):
            _, o = self.fetch(order_url)
            if o.get("status") == "valid" and o.get("certificate"):
                return o["certificate"]
            if o.get("status") == "invalid":
                raise RuntimeError(f"order invalid: {o}")
            time.sleep(2)
        raise RuntimeError("order finalization timed out")

    def download_cert(self, cert_url):
        status, _, body = self._signed(cert_url, None)
        if status != 200:
            raise RuntimeError(f"cert download failed: {status}")
        return body   # PEM chain


def _safe_unlink(path):
    try:
        os.remove(path)
    except OSError:
        pass


# ── public entry points ─────────────────────────────────────────────────────────

def _resolvable(domains):
    """Split *domains* into (resolvable, skipped) by DNS lookup.

    A domain with no A/AAAA record (NXDOMAIN) fails ACME http-01, and because a
    Let's Encrypt order validates every SAN, one missing record would fail the
    WHOLE certificate — blocking even the domains that ARE set up. So skip the
    unresolvable ones and issue for the rest; they join automatically on a later
    renewal once their DNS exists. (Best-effort: a resolver hiccup just means we
    try the domain anyway — Let's Encrypt is the source of truth.)"""
    import socket
    ok, skipped = [], []
    for d in domains:
        try:
            socket.getaddrinfo(d, 443)
            ok.append(d)
        except socket.gaierror:
            skipped.append(d)
        except Exception:
            ok.append(d)          # non-DNS error: don't wrongly drop the domain
    return ok, skipped


def obtain_certificate(data_dir, domains, email="", directory_url=None,
                       challenge_dir=None):
    """Run the full ACME http-01 flow and write fullchain.pem + privkey.pem into
    <data>/tls/. The caller MUST have a port-80 responder serving *challenge_dir*
    (services.tls.start_http_responder) reachable from the public internet for
    each domain. Returns the cert path on success; raises on failure."""
    from services.tls import tls_dir, challenge_dir as _cd
    directory_url = directory_url or _directory_url()
    challenge_dir = challenge_dir or _cd(data_dir)
    tdir = tls_dir(data_dir)
    os.makedirs(tdir, exist_ok=True)

    # Drop domains with no DNS record so one missing record can't fail the whole
    # certificate (the reported world.akashicarchives.net NXDOMAIN case).
    domains, skipped = _resolvable(domains)
    if skipped:
        logger.warning("[ACME] Skipping domains with no DNS record: %s — add an "
                       "A/AAAA record and they join on the next renewal.",
                       ", ".join(skipped))
    if not domains:
        raise RuntimeError("no configured domain resolves — check DNS / AKASHA_TLS_DOMAINS")

    account = _Account.load_or_create(os.path.join(tdir, "account.key"))
    client = _AcmeClient(directory_url, account)
    client.bootstrap()
    client.register_account(email)

    order = client.new_order(domains)
    for authz_url in order["authorizations"]:
        client.solve_http01(authz_url, challenge_dir)

    key_pem, csr_der = _make_domain_key_and_csr(domains)
    cert_url = client.finalize(order, csr_der)
    chain_pem = client.download_cert(cert_url)

    cert_path = os.path.join(tdir, "fullchain.pem")
    key_path = os.path.join(tdir, "privkey.pem")
    with open(cert_path, "wb") as f:
        f.write(chain_pem)
    _write_private(key_path, key_pem)
    logger.info("[ACME] Certificate obtained for %s → %s", ", ".join(domains), cert_path)
    return cert_path


def _cert_is_staging(certfile):
    """True if *certfile* was issued by a Let's Encrypt STAGING CA (untrusted by
    browsers), False if by a real CA, None if it can't be read. Staging issuers
    carry '(STAGING)' / 'Fake LE' in their name."""
    try:
        from cryptography import x509
        with open(certfile, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        issuer = cert.issuer.rfc4514_string().upper()
        return ("STAGING" in issuer) or ("FAKE" in issuer)
    except Exception:
        return None


def ensure_certificate(data_dir, start_responder=True):
    """Boot hook: obtain/renew the cert if ACME is configured and it is missing
    or near expiry. Safe to call unconditionally — a no-op when unconfigured or
    when a valid cert already exists. Returns one of:
      "unconfigured" | "current" | "issued" | "skipped" | "failed:<reason>".

    When *start_responder* is True and no portal is running yet, a temporary
    port-80 responder is stood up for the duration of issuance (boot-time case).
    """
    domains = _domains_from_env()
    if not domains:
        return "unconfigured"

    from services.tls import tls_dir, challenge_dir as _cd
    certfile = os.path.join(tls_dir(data_dir), "fullchain.pem")
    operator_supplied = bool(os.environ.get("AKASHA_TLS_CERT", "").strip())
    if operator_supplied:
        certfile = os.environ["AKASHA_TLS_CERT"].strip()

    if not needs_issue(certfile, _renew_days()):
        # The cert is current — but if akasha manages it (not operator-supplied)
        # and its CA no longer matches this run's environment (a staging cert
        # while now configured for PRODUCTION, or vice versa), re-issue. Otherwise
        # `unset AKASHA_ACME_STAGING` would keep serving the untrusted staging cert.
        if operator_supplied:
            return "current"
        _cs = _cert_is_staging(certfile)
        _staging_now = "staging" in _directory_url()
        if _cs is None or _cs == _staging_now:
            return "current"
        logger.warning("[ACME] Existing cert is a %s cert but this run is configured "
                       "for %s — re-issuing a %s certificate.",
                       "staging" if _cs else "production",
                       "staging" if _staging_now else "production",
                       "staging" if _staging_now else "production")
        # fall through → re-issue

    # cryptography is required for the ACME crypto; auto-install if possible.
    # A broken native binding raises a pyo3 panic (BaseException, not Exception),
    # so guard against that too and degrade to "skipped" rather than crash boot.
    try:
        import cryptography  # noqa: F401
    except ImportError:
        try:
            from api.env_detector import Symbiosis
            if not Symbiosis.ensure("cryptography", "cryptography",
                                    scope="[TLS]", feature="Let's Encrypt (ACME)"):
                return "skipped"
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            return "skipped"

    chal = _cd(data_dir)
    responder = None
    if start_responder:
        from services.tls import start_http_responder, resolve_tls
        hp = resolve_tls(data_dir)["https_port"]
        responder = start_http_responder(chal, hp, host="0.0.0.0", http_port=80)
    try:
        obtain_certificate(data_dir, domains,
                           email=os.environ.get("AKASHA_TLS_EMAIL", "").strip(),
                           challenge_dir=chal)
        return "issued"
    except Exception as exc:
        logger.warning("[ACME] Certificate provisioning failed: %s", exc)
        return f"failed:{exc}"
    finally:
        if responder is not None:
            try:
                responder.shutdown()
            except Exception:
                pass
