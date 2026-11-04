import httpx
import pymupdf
import pytest
from pydantic import ValidationError

from server import (
    SearchWebsiteInput,
    _SEARCH_CACHE,
    _URL_CACHE,
    _is_antibot_or_error_page,
    _unwrap_consent_redirect,
    search_website,
)


@pytest.fixture(autouse=True)
def _clear_session_caches():
    _SEARCH_CACHE.clear()
    _URL_CACHE.clear()
    yield
    _SEARCH_CACHE.clear()
    _URL_CACHE.clear()


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


def test_dom_cards_kleinanzeigen_strips_script_and_extracts_price_and_skips_mailto():
    """Feature 09: _extract_dom_cards strips nested <script>/<style> JSON-LD noise, skips mailto: links, extracts suffix prices ('950 € VB'), and skips wanted ('Gezocht') EUR 0.00 ads."""
    from lxml import html as lxml_html
    from server import _extract_dom_cards

    html_sample = """
    <html><body>
      <article class="aditem">
        <a href="mailto:?subject=Share"><svg>share-icon</svg></a>
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"ImageObject","creditText":"Kleinanzeigen","contentUrl":"https://img.kleinanzeigen.de/1.jpg"}</script>
        <h2 class="text-module-begin"><a href="/s-anzeige/ps5-pro-30th-anniversary/111">PlayStation 5 Pro 30th Anniversary Limited Edition</a></h2>
        <p class="aditem-main--middle--price-shipping--price">950 € VB</p>
        <p>47533 Kleve - Neu &amp; OVP versiegelt</p>
      </article>
      <article class="aditem">
        <script type="application/ld+json">{"creditText":"Kleinanzeigen"}</script>
        <h2><a href="/s-anzeige/ps5-pro-2tb/222">Sony PS5 Pro 2TB Konsole</a></h2>
        <div class="price-block">1.299,99 €</div>
        <p>46446 Emmerich am Rhein</p>
      </article>
      <article class="aditem">
        <h2><a href="/s-anzeige/gezocht-ps5/333">GEZOCHT: Wij kopen jouw PS5 voor cash</a></h2>
        <p>Direct geld</p>
      </article>
    </body></html>
    """
    tree = lxml_html.fromstring(html_sample)
    cards = _extract_dom_cards(tree, "https://www.kleinanzeigen.de")
    assert len(cards) == 2
    assert (
        cards[0]
        == "PlayStation 5 Pro 30th Anniversary Limited Edition|950 € VB|https://www.kleinanzeigen.de/s-anzeige/ps5-pro-30th-anniversary/111|950 € VB 47533 Kleve - Neu & OVP versiegelt"
    )
    assert "creditText" not in cards[0]
    assert "mailto:" not in cards[0]
    assert (
        cards[1]
        == "Sony PS5 Pro 2TB Konsole|1.299,99 €|https://www.kleinanzeigen.de/s-anzeige/ps5-pro-2tb/222|1.299,99 € 46446 Emmerich am Rhein"
    )


def test_clean_plain_text_body_strips_financing_footnotes_and_dedups_consecutive_lines():
    """Feature 09: _clean_plain_text_body strips MediaMarkt-style financing footnotes while keeping normal markdown bullets and deduplicating consecutive identical UI lines."""
    from server import _clean_plain_text_body

    raw = (
        "# PlayStation 5 Pro 2TB\n"
        "* Regular product bullet point: 2TB SSD storage included\n"
        "* Second normal bullet point: DualSense wireless controller\n"
        "Diese Variante ist in dieser Kombination nicht verfügbar.\n"
        "Diese Variante ist in dieser Kombination nicht verfügbar.\n\n"
        "Diese Variante ist in dieser Kombination nicht verfügbar.\n"
        "* 0% effektiver Jahreszins, ab € 100.- Finanzierungssumme, Ratenfinanzierung über Finanzierungspartner.\n"
        "** Ratenfinanzierung wählbar ab € 100.- (Sollzinssatz 10,37%, vorbehaltlich Kreditwürdigkeitsprüfung).\n"
        "¹ Bei Kauf erhältst du einen 10 € Einkaufscoupon (Mindesteinkaufswert 50 €).\n"
        "⁴⁸ Gesetzliche Rechte (Widerrufsrecht) bleiben unberührt.\n"
        "Final informative paragraph about local pickup in Kleve.\n"
    )
    cleaned = _clean_plain_text_body(raw, include_code=False)
    assert "* Regular product bullet point: 2TB SSD storage included" in cleaned
    assert "* Second normal bullet point: DualSense wireless controller" in cleaned
    assert (
        cleaned.count(
            "Diese Variante ist in dieser Kombination nicht verfügbar."
        )
        == 1
    )
    assert "Ratenfinanzierung" not in cleaned
    assert "Sollzinssatz" not in cleaned
    assert "Einkaufscoupon" not in cleaned
    assert "Widerrufsrecht" not in cleaned
    assert "Final informative paragraph about local pickup in Kleve." in cleaned


