import contextlib
import sys
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

with contextlib.redirect_stdout(sys.stderr):
    import httpx
    import pymupdf
    import pymupdf4llm
    import trafilatura
    from fastmcp import FastMCP
    from lxml import html as lxml_html
    from pydantic import BaseModel, ConfigDict, field_validator

mcp = FastMCP("web-search")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "application/pdf,*/*;q=0.8"
    ),
}

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


class SearchWebsiteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query_or_url: str

    @field_validator("query_or_url")
    @classmethod
    def _must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("query_or_url must not be empty")
        return value


def _http_get(url: str, timeout: float = 30.0) -> httpx.Response:
    return httpx.get(
        url,
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout,
    )


def _http_post(
    url: str, data: dict[str, str], timeout: float = 20.0
) -> httpx.Response:
    headers = {**DEFAULT_HEADERS, "Referer": "https://html.duckduckgo.com/"}
    return httpx.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
        timeout=timeout,
    )


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
        results.append(
            {
                "title": " ".join(title_el[0].text_content().split()),
                "href": _clean_ddg_href(raw_href),
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


def _fetch_url_as_markdown(url: str) -> str:
    try:
        response = _http_get(url)
    except Exception as exc:
        return f"ERROR: Failed to fetch URL '{url}': {type(exc).__name__}: {exc}"

    if response.status_code >= 400:
        return (
            f"ERROR: HTTP {response.status_code} when fetching URL '{url}'."
        )

    content_type = response.headers.get("content-type", "")
    raw_bytes = response.content

    if not raw_bytes:
        return f"ERROR: Empty response body from URL '{url}'."

    with contextlib.redirect_stdout(sys.stderr):
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

        html_text = response.text
        extracted = trafilatura.extract(
            html_text,
            url=url,
            output_format="markdown",
            include_tables=True,
            include_links=True,
            include_formatting=True,
        )
        if not extracted or not extracted.strip():
            return (
                f"ERROR: Could not extract readable content from '{url}' "
                "(page may require JavaScript or have no main article text)."
            )
        return f"# Source: {url}\n\n{extracted.strip()}"


def _search_duckduckgo(query: str) -> str:
    try:
        resp = _http_post(DDG_HTML_URL, data={"q": query})
    except Exception as exc:
        return f"ERROR: DuckDuckGo search failed for '{query}': {exc}"

    if resp.status_code >= 400:
        return (
            f"ERROR: DuckDuckGo returned HTTP {resp.status_code} "
            f"for query '{query}'."
        )

    results = _parse_ddg_html(resp.text, max_results=10)
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
