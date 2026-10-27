import httpx
import pymupdf
import pytest
from pydantic import ValidationError

from server import (
    SearchWebsiteInput,
    _is_antibot_or_error_page,
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
    """Contract must enforce extra='forbid', support filter_query, and reject empty input."""
    valid = SearchWebsiteInput(query_or_url="python fastmcp")
    assert valid.query_or_url == "python fastmcp"
    assert valid.filter_query is None

    with_filter = SearchWebsiteInput(
        query_or_url="https://www.coolblue.nl/home-cinema-sets",
        filter_query="Sonos",
    )
    assert with_filter.filter_query == "Sonos"

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
    monkeypatch.setattr(
        "server._fetch_html_via_browser", lambda url, timeout=25.0: None
    )
    out_403 = search_website("https://example.org/blocked")
    assert "ERROR" in out_403
    assert "403" in out_403

    def fake_get_timeout(url, **kwargs):
        raise httpx.ConnectTimeout("Connection timed out")

    monkeypatch.setattr("server._http_get", fake_get_timeout)
    out_timeout = search_website("https://example.org/timeout")
    assert "ERROR" in out_timeout
    assert "Connection timed out" in out_timeout


def test_opposite_antibot_something_went_wrong_never_fake_green(monkeypatch):
    """Opposite test: eBay/Akamai 'Something went wrong on our end' page must fail closed with ERROR."""
    ebay_error_html = (
        "<html><head><title>Error Page | eBay</title></head>"
        "<body><h1>SORRY</h1><p>Something went wrong on our end</p>"
        "<p>0.6b661702.1792995278.8668249</p>"
        "<p>Please go back and try again.</p></body></html>"
    )
    assert _is_antibot_or_error_page(
        200, ebay_error_html, "https://www.ebay.nl/sch/i.html"
    )
    assert _is_antibot_or_error_page(
        200,
        "<html><head><title>Sorry voor de onderbreking...</title></head></html>",
        "https://www.ebay.nl/splashui/challenge?ap=1",
    )

    def fake_get_soft_block(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=ebay_error_html,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get_soft_block)
    monkeypatch.setattr(
        "server._fetch_html_via_browser",
        lambda url, timeout=25.0: ebay_error_html,
    )

    out = search_website(
        "https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15"
    )
    assert out.startswith("ERROR:")
    assert "Something went wrong on our end" not in out


def test_layer_a_json_ld_itemlist_extraction(monkeypatch):
    """Layer A: JSON-LD ItemList/Product catalog pages (like Coolblue) must extract all products & prices."""
    coolblue_html = """
    <html>
      <head>
        <title>Home cinema sets | Coolblue</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "ItemList",
          "itemListElement": [
            {
              "@type": "ListItem",
              "position": 1,
              "item": {
                "@type": "Product",
                "name": "Sonos Arc Ultra + Era 300 Home Cinema Set Zwart",
                "url": "/product/956406/sonos-arc-ultra.html",
                "offers": {
                  "@type": "Offer",
                  "price": 2669,
                  "priceCurrency": "EUR",
                  "availability": "https://schema.org/InStock"
                }
              }
            },
            {
              "@type": "ListItem",
              "position": 2,
              "item": {
                "@type": "Product",
                "name": "Sony Bravia Theatre System 6 Zwart",
                "url": "/product/961843/sony-bravia.html",
                "offers": {
                  "@type": "Offer",
                  "price": 499,
                  "priceCurrency": "EUR",
                  "availability": "https://schema.org/InStock"
                }
              }
            }
          ]
        }
        </script>
      </head>
      <body><p>Met een home cinema set haal je krachtig geluid in huis.</p></body>
    </html>
    """

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=coolblue_html,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out = search_website("https://www.coolblue.nl/home-cinema-sets")
    assert "## Extracted Items (2)" in out
    assert "Sonos Arc Ultra + Era 300 Home Cinema Set Zwart" in out
    assert "EUR 2669" in out
    assert "Sony Bravia Theatre System 6 Zwart" in out
    assert "EUR 499" in out


def test_layer_b_hydration_next_data_extraction_and_inline_filter(monkeypatch):
    """Layer B: __NEXT_DATA__ listings (like Marktplaats) must be extracted and filterable inline."""
    mp_html = """
    <html>
      <head><title>Marktplaats Venray</title></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "listings": [
                {
                  "itemId": "m1",
                  "title": "Dexcom G7 45 per stuk",
                  "vipUrl": "/v/diversen/m1-dexcom-g7",
                  "priceInfo": {"priceCents": 4500, "priceType": "FIXED"},
                  "location": {"cityName": "Venray"},
                  "description": "10 voor 440 euro nieuw"
                },
                {
                  "itemId": "m2",
                  "title": "Professionele dakdekker Limburg",
                  "vipUrl": "/v/diensten/m2-dakdekker",
                  "priceInfo": {"priceCents": 0, "priceType": "RESERVED"},
                  "location": {"cityName": "Venray"},
                  "description": "Voor al uw platte en pannendaken in Venray"
                }
              ]
            }
          }
        }
        </script>
        <p>Ontdek Venray op Marktplaats.</p>
      </body>
    </html>
    """

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=mp_html,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out_all = search_website("https://www.marktplaats.nl/q/venray/")
    assert "## Extracted Items (2)" in out_all
    assert "#schema:title|price|url|details" in out_all
    assert "Dexcom G7 45 per stuk" in out_all
    assert "EUR 45.00" in out_all
    assert "Professionele dakdekker Limburg" in out_all

    out = search_website("https://www.marktplaats.nl/q/venray/ dakdekker")
    assert "## Page Headings Index" in out
    assert "## Extracted Items (2)" in out
    assert "blocks matching `dakdekker`" in out
    assert "Professionele dakdekker Limburg" in out
    assert "Dexcom G7 45 per stuk" not in out
    assert "\n\n---\n\n" not in out


def test_layer_c_dom_cards_and_site_fallback_on_zero_matches(monkeypatch):
    """Layer C: DOM cards (like eBay .s-card) extract cleanly, and 0 filter matches trigger site: fallback."""
    ebay_html = """
    <html>
      <head><title>Nvidia tesla p40 | eBay</title></head>
      <body>
        <ul>
          <li class="s-card">
            <div class="s-card__title">Shop on eBay</div>
            <a href="https://ebay.com/itm/123456">Brand New $20.00</a>
          </li>
          <li class="s-card">
            <div class="s-card__title">Nvidia Tesla P40 24GB GDDR5 GPU Server CardNieuw venster of tabblad</div>
            <a href="https://www.ebay.nl/itm/404448529212">Bekijk item</a>
            <span>Tweedehands | EUR 245,00 | Gratis verzending drosnopseG</span>
          </li>
        </ul>
      </body>
    </html>
    """

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=ebay_html,
            request=request,
        )

    def fake_ddg_search(query: str) -> str:
        return f"# DuckDuckGo Search Results for: `{query}`\n## 1. [MI50 32GB](https://www.ebay.nl/itm/999)"

    monkeypatch.setattr("server._http_get", fake_get)
    monkeypatch.setattr("server._search_duckduckgo", fake_ddg_search)

    out_direct = search_website(
        "https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15"
    )
    assert "Nvidia Tesla P40 24GB GDDR5 GPU Server Card" in out_direct
    assert "EUR 245,00" in out_direct
    assert "itm/123456" not in out_direct
    assert "Nieuw venster of tabblad" not in out_direct
    assert "drosnopseG" not in out_direct

    out_fallback = search_website(
        "https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15",
        filter_query="instinct mi50",
    )
    assert "0 direct matches on page; `site:ebay.nl` fallback below" in out_fallback
    assert "site:ebay.nl instinct mi50" in out_fallback


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
    assert (
        target_url
        == "https://tweakers.net/privacygate-confirm?redirectUri=%2F"
    )


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
    monkeypatch.setattr(
        "server._search_ddgs_fallback", fake_ddgs_fallback, raising=False
    )

    out = search_website(
        "azurepolicy k8sazurev2noprivilege deployment safeguards"
    )
    assert "Deployment Safeguards on AKS" in out
    assert (
        "https://learn.microsoft.com/en-us/azure/aks/deployment-safeguards"
        in out
    )
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
    monkeypatch.setattr(
        "server._search_ddgs_fallback", fake_ddgs_error, raising=False
    )

    out = search_website("kaniko kubernetes non-root securityContext")
    assert out.startswith("ERROR:")
    assert "No DuckDuckGo results found" not in out