def test_html_to_markdown_article_body_preserved_when_unpriced_article_cards_present():
    """Feature 09: Blog articles with >= 5 unpriced <article> related-post cards in the footer preserve the full article body and do not discard it via skip_duplicate_body."""
    from server import _html_to_markdown

    related_cards = "\n".join(
        f'<article><h3><a href="/blog/post-{i}">Related PlayStation Blog Story Number {i}</a></h3><p>Read more about game {i} on our blog.</p></article>'
        for i in range(1, 8)
    )
    article_prose = (
        "Welcome to the official PlayStation 30th Anniversary celebration announcement. "
        "The PlayStation 5 Pro Limited Edition bundle includes a 2TB SSD, Wi-Fi 7 support, "
        "a DualSense Edge wireless controller, a DualSense charging station, and a vertical stand. "
        "Pre-orders open on September 26 via direct.playstation.com and participating retailers, "
        "with official release scheduled for November 21, 2024 across Europe and North America. "
        "This collector bundle is strictly limited to 12,300 individually numbered units worldwide."
    )
    blog_html = f"""
    <html>
      <body>
        <main>
          <h1>PlayStation 30th Anniversary Collection Detailed</h1>
          <p>{article_prose}</p>
        </main>
        <footer>
          {related_cards}
        </footer>
      </body>
    </html>
    """
    md = _html_to_markdown(
        blog_html, "https://blog.playstation.com/2024/09/19/30th-anniversary/"
    )
    assert md is not None
    assert "12,300 individually numbered units worldwide" in md
    assert "DualSense Edge wireless controller" in md
    assert "## Extracted Items" not in md




def test_l1_tool_call_has_no_structured_content(monkeypatch):
    """L1: search_website tool result is text-only (no duplicated structuredContent)."""
    import asyncio

    import fastmcp

    from server import mcp

    ddg_html = """
    <html><body>
      <div class="result__body">
        <a class="result__a" href="https://gofastmcp.com/docs">FastMCP Documentation</a>
        <a class="result__snippet">The fast, Pythonic way to build MCP servers.</a>
      </div>
    </body></html>
    """

    def fake_post(url, data, **kwargs):
        return httpx.Response(200, text=ddg_html, request=httpx.Request("POST", url))

    monkeypatch.setattr("server._http_post", fake_post)

    async def _call():
        async with fastmcp.Client(mcp) as client:
            return await client.call_tool("search_website", {"query_or_url": "fastmcp docs"})

    result = asyncio.run(_call())
    assert result.structured_content is None
    assert result.content[0].text == search_website("fastmcp docs")
    assert "FastMCP Documentation" in result.content[0].text


