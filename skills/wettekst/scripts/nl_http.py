"""Small HTTP helper shared by the nl-juridische-skills clients (stdlib only).

- Honest User-Agent: ``nl-juridische-skills/<versie>``. No spoofed headers.
- Polite per-host throttle (minimum gap between requests to the same host).
- Retries with exponential backoff (+ jitter) on 429/502/503/504 and on
  transient network errors. ``Retry-After`` is honoured when present.
- Errors are raised as ``FetchError`` with a Dutch message; callers decide
  whether to exit.

Environment overrides:
    NLJS_MIN_GAP      minimum seconds between requests to one host (default 1.0)
    NLJS_MAX_RETRIES  attempts per request (default 4)
    NLJS_BACKOFF      first backoff in seconds (default 2.0)
    NLJS_TIMEOUT      socket timeout in seconds (default 45)
"""
from __future__ import annotations

import os
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

VERSION = "0.1"
USER_AGENT = f"nl-juridische-skills/{VERSION}"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


MIN_GAP_SEC = _env_float("NLJS_MIN_GAP", 1.0)
MAX_RETRIES = max(1, int(_env_float("NLJS_MAX_RETRIES", 4)))
INITIAL_BACKOFF_SEC = _env_float("NLJS_BACKOFF", 2.0)
TIMEOUT_SEC = _env_float("NLJS_TIMEOUT", 45.0)

RETRY_STATUSES = (429, 502, 503, 504)

_last_request: dict[str, float] = {}


class FetchError(Exception):
    """Network/HTTP failure with a Dutch, user-facing message.

    ``status`` is the HTTP status (or None for network errors).
    ``kind`` is one of: "niet_gevonden", "http", "netwerk", "overbelast".
    """

    def __init__(self, message: str, status: int | None = None, kind: str = "http", url: str = ""):
        super().__init__(message)
        self.status = status
        self.kind = kind
        self.url = url


@dataclass
class Response:
    status: int
    body: bytes
    url: str
    headers: dict = field(default_factory=dict)

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def _throttle(host: str) -> None:
    now = time.monotonic()
    last = _last_request.get(host)
    if last is not None:
        gap = now - last
        if gap < MIN_GAP_SEC:
            time.sleep(MIN_GAP_SEC - gap)
    _last_request[host] = time.monotonic()


def _retry_after(headers) -> float | None:
    try:
        value = headers.get("Retry-After") if headers else None
        return min(float(value), 120.0) if value else None
    except (TypeError, ValueError):
        return None


def get(url: str, accept: str = "*/*", headers: dict | None = None,
        allow_status: tuple[int, ...] = ()) -> Response:
    """GET ``url`` with throttle + retries.

    Returns a Response for 2xx and for any status listed in ``allow_status``.
    Raises FetchError otherwise.
    """
    host = urllib.parse.urlsplit(url).netloc
    req_headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if headers:
        req_headers.update(headers)
    backoff = INITIAL_BACKOFF_SEC
    last_problem = ""
    for attempt in range(1, MAX_RETRIES + 1):
        _throttle(host)
        req = urllib.request.Request(url, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
                return Response(resp.status, resp.read(), resp.geturl(), dict(resp.headers))
        except urllib.error.HTTPError as exc:
            body = b""
            try:
                body = exc.read()
            except Exception:  # noqa: BLE001 - body is best effort
                pass
            if exc.code in allow_status:
                return Response(exc.code, body, url, dict(exc.headers or {}))
            if exc.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                wait = _retry_after(exc.headers) or backoff * random.uniform(0.75, 1.25)
                last_problem = f"HTTP {exc.code}"
                time.sleep(wait)
                backoff *= 2
                continue
            if exc.code == 404:
                raise FetchError(f"Niet gevonden (HTTP 404): {url}", 404, "niet_gevonden", url) from None
            if exc.code in RETRY_STATUSES:
                raise FetchError(
                    f"De server van {host} is overbelast of tijdelijk onbereikbaar (HTTP {exc.code}), "
                    f"ook na {MAX_RETRIES} pogingen. Probeer het over een paar minuten opnieuw.",
                    exc.code, "overbelast", url) from None
            snippet = body.decode("utf-8", "replace").strip()[:300]
            raise FetchError(f"HTTP {exc.code} van {url}" + (f": {snippet}" if snippet else ""),
                             exc.code, "http", url) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
            reason = getattr(exc, "reason", exc)
            last_problem = str(reason)
            if attempt < MAX_RETRIES:
                time.sleep(backoff * random.uniform(0.75, 1.25))
                backoff *= 2
                continue
            raise FetchError(
                f"Kan {host} niet bereiken ({reason}). Controleer de internetverbinding en of "
                f"{host} is toegestaan in de netwerkinstellingen van je omgeving.",
                None, "netwerk", url) from None
    raise FetchError(f"Geen antwoord van {host} na {MAX_RETRIES} pogingen ({last_problem}).",
                     None, "netwerk", url)


def check_host(url: str, accept: str = "*/*", headers: dict | None = None) -> tuple[bool, str]:
    """Connectivity probe for doctor scripts: (ok, Dutch description)."""
    host = urllib.parse.urlsplit(url).hostname or url
    try:
        addr = socket.getaddrinfo(host, 443)[0][4][0]
    except OSError as exc:
        return False, f"DNS-fout voor {host}: {exc}"
    try:
        resp = get(url, accept=accept, headers=headers)
        return True, f"{host} ({addr}) antwoordt met HTTP {resp.status}"
    except FetchError as exc:
        return False, str(exc)