def test_ddg_empty_200_and_ddgs_no_results_returns_no_results_message(monkeypatch):
    """When both DDG (HTTP 200) and ddgs find 0 organic results without error, return No results."""
    def fake_post_200_empty(url, data, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(200, text="<html><body></body></html>", request=request)

    monkeypatch.setattr("server._http_post", fake_post_200_empty)
    monkeypatch.setattr(
        "server._search_ddgs_fallback", lambda q, max_results=10: []
    )

    out = search_website("nonexistent_xyz_query_987654321")
    assert (
        out
        == "No DuckDuckGo results found for query: 'nonexistent_xyz_query_987654321'."
    )


def test_code_and_plain_text_preserves_inline_code_values(monkeypatch):
    """Tip 3 & 4 + bugs/04: include_code=False keeps inline <code> and visible <pre> code as plain text without ``` fences, strips <script>/<style>, inline URLs and trailing '#'; include_code=True keeps ``` fences."""
    html_doc = (
        "<html><head><style>.hidden { display: none; }</style>"
        "<script>const secretToken = 'xyz_hidden_js';</script></head>"
        "<body><article>"
        "<h1>FastMCP Guide<a href='#fastmcp-guide'>#</a></h1>"
        "<p>Timeout is <code>30.0</code> seconds with "
        "<a href=\"https://example.org/x\">inline link</a> and <strong>bold text</strong>.</p>"
        "<pre><code># define document and load it with LXML\ndef big_block(): pass</code></pre>"
        "</article></body></html>"
    )

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=html_doc,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out_no_code = search_website("https://example.org/docs")
    assert "# FastMCP Guide" in out_no_code
    assert "# FastMCP Guide#" not in out_no_code
    assert "30.0" in out_no_code
    assert "inline link" in out_no_code
    assert "bold text" in out_no_code
    assert "# define document and load it with LXML" in out_no_code
    assert "def big_block(): pass" in out_no_code
    assert "```" not in out_no_code
    assert "secretToken" not in out_no_code
    assert "display: none" not in out_no_code
    assert "https://example.org/x" not in out_no_code
    assert "[#]" not in out_no_code

    out_with_code = search_website(
        "https://example.org/docs", include_code=True
    )
    assert "30.0" in out_with_code
    assert "# define document and load it with LXML" in out_with_code
    assert "def big_block(): pass" in out_with_code
    assert "```" in out_with_code


def test_tip1_filter_omits_duplicate_raw_body_and_keeps_headings_index(monkeypatch):
    """Tip 1: _apply_content_filter returns Page Headings Index + Filtered Matches without appending full raw page."""
    html_doc = (
        "<html><body><article>"
        "<h1>Architecture Overview</h1>"
        "<p>Unrelated introductory paragraph with lots of prose that does not match.</p>"
        "<h2>Token Budget Controls</h2>"
        "<p>Enforce strict timeout budgets of 30 seconds on every outbound request.</p>"
        "</article></body></html>"
    )

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=html_doc,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out = search_website(
        "https://example.org/arch", filter_query="timeout budgets"
    )
    assert "## Page Headings Index" in out
    assert "## Filtered Matches (" in out
    assert "blocks matching `timeout budgets`" in out
    assert "Enforce strict timeout budgets of 30 seconds" in out
    assert "Unrelated introductory paragraph" not in out
    assert "\n\n---\n\n" not in out


def test_tip2_and_tip5_dsv_schema_and_tracking_url_cleanup(monkeypatch):
    """Tip 2 & 5: DDG and Extracted Items use #schema: Pipe-DSV and strip tracking query params."""
    ddg_html = """
    <html><body>
      <div class="result__body">
        <a class="result__a" href="https://example.org/item?id=42&utm_source=ddg&fbclid=abc123">Pipe | Title</a>
        <a class="result__snippet">Snippet with | pipe and clean URL.</a>
      </div>
    </body></html>
    """

    def fake_post(url, data, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(200, text=ddg_html, request=request)

    monkeypatch.setattr("server._http_post", fake_post)

    out = search_website("pipe dsv test")
    assert "#schema:idx|title|url|snippet" in out
    assert r"1|Pipe \| Title|https://example.org/item?id=42|Snippet with \| pipe and clean URL." in out
    assert "utm_source" not in out
    assert "fbclid" not in out


def test_tip6_catalog_dedup_omits_duplicate_trafilatura_body_when_5_or_more_items(monkeypatch):
    """Tip 6: When >= 5 structured items are extracted, omit duplicate trafilatura body below Extracted Items."""
    items_json = ", ".join(
        f'{{"@type": "ListItem", "position": {i}, "item": {{"@type": "Product", "name": "GPU Card Model {i}", '
        f'"url": "/itm/{100 + i}?hash=item123&itmprp=enc456&id={i}", '
        f'"offers": {{"@type": "Offer", "price": {200 + i}, "priceCurrency": "EUR"}}}}}}'
        for i in range(1, 7)
    )
    catalog_html = f"""
    <html>
      <head>
        <script type="application/ld+json">
        {{"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [{items_json}]}}
        </script>
      </head>
      <body>
        <article>
          <h1>Duplicate Catalog Body Heading</h1>
          <p>Duplicate SEO footer text repeating GPU Card Model 1 through 6.</p>
        </article>
      </body>
    </html>
    """

    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=catalog_html,
            request=request,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out = search_website("https://www.ebay.nl/sch/i.html")
    assert "## Extracted Items (6)" in out
    assert "#schema:title|price|url|details" in out
    assert "GPU Card Model 1|EUR 201|https://www.ebay.nl/itm/101?id=1|" in out
    assert "hash=" not in out
    assert "itmprp=" not in out
    assert "Duplicate SEO footer text" not in out


def test_tip7_strip_ui_boilerplate_and_ascii_boxes():
    """Tip 7: _clean_plain_text_body strips UI button lines and Unicode/ASCII box lines while preserving prose."""
    from server import _clean_plain_text_body

    raw = (
        "# Section Title #\n"
        "Copy\n"
        "Copied!\n"
        "Ask AI\n"
        "┌────────────────────┐\n"
        "│ Boxed diagram line │\n"
        "└────────────────────┘\n"
        "Normative paragraph that must remain intact.\n"
        "Was this page helpful?\n"
        "Edit this page\n"
    )
    cleaned = _clean_plain_text_body(raw, include_code=False)
    assert "# Section Title" in cleaned
    assert "# Section Title #" not in cleaned
    assert "Normative paragraph that must remain intact." in cleaned
    assert "Copy" not in cleaned
    assert "Ask AI" not in cleaned
    assert "Boxed diagram line" not in cleaned
    assert "Was this page helpful?" not in cleaned