def test_alias_choices_query_and_url_and_opposite_unknown_rejected(monkeypatch):
    """bugs/05: search_website accepts query/url/q and filter/keywords aliases via FastMCP without schema bloat, while rejecting unknown keys and empty queries."""
    import asyncio

    import fastmcp
    from fastmcp.exceptions import ToolError

    from server import SearchWebsiteInput, mcp

    # Direct Pydantic model alias check
    m1 = SearchWebsiteInput.model_validate({"query": "  test query  ", "filter": "kw"})
    assert m1.query_or_url == "test query"
    assert m1.filter_query == "kw"
    m2 = SearchWebsiteInput.model_validate({"url": "https://gofastmcp.com/docs", "keywords": "FastMCP"})
    assert m2.query_or_url == "https://gofastmcp.com/docs"
    assert m2.filter_query == "FastMCP"

    ddg_html = """
    <html><body>
      <div class="result__body">
        <a class="result__a" href="https://www.nngroup.com/articles/skeleton-screens/">Skeleton Screens 101</a>
        <a class="result__snippet">Perceived performance with bento-grid-ui and dark-mode-ui.</a>
      </div>
    </body></html>
    """
    page_html = """
    <html><body>
      <main>
        <h1>FastMCP Tools Guide</h1>
        <p>FastMCP validates tool arguments via Pydantic TypeAdapter and AliasChoices.</p>
      </main>
    </body></html>
    """

    def fake_post(url, data, **kwargs):
        return httpx.Response(200, text=ddg_html, request=httpx.Request("POST", url))

    def fake_get(url, **kwargs):
        return httpx.Response(
            200,
            text=page_html,
            headers={"content-type": "text/html; charset=utf-8"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("server._http_post", fake_post)
    monkeypatch.setattr("server._http_get", fake_get)

    async def _run():
        async with fastmcp.Client(mcp) as client:
            tools = await client.list_tools()
            tool = next(t for t in tools if t.name == "search_website")
            schema = tool.input_schema if hasattr(tool, "input_schema") else tool.inputSchema
            assert schema.get("additionalProperties") is False
            assert set(schema["properties"].keys()) == {
                "query_or_url",
                "queries_or_urls",
                "filter_query",
                "include_code",
                "auto_open_top",
            }

            r_query = await client.call_tool(
                "search_website",
                {"query": "bento-grid-ui dark-mode-ui site:nngroup.com skeleton screens perceived performance"},
            )
            assert "Skeleton Screens 101" in r_query.content[0].text

            r_q = await client.call_tool("search_website", {"q": "skeleton screens"})
            assert "Skeleton Screens 101" in r_q.content[0].text

            r_url = await client.call_tool(
                "search_website",
                {"url": "https://gofastmcp.com/servers/tools", "filter": "AliasChoices"},
            )
            assert "AliasChoices" in r_url.content[0].text

            with pytest.raises(ToolError):
                await client.call_tool("search_website", {"bogus": "x"})

            with pytest.raises(ToolError):
                await client.call_tool("search_website", {"query": "   "})

    asyncio.run(_run())


def test_autonomous_pow_and_cookie_wall_retry_in_http_get(monkeypatch):
    """feature/16: _http_get autonomously solves SHA-256 /_pow/solve cookie challenges (like NCBI PMC HTTP 203) and retries on the same session without returning 'Cookies must be enabled'."""
    import hashlib
    import json

    pow_html = """
    <!doctype html>
    <html><body>
      <div id="cookie-required">
        <h1>Cookies must be enabled</h1>
        <p>Enable cookies for pmc.ncbi.nlm.nih.gov and reload this page to continue.</p>
      </div>
      <script>
        const challengeId = "test-pmc-123";
        const bits = 8;
        fetch("/_pow/solve", { method: "POST" });
      </script>
    </body></html>
    """
    article_html = """
    <html><body>
      <main>
        <h1>Wagyu Intramuscular Fat Study</h1>
        <p>Melting temperature of oleic acid in Japanese Black cattle is below 38 C.</p>
      </main>
    </body></html>
    """
    state = {"pow_solved": False, "get_calls": 0, "post_calls": 0}

    class FakeSession:
        def __init__(self):
            self.cookies = {}

        def get(self, url, **kwargs):
            state["get_calls"] += 1
            req = httpx.Request("GET", url)
            if not state["pow_solved"]:
                return httpx.Response(
                    203,
                    headers={"content-type": "text/html; charset=utf-8"},
                    text=pow_html,
                    request=req,
                )
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text=article_html,
                request=req,
            )

        def post(self, url, data=None, **kwargs):
            state["post_calls"] += 1
            assert url == "https://pmc.ncbi.nlm.nih.gov/_pow/solve"
            payload = json.loads(data)
            assert payload["challenge_id"] == "test-pmc-123"
            nonce = int(payload["nonce"])
            digest = hashlib.sha256(f"test-pmc-123:{nonce}".encode()).digest()
            assert int.from_bytes(digest, "big") >> (256 - 8) == 0
            state["pow_solved"] = True
            req = httpx.Request("POST", url)
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                text='{"success": true}',
                request=req,
            )

    fake_session = FakeSession()
    monkeypatch.setattr(
        "server._get_or_create_session", lambda profile: fake_session
    )

    out = search_website("https://pmc.ncbi.nlm.nih.gov/articles/PMC5672612/")
    assert state["pow_solved"] is True
    assert state["post_calls"] == 1
    assert state["get_calls"] == 2
    assert "Wagyu Intramuscular Fat Study" in out
    assert "Melting temperature of oleic acid" in out
    assert "Cookies must be enabled" not in out


