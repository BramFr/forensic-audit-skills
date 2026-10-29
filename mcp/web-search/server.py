import contextlib
import json
import re
import sys
from collections.abc import Mapping
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
    from curl_cffi import requests as curl_requests
    from ddgs import DDGS
    from ddgs.exceptions import DDGSException
    from fastmcp import FastMCP
    from lxml import html as lxml_html
    from pydantic import BaseModel, ConfigDict, Field, field_validator

mcp = FastMCP("web-search")

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
    r"splashui/captcha|enable javascript and cookies to continue)",
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


class SearchWebsiteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query_or_url: str = Field(
        description=(
            "Search query, http(s) URL, or 'https://... <filter_keywords>' to scrape and filter a URL. "
            "MANDATORY FOR SEARCH QUERIES: before searching, check whether ./docs/index.md exists with "
            "a '## Search keywords' section (using compress_context(file_path='docs/index.md', section='Search keywords') "
            "when available). If present AND the user's request is about the project or its domain, you MUST "
            "include 1 to 3 fitting terms from '## Search keywords' in query_or_url (for architecture, UI, "
            "canvas, scale or performance queries, pick 1-2 leading vision/scale priority terms from the start "
            "of the list; for protocol, RFC or standard specs, pick 1-2 matching technical domain terms from "
            "the list; strip search-operator punctuation like '+' from keywords). Never send 0 keywords when "
            "'## Search keywords' is present. If the request is a standalone question outside the project's "
            "domain (e.g., an unrelated consumer or personal question while the project folder is open), "
            "do NOT inject project keywords into the search query."
        )
    )
    filter_query: str | None = Field(
        default=None,
        description=(
            "Recommended keyword filter when query_or_url is an http(s) URL (or pass 'https://... <keywords>' "
            "inline in query_or_url). Pass filter_query by default on long pages, product catalogs, legal texts "
            "or PDFs to keep outputs under 10 KB. Filters extracted products, listings and text sections on the "
            "page by matching terms from the user's question, and falls back to a 'site:<domain> <filter_query>' "
            "search if 0 items match on the page."
        ),
    )
    include_code: bool = Field(
        default=False,
        description=(
            "Optional flag when fetching an http(s) URL (default False). By default, multi-line code "
            "blocks (<pre>, ```...```) are stripped while preserving inline <code> values in prose. "
            "Set to True only when verbatim code examples from a page are explicitly needed."
        ),
    )

    @field_validator("query_or_url")
    @classmethod
    def _must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("query_or_url must not be empty")
        return value


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


def _http_get(url: str, timeout: float = 30.0) -> Any:
    """Fetch URL with persistent cookie jar, consent-gate unwrapping and TLS profile rotation."""
    parsed = urlparse(url)
    origin_referer = (
        f"{parsed.scheme}://{parsed.netloc}/"
        if parsed.scheme and parsed.netloc
        else url
    )
    last_resp: Any = None
    last_exc: Exception | None = None

    for profile in IMPERSONATE_PROFILES:
        session = _get_or_create_session(profile)
        for attempt in range(3):
            req_headers = (
                {**DEFAULT_HEADERS, "Referer": origin_referer}
                if attempt > 0
                else DEFAULT_HEADERS
            )
            try:
                resp = session.get(
                    url,
                    headers=req_headers,
                    allow_redirects=True,
                    timeout=timeout,
                )
            except Exception as exc:
                last_exc = exc
                break

            content_type = resp.headers.get("content-type", "")
            if "html" in content_type.lower() and resp.status_code < 400:
                final_url = str(getattr(resp, "url", url))
                callback_url = _unwrap_consent_redirect(final_url, resp.text)
                if callback_url and callback_url != final_url:
                    resp = session.get(
                        callback_url,
                        headers=DEFAULT_HEADERS,
                        allow_redirects=True,
                        timeout=timeout,
                    )

            last_resp = resp
            final_url = str(getattr(resp, "url", url))
            if "html" not in content_type.lower() and resp.status_code < 400:
                return resp
            if not _is_antibot_or_error_page(
                resp.status_code, resp.text, final_url
            ):
                return resp

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


