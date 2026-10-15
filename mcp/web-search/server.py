import contextlib
import re
import sys
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

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
    from pydantic import BaseModel, ConfigDict, field_validator

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

DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_JS_CALLBACK_RE = re.compile(
    r"decodeURIComponent\(\s*['\"](https?%3A%2F%2F[^'\"]+)['\"]\s*\)"
)
_META_REFRESH_RE = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+content=["\']?\d+\s*;\s*url=([^"\'>\s]+)',
    re.IGNORECASE,
)


class SearchWebsiteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query_or_url: str

    @field_validator("query_or_url")
    @classmethod
    def _must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("query_or_url must not be empty")
        return value


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


def _http_get(url: str, timeout: float = 30.0) -> Any:
    """Fetch URL using Chrome TLS/HTTP2 impersonation and automatic consent-gate unwrapping."""
    session = curl_requests.Session(impersonate="chrome")
    resp = session.get(
        url,
        headers=DEFAULT_HEADERS,
        cookies=DEFAULT_COOKIES,
        allow_redirects=True,
        timeout=timeout,
    )
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
    return resp


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
                context = browser.new_context(
                    locale="nl-NL",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                )
                page = context.new_page()
                page.goto(
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
                return page.content()
            finally:
                browser.close()
    except Exception:
        return None


def _is_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


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


def _clean_ddg_href(raw_href: str) -> str:
    href = raw_href.strip()
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return unquote(qs["uddg"][0])
    return href


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
        href = (item.get("href") or "").strip()
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
        'or ancestor::article//a]'
    )
    for node in tree.xpath(xpath_query):
        text = " ".join(node.text_content().split())
        href = (node.get("href") or "").strip()
        if len(text) < 12 or not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        key = f"{text}|{full_url}"
        if key in seen:
            continue
        seen.add(key)
        items.append(f"- [{text}]({full_url})")
    return "\n".join(items)


def _html_to_markdown(html_text: str, url: str) -> str | None:
    extracted = trafilatura.extract(
        html_text,
        url=url,
        output_format="markdown",
        include_tables=True,
        include_links=True,
        include_formatting=True,
        favor_recall=True,
    )
    body = (extracted or "").strip()
    if len(html_text) > 30000 and len(body) < 4000:
        headlines = _extract_portal_headlines(html_text, url)
        if headlines:
            body = f"{headlines}\n\n{body}".strip()
    return body or None


def _fetch_url_as_markdown(url: str) -> str:
    try:
        response = _http_get(url)
    except Exception as exc:
        return f"ERROR: Failed to fetch URL '{url}': {type(exc).__name__}: {exc}"

    with contextlib.redirect_stdout(sys.stderr):
        if response.status_code >= 400:
            rendered_html = _fetch_html_via_browser(url)
            if rendered_html:
                md_from_browser = _html_to_markdown(rendered_html, url)
                if md_from_browser:
                    return f"# Source: {url}\n\n{md_from_browser}"
            return (
                f"ERROR: HTTP {response.status_code} when fetching URL '{url}'."
            )

        content_type = response.headers.get("content-type", "")
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
            return f"# Source: {url}\n\n{md_text.strip()}"

        lowered_ct = content_type.lower()
        if any(
            token in lowered_ct
            for token in ("text/plain", "text/markdown", "application/json")
        ):
            return f"# Source: {url}\n\n{response.text}"

        md_body = _html_to_markdown(response.text, url)
        if not md_body:
            rendered_html = _fetch_html_via_browser(url)
            if rendered_html:
                md_body = _html_to_markdown(rendered_html, url)

        if not md_body:
            return (
                f"ERROR: Could not extract readable content from '{url}' "
                "(page may require JavaScript or have no main article text)."
            )
        return f"# Source: {url}\n\n{md_body}"


def _search_duckduckgo(query: str) -> str:
    results: list[dict[str, Any]] = []
    tier1_blocked_or_failed = False
    tier1_error_detail = ""

    try:
        resp = _http_post(DDG_HTML_URL, data={"q": query})
        if resp.status_code >= 400 or _is_ddg_anomaly(resp.status_code, resp.text):
            tier1_blocked_or_failed = True
            tier1_error_detail = f"HTTP {resp.status_code} (anti-bot challenge or error)"
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

    lines = [f"# DuckDuckGo Search Results for: `{query}`\n"]
    for idx, item in enumerate(results, start=1):
        title = item.get("title") or "Untitled"
        href = item.get("href") or ""
        body = item.get("body") or ""
        lines.append(f"## {idx}. [{title}]({href})")
        lines.append(f"- **URL**: {href}")
        if body:
            lines.append(f"- **Snippet**: {body}")
        lines.append("")
    return "\n".join(lines).strip()


@mcp.tool()
def search_website(query_or_url: str) -> str:
    """Search DuckDuckGo for a query, or fetch a webpage/PDF as Markdown for an http(s) URL."""
    validated = SearchWebsiteInput(query_or_url=query_or_url)
    target = validated.query_or_url
    if _is_url(target):
        return _fetch_url_as_markdown(target)
    return _search_duckduckgo(target)


if __name__ == "__main__":
    mcp.run()