def test_opposite_cookie_wall_all_tiers_exhausted_fails_closed(monkeypatch):
    """feature/16 opposite test: when a page returns 'Cookies must be enabled' across all HTTP attempts and Playwright fallback, or is padded >45KB with only a cookie-wall message, search_website fails closed with ERROR."""
    short_cookie_wall = (
        "<html><body><h1>Cookies must be enabled</h1>"
        "<p>Enable cookies for example.com and reload this page to continue.</p>"
        "</body></html>"
    )
    assert _is_antibot_or_error_page(
        203, short_cookie_wall, "https://example.com/locked"
    )
    assert _is_antibot_or_error_page(
        200, short_cookie_wall, "https://example.com/locked"
    )

    class AlwaysBlockedSession:
        def __init__(self):
            self.cookies = {}

        def get(self, url, **kwargs):
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text=short_cookie_wall,
                request=req,
            )

    monkeypatch.setattr(
        "server._get_or_create_session", lambda profile: AlwaysBlockedSession()
    )
    monkeypatch.setattr(
        "server._fetch_html_via_browser", lambda url, timeout=25.0: None
    )

    out_short = search_website("https://example.com/locked")
    assert out_short.startswith("ERROR:")
    assert "Cookies must be enabled" not in out_short

    padded_cookie_wall = (
        "<html><head><style>" + ("/* pad */ " * 5000) + "</style></head>"
        "<body><h1>Cookies must be enabled</h1>"
        "<p>Enable cookies for example.com and reload this page to continue.</p>"
        "</body></html>"
    )
    assert len(padded_cookie_wall) > 45000

    class PaddedBlockedSession:
        def __init__(self):
            self.cookies = {}

        def get(self, url, **kwargs):
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text=padded_cookie_wall,
                request=req,
            )

    monkeypatch.setattr(
        "server._get_or_create_session", lambda profile: PaddedBlockedSession()
    )
    out_padded = search_website("https://example.com/locked-padded")
    assert out_padded.startswith("ERROR:")
    assert "Cookies must be enabled" not in out_padded


def test_http_get_retries_with_identity_encoding_on_curl_61(monkeypatch):
    """When curl_cffi raises curl: (61) Unrecognized content encoding, _http_get retries with Accept-Encoding: identity."""
    calls: list[dict[str, str]] = []

    class FakeIdentitySession:
        def __init__(self):
            self.cookies = {}

        def get(self, url, headers=None, **kwargs):
            hdrs = dict(headers or {})
            calls.append(hdrs)
            if hdrs.get("Accept-Encoding") != "identity":
                raise RuntimeError(
                    "Failed to perform, curl: (61) Unrecognized content encoding type."
                )
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                text="200 OK [RFC9110]\n429 Too Many Requests [RFC6585]\n",
                request=req,
            )

    monkeypatch.setattr(
        "server._get_or_create_session", lambda profile: FakeIdentitySession()
    )

    out = search_website(
        "https://www.iana.org/assignments/http-status-codes/http-status-codes.txt"
    )
    assert len(calls) == 2
    assert calls[0].get("Accept-Encoding") != "identity"
    assert calls[1].get("Accept-Encoding") == "identity"
    assert "200 OK" in out
    assert "429 Too Many Requests" in out
    assert not out.startswith("ERROR:")