def _escape_dsv_field(val: str, is_url: bool = False) -> str:
    """Escape a field for Positional Pipe-DSV (#schema:)."""
    cleaned = " ".join(str(val or "").splitlines()).strip()
    if is_url:
        return cleaned.replace("|", "%7C")
    return cleaned.replace("|", r"\|")


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
                "title": " ".join(title_el[0].text_content().split()),
                "href": cleaned_href,
                "body": (
                    " ".join(snippet_el[0].text_content().split())
                    if snippet_el
                    else ""
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
                "title": (item.get("title") or "Untitled").strip(),
                "href": href,
                "body": (item.get("body") or "").strip(),
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
    return combined or None


def _apply_content_filter(
    markdown_body: str, url: str, filter_query: str
) -> str:
    """Filter extracted Markdown items/blocks by filter_query; return Headings Index + Filtered Matches only."""
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
            clean_h = re.sub(
                r"\[(?:#|¶|permalink)\]\([^)]*\)", "", s, flags=re.IGNORECASE
            ).strip()
            clean_h = re.sub(r"\s*[#¶]+\s*$", "", clean_h).strip()
            if clean_h and clean_h not in headings and len(headings) < 25:
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

    toc = (
        "## Page Headings Index\n" + "\n".join(headings) + "\n\n"
        if headings
        else ""
    )

    if scored:
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        selected = [item[2] for item in scored[:40]]
        filter_block = (
            f"## Filtered Matches ({len(selected)} of {len(blocks)} blocks matching `{filter_query}`)\n\n"
            + "\n\n".join(selected)
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


def _fetch_url_as_markdown(
    url: str, filter_query: str | None = None, include_code: bool = False
) -> str:
    try:
        response = _http_get(url)
    except Exception as exc:
        return f"ERROR: Failed to fetch URL '{url}': {type(exc).__name__}: {exc}"

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
                    if filter_query:
                        md_from_browser = _apply_content_filter(
                            md_from_browser, url, filter_query
                        )
                    return f"# Source: {url}\n\n{md_from_browser}"
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
            if filter_query:
                body_out = _apply_content_filter(body_out, url, filter_query)
            return f"# Source: {url}\n\n{body_out}"

        lowered_ct = content_type.lower()
        if any(
            token in lowered_ct
            for token in ("text/plain", "text/markdown", "application/json")
        ):
            body_out = response.text
            if filter_query:
                body_out = _apply_content_filter(body_out, url, filter_query)
            return f"# Source: {url}\n\n{body_out}"

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
        if filter_query:
            md_body = _apply_content_filter(md_body, url, filter_query)
        return f"# Source: {url}\n\n{md_body}"


def _search_duckduckgo(query: str) -> str:
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
        title = _escape_dsv_field(item.get("title") or "Untitled")
        href = _escape_dsv_field(
            _clean_tracking_url(item.get("href") or ""), is_url=True
        )
        body = _escape_dsv_field(item.get("body") or "")
        lines.append(f"{idx}|{title}|{href}|{body}")
    return "\n".join(lines).strip()


@mcp.tool()
def search_website(
    query_or_url: Annotated[
        str,
        Field(
            description=(
                "Search query, http(s) URL, or 'https://... <filter_keywords>' to scrape and filter a URL. "
                "MANDATORY FOR SEARCH QUERIES: before searching, check whether ./docs/index.md exists with "
                "a '## Search keywords' section (using compress_context(file_path='docs/index.md', section='Search keywords') "
                "when available). If present AND the user's request is about the project or its domain, you MUST "
                "include 1 to 3 fitting terms from '## Search keywords' in query_or_url (for architecture, UI, "
                "canvas, scale or performance queries, pick 1-2 leading vision/scale priority terms from the start "
                "of the list; for protocol, RFC or standard specs, pick 1-2 matching technical domain terms from "
                "the list; strip search-operator punctuation like '+' from keywords). Never send 0 keywords when "
                "'## Search keywords' is present. If the request is a standalone question outside the project's "
                "domain (e.g., an unrelated consumer or personal question while the project folder is open), "
                "do NOT inject project keywords into the search query."
            )
        ),
    ],
    filter_query: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Recommended keyword filter when query_or_url is an http(s) URL (or pass 'https://... <keywords>' "
                "inline in query_or_url). Pass filter_query by default on long pages, product catalogs, legal texts "
                "or PDFs to keep outputs under 10 KB. Filters extracted products, listings and text sections on the "
                "page by matching terms from the user's question, and falls back to a 'site:<domain> <filter_query>' "
                "search if 0 items match on the page."
            ),
        ),
    ] = None,
    include_code: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Optional flag when fetching an http(s) URL (default False). By default, multi-line code "
                "blocks (<pre>, ```...```) are stripped while preserving inline <code> values in prose. "
                "Set to True only when verbatim code examples from a page are explicitly needed."
            ),
        ),
    ] = False,
) -> str:
    """Search DuckDuckGo for a query, or fetch a webpage/PDF/catalog as Markdown for an http(s) URL (pass filter_query or inline 'https://... <keywords>' by default on long pages, catalogs or PDFs to avoid >10 KB outputs; include_code=False by default). MANDATORY BEFORE SEARCHING: check whether ./docs/index.md exists with '## Search keywords' (via compress_context(file_path='docs/index.md', section='Search keywords') when available). If present and the question relates to the project or its domain, always include 1 to 3 fitting keywords from '## Search keywords' in every search query (1-2 leading vision/scale priority terms for architecture/UI/scale/performance queries, or 1-2 technical domain terms for protocol/RFC/standard queries; never 0 keywords). For standalone questions outside the project's domain, search normally without project keywords."""
    validated = SearchWebsiteInput(
        query_or_url=query_or_url,
        filter_query=filter_query,
        include_code=include_code,
    )
    target, active_filter = _split_url_and_filter(
        validated.query_or_url, validated.filter_query
    )
    if _is_url(target):
        return _fetch_url_as_markdown(
            target,
            filter_query=active_filter,
            include_code=validated.include_code,
        )
    return _search_duckduckgo(target)


if __name__ == "__main__":
    mcp.run()
