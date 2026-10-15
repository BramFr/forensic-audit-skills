import httpx
import pymupdf
import pytest
from pydantic import ValidationError

from server import SearchWebsiteInput, search_website


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
    """Fault injection: HTTP 403 and network timeouts must return explicit ERROR messages."""
    def fake_get_403(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(403, text="Forbidden", request=request)

    monkeypatch.setattr("server._http_get", fake_get_403)
    out_403 = search_website("https://example.org/blocked")
    assert "ERROR" in out_403
    assert "403" in out_403

    def fake_get_timeout(url, **kwargs):
        raise httpx.ConnectTimeout("Connection timed out")

    monkeypatch.setattr("server._http_get", fake_get_timeout)
    out_timeout = search_website("https://example.org/timeout")
    assert "ERROR" in out_timeout
    assert "Connection timed out" in out_timeout