def test_batch_queries_or_urls_and_inline_pipe_deduplicates_urls(monkeypatch):
    """feature/17: search_website supports batching via queries_or_urls=[...] and 'q1 || q2' and deduplicates URLs across DuckDuckGo results in the same batch."""
    post_calls: list[str] = []

    def fake_post(url, data, **kwargs):
        q = data.get("q", "")
        post_calls.append(q)
        if "first" in q:
            html = """
            <html><body>
              <div class="result__body">
                <a class="result__a" href="https://shared.example.org/spec">Shared Spec</a>
                <a class="result__snippet">Shared primary standard document.</a>
              </div>
              <div class="result__body">
                <a class="result__a" href="https://only1.example.org/doc">Only First</a>
                <a class="result__snippet">First unique result.</a>
              </div>
            </body></html>
            """
        else:
            html = """
            <html><body>
              <div class="result__body">
                <a class="result__a" href="https://shared.example.org/spec">Shared Spec Duplicate</a>
                <a class="result__snippet">Duplicate URL that should be omitted in batch item 2.</a>
              </div>
              <div class="result__body">
                <a class="result__a" href="https://only2.example.org/doc">Only Second</a>
                <a class="result__snippet">Second unique result.</a>
              </div>
            </body></html>
            """
        return httpx.Response(200, text=html, request=httpx.Request("POST", url))

    monkeypatch.setattr("server._http_post", fake_post)

    out_batch = search_website(
        queries_or_urls=["ISO-NEN-IEC first query", "ISO-NEN-IEC second query"]
    )
    assert len(post_calls) == 2
    assert "\n\n---\n\n" in out_batch
    assert out_batch.count("https://shared.example.org/spec") == 1
    assert "https://only1.example.org/doc" in out_batch
    assert "https://only2.example.org/doc" in out_batch

    # Inline '||' batching hits session cache without extra HTTP calls
    out_inline = search_website(
        "ISO-NEN-IEC first query || ISO-NEN-IEC second query"
    )
    assert len(post_calls) == 2
    assert out_inline == out_batch


def test_session_search_and_url_cache_and_opposite_error_never_cached(monkeypatch):
    """feature/17: _SEARCH_CACHE and _URL_CACHE prevent duplicate HTTP requests on identical queries/URLs, while ERROR responses are never cached (opposite test)."""
    get_calls = {"ok": 0, "err": 0}

    def fake_get(url, **kwargs):
        req = httpx.Request("GET", url)
        if "fail" in url:
            get_calls["err"] += 1
            return httpx.Response(503, text="Service Unavailable", request=req)
        get_calls["ok"] += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><body><article><h1>Cached Normative Document</h1><p>Verified threshold is 42.</p></article></body></html>",
            request=req,
        )

    monkeypatch.setattr("server._http_get", fake_get)
    monkeypatch.setattr("server._fetch_html_via_browser", lambda url, timeout=25.0: None)

    out1 = search_website("https://example.org/cached-doc")
    out2 = search_website("https://example.org/cached-doc")
    assert out1 == out2
    assert "Cached Normative Document" in out1
    assert get_calls["ok"] == 1

    # Opposite test: ERROR response is never cached and retries on next call
    err1 = search_website("https://example.org/fail-doc")
    err2 = search_website("https://example.org/fail-doc")
    assert err1.startswith("ERROR:")
    assert err2.startswith("ERROR:")
    assert get_calls["err"] == 2


def test_feature18_rfc3986_normalize_cache_url_and_sorted_filter_key(monkeypatch):
    """feature/18: _normalize_cache_url normalizes scheme/host case, default ports, unreserved %XX, #fragment, and trailing slash; _normalize_filter_key normalizes token order; different functional query params do not collide (opposite test)."""
    from server import _normalize_cache_url, _normalize_filter_key

    u1 = _normalize_cache_url("HTTPS://Example.ORG:443/docs/%7Euser/spec/?utm_source=x&id=1#section-4")
    u2 = _normalize_cache_url("https://example.org/docs/~user/spec?id=1#other-fragment")
    assert u1 == "https://example.org/docs/~user/spec?id=1"
    assert u1 == u2

    # Opposite check: distinct functional query parameters stay distinct
    u_diff = _normalize_cache_url("https://example.org/docs/~user/spec?id=2")
    assert u1 != u_diff

    assert _normalize_filter_key("RFC 3986, URI! normalization") == _normalize_filter_key(
        "normalization uri rfc 3986"
    )

    get_calls = {"count": 0}

    def fake_get(url, **kwargs):
        get_calls["count"] += 1
        req = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><body><article>"
                "<h1>RFC 3986 URI Generic Syntax</h1>"
                "<p>Section 6 defines normalization and comparison of URI references.</p>"
                "</article></body></html>"
            ),
            request=req,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    out1 = search_website(
        "HTTPS://Example.ORG:443/rfc/rfc3986/#section-6",
        filter_query="normalization comparison",
    )
    out2 = search_website(
        "https://example.org/rfc/rfc3986#section-2",
        filter_query="comparison, Normalization!",
    )
    assert out1 == out2
    assert get_calls["count"] == 1


