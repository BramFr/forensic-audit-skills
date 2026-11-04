import contextlib
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import (
    parse_qs,
    parse_qsl,
    unquote,
    urlencode,
    urljoin,
    urlparse,
    urlsplit,
    urlunsplit,
)

with contextlib.redirect_stdout(sys.stderr):
    import primp
    import pymupdf
    import pymupdf4llm
    import trafilatura
    from curl_cffi import CurlOpt, requests as curl_requests
    from ddgs import DDGS
    from ddgs.exceptions import DDGSException
    from fastmcp import FastMCP
    from lxml import html as lxml_html
    from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

mcp = FastMCP("web-search")

_MAX_CACHE_ENTRIES = 128
_SESSION_SENT_BLOCKS: dict[str, set[str]] = {}
_SQLITE_CONNS: dict[str, sqlite3.Connection] = {}


def _get_sqlite_conn() -> sqlite3.Connection | None:
    db_path_str = os.environ.get(
        "WEB_SEARCH_CACHE_DB",
        str(Path(__file__).resolve().parent / ".cache" / "web_search_cache.sqlite3"),
    )
    conn = _SQLITE_CONNS.get(db_path_str)
    if conn is not None:
        return conn
    try:
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=5.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS http_cache ("
            "norm_url TEXT PRIMARY KEY, include_code INTEGER, markdown_body TEXT, "
            "etag TEXT, last_modified TEXT, fetched_at REAL, expires_at REAL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS search_cache ("
            "norm_query TEXT PRIMARY KEY, output TEXT, fetched_at REAL, expires_at REAL)"
        )
        conn.commit()
        _SQLITE_CONNS[db_path_str] = conn
        return conn
    except Exception:
        return None


class _CacheDict(dict):
    def __init__(self, table: str) -> None:
        super().__init__()
        self._table = table

    def clear(self) -> None:
        super().clear()
        if self._table == "http_cache":
            _SESSION_SENT_BLOCKS.clear()
        conn = _get_sqlite_conn()
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.execute(f"DELETE FROM {self._table}")
                conn.commit()


_SEARCH_CACHE: dict[str, str] = _CacheDict("search_cache")
_URL_CACHE: dict[tuple[str, str, bool], str] = _CacheDict("http_cache")

DEFAULT_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "application/pdf,*/*;q=0.8"
    ),
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
}

DEFAULT_COOKIES = {
    "SOCS": "CAISHAgBEhJnd3NfMjAyMzA4MTUtMF9SQzIaAm5sIAEaBgiAo_CmBg",
}

IMPERSONATE_PROFILES: tuple[str, ...] = (
    "chrome",
    "safari260",
    "safari184",
    "firefox144",
    "safari184_ios",
)

_SESSIONS: dict[str, Any] = {}

DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_JS_CALLBACK_RE = re.compile(
    r"decodeURIComponent\(\s*['\"](https?%3A%2F%2F[^'\"]+)['\"]\s*\)"
)
_META_REFRESH_RE = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+content=["\']?\d+\s*;\s*url=([^"\'>\s]+)',
    re.IGNORECASE,
)
_ANTIBOT_PATTERNS = re.compile(
    r"(something went wrong on our end|pardon our interruption|"
    r"error page\s*\|\s*ebay|sorry voor de onderbreking|"
    r"attention required!\s*\|\s*cloudflare|just a moment\.\.\.|"
    r"verify you are human|access denied|cc=botnet|anomaly-modal|"
    r"splashui/captcha|enable javascript and cookies to continue|"
    r"cookies must be enabled|enable cookies for|please enable cookies|"
    r"__identity_pow_cookie_check|/_pow/solve)",
    re.IGNORECASE,
)
_POW_CHALLENGE_ID_RE = re.compile(
    r"""(?:challengeId|challenge_id)\s*[:=]\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)
_POW_BITS_RE = re.compile(
    r"""\bbits\s*[:=]\s*(\d+)""",
    re.IGNORECASE,
)
_POW_SOLVE_PATH_RE = re.compile(
    r"""fetch\(\s*['"]([^'"]*?_pow/solve[^'"]*)['"]""",
    re.IGNORECASE,
)
_COOKIE_GATE_RE = re.compile(
    r"(cookies must be enabled|enable cookies for|please enable cookies|enable cookies)",
    re.IGNORECASE,
)
_UI_NOISE_RE = re.compile(
    r"(Nieuw venster of tabblad|Opent in nieuw venster of tabblad|"
    r"Bewaren in Mijn Favorieten|drosnopseG)",
    re.IGNORECASE,
)
_BOILERPLATE_LINE_RE = re.compile(
    r"^(?:Copy|Copied!|Ask AI|Report incorrect code|Edit this page|On this page|"
    r"Was this page helpful\?|Skip to main content)$",
    re.IGNORECASE,
)
_FINANCING_FOOTNOTE_RE = re.compile(
    r"^\s*(?:\*{1,4}|[⁰¹²³⁴⁵⁶⁷⁸⁹ᵂ]+)\s*.*"
    r"(?:Ratenfinanzierung|Sollzinssatz|Jahreszins|Finanzierungspartner|"
    r"Einkaufscoupon|Widerrufsrecht|Widerrufs-\s*bzw\.\s*Umtauschrecht|"
    r"Mindesteinkaufswert|vorbehaltlich Kreditwürdigkeitsprüfung|"
    r"Gesetzliche Rechte \(Widerrufsrecht|Apple Music)",
    re.IGNORECASE,
)
_DOM_PRICE_RE = re.compile(
    r"(?:(?:EUR|USD|GBP|€|\$)\s*\d[\d.,]*(?:\s*VB)?|\d[\d.,]*\s*(?:€|EUR\b)(?:\s*VB)?)",
    re.IGNORECASE,
)
_KLEINANZEIGEN_LD_NOISE_RE = re.compile(
    r'\{[^{}]*"creditText"\s*:\s*"Kleinanzeigen"[^{}]*\}'
)
_BOX_BORDER_CHARS = frozenset("┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬ ")
_ASCII_BOX_LINE_RE = re.compile(r"^\+[-=+]{3,}\+$")
_TRACKING_PARAMS_EXACT = frozenset(
    {
        "fbclid",
        "gclid",
        "msockid",
        "amdata",
        "hash",
        "itmmeta",
        "itmprp",
        "epid",
        "mkcid",
        "mkrid",
        "campid",
        "toolid",
        "mkevt",
        "spm",
    }
)
_TRACKING_PARAM_PREFIXES = ("utm_", "_trk")
_STOPWORDS = frozenset(
    {
        "de",
        "het",
        "een",
        "en",
        "van",
        "in",
        "op",
        "voor",
        "met",
        "te",
        "om",
        "naar",
        "bij",
        "of",
        "the",
        "and",
        "for",
        "with",
        "in",
        "on",
        "to",
        "of",
    }
)
_TIER1_AUTHORITY_DOMAINS = (
    "ietf.org",
    "rfc-editor.org",
    "iso.org",
    "nen.nl",
    "iec.ch",
    "w3.org",
    "whatwg.org",
    "owasp.org",
    "nist.gov",
    "arxiv.org",
    "aclanthology.org",
    "doi.org",
    "docs.python.org",
    "sqlite.org",
    "modelcontextprotocol.io",
    "antigravity.google",
    "ncbi.nlm.nih.gov",
    "ema.europa.eu",
    "eur-lex.europa.eu",
    "wetten.overheid.nl",
)
_TIER2_AUTHORITY_DOMAINS = (
    "readthedocs.io",
    "github.com",
    "gitlab.com",
    "microsoft.com",
    "google.com",
    "anthropic.com",
    "openai.com",
    "mozilla.org",
    "postgresql.org",
    "niso.org",
)
_IMMUTABLE_STD_DOMAINS = (
    "rfc-editor.org",
    "datatracker.ietf.org",
    "ietf.org",
    "arxiv.org",
    "doi.org",
    "w3.org",
    "iso.org",
    "niso.org",
)


class SearchWebsiteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query_or_url: str = Field(
        default="",
        validation_alias=AliasChoices("query_or_url", "query", "url", "q"),
        description=(
            "Search query (4-6 core terms, or 'open: <query>' to auto-open top primary URL), "
            "http(s) URL, 'https://... <keywords>', or ' || '-separated items. Follow the "
            "'## Search keywords' rule when ./docs/index.md exists."
        ),
    )
    queries_or_urls: list[str] | None = Field(
        default=None,
        description=(
            "Optional batch list of up to 10 search queries or http(s) URLs executed in one "
            "call with shared SQLite WAL cache and URL deduplication."
        ),
    )
    filter_query: str | None = Field(
        default=None,
        validation_alias=AliasChoices("filter_query", "filter", "keywords"),
        description=(
            "Keyword filter for http(s) URLs (or inline 'https://... <keywords>'). Pass by "
            "default on long pages, catalogs or PDFs (<10 KB) to filter items/sections by "
            "matching terms, with 'site:<domain>' fallback on 0 matches."
        ),
    )
    include_code: bool = Field(
        default=False,
        description=(
            "Keep multi-line code blocks (<pre>, ```) when fetching an http(s) URL "
            "(default False keeps inline <code> only)."
        ),
    )
    auto_open_top: int = Field(
        default=0,
        ge=0,
        le=3,
        validation_alias=AliasChoices("auto_open_top", "auto_open"),
        description=(
            "Number of top authoritative primary URLs (0-3) to auto-open and filter "
            "after a DuckDuckGo search (or prefix 'open: ')."
        ),
    )

    @model_validator(mode="after")
    def _must_not_be_empty(self) -> "SearchWebsiteInput":
        has_single = bool(self.query_or_url and self.query_or_url.strip())
        cleaned_batch = [
            item.strip()
            for item in (self.queries_or_urls or [])
            if isinstance(item, str) and item.strip()
        ]
        if not has_single and not cleaned_batch:
            raise ValueError("query_or_url must not be empty")
        self.queries_or_urls = cleaned_batch if cleaned_batch else None
        return self


def _is_antibot_or_error_page(
    status_code: int, html_text: str, final_url: str = ""
) -> bool:
    """Detect HTTP error status codes and HTTP 200 WAF/anti-bot interstitials."""
    if status_code >= 400:
        return True
    if not html_text or not html_text.strip():
        return True
    lowered_url = final_url.lower()
    if "splashui/challenge" in lowered_url or "splashui/captcha" in lowered_url:
        return True
    if len(html_text) < 40000 and _ANTIBOT_PATTERNS.search(html_text):
        return True
    return False


def _unwrap_consent_redirect(current_url: str, html_text: str) -> str | None:
    """Detect DPG Media / CMP JavaScript callbackUrl or meta-refresh redirect."""
    if not html_text:
        return None
    js_match = _JS_CALLBACK_RE.search(html_text)
    if js_match:
        return unquote(js_match.group(1))

    parsed = urlparse(current_url)
    if any(
        host in parsed.netloc.lower()
        for host in ("myprivacy.", "consent.", "privacygate")
    ):
        qs = parse_qs(parsed.query)
        for key in ("callbackUrl", "redirectUri", "continue"):
            if key in qs and qs[key]:
                target = unquote(qs[key][0])
                if target.startswith("http://") or target.startswith("https://"):
                    return target

    if len(html_text) < 16384:
        meta_match = _META_REFRESH_RE.search(html_text)
        if meta_match:
            return urljoin(current_url, meta_match.group(1).strip("'\""))
    return None


def _get_or_create_session(profile: str) -> Any:
    session = _SESSIONS.get(profile)
    if session is None:
        session = curl_requests.Session(impersonate=profile)
        session.cookies.update(DEFAULT_COOKIES)
        _SESSIONS[profile] = session
    return session


def _try_solve_cookie_or_pow_challenge(
    session: Any,
    url: str,
    html_text: str,
    req_headers: dict[str, str],
    timeout: float,
) -> Any | None:
    """Autonomously solve SHA-256 Proof-of-Work (/ _pow/solve) or cookie-priming challenges on the active session."""
    if not html_text:
        return None

    parsed = urlparse(url)
    origin_referer = (
        f"{parsed.scheme}://{parsed.netloc}/"
        if parsed.scheme and parsed.netloc
        else url
    )

    cid_match = _POW_CHALLENGE_ID_RE.search(html_text)
    if cid_match and (
        "/_pow/solve" in html_text or _POW_SOLVE_PATH_RE.search(html_text)
    ):
        challenge_id = cid_match.group(1)
        bits_match = _POW_BITS_RE.search(html_text)
        bits = min(max(int(bits_match.group(1)), 1), 22) if bits_match else 12
        path_match = _POW_SOLVE_PATH_RE.search(html_text)
        pow_path = path_match.group(1) if path_match else "/_pow/solve"
        solve_url = urljoin(url, pow_path)

        shift = 256 - bits
        solved_nonce: int | None = None
        for nonce in range(1 << (bits + 5)):
            digest = hashlib.sha256(
                f"{challenge_id}:{nonce}".encode()
            ).digest()
            if int.from_bytes(digest, "big") >> shift == 0:
                solved_nonce = nonce
                break

        if solved_nonce is not None:
            payload = json.dumps(
                {
                    "challenge_id": challenge_id,
                    "nonce": str(solved_nonce),
                    "redirect_url": url,
                }
            )
            post_headers = {
                **req_headers,
                "Content-Type": "application/json",
                "Referer": url,
            }
            try:
                pow_resp = session.post(
                    solve_url,
                    data=payload,
                    headers=post_headers,
                    allow_redirects=True,
                    timeout=timeout,
                )
                target_url = url
                if getattr(pow_resp, "status_code", 500) < 400:
                    try:
                        res_json = pow_resp.json()
                        if isinstance(res_json, dict) and res_json.get(
                            "redirect_url"
                        ):
                            target_url = urljoin(
                                url, str(res_json["redirect_url"])
                            )
                    except Exception:
                        pass
                    re_resp = session.get(
                        target_url,
                        headers={**req_headers, "Referer": url},
                        allow_redirects=True,
                        timeout=timeout,
                    )
                    re_url = str(getattr(re_resp, "url", target_url))
                    if not _is_antibot_or_error_page(
                        re_resp.status_code, re_resp.text, re_url
                    ):
                        return re_resp
            except Exception:
                pass

    if _COOKIE_GATE_RE.search(html_text):
        try:
            session.get(
                origin_referer,
                headers=DEFAULT_HEADERS,
                allow_redirects=True,
                timeout=timeout,
            )
        except Exception:
            pass
        if hasattr(session, "cookies"):
            try:
                session.cookies.update(
                    {"cookie_consent": "true", "cookies_enabled": "1"}
                )
            except Exception:
                pass
        try:
            re_resp = session.get(
                url,
                headers={**req_headers, "Referer": origin_referer},
                allow_redirects=True,
                timeout=timeout,
            )
            re_url = str(getattr(re_resp, "url", url))
            if not _is_antibot_or_error_page(
                re_resp.status_code, re_resp.text, re_url
            ):
                return re_resp
        except Exception:
            pass

    return None


def _http_get(
    url: str,
    timeout: float = 30.0,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    """Fetch URL with persistent cookie jar, consent-gate unwrapping, PoW/cookie-wall solving and TLS profile rotation."""
    parsed = urlparse(url)
    origin_referer = (
        f"{parsed.scheme}://{parsed.netloc}/"
        if parsed.scheme and parsed.netloc
        else url
    )
    last_resp: Any = None
    last_exc: Exception | None = None
    base_hdrs = {**DEFAULT_HEADERS, **(extra_headers or {})}

    for profile in IMPERSONATE_PROFILES:
        session = _get_or_create_session(profile)
        for attempt in range(3):
            req_headers = (
                {**base_hdrs, "Referer": origin_referer}
                if attempt > 0
                else base_hdrs
            )
            try:
                resp = session.get(
                    url,
                    headers=req_headers,
                    allow_redirects=True,
                    timeout=timeout,
                )
            except Exception as exc:
                exc_msg = str(exc)
                if "61" in exc_msg or "content encoding" in exc_msg.lower():
                    identity_headers = {
                        **req_headers,
                        "Accept-Encoding": "identity",
                    }
                    try:
                        resp = session.get(
                            url,
                            headers=identity_headers,
                            allow_redirects=True,
                            timeout=timeout,
                        )
                    except Exception:
                        try:
                            raw_session = curl_requests.Session(
                                impersonate=profile,
                                curl_options={CurlOpt.HTTP_CONTENT_DECODING: 0},
                            )
                            raw_session.cookies.update(DEFAULT_COOKIES)
                            resp = raw_session.get(
                                url,
                                headers=identity_headers,
                                allow_redirects=True,
                                timeout=timeout,
                            )
                        except Exception as retry_exc:
                            last_exc = retry_exc
                            break
                else:
                    last_exc = exc
                    break

            if resp.status_code == 304:
                return resp

            content_type = resp.headers.get("content-type", "")
            is_html = "html" in content_type.lower() or not content_type
            if is_html and resp.status_code < 400:
                final_url = str(getattr(resp, "url", url))
                callback_url = _unwrap_consent_redirect(final_url, resp.text)
                if callback_url and callback_url != final_url:
                    resp = session.get(
                        callback_url,
                        headers=base_hdrs,
                        allow_redirects=True,
                        timeout=timeout,
                    )

            last_resp = resp
            final_url = str(getattr(resp, "url", url))
            if not is_html and resp.status_code < 400:
                return resp
            if not _is_antibot_or_error_page(
                resp.status_code, resp.text, final_url
            ):
                return resp
            if is_html:
                solved = _try_solve_cookie_or_pow_challenge(
                    session, final_url, resp.text, req_headers, timeout
                )
                if solved is not None:
                    last_resp = solved
                    solved_url = str(getattr(solved, "url", final_url))
                    if not _is_antibot_or_error_page(
                        solved.status_code, solved.text, solved_url
                    ):
                        return solved

    if last_resp is not None:
        return last_resp
    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"Failed to fetch URL '{url}'")


def _http_post(
    url: str, data: dict[str, str], timeout: float = 20.0
) -> Any:
    headers = {**DEFAULT_HEADERS, "Referer": "https://html.duckduckgo.com/"}
    session = curl_requests.Session(impersonate="chrome")
    return session.post(
        url,
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=timeout,
    )


def _fetch_html_via_browser(url: str, timeout: float = 25.0) -> str | None:
    """Tier 3 fallback: render JS-only SPAs or strict WAF pages via local headless Chrome."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                probe_page = browser.new_page()
                native_ua = probe_page.evaluate("navigator.userAgent").replace(
                    "HeadlessChrome", "Chrome"
                )
                probe_page.close()

                context = browser.new_context(
                    locale="nl-NL",
                    user_agent=native_ua,
                )
                page = context.new_page()
                resp = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=int(timeout * 1000),
                )
                page.wait_for_timeout(1200)
                for selector in (
                    "button:has-text('Akkoord')",
                    "button:has-text('Accepteren')",
                    "button:has-text('Accept all')",
                    "button:has-text('Accept')",
                ):
                    try:
                        loc = page.locator(selector).first
                        if loc.is_visible(timeout=400):
                            loc.click(timeout=1000)
                            page.wait_for_timeout(800)
                            break
                    except Exception:
                        pass
                html_content = page.content()
                status_code = resp.status if resp is not None else 200
                if _is_antibot_or_error_page(
                    status_code, html_content, page.url
                ):
                    return None
                return html_content
            finally:
                browser.close()
    except Exception:
        return None


def _is_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _split_url_and_filter(
    query_or_url: str, filter_query: str | None = None
) -> tuple[str, str | None]:
    """Split inline 'https://... <filter terms>' and combine with explicit filter_query."""
    stripped = query_or_url.strip()
    explicit_filter = (filter_query or "").strip()
    if _is_url(stripped):
        parts = stripped.split(None, 1)
        url_part = parts[0]
        inline_filter = parts[1].strip() if len(parts) > 1 else ""
        combined = " ".join(
            f for f in (inline_filter, explicit_filter) if f
        ).strip()
        return url_part, (combined or None)
    return stripped, (explicit_filter or None)


def _is_pdf(url: str, content_type: str, content: bytes) -> bool:
    if "application/pdf" in content_type.lower():
        return True
    if content.startswith(b"%PDF-"):
        return True
    clean_url = url.split("?", 1)[0].split("#", 1)[0].lower()
    return clean_url.endswith(".pdf")


class _CurlPrimpClient:
    """Drop-in replacement for primp.Client using curl_cffi and OS native DNS."""

    def __init__(
        self, proxy: str | None = None, timeout: int | None = 10, **kwargs: Any
    ) -> None:
        self._timeout = float(timeout or 10)
        self._session = curl_requests.Session(
            impersonate="chrome",
            proxy=proxy,
            timeout=self._timeout,
        )

    def headers_update(self, headers: Mapping[str, str] | None) -> None:
        if headers:
            self._session.headers.update(dict(headers))

    def set_cookies(self, url: str, cookies: Mapping[str, str] | None) -> None:
        if cookies:
            self._session.cookies.update(dict(cookies))

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> Any:
        return self._session.request(method, url, *args, **kwargs)


def _is_ad_url(href: str) -> bool:
    lowered = href.strip().lower()
    return (
        not lowered.startswith(("http://", "https://"))
        or "bing.com/aclick" in lowered
        or "duckduckgo.com/y.js" in lowered
    )


def _is_ddg_anomaly(status_code: int, html_text: str) -> bool:
    if status_code != 200:
        return True
    return "anomaly-modal" in html_text or "cc=botnet" in html_text


def _clean_tracking_url(url: str) -> str:
    """Strip tracking and session query parameters from URLs while preserving functional parameters."""
    if not url or "?" not in url:
        return url
    try:
        parts = urlsplit(url)
        if not parts.query:
            return url
        kept = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in _TRACKING_PARAMS_EXACT
            and not k.lower().startswith(_TRACKING_PARAM_PREFIXES)
        ]
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(kept, doseq=True),
                parts.fragment,
            )
        )
    except Exception:
        return url


_UNRESERVED_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_PCT_ENCODED_RE = re.compile(r"%([0-9A-Fa-f]{2})")


def _normalize_pct_encoding(val: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        hex_str = m.group(1).upper()
        byte_val = int(hex_str, 16)
        if byte_val < 128 and chr(byte_val) in _UNRESERVED_CHARS:
            return chr(byte_val)
        return f"%{hex_str}"

    return _PCT_ENCODED_RE.sub(_repl, val)


def _normalize_cache_url(url: str) -> str:
    """Normalize HTTP(S) URI per RFC 3986 Section 6 (scheme/host case, unreserved %XX, default port, fragment, trailing slash)."""
    cleaned = _clean_tracking_url((url or "").strip())
    if not cleaned:
        return ""
    try:
        parts = urlsplit(cleaned)
        scheme = parts.scheme.lower()
        hostname = (parts.hostname or "").lower()
        port = parts.port
        if (scheme == "http" and port == 80) or (
            scheme == "https" and port == 443
        ):
            port = None
        if hostname:
            if ":" in hostname and not hostname.startswith("["):
                host_part = f"[{hostname}]"
            else:
                host_part = hostname
            netloc = f"{host_part}:{port}" if port else host_part
            if parts.username is not None:
                userinfo = parts.username
                if parts.password is not None:
                    userinfo += f":{parts.password}"
                netloc = f"{userinfo}@{netloc}"
        else:
            netloc = parts.netloc.lower()

        path = _normalize_pct_encoding(parts.path or "/")
        if not path:
            path = "/"
        elif path != "/" and path.endswith("/"):
            path = path.rstrip("/") or "/"

        query = _normalize_pct_encoding(parts.query)
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return cleaned


def _normalize_filter_key(filter_query: str | None) -> str:
    """Normalize filter_query into sorted unique lowercase tokens for order-independent cache keys."""
    tokens = [
        t
        for t in re.split(r"\W+", (filter_query or "").lower())
        if t
    ]
    return " ".join(sorted(set(tokens)))


def _escape_dsv_field(val: str, is_url: bool = False) -> str:
    """Escape a field for Positional Pipe-DSV (#schema:)."""
    cleaned = " ".join(str(val or "").splitlines()).strip()
    if is_url:
        return cleaned.replace("|", "%7C")
    return cleaned.replace("|", r"\|")


def _clean_ddgs_snippet(text: str, max_bytes: int = 380) -> str:
    """Deduplicate concatenated multi-card ddgs snippets and keep complete sentences within max_bytes."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return ""
    if max_bytes <= 200 and " | " in cleaned:
        segments = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+|\s+\|\s+", cleaned)
            if s.strip()
        ]
    else:
        segments = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", cleaned)
            if s.strip()
        ]
    deduped: list[str] = []
    seen_lower: set[str] = set()
    for seg in segments:
        key = seg.casefold()
        if key not in seen_lower:
            seen_lower.add(key)
            deduped.append(seg)
    if not deduped:
        return cleaned
    kept: list[str] = []
    sep = " | " if (max_bytes <= 200 and " | " in cleaned) else " "
    for idx, seg in enumerate(deduped):
        candidate = f"{sep.join(kept)}{sep}{seg}" if kept else seg
        if len(candidate.encode("utf-8")) <= max_bytes or idx == 0:
            kept.append(seg)
            if len(candidate.encode("utf-8")) >= max_bytes:
                break
        else:
            break
    return sep.join(kept)


def _rank_primary_authority_urls(results: list[Any]) -> list[str]:
    """Rank candidate URLs by primary authority tier (Tier 1 standards/gov/edu, Tier 2 official docs/code, Tier 3 other)."""
    scored: list[tuple[int, int, str]] = []
    seen_norm: set[str] = set()
    for idx, item in enumerate(results):
        raw_url = (
            (item.get("href") or item.get("url") or "")
            if isinstance(item, dict)
            else str(item or "")
        ).strip()
        if not _is_url(raw_url) or _is_ad_url(raw_url):
            continue
        norm = _normalize_cache_url(raw_url)
        if not norm or norm in seen_norm:
            continue
        seen_norm.add(norm)
        host = (urlparse(raw_url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        tier = 3
        if (
            host.endswith((".gov", ".mil", ".edu"))
            or any(
                host == d or host.endswith("." + d)
                for d in _TIER1_AUTHORITY_DOMAINS
            )
        ):
            tier = 1
        elif (
            host.startswith("docs.")
            or ".docs." in host
            or any(
                host == d or host.endswith("." + d)
                for d in _TIER2_AUTHORITY_DOMAINS
            )
        ):
            tier = 2
        scored.append((tier, idx, raw_url))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in scored]


def _clean_ddg_href(raw_href: str) -> str:
    href = raw_href.strip()
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return _clean_tracking_url(unquote(qs["uddg"][0]))
    return _clean_tracking_url(href)


def _parse_ddg_html(
    html_text: str, max_results: int = 10
) -> list[dict[str, Any]]:
    tree = lxml_html.fromstring(html_text)
    results: list[dict[str, Any]] = []
    for div in tree.xpath('//div[contains(@class, "result__body")]'):
        title_el = div.xpath('.//a[contains(@class, "result__a")]')
        if not title_el:
            continue
        snippet_el = div.xpath('.//*[contains(@class, "result__snippet")]')
        raw_href = title_el[0].get("href", "")
        cleaned_href = _clean_ddg_href(raw_href)
        if _is_ad_url(cleaned_href):
            continue
        results.append(
            {
                "title": _clean_ddgs_snippet(
                    " ".join(title_el[0].text_content().split()), max_bytes=160
                ),
                "href": cleaned_href,
                "body": _clean_ddgs_snippet(
                    " ".join(snippet_el[0].text_content().split())
                    if snippet_el
                    else "",
                    max_bytes=380,
                ),
            }
        )
        if len(results) >= max_results:
            break
    return results


def _search_ddgs_fallback(
    query: str, max_results: int = 10
) -> list[dict[str, Any]]:
    """Tier 2 metasearch fallback via ddgs routed through curl_cffi OS DNS."""
    primp.Client = _CurlPrimpClient
    try:
        with contextlib.redirect_stdout(sys.stderr):
            raw_results = DDGS().text(
                query, max_results=max_results * 2, backend="auto"
            )
    except DDGSException as exc:
        if str(exc).strip() == "No results found.":
            return []
        raise

    cleaned: list[dict[str, Any]] = []
    for item in raw_results or []:
        href = _clean_tracking_url((item.get("href") or "").strip())
        if _is_ad_url(href):
            continue
        cleaned.append(
            {
                "title": _clean_ddgs_snippet(
                    (item.get("title") or "Untitled").strip(), max_bytes=160
                ),
                "href": href,
                "body": _clean_ddgs_snippet(
                    (item.get("body") or "").strip(), max_bytes=380
                ),
            }
        )
        if len(cleaned) >= max_results:
            break
    return cleaned


def _extract_json_ld_items(
    tree: Any, base_url: str, max_items: int = 20
) -> list[str]:
    """Layer A: Extract Schema.org Product, Offer and ItemList entries from JSON-LD scripts."""
    items_dsv: list[str] = []
    seen_titles: set[str] = set()

    def _format_product(obj: dict[str, Any]) -> str | None:
        name = " ".join(str(obj.get("name") or "").split())
        if not name:
            return None
        raw_url = obj.get("url") or ""
        offers = obj.get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if not raw_url and isinstance(offers, dict):
            raw_url = offers.get("url") or ""
        item_url = (
            _clean_tracking_url(urljoin(base_url, str(raw_url)))
            if raw_url
            else ""
        )

        price_str = ""
        if isinstance(offers, dict):
            price = offers.get("price")
            if price is None:
                price = offers.get("lowPrice")
            currency = offers.get("priceCurrency") or "EUR"
            avail = str(offers.get("availability") or "").rsplit("/", 1)[-1]
            if price is not None:
                if (
                    not item_url
                    and str(price) in ("1", "1.0", "1.00")
                    and not obj.get("description")
                ):
                    return None
                price_str = f"{currency} {price}"
                if avail:
                    price_str += f" ({avail})"

        rating_str = ""
        agg = obj.get("aggregateRating")
        if isinstance(agg, dict):
            rv = agg.get("ratingValue")
            rc = agg.get("reviewCount") or agg.get("ratingCount")
            if rv:
                rating_str = f"Rating: {rv}" + (
                    f" ({rc} reviews)" if rc else ""
                )

        desc = " ".join(str(obj.get("description") or "").split())
        if len(desc) > 180:
            desc = desc[:177] + "..."

        norm_key = name.lower()
        if norm_key in seen_titles:
            return None
        seen_titles.add(norm_key)

        details_parts: list[str] = []
        if rating_str:
            details_parts.append(rating_str)
        if desc and desc.lower() != name.lower():
            details_parts.append(desc)
        details = " — ".join(details_parts)
        return (
            f"{_escape_dsv_field(name)}|"
            f"{_escape_dsv_field(price_str)}|"
            f"{_escape_dsv_field(item_url, is_url=True)}|"
            f"{_escape_dsv_field(details)}"
        )

    def _walk_ld(node: Any) -> None:
        if len(items_dsv) >= max_items:
            return
        if isinstance(node, list):
            for el in node:
                _walk_ld(el)
        elif isinstance(node, dict):
            t_raw = node.get("@type")
            types = (
                [str(x) for x in t_raw]
                if isinstance(t_raw, list)
                else [str(t_raw or "")]
            )
            if any(
                t in ("Product", "Offer", "IndividualProduct") for t in types
            ):
                formatted = _format_product(node)
                if formatted:
                    items_dsv.append(formatted)
            elif "ListItem" in types and isinstance(node.get("item"), dict):
                _walk_ld(node["item"])
            else:
                for k in (
                    "itemListElement",
                    "@graph",
                    "mainEntity",
                    "hasVariant",
                ):
                    if k in node:
                        _walk_ld(node[k])

    for raw in tree.xpath("//script[@type='application/ld+json']/text()"):
        try:
            data = json.loads(raw.strip())
            _walk_ld(data)
        except Exception:
            continue
    return items_dsv


def _extract_hydration_items(
    tree: Any, base_url: str, max_items: int = 20
) -> list[str]:
    """Layer B: Extract listing/product items from Next.js __NEXT_DATA__ or SSR state JSON."""
    items_dsv: list[str] = []
    seen_titles: set[str] = set()

    def _format_candidate(d: dict[str, Any]) -> str | None:
        title = d.get("title") or d.get("name") or d.get("headline")
        if not isinstance(title, str) or len(title.strip()) < 3:
            return None
        title = " ".join(title.split())

        price_val = ""
        pi = d.get("priceInfo") or d.get("price") or d.get("offers")
        if isinstance(pi, dict):
            cents = pi.get("priceCents")
            ptype = pi.get("priceType")
            if cents is not None:
                price_val = f"EUR {cents / 100:.2f}"
            elif pi.get("price") is not None:
                price_val = f"{pi.get('currency', 'EUR')} {pi.get('price')}"
            elif ptype:
                price_val = str(ptype)
        elif isinstance(pi, (int, float, str)) and str(pi).strip():
            price_val = str(pi).strip()

        title_lower = title.lower()
        if price_val in ("", "0", "0.00", "EUR 0.00", "EUR 0") and any(
            kw in title_lower
            for kw in ("gezocht", "wij kopen", "hoogste inkoop")
        ):
            return None

        raw_url = (
            d.get("vipUrl")
            or d.get("url")
            or d.get("href")
            or d.get("seoUrl")
            or ""
        )
        item_url = (
            _clean_tracking_url(urljoin(base_url, raw_url))
            if isinstance(raw_url, str) and raw_url
            else ""
        )

        desc_raw = (
            d.get("description")
            or d.get("categorySpecificDescription")
            or d.get("summary")
            or ""
        )
        desc = " ".join(str(desc_raw).split()) if isinstance(desc_raw, str) else ""
        if len(desc) > 180:
            desc = desc[:177] + "..."

        city = ""
        if isinstance(d.get("location"), dict):
            city = str(
                d["location"].get("cityName")
                or d["location"].get("countryName")
                or ""
            ).strip()

        if not (price_val or item_url):
            return None
        if not price_val and not d.get("itemId") and not d.get("vipUrl"):
            return None

        norm_key = f"{title.lower()}|{item_url}"
        if norm_key in seen_titles:
            return None
        seen_titles.add(norm_key)

        details_parts = [p for p in (city, desc) if p]
        details = " — ".join(details_parts)
        return (
            f"{_escape_dsv_field(title)}|"
            f"{_escape_dsv_field(price_val)}|"
            f"{_escape_dsv_field(item_url, is_url=True)}|"
            f"{_escape_dsv_field(details)}"
        )

    def _walk_json(node: Any) -> None:
        if len(items_dsv) >= max_items:
            return
        if isinstance(node, list):
            for el in node:
                _walk_json(el)
        elif isinstance(node, dict):
            line = _format_candidate(node)
            if line:
                items_dsv.append(line)
            for v in node.values():
                if isinstance(v, (dict, list)):
                    _walk_json(v)

    for raw in tree.xpath(
        "//script[@id='__NEXT_DATA__' or contains(@id, 'STATE')]/text()"
    ):
        try:
            data = json.loads(raw.strip())
            _walk_json(data)
        except Exception:
            continue
    return items_dsv


def _extract_dom_cards(
    tree: Any, base_url: str, max_items: int = 20
) -> list[str]:
    """Layer C: Extract repeating product/result cards from generic semantic DOM structures."""
    items_dsv: list[str] = []
    seen_titles: set[str] = set()
    xpath_cards = (
        "//li[contains(@class, 's-card') or contains(@class, 's-item') "
        "or contains(@class, 'Listing') or contains(@class, 'product') "
        "or contains(@class, 'result')]"
        " | //div[contains(@class, 's-card') or contains(@class, 'product-card') "
        "or contains(@class, 'search-result')]"
    )
    cards = tree.xpath(xpath_cards)
    if not cards:
        article_nodes = tree.xpath("//article")
        if len(article_nodes) >= 2:
            cards = article_nodes
    for card in cards:
        if len(items_dsv) >= max_items:
            break
        for bad_el in card.xpath(
            ".//script | .//style | .//svg | .//noscript"
        ):
            parent = bad_el.getparent()
            if parent is not None:
                parent.remove(bad_el)

        title_nodes = card.xpath(
            ".//*[contains(@class, 's-card__title') or contains(@class, 's-item__title') "
            "or contains(@class, 'title') or self::h2 or self::h3 or self::h4]"
        )
        title = ""
        for tn in title_nodes:
            t_cand = _UI_NOISE_RE.sub(
                "", " ".join(tn.text_content().split())
            ).strip()
            if len(t_cand) >= 5 and t_cand.lower() not in (
                "shop on ebay",
                "vergelijken",
                "brand new",
                "nieuw (anders) | zakelijk",
                "tweedehands | zakelijk",
            ):
                title = t_cand
                break
        if not title:
            continue

        href = ""
        for a in card.xpath(".//a[@href]"):
            h = (a.get("href") or "").strip()
            if h and not h.lower().startswith(
                ("#", "javascript:", "mailto:", "tel:")
            ):
                href = _clean_tracking_url(urljoin(base_url, h))
                break
        if "itm/123456" in href:
            continue

        price_str = ""
        for pnode in card.xpath(
            ".//*[contains(@class, 'price') or contains(@id, 'price')]"
        ):
            p_text = " ".join(pnode.text_content().split())
            pm = _DOM_PRICE_RE.search(p_text)
            if pm:
                price_str = pm.group(0).strip()
                break

        raw_card_text = _KLEINANZEIGEN_LD_NOISE_RE.sub(
            " ", card.text_content()
        )
        full_text = _UI_NOISE_RE.sub(
            " ", " ".join(raw_card_text.split())
        ).strip()
        details = full_text.replace(title, "", 1).strip(" -|·,")
        if not details and not href:
            continue
        if not price_str:
            price_match = _DOM_PRICE_RE.search(details)
            price_str = price_match.group(0).strip() if price_match else ""

        if len(details) > 220:
            details = details[:217] + "..."

        norm_title = title.lower()
        if price_str in ("", "0", "0 €", "EUR 0.00", "EUR 0") and (
            norm_title.startswith(("gezocht", "suche "))
            or "wij kopen" in norm_title
            or "hoogste inkoop" in norm_title
        ):
            continue
        if norm_title in seen_titles:
            continue
        seen_titles.add(norm_title)

        items_dsv.append(
            f"{_escape_dsv_field(title)}|"
            f"{_escape_dsv_field(price_str)}|"
            f"{_escape_dsv_field(href, is_url=True)}|"
            f"{_escape_dsv_field(details)}"
        )
    return items_dsv


def _format_structured_items(
    items: list[Any], heading: str = "## Extracted Items"
) -> str:
    """Format extracted catalog/product items in Positional Pipe-DSV (#schema:title|price|url|details)."""
    if not items:
        return ""
    rows = [f"{heading} ({len(items)})", "#schema:title|price|url|details"]
    for item in items:
        if isinstance(item, dict):
            t = _escape_dsv_field(item.get("title", ""))
            p = _escape_dsv_field(item.get("price", ""))
            u = _escape_dsv_field(
                _clean_tracking_url(str(item.get("url", ""))), is_url=True
            )
            d = _escape_dsv_field(item.get("details", ""))
            rows.append(f"{t}|{p}|{u}|{d}")
        else:
            rows.append(str(item))
    return "\n".join(rows)


def _extract_portal_headlines(html_text: str, base_url: str) -> str:
    """Extract structured headlines and links from portal/overview pages."""
    try:
        tree = lxml_html.fromstring(html_text)
    except Exception:
        return ""

    seen: set[str] = set()
    items: list[str] = []
    xpath_query = (
        '//a[contains(@class, "headline") '
        "or ancestor::h1 or ancestor::h2 or ancestor::h3 "
        "or ancestor::article//a]"
    )
    for node in tree.xpath(xpath_query):
        text = " ".join(node.text_content().split())
        href = (node.get("href") or "").strip()
        if (
            len(text) < 12
            or not href
            or href.startswith("#")
            or href.startswith("javascript:")
        ):
            continue
        full_url = _clean_tracking_url(urljoin(base_url, href))
        key = f"{text}|{full_url}"
        if key in seen:
            continue
        seen.add(key)
        items.append(f"- [{text}]({full_url})")
    return "\n".join(items)


def _is_box_drawing_line(stripped: str) -> bool:
    """Detect pure Unicode/ASCII box-drawing lines without touching Markdown tables."""
    if not stripped:
        return False
    if _ASCII_BOX_LINE_RE.match(stripped):
        return True
    if any(ch in _BOX_BORDER_CHARS - {" "} for ch in stripped):
        if all(ch in _BOX_BORDER_CHARS for ch in stripped):
            return True
        if stripped.startswith(
            ("┌", "└", "├", "│", "╔", "╚", "║")
        ) and stripped.endswith(("┐", "┘", "┤", "│", "╗", "╝", "║")):
            return True
    return False


def _clean_plain_text_body(text: str, include_code: bool = False) -> str:
    """Clean extracted HTML/PDF body text: strip permalinks, inline link URLs, formatting, UI buttons & code fences."""
    if not text:
        return ""
    working = text
    if not include_code:
        working = re.sub(r"`([^`\n]+)`", r"\1", working)

    out_lines: list[str] = []
    in_fenced_code = False
    last_non_empty_stripped = ""
    for raw_line in working.splitlines():
        if "itm/123456" in raw_line:
            continue
        stripped_raw = raw_line.strip()
        if stripped_raw.startswith(("```", "~~~")):
            if include_code:
                in_fenced_code = not in_fenced_code
                out_lines.append(raw_line.rstrip())
            continue
        if in_fenced_code:
            out_lines.append(raw_line.rstrip())
            continue
        if _FINANCING_FOOTNOTE_RE.match(stripped_raw):
            continue

        line = _UI_NOISE_RE.sub("", raw_line)
        line = re.sub(
            r"\[(?:#|¶|permalink)\]\([^)]*\)", "", line, flags=re.IGNORECASE
        )
        if line.lstrip().startswith("#"):
            line = re.sub(r"\s*[#¶]+\s*$", "", line)
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)

        s = line.strip()
        if _BOILERPLATE_LINE_RE.match(s):
            continue
        if _FINANCING_FOOTNOTE_RE.match(s):
            continue
        if _is_box_drawing_line(s):
            continue
        if re.search(r"(?:\.\s*){4,}\d+\s*$", s):
            continue
        if re.search(r"Standards Track\s+\[Page \d+\]", s, re.I):
            continue
        if s:
            if s == last_non_empty_stripped:
                continue
            last_non_empty_stripped = s
        out_lines.append(line.rstrip())

    cleaned = "\n".join(out_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_main_markdown(
    html_text: str, url: str, include_code: bool = False
) -> str:
    """Extract main readable text via trafilatura keeping visible <pre> blocks while stripping hidden website scripts/styles."""
    prune_xpath = ["//script", "//style", "//svg", "//noscript", "//iframe"]
    extracted = trafilatura.extract(
        html_text,
        url=url,
        output_format="markdown",
        include_tables=True,
        include_links=False,
        include_formatting=False,
        favor_recall=True,
        prune_xpath=prune_xpath,
    )
    body = (extracted or "").strip()
    if body or "<pre" in html_text.lower():
        try:
            tree = lxml_html.fromstring(html_text)
            for bad in tree.xpath("//script | //style | //svg | //noscript | //iframe"):
                parent = bad.getparent()
                if parent is not None:
                    parent.remove(bad)
            heading_map: dict[str, str] = {}
            for level, tag in (("#", "h1"), ("##", "h2"), ("###", "h3")):
                for h_node in tree.xpath(f"//{tag}"):
                    h_txt = " ".join(h_node.text_content().split())
                    h_txt = re.sub(r"\s*[#¶]+\s*$", "", h_txt).strip()
                    if h_txt and h_txt not in heading_map:
                        heading_map[h_txt] = f"{level} {h_txt}"
            if heading_map and body:
                restored_lines: list[str] = []
                for line in body.splitlines():
                    s_line = re.sub(
                        r"\s*[#¶]+\s*$", "", line.strip()
                    ).strip()
                    if s_line in heading_map:
                        restored_lines.append("")
                        restored_lines.append(heading_map[s_line])
                        restored_lines.append("")
                    else:
                        restored_lines.append(line)
                body = "\n".join(restored_lines)

            for pre in tree.xpath("//article//pre | //main//pre | //body//pre | //pre"):
                pre_txt = pre.text_content().strip()
                if not pre_txt:
                    continue
                first_line = next(
                    (l.strip() for l in pre_txt.splitlines() if l.strip()), ""
                )
                if pre_txt in body:
                    if include_code and f"```\n{pre_txt}\n```" not in body:
                        body = body.replace(
                            pre_txt, f"```\n{pre_txt}\n```", 1
                        )
                elif not first_line or first_line not in body:
                    if include_code:
                        body = f"{body}\n\n```\n{pre_txt}\n```".strip()
                    else:
                        body = f"{body}\n\n{pre_txt}".strip()
        except Exception:
            pass
    return _clean_plain_text_body(body, include_code=include_code)


def _html_to_markdown(
    html_text: str,
    url: str,
    filter_query: str | None = None,
    include_code: bool = False,
) -> str | None:
    cleaned_body = _extract_main_markdown(
        html_text, url, include_code=include_code
    )

    structured_items: list[str] = []
    from_fallback_dom = False
    try:
        tree = lxml_html.fromstring(html_text)
        ld_items = _extract_json_ld_items(tree, url)
        hyd_items = _extract_hydration_items(tree, url)
        dom_items = _extract_dom_cards(tree, url)
        if len(ld_items) >= 2 and len(ld_items) >= len(hyd_items):
            structured_items = ld_items
        elif hyd_items:
            structured_items = hyd_items
        elif ld_items:
            structured_items = ld_items
        else:
            structured_items = dom_items
            from_fallback_dom = True
    except Exception:
        structured_items = []

    priced_count = sum(
        1
        for item in structured_items
        if len(item.split("|")) >= 2 and bool(item.split("|")[1].strip())
    )
    if (
        from_fallback_dom
        and priced_count == 0
        and len(cleaned_body) >= 400
    ):
        structured_items = []

    sections: list[str] = []
    if structured_items:
        sections.append(_format_structured_items(structured_items))

    if (
        len(html_text) > 30000
        and len(cleaned_body) < 4000
        and not structured_items
    ):
        headlines = _extract_portal_headlines(html_text, url)
        if headlines:
            sections.append(headlines)

    skip_duplicate_body = False
    if len(structured_items) >= 5 and priced_count >= 2:
        if not filter_query:
            skip_duplicate_body = True
        else:
            raw_terms = [
                t.lower()
                for t in re.split(r"\W+", filter_query)
                if len(t) >= 2 and t.lower() not in _STOPWORDS
            ] or [filter_query.strip().lower()]
            if any(
                any(term in item.lower() for term in raw_terms)
                for item in structured_items
            ):
                skip_duplicate_body = True

    if cleaned_body and not skip_duplicate_body:
        sections.append(cleaned_body)

    combined = "\n\n".join(s for s in sections if s).strip()
    if not combined:
        return None
    if len(combined) < 600 and _ANTIBOT_PATTERNS.search(combined):
        return None
    return combined


def _apply_content_filter(
    markdown_body: str,
    url: str,
    filter_query: str,
    max_blocks: int = 40,
    max_headings: int = 25,
    max_bytes: int | None = None,
) -> str:
    """Filter extracted Markdown items/blocks by filter_query; enforce max_bytes on complete blocks and apply session delta."""
    raw_terms = [
        t.lower()
        for t in re.split(r"\W+", filter_query)
        if len(t) >= 2 and t.lower() not in _STOPWORDS
    ]
    if not raw_terms:
        raw_terms = [filter_query.strip().lower()]

    headings: list[str] = []
    for line in markdown_body.splitlines():
        s = line.strip()
        if s.startswith("#") and not s.startswith("#schema:"):
            if max_headings < 25 and not s.startswith(("# ", "## ", "### ")):
                continue
            clean_h = re.sub(
                r"\[(?:#|¶|permalink)\]\([^)]*\)", "", s, flags=re.IGNORECASE
            ).strip()
            clean_h = re.sub(r"\s*[#¶]+\s*$", "", clean_h).strip()
            if clean_h and clean_h not in headings and len(headings) < max_headings:
                headings.append(clean_h)

    blocks: list[str] = []
    for chunk in re.split(r"\n\s*\n", markdown_body):
        c = chunk.strip()
        if not c:
            continue
        if "#schema:" in c or c.startswith("## Extracted Items"):
            for row in c.splitlines():
                rs = row.strip()
                if rs and not rs.startswith("#"):
                    blocks.append(rs)
        elif "\n" in c and not c.startswith(("```", "|")):
            for row in c.splitlines():
                rs = row.strip()
                if rs and not rs.startswith("#"):
                    blocks.append(rs)
        elif not c.startswith("#"):
            blocks.append(c)

    scored: list[tuple[int, int, str]] = []
    for idx, block in enumerate(blocks):
        if block.startswith("#") and "\n" not in block:
            continue
        lowered = block.lower()
        hits = sum(1 for term in raw_terms if term in lowered)
        if hits > 0:
            scored.append((hits, -idx, block))

    norm_url = _normalize_cache_url(url)
    prior_sent = _SESSION_SENT_BLOCKS.get(norm_url)
    toc = (
        "## Page Headings Index\n" + "\n".join(headings) + "\n\n"
        if headings and prior_sent is None
        else ""
    )

    if scored:
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        candidates = [item[2] for item in scored[:max_blocks]]
        delta_notice = ""
        if prior_sent is not None:
            new_cands = [
                b
                for b in candidates
                if hashlib.sha1(b.encode("utf-8")).hexdigest()[:16] not in prior_sent
            ]
            if new_cands:
                omitted_n = len(candidates) - len(new_cands)
                candidates = new_cands
                delta_notice = f"\n\n<!-- +{omitted_n} already-shown blocks & ToC omitted for this URL in current session -->"
            else:
                delta_notice = "\n\n<!-- +0 already-shown blocks & ToC omitted for this URL in current session -->"

        if max_bytes is not None and max_bytes > 0 and candidates:
            if toc and len(toc.encode("utf-8")) > max_bytes // 4:
                max_h = 3 if max_bytes <= 1200 else 8
                short_h = headings[: min(len(headings), max_h)]
                toc = "## Page Headings Index\n" + "\n".join(short_h) + "\n\n"
            selected: list[str] = [candidates[0]]
            overhead = len(toc.encode("utf-8")) + len(delta_notice.encode("utf-8")) + 120
            for blk in candidates[1:]:
                trial = "\n\n".join(selected + [blk])
                if overhead + len(trial.encode("utf-8")) <= max_bytes:
                    selected.append(blk)
                else:
                    break
        else:
            selected = candidates

        sent_set = _SESSION_SENT_BLOCKS.setdefault(norm_url, set())
        for blk in selected:
            sent_set.add(hashlib.sha1(blk.encode("utf-8")).hexdigest()[:16])

        filter_block = (
            f"## Filtered Matches ({len(selected)} of {len(blocks)} blocks matching `{filter_query}`)\n\n"
            + "\n\n".join(selected)
            + delta_notice
        )
        return f"{toc}{filter_block}"

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    site_fallback = (
        _search_duckduckgo(f"site:{domain} {filter_query}")
        if domain
        else ""
    )
    fallback_block = (
        f"## Filtered Matches for `{filter_query}` (0 direct matches on page; `site:{domain}` fallback below)\n\n"
        f"{site_fallback}"
    )
    summary_excerpt = markdown_body[:2500].strip()
    if summary_excerpt:
        return f"{toc}{fallback_block}\n\n---\n\n{summary_excerpt}"
    return f"{toc}{fallback_block}"


def _fetch_url_as_markdown_uncached(
    url: str,
    filter_query: str | None = None,
    include_code: bool = False,
    max_blocks: int = 40,
    max_headings: int = 25,
    max_bytes: int | None = None,
) -> str:
    norm_url = _normalize_cache_url(url)
    code_int = int(bool(include_code))
    now = time.time()
    host = (urlparse(url).hostname or "").lower()
    url_ttl = (
        7 * 86400.0
        if any(host == d or host.endswith("." + d) for d in _IMMUTABLE_STD_DOMAINS) or "/TR/" in url
        else 24 * 3600.0
    )
    conn = _get_sqlite_conn()
    cached_row: tuple[Any, ...] | None = None
    if conn is not None and norm_url:
        with contextlib.suppress(Exception):
            cur = conn.execute(
                "SELECT markdown_body, etag, last_modified, fetched_at, expires_at "
                "FROM http_cache WHERE norm_url = ? AND include_code = ?",
                (norm_url, code_int),
            )
            cached_row = cur.fetchone()

    def _finalize_body(raw_body: str) -> str:
        body_out = raw_body
        active_fq = filter_query
        if (
            not active_fq
            and max_bytes is not None
            and len(body_out.encode("utf-8")) > max_bytes
        ):
            path_words = [
                w.lower()
                for w in re.split(r"\W+", urlparse(url).path)
                if len(w) >= 3 and not w.isdigit() and w.lower() not in _STOPWORDS and w.lower() not in ("html", "htm", "php", "pdf", "docs", "articles")
            ]
            active_fq = " ".join(path_words[:6]) if path_words else "overview specification"
        if active_fq:
            body_out = _apply_content_filter(
                body_out,
                url,
                active_fq,
                max_blocks=max_blocks,
                max_headings=max_headings,
                max_bytes=max_bytes,
            )
        return f"# Source: {url}\n\n{body_out}"

    if cached_row is not None and cached_row[0] and now <= float(cached_row[4] or 0):
        return _finalize_body(str(cached_row[0]))

    cond_headers: dict[str, str] = {}
    if cached_row is not None and cached_row[0]:
        if cached_row[1]:
            cond_headers["If-None-Match"] = str(cached_row[1])
        if cached_row[2]:
            cond_headers["If-Modified-Since"] = str(cached_row[2])

    try:
        if cond_headers:
            try:
                response = _http_get(url, extra_headers=cond_headers)
            except TypeError:
                response = _http_get(url)
        else:
            response = _http_get(url)
    except Exception as exc:
        return f"ERROR: Failed to fetch URL '{url}': {type(exc).__name__}: {exc}"

    if getattr(response, "status_code", 200) == 304 and cached_row is not None and cached_row[0]:
        if conn is not None and norm_url:
            with contextlib.suppress(Exception):
                conn.execute(
                    "UPDATE http_cache SET fetched_at = ?, expires_at = ? WHERE norm_url = ?",
                    (now, now + url_ttl, norm_url),
                )
                conn.commit()
        return _finalize_body(str(cached_row[0]))

    def _save_to_sqlite(raw_md: str) -> None:
        if conn is None or not norm_url or not raw_md or raw_md.startswith("ERROR:"):
            return
        etag_val = str(response.headers.get("etag", "") or "")
        lm_val = str(response.headers.get("last-modified", "") or "")
        with contextlib.suppress(Exception):
            conn.execute(
                "INSERT OR REPLACE INTO http_cache "
                "(norm_url, include_code, markdown_body, etag, last_modified, fetched_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (norm_url, code_int, raw_md, etag_val, lm_val, now, now + url_ttl),
            )
            conn.commit()

    with contextlib.redirect_stdout(sys.stderr):
        final_url = str(getattr(response, "url", url))
        content_type = response.headers.get("content-type", "")
        is_html_like = (
            "html" in content_type.lower() or not content_type
        ) and not _is_pdf(url, content_type, response.content or b"")

        if response.status_code >= 400 or (
            is_html_like
            and _is_antibot_or_error_page(
                response.status_code, response.text, final_url
            )
        ):
            rendered_html = _fetch_html_via_browser(url)
            if rendered_html and not _is_antibot_or_error_page(
                200, rendered_html, url
            ):
                md_from_browser = _html_to_markdown(
                    rendered_html,
                    url,
                    filter_query=filter_query,
                    include_code=include_code,
                )
                if md_from_browser:
                    _save_to_sqlite(md_from_browser)
                    return _finalize_body(md_from_browser)
            return (
                f"ERROR: HTTP {response.status_code} (or anti-bot challenge page) "
                f"when fetching URL '{url}'."
            )

        raw_bytes = response.content

        if not raw_bytes:
            return f"ERROR: Empty response body from URL '{url}'."

        if _is_pdf(url, content_type, raw_bytes):
            try:
                doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
                try:
                    md_text = pymupdf4llm.to_markdown(doc)
                finally:
                    doc.close()
            except Exception as exc:
                return f"ERROR: Failed to parse PDF from '{url}': {exc}"

            if not md_text or not md_text.strip():
                return f"ERROR: PDF at '{url}' contained no extractable text."
            body_out = _clean_plain_text_body(
                md_text, include_code=include_code
            )
            if not body_out:
                body_out = md_text.strip()
            _save_to_sqlite(body_out)
            return _finalize_body(body_out)

        lowered_ct = content_type.lower()
        if any(
            token in lowered_ct
            for token in ("text/plain", "text/markdown", "application/json")
        ):
            body_out = _clean_plain_text_body(
                response.text, include_code=include_code
            )
            if not body_out:
                body_out = response.text
            _save_to_sqlite(body_out)
            return _finalize_body(body_out)

        md_body = _html_to_markdown(
            response.text,
            url,
            filter_query=filter_query,
            include_code=include_code,
        )
        if not md_body:
            rendered_html = _fetch_html_via_browser(url)
            if rendered_html and not _is_antibot_or_error_page(
                200, rendered_html, url
            ):
                md_body = _html_to_markdown(
                    rendered_html,
                    url,
                    filter_query=filter_query,
                    include_code=include_code,
                )

        if not md_body:
            return (
                f"ERROR: Could not extract readable content from '{url}' "
                "(page may require JavaScript or have no main article text)."
            )
        _save_to_sqlite(md_body)
        return _finalize_body(md_body)


def _fetch_url_as_markdown(
    url: str,
    filter_query: str | None = None,
    include_code: bool = False,
    max_blocks: int = 40,
    max_headings: int = 25,
    max_bytes: int | None = None,
) -> str:
    cache_key = (
        _normalize_cache_url(url),
        _normalize_filter_key(filter_query),
        bool(include_code),
    )
    cached = _URL_CACHE.get(cache_key)
    if cached is not None and (
        max_bytes is None or len(cached.encode("utf-8")) <= max_bytes
    ):
        return cached
    result = _fetch_url_as_markdown_uncached(
        url,
        filter_query=filter_query,
        include_code=include_code,
        max_blocks=max_blocks,
        max_headings=max_headings,
        max_bytes=max_bytes,
    )
    if not result.startswith("ERROR:"):
        if len(_URL_CACHE) >= _MAX_CACHE_ENTRIES:
            _URL_CACHE.pop(next(iter(_URL_CACHE)))
        _URL_CACHE[cache_key] = result
    return result


def _search_duckduckgo(query: str, max_results: int = 10) -> str:
    norm_query = " ".join(query.split())
    cached = _SEARCH_CACHE.get(norm_query)
    conn = _get_sqlite_conn()
    now = time.time()
    if cached is None and conn is not None and norm_query:
        with contextlib.suppress(Exception):
            cur = conn.execute(
                "SELECT output, expires_at FROM search_cache WHERE norm_query = ?",
                (norm_query,),
            )
            row = cur.fetchone()
            if row and row[0] and now <= float(row[1] or 0):
                cached = str(row[0])
                _SEARCH_CACHE[norm_query] = cached
    if cached is not None:
        if max_results < 10 and cached.startswith("# DuckDuckGo Search Results for:"):
            c_lines = cached.splitlines()
            if len(c_lines) > 2 + max_results:
                return "\n".join(c_lines[: 2 + max_results])
        return cached

    results: list[dict[str, Any]] = []
    tier1_blocked_or_failed = False
    tier1_error_detail = ""

    try:
        resp = _http_post(DDG_HTML_URL, data={"q": query})
        if resp.status_code >= 400 or _is_ddg_anomaly(
            resp.status_code, resp.text
        ):
            tier1_blocked_or_failed = True
            tier1_error_detail = (
                f"HTTP {resp.status_code} (anti-bot challenge or error)"
            )
        else:
            results = _parse_ddg_html(resp.text, max_results=10)
    except Exception as exc:
        tier1_blocked_or_failed = True
        tier1_error_detail = str(exc)

    if not results:
        try:
            fallback_items = _search_ddgs_fallback(query, max_results=10)
            results = [
                item
                for item in fallback_items
                if not _is_ad_url(item.get("href", ""))
            ][:10]
        except Exception as exc:
            if tier1_blocked_or_failed:
                return (
                    f"ERROR: DuckDuckGo search failed ({tier1_error_detail}) "
                    f"and ddgs fallback failed for '{query}': {exc}"
                )

    if not results:
        return f"No DuckDuckGo results found for query: '{query}'."

    lines = [
        f"# DuckDuckGo Search Results for: `{query}`",
        "#schema:idx|title|url|snippet",
    ]
    for idx, item in enumerate(results, start=1):
        title = _escape_dsv_field(
            _clean_ddgs_snippet(item.get("title") or "Untitled", max_bytes=160)
        )
        href = _escape_dsv_field(
            _clean_tracking_url(item.get("href") or ""), is_url=True
        )
        body = _escape_dsv_field(
            _clean_ddgs_snippet(item.get("body") or "", max_bytes=380)
        )
        lines.append(f"{idx}|{title}|{href}|{body}")
    output = "\n".join(lines).strip()
    if len(_SEARCH_CACHE) >= _MAX_CACHE_ENTRIES:
        _SEARCH_CACHE.pop(next(iter(_SEARCH_CACHE)))
    _SEARCH_CACHE[norm_query] = output
    if conn is not None and norm_query:
        with contextlib.suppress(Exception):
            conn.execute(
                "INSERT OR REPLACE INTO search_cache (norm_query, output, fetched_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (norm_query, output, now, now + 12 * 3600.0),
            )
            conn.commit()
    if max_results < 10 and len(lines) > 2 + max_results:
        return "\n".join(lines[: 2 + max_results])
    return output


_UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")


def _deduplicate_ddg_batch_output(
    ddg_output: str, seen_urls: set[str], max_bytes: int | None = None
) -> str:
    """Remove duplicate URLs already returned in earlier queries of the same batch and fit within max_bytes."""
    if not ddg_output.startswith("# DuckDuckGo Search Results for:"):
        return ddg_output
    top_part, sep_part, tail_part = ddg_output.partition("\n\n# Source: ")
    lines = top_part.splitlines()
    if len(lines) < 3 or lines[1] != "#schema:idx|title|url|snippet":
        return ddg_output
    header_lines = lines[:2]
    kept_rows: list[str] = []
    for line in lines[2:]:
        parts = _UNESCAPED_PIPE_RE.split(line, maxsplit=3)
        if len(parts) < 4:
            kept_rows.append(line)
            continue
        _, title, url_field, snippet = parts
        norm_url = _normalize_cache_url(url_field)
        if norm_url and norm_url in seen_urls:
            continue
        if norm_url:
            seen_urls.add(norm_url)
        row_str = f"{len(kept_rows) + 1}|{title}|{url_field}|{snippet}"
        if max_bytes is not None and kept_rows:
            candidate_table = "\n".join(header_lines + kept_rows + [row_str])
            if len(candidate_table.encode("utf-8")) > max_bytes:
                break
        kept_rows.append(row_str)
    rebuilt = "\n".join(header_lines + kept_rows)
    return f"{rebuilt}{sep_part}{tail_part}" if sep_part else rebuilt


def _execute_single_target(
    raw_item: str,
    filter_query: str | None,
    include_code: bool,
    max_blocks: int = 40,
    max_headings: int = 25,
    max_ddg_results: int = 10,
    auto_open_top: int = 0,
    max_bytes: int | None = None,
) -> str:
    effective_auto_open = auto_open_top
    cleaned_raw = raw_item.strip()
    open_match = re.match(r"^(?:open:|@open\b)\s*(.+)$", cleaned_raw, re.IGNORECASE)
    if open_match and not _is_url(cleaned_raw):
        cleaned_raw = open_match.group(1).strip()
        effective_auto_open = max(1, effective_auto_open)

    target, active_filter = _split_url_and_filter(cleaned_raw, filter_query)
    if _is_url(target):
        return _fetch_url_as_markdown(
            target,
            filter_query=active_filter,
            include_code=include_code,
            max_blocks=max_blocks,
            max_headings=max_headings,
            max_bytes=max_bytes,
        )

    ddg_out = _search_duckduckgo(target, max_results=max_ddg_results)
    if effective_auto_open <= 0 or not ddg_out.startswith("# DuckDuckGo Search Results for:"):
        return ddg_out

    row_dicts: list[dict[str, Any]] = []
    for line in ddg_out.splitlines()[2:]:
        parts = _UNESCAPED_PIPE_RE.split(line, maxsplit=3)
        if len(parts) == 4:
            row_dicts.append({"title": parts[1], "href": parts[2], "body": parts[3]})

    ranked_urls = _rank_primary_authority_urls(row_dicts)
    if not ranked_urls:
        return ddg_out

    open_filter = active_filter or target
    opened_sections: list[str] = []
    budget_total = max_bytes if max_bytes is not None else 9200
    min_open_floor = 350 if max_bytes is not None else 1400
    rem_open_bytes = max(min_open_floor, budget_total - len(ddg_out.encode("utf-8")) - 8)
    for cand_url in ranked_urls:
        rem_slots = effective_auto_open - len(opened_sections)
        slot_bytes = max(min_open_floor, rem_open_bytes // max(1, rem_slots))
        page_out = _fetch_url_as_markdown(
            cand_url,
            filter_query=open_filter,
            include_code=include_code,
            max_blocks=min(max_blocks, 15),
            max_headings=min(max_headings, 15),
            max_bytes=slot_bytes,
        )
        if not page_out.startswith("ERROR:"):
            opened_sections.append(page_out)
            rem_open_bytes = max(min_open_floor, rem_open_bytes - len(page_out.encode("utf-8")))
            if len(opened_sections) >= effective_auto_open:
                break

    if not opened_sections:
        return ddg_out
    return ddg_out + "\n\n" + "\n\n".join(opened_sections)


@mcp.tool(output_schema=None)
def search_website(
    query_or_url: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("query_or_url", "query", "url", "q"),
            description=(
                "Search query (4-6 core terms, or 'open: <query>' to auto-open top primary URL), "
                "http(s) URL, 'https://... <keywords>', or ' || '-separated items. Follow the "
                "'## Search keywords' rule when ./docs/index.md exists."
            ),
        ),
    ] = "",
    filter_query: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("filter_query", "filter", "keywords"),
            description=(
                "Keyword filter for http(s) URLs (or inline 'https://... <keywords>'). Pass by "
                "default on long pages, catalogs or PDFs (<10 KB) to filter items/sections by "
                "matching terms, with 'site:<domain>' fallback on 0 matches."
            ),
        ),
    ] = None,
    include_code: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Keep multi-line code blocks (<pre>, ```) when fetching an http(s) URL "
                "(default False keeps inline <code> only)."
            ),
        ),
    ] = False,
    queries_or_urls: Annotated[
        list[str] | None,
        Field(
            default=None,
            description=(
                "Optional batch list of up to 10 search queries or http(s) URLs executed in one "
                "call with shared SQLite WAL cache and URL deduplication."
            ),
        ),
    ] = None,
    auto_open_top: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            le=3,
            validation_alias=AliasChoices("auto_open_top", "auto_open"),
            description=(
                "Number of top authoritative primary URLs (0-3) to auto-open and filter "
                "after a DuckDuckGo search (or prefix 'open: ')."
            ),
        ),
    ] = 0,
) -> str:
    """Search DuckDuckGo (4-6 core terms; pass auto_open_top=1 or 'open: <query>' to auto-open top authoritative primary URL in 1 call), fetch an http(s) webpage/PDF/catalog as Markdown (pass filter_query or inline 'https://... <keywords>' on long pages/PDFs for <=10 KB; include_code=False default), or run up to 10 items via queries_or_urls=[...] (or 'q1 || q2') with SQLite WAL caching, <=9.5 KB slack-redistributed batch budget, and URL deduplication. MANDATORY BEFORE SEARCHING: check whether ./docs/index.md has '## Search keywords' (via compress_context(file_path='docs/index.md', section='Search keywords')). If present and in the project's domain, include 1-3 fitting keywords from '## Search keywords' in every query (1-2 leading vision/scale priority terms for project architecture/UI/scale/workflow queries, or 1-2 technical/methodological terms like primary-source-verification, ISO-NEN-IEC, IETF-RFC, NIST-SP-800, OWASP-ASVS, Python-stdlib for external protocol/RFC/standard/scientific queries instead of abstract vision words like zero-trust; never 0 keywords). Outside the project's domain, search without project keywords."""
    validated = SearchWebsiteInput(
        query_or_url=query_or_url,
        queries_or_urls=queries_or_urls,
        filter_query=filter_query,
        include_code=include_code,
        auto_open_top=auto_open_top,
    )
    items: list[str] = []
    if validated.query_or_url:
        if "||" in validated.query_or_url or "\n" in validated.query_or_url:
            for part in re.split(r"\s*\|\|\s*|\r?\n", validated.query_or_url):
                cleaned_part = part.strip()
                if cleaned_part and cleaned_part not in items:
                    items.append(cleaned_part)
        else:
            items.append(validated.query_or_url)
    if validated.queries_or_urls:
        for batch_item in validated.queries_or_urls:
            if batch_item not in items:
                items.append(batch_item)

    items = items[:10]
    batch_size = len(items)
    if batch_size == 1:
        return _execute_single_target(
            items[0],
            validated.filter_query,
            validated.include_code,
            auto_open_top=validated.auto_open_top,
        )

    batch_max_blocks = max(8, 32 // batch_size)
    batch_max_headings = min(20, max(10, 40 // batch_size))
    batch_max_ddg = max(5, 18 // batch_size) if batch_size >= 3 else 10
    total_batch_budget = 9400
    remaining_budget = total_batch_budget - (batch_size - 1) * 7

    seen_ddg_urls: set[str] = set()
    outputs: list[str] = []
    for idx, raw_item in enumerate(items):
        remaining_items = batch_size - idx
        item_max_bytes = max(450, remaining_budget // remaining_items)
        out = _execute_single_target(
            raw_item,
            validated.filter_query,
            validated.include_code,
            max_blocks=batch_max_blocks,
            max_headings=batch_max_headings,
            max_ddg_results=batch_max_ddg,
            auto_open_top=validated.auto_open_top,
            max_bytes=item_max_bytes,
        )
        out = _deduplicate_ddg_batch_output(
            out, seen_ddg_urls, max_bytes=item_max_bytes
        )
        used_bytes = len(out.encode("utf-8"))
        remaining_budget = max(0, remaining_budget - used_bytes)
        outputs.append(out)
    return "\n\n---\n\n".join(outputs)


if __name__ == "__main__":
    mcp.run()
