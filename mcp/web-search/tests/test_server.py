import httpx
import pymupdf
import pytest
from pydantic import ValidationError

from server import (
    SearchWebsiteInput,
    _unwrap_consent_redirect,
    search_website,
)


def _make_sample_pdf_bytes(text: str) -> bytes:
    """Create a real in-memory PDF byte stream using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pydantic_contract_strict_extra_forbid():
    """Contract must enforce extra='forbid' and reject empty input."""
    valid = SearchWebsiteInput(query_or_url="python fastmcp")
    assert valid.query_or_url == "python fastmcp"

    with pytest.raises(ValidationError):
        SearchWebsiteInput(query_or_url="test", unexpected_field="nope")

    with pytest.raises(ValidationError):
        SearchWebsiteInput(query_or_url="   ")


def test_search_duckduckgo_query(monkeypatch):
    """Non-URL input must query DuckDuckGo HTML endpoint and return Markdown results."""
    ddg_html = """
    <html><body>
      <div class="result__body">
        <a class="result__a" href="https://gofastmcp.com/docs">FastMCP Documentation</a>
        <a class="result__snippet">The fast, Pythonic way to build MCP servers.</a>
      </div>
      <div class="result__body">
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.io">Docs</a>
        <a class="result__snippet">Web scraping and text extraction library.</a>
      </div>
    </body></html>
    """

    def fake_post(url, data, **kwargs):
        assert data == {"q": "fastmcp trafilatura"}
        request = httpx.Request("POST", url)
        return httpx.Response(200, text=ddg_html, request=request)

    monkeypatch.setattr("server._http_post", fake_post)

    output = search_website("fastmcp trafilatura")
    assert "FastMCP Documentation" in output
    assert "https://gofastmcp.com/docs" in output
    assert "The fast, Pythonic way to build MCP servers." in output
    assert "Docs" in output
    assert "https://a.io" in output


def test_fetch_html_url_to_markdown(monkeypatch):
    """HTML URL must be fetched and converted to full Markdown via trafilatura."""
    html_body = """
    <html>
      <head><title>Audit Specification</title></head>
      <body>
        <article>
          <h1>Main Normative Heading</h1>
          <p>Primary normative paragraph with <a href="https://example.org/ref">link</a>.</p>
          <table>
            <tr><th>Metric</th><th>Limit</th></tr>
            <tr><td>Voltage</td><td>230V</td></tr>
          </table>
        </article>
      </body>
    </html>
    """

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=html_body,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    output = search_website("https://example.org/spec")
    assert "Main Normative Heading" in output
    assert "230V" in output
    assert "https://example.org/spec" in output


def test_fetch_pdf_url_to_markdown(monkeypatch):
    """PDF URL must be detected and converted to full Markdown via pymupdf4llm."""
    pdf_bytes = _make_sample_pdf_bytes("NEN-ISO-9001 Normative PDF Content")

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "application/pdf"},
            content=pdf_bytes,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    output = search_website("https://example.org/standard.pdf")
    assert "NEN-ISO-9001 Normative PDF Content" in output


def test_fault_injection_http_error_and_network_failure(monkeypatch):
    """Fault injection: HTTP 403 (when browser fallback also fails) and timeouts return ERROR."""
    def fake_get_403(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(403, text="Forbidden", request=request)

    monkeypatch.setattr("server._http_get", fake_get_403)
    monkeypatch.setattr("server._fetch_html_via_browser", lambda url, timeout=25.0: None)
    out_403 = search_website("https://example.org/blocked")
    assert "ERROR" in out_403
    assert "403" in out_403

    def fake_get_timeout(url, **kwargs):
        raise httpx.ConnectTimeout("Connection timed out")

    monkeypatch.setattr("server._http_get", fake_get_timeout)
    out_timeout = search_website("https://example.org/timeout")
    assert "ERROR" in out_timeout
    assert "Connection timed out" in out_timeout


def test_unwrap_dpg_consent_gate_redirect():
    """Consent gate HTML with decodeURIComponent callbackUrl must be unwrapped."""
    consent_html = (
        "<script>const callbackUrl = new URL("
        "decodeURIComponent("
        "'https%3A%2F%2Ftweakers.net%2Fprivacygate-confirm%3FredirectUri%3D%252F'"
        "));</script>"
    )
    target_url = _unwrap_consent_redirect(
        "https://myprivacy.dpgmedia.nl/consent", consent_html
    )
    assert target_url == "https://tweakers.net/privacygate-confirm?redirectUri=%2F"


def test_tier3_browser_fallback_on_waf_403(monkeypatch):
    """When HTTP returns 403 WAF block, server must attempt headless browser fallback."""
    def fake_get_403(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(403, text="Blocked by WAF", request=request)

    def fake_browser_fetch(url, timeout=25.0):
        return (
            "<html><body><article><h1>Rendered After WAF Bypass</h1>"
            "<p>Full article content rendered by headless Chrome.</p>"
            "</article></body></html>"
        )

    monkeypatch.setattr("server._http_get", fake_get_403)
    monkeypatch.setattr("server._fetch_html_via_browser", fake_browser_fetch)

    out = search_website("https://example.org/waf-protected")
    assert "Rendered After WAF Bypass" in out
    assert "Full article content rendered by headless Chrome." in out


def test_ddg_http_202_anomaly_triggers_ddgs_fallback_and_filters_ads(monkeypatch):
    """When DDG returns HTTP 202 anomaly-modal, fallback to ddgs and filter out ads."""
    anomaly_html = (
        '<html><body><div class="anomaly-modal__modal" data-testid="anomaly-modal">'
        "Unfortunately, bots use DuckDuckGo too. cc=botnet</div></body></html>"
    )

    def fake_post_202(url, data, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(202, text=anomaly_html, request=request)

    def fake_ddgs_fallback(query, max_results=10):
        return [
            {
                "title": "Sponsored Ad",
                "href": "https://www.bing.com/aclick?ld=123",
                "body": "Ad snippet",
            },
            {
                "title": "DDG Ad",
                "href": "https://duckduckgo.com/y.js?ad_domain=example.com",
                "body": "DDG ad snippet",
            },
            {
                "title": "Deployment Safeguards on AKS",
                "href": "https://learn.microsoft.com/en-us/azure/aks/deployment-safeguards",
                "body": "Official Azure AKS Deployment Safeguards reference.",
            },
        ]

    monkeypatch.setattr("server._http_post", fake_post_202)
    monkeypatch.setattr("server._search_ddgs_fallback", fake_ddgs_fallback, raising=False)

    out = search_website("azurepolicy k8sazurev2noprivilege deployment safeguards")
    assert "Deployment Safeguards on AKS" in out
    assert "https://learn.microsoft.com/en-us/azure/aks/deployment-safeguards" in out
    assert "bing.com/aclick" not in out
    assert "duckduckgo.com/y.js" not in out


def test_ddg_anomaly_and_ddgs_failure_returns_fail_closed_error(monkeypatch):
    """When DDG returns HTTP 202 anomaly AND ddgs fallback raises, return fail-closed ERROR."""
    anomaly_html = (
        '<html><body><div data-testid="anomaly-modal">cc=botnet</div></body></html>'
    )

    def fake_post_202(url, data, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(202, text=anomaly_html, request=request)

    def fake_ddgs_error(query, max_results=10):
        raise RuntimeError("All ddgs backends rate-limited or unreachable")

    monkeypatch.setattr("server._http_post", fake_post_202)
    monkeypatch.setattr("server._search_ddgs_fallback", fake_ddgs_error, raising=False)

    out = search_website("kaniko kubernetes non-root securityContext")
    assert out.startswith("ERROR:")
    assert "No DuckDuckGo results found" not in out


def test_ddg_empty_200_and_ddgs_no_results_returns_no_results_message(monkeypatch):
    """When both DDG (HTTP 200) and ddgs find 0 organic results without error, return No results."""
    def fake_post_200_empty(url, data, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(200, text="<html><body></body></html>", request=request)

    monkeypatch.setattr("server._http_post", fake_post_200_empty)
    monkeypatch.setattr("server._search_ddgs_fallback", lambda q, max_results=10: [])

    out = search_website("nonexistent_xyz_query_987654321")
    assert out == "No DuckDuckGo results found for query: 'nonexistent_xyz_query_987654321'."