def test_feature18_toc_dotted_lines_and_rfc_footer_stripped_and_batch_scaling(monkeypatch):
    """feature/18: _clean_plain_text_body strips ToC dotted lines and RFC page headers/footers while keeping normal numbered sentences (opposite test); batch mode scales blocks/headings/DDG results without character slicing."""
    from server import _clean_plain_text_body

    raw_rfc = (
        "1. Introduction .................................................... 4\n"
        "6.2.2. Syntax-Based Normalization . . . . . . . . . . . . . . . . . 39\n"
        "Berners-Lee, et al.         Standards Track                    [Page 39]\n"
        "Section 6.2.2 states that case normalization applies to scheme and host.\n"
        "Wait 5 seconds before retrying port 443.\n"
    )
    cleaned = _clean_plain_text_body(raw_rfc, include_code=False)
    assert "1. Introduction" not in cleaned
    assert "6.2.2. Syntax-Based Normalization" not in cleaned
    assert "[Page 39]" not in cleaned
    assert "Section 6.2.2 states that case normalization applies to scheme and host." in cleaned
    assert "Wait 5 seconds before retrying port 443." in cleaned

    # Batch scaling test: 4 URLs with 25 matching paragraphs each + H4 headings
    paragraphs = "\n\n".join(
        f"<h4>Subheading {i}</h4><p>Normative token budget requirement paragraph number {i} with complete unclipped sentence.</p>"
        for i in range(1, 26)
    )
    big_html = f"<html><body><article><h1>Main Spec</h1>{paragraphs}</article></body></html>"

    def fake_get(url, **kwargs):
        req = httpx.Request("GET", url)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=big_html,
            request=req,
        )

    monkeypatch.setattr("server._http_get", fake_get)

    batch_urls = [
        f"https://example.org/spec-{idx} token budget"
        for idx in range(1, 5)
    ]
    batch_out = search_website(queries_or_urls=batch_urls)
    assert "## Filtered Matches (8 of " in batch_out
    assert "blocks matching `token budget`" in batch_out
    assert "with complete unclipped sentence." in batch_out
    assert "#### Subheading" not in batch_out
    assert len(batch_out.encode("utf-8")) <= 10240


def test_feature19_auto_open_top_authority_ranking_and_failover(monkeypatch):
    """feature/19 (Upgrade 1): auto_open_top and inline 'open:' rank primary authority domains (Tier 1 > Tier 2 > Tier 3) and fail over to hit #2 if hit #1 returns ERROR."""
    from server import _rank_primary_authority_urls

    candidates = [
        {"href": "https://medium.com/random-blog/http-caching"},
        {"href": "https://github.com/org/repo/blob/main/README.md"},
        {"href": "https://www.rfc-editor.org/rfc/rfc9111"},
    ]
    ranked = _rank_primary_authority_urls(candidates)
    assert ranked == [
        "https://www.rfc-editor.org/rfc/rfc9111",
        "https://github.com/org/repo/blob/main/README.md",
        "https://medium.com/random-blog/http-caching",
    ]

    ddg_html = """
    <html><body>
      <div class="result__body">
        <a class="result__a" href="https://medium.com/blog/caching">Blog Post</a>
        <a class="result__snippet">Secondary blog post about caching.</a>
      </div>
      <div class="result__body">
        <a class="result__a" href="https://www.rfc-editor.org/rfc/rfc9111-broken">Broken Tier 1</a>
        <a class="result__snippet">Broken link that fails with 403.</a>
      </div>
      <div class="result__body">
        <a class="result__a" href="https://datatracker.ietf.org/doc/html/rfc9111">RFC 9111 HTTP Caching</a>
        <a class="result__snippet">Normative IETF HTTP Caching specification.</a>
      </div>
    </body></html>
    """

    def fake_post(url, data, **kwargs):
        return httpx.Response(200, text=ddg_html, request=httpx.Request("POST", url))

    fetched_urls: list[str] = []

    def fake_get(url, **kwargs):
        fetched_urls.append(url)
        req = httpx.Request("GET", url)
        if "broken" in url:
            return httpx.Response(403, text="Forbidden", request=req)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><body><article>"
                "<h1>RFC 9111 Section 4.3 Validation</h1>"
                "<p>The If-None-Match header field makes a request method conditional on ETag revalidation.</p>"
                "</article></body></html>"
            ),
            request=req,
        )

    monkeypatch.setattr("server._http_post", fake_post)
    monkeypatch.setattr("server._http_get", fake_get)
    monkeypatch.setattr("server._fetch_html_via_browser", lambda url, timeout=25.0: None)

    out = search_website("open: IETF-RFC RFC 9111 ETag revalidation")
    assert "# DuckDuckGo Search Results for: `IETF-RFC RFC 9111 ETag revalidation`" in out
    assert "# Source: https://datatracker.ietf.org/doc/html/rfc9111" in out
    assert "If-None-Match header field makes a request method conditional" in out
    # Tier 1 broken URL was tried first, then failed over to Tier 1 datatracker.ietf.org (skipping Tier 3 medium.com!)
    assert fetched_urls == [
        "https://www.rfc-editor.org/rfc/rfc9111-broken",
        "https://datatracker.ietf.org/doc/html/rfc9111",
    ]


def test_feature19_batch_byte_budget_slack_redistribution_and_ddgs_snippet_guard(monkeypatch):
    """feature/19 (Upgrade 2): _clean_ddgs_snippet deduplicates repeated multi-card sentences within <=380 B without mid-sentence cuts, and batch mode enforces <=9,500 B with slack redistribution."""
    from server import _clean_ddgs_snippet

    repeated_body = (
        "Lost in the Middle shows U-shaped performance on long contexts. "
        "Lost in the Middle shows U-shaped performance on long contexts. "
        "Models retrieve best from the very beginning and very end of the input window. "
        + ("Extra card sentence number X with unrelated metadata that would bloat the snippet past 380 bytes easily. " * 6)
    )
    cleaned_snip = _clean_ddgs_snippet(repeated_body, max_bytes=380)
    assert len(cleaned_snip.encode("utf-8")) <= 380
    assert cleaned_snip.count("Lost in the Middle shows U-shaped performance") == 1
    assert cleaned_snip.endswith(".")

    # Opposite check: a single long first sentence (>380 B) is never cut mid-sentence
    long_single_sentence = "A" * 420 + " complete ending."
    kept_single = _clean_ddgs_snippet(long_single_sentence, max_bytes=380)
    assert kept_single == long_single_sentence

    # Batch budget test: 1 short DDG search + 3 very large unfiltered URLs (each ~12 KB raw)
    def fake_post(url, data, **kwargs):
        html = """
        <html><body>
          <div class="result__body">
            <a class="result__a" href="https://sqlite.org/wal.html">SQLite WAL</a>
            <a class="result__snippet">Write-Ahead Logging mode in SQLite.</a>
          </div>
        </body></html>
        """
        return httpx.Response(200, text=html, request=httpx.Request("POST", url))

    long_blocks = "\n\n".join(
        f"<h2>Section {i}</h2><p>Normative specification paragraph {i} about sqlite wal concurrency and checkpointing with a complete ending sentence.</p>"
        for i in range(1, 60)
    )
    huge_html = f"<html><body><article><h1>SQLite WAL Spec</h1>{long_blocks}</article></body></html>"

    def fake_get(url, **kwargs):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=huge_html,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("server._http_post", fake_post)
    monkeypatch.setattr("server._http_get", fake_get)

    batch_res = search_website(
        queries_or_urls=[
            "Python-stdlib sqlite wal mode",
            "https://sqlite.org/wal-spec-1",
            "https://sqlite.org/wal-spec-2",
            "https://sqlite.org/wal-spec-3",
        ]
    )
    total_bytes = len(batch_res.encode("utf-8"))
    assert total_bytes <= 9500
    assert "with a complete ending sentence." in batch_res


def test_feature19_sqlite_wal_cache_rfc9111_etag_304_and_session_delta_reslicing(monkeypatch, tmp_path):
    """feature/19 (Upgrade 5): SQLite WAL persists cached pages across memory eviction, revalidates expired entries via If-None-Match/304, omits already-shown blocks & ToC on 2nd filter_query in same session, and never caches ERROR responses (opposite test)."""
    db_file = tmp_path / "test_web_cache.sqlite3"
    monkeypatch.setenv("WEB_SEARCH_CACHE_DB", str(db_file))
    _URL_CACHE.clear()

    state = {"get_calls": 0, "last_headers": {}, "return_304": False}
    doc_html = (
        "<html><body><article>"
        "<h1>RFC 9111 Caching</h1>"
        "<h2>Freshness Lifetime</h2>"
        "<p>Shared paragraph about freshness lifetime and ETag validation in HTTP caches.</p>"
        "<h2>Validation Model</h2>"
        "<p>Unique second paragraph explaining If-None-Match 304 Not Modified validation responses.</p>"
        "</article></body></html>"
    )

    def fake_get(url, **kwargs):
        state["get_calls"] += 1
        state["last_headers"] = dict(kwargs.get("extra_headers") or {})
        req = httpx.Request("GET", url)
        if "broken-500" in url:
            return httpx.Response(500, text="Internal Server Error", request=req)
        if state["return_304"]:
            return httpx.Response(304, headers={"etag": '"v1-rfc9111"'}, text="", request=req)
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "etag": '"v1-rfc9111"',
            },
            text=doc_html,
            request=req,
        )

    monkeypatch.setattr("server._http_get", fake_get)
    monkeypatch.setattr("server._fetch_html_via_browser", lambda url, timeout=25.0: None)

    # 1. First filtered call fetches from network and populates SQLite WAL + _SESSION_SENT_BLOCKS
    out1 = search_website("https://www.rfc-editor.org/rfc/rfc9111", filter_query="freshness")
    assert state["get_calls"] == 1
    assert "## Page Headings Index" in out1
    assert "Shared paragraph about freshness lifetime" in out1

    # 2. Second filtered call on SAME URL with DIFFERENT filter_query in same session:
    #    0 network calls (served from SQLite WAL) AND omits ToC + already-shown block!
    out2 = search_website("https://www.rfc-editor.org/rfc/rfc9111", filter_query="validation")
    assert state["get_calls"] == 1
    assert "## Page Headings Index" not in out2
    assert "Shared paragraph about freshness lifetime" not in out2
    assert "Unique second paragraph explaining If-None-Match 304 Not Modified" in out2
    assert "already-shown blocks & ToC omitted for this URL in current session" in out2

    # 3. Simulate process restart (evict in-memory dict only) + expire SQLite row to test RFC 9111 ETag -> 304
    dict.clear(_URL_CACHE)
    from server import _SESSION_SENT_BLOCKS, _get_sqlite_conn

    _SESSION_SENT_BLOCKS.clear()
    conn = _get_sqlite_conn()
    assert conn is not None
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert str(mode).lower() == "wal"
    conn.execute("UPDATE http_cache SET expires_at = 1.0")
    conn.commit()

    state["return_304"] = True
    out3 = search_website("https://www.rfc-editor.org/rfc/rfc9111", filter_query="freshness")
    assert state["get_calls"] == 2
    assert state["last_headers"].get("If-None-Match") == '"v1-rfc9111"'
    assert "Shared paragraph about freshness lifetime" in out3

    # 4. Opposite test: ERROR response is never stored in SQLite http_cache
    err_out = search_website("https://www.rfc-editor.org/rfc/broken-500")
    assert err_out.startswith("ERROR:")
    cur = conn.execute(
        "SELECT COUNT(*) FROM http_cache WHERE norm_url LIKE '%broken-500%'"
    )
    assert cur.fetchone()[0] == 0


def test_feature20_search_website_json_schema_under_3100_bytes():
    """feature/20: search_website FastMCP tool schema and search_website.json stay strictly <= 3,100 B while preserving mandatory ## Search keywords rules."""
    import asyncio
    import json
    from pathlib import Path
    import fastmcp
    from server import mcp

    async def _check():
        async with fastmcp.Client(mcp) as client:
            tools = await client.list_tools()
            t = next(x for x in tools if x.name == "search_website")
            schema = t.input_schema if hasattr(t, "input_schema") else t.inputSchema
            obj = {"name": t.name, "description": t.description, "parameters": schema}
            dumped = json.dumps(obj, separators=(",", ":"), sort_keys=False)
            dumped = dumped.replace("<", "\\u003c").replace(">", "\\u003e")
            return dumped

    schema_str = asyncio.run(_check())
    assert len(schema_str.encode("utf-8")) <= 3100
    assert "## Search keywords" in schema_str
    assert "auto_open_top" in schema_str
    assert "filter_query" in schema_str
    assert "queries_or_urls" in schema_str

    schema_file = Path(__file__).resolve().parents[1] / "search_website.json"
    assert schema_file.is_file()
    assert len(schema_file.read_bytes()) <= 3100





