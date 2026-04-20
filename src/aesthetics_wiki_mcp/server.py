"""Aesthetics Wiki MCP server.

Exposes the Aesthetics Wiki (aesthetics.fandom.com) to LLMs via the MCP protocol.
Backed by the MediaWiki API; HTML is cleaned into readable markdown-like text.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag
from mcp.server.fastmcp import FastMCP

API_URL = "https://aesthetics.fandom.com/api.php"
WIKI_URL = "https://aesthetics.fandom.com/wiki/"
USER_AGENT = "aesthetics-wiki-mcp/0.1 (https://github.com/leonardoca1/aesthetics-wiki-mcp)"
REQUEST_TIMEOUT = 20.0

mcp = FastMCP("aesthetics-wiki")


async def _api_get(params: dict[str, Any]) -> dict[str, Any]:
    """Call the MediaWiki API with shared defaults."""
    query = {"format": "json", "formatversion": "2", **params}
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        resp = await client.get(API_URL, params=query)
        resp.raise_for_status()
        return resp.json()


def _page_url(title: str) -> str:
    return WIKI_URL + quote(title.replace(" ", "_"))


def _clean_html_to_text(html: str, max_chars: int = 6000) -> str:
    """Extract readable text from a MediaWiki page HTML blob.

    Strips infoboxes, navigation, references, galleries, and edit links.
    Preserves section headings and paragraphs as lightweight markdown.
    """
    soup = BeautifulSoup(html, "html.parser")

    root = soup.select_one(".mw-parser-output") or soup

    junk_selectors = [
        ".mbox",
        ".cw-mobile-box",
        ".infobox",
        ".portable-infobox",
        ".navbox",
        ".toc",
        ".mw-editsection",
        ".reference",
        ".references",
        ".gallery",
        ".thumb",
        ".image",
        "figure",
        "table",
        "style",
        "script",
        "sup.reference",
        ".noprint",
        ".hatnote",
    ]
    for sel in junk_selectors:
        for node in root.select(sel):
            node.decompose()

    for a in root.find_all("a"):
        a.replace_with(NavigableString(a.get_text(" ", strip=True)))

    lines: list[str] = []
    for el in root.children:
        if isinstance(el, NavigableString):
            continue
        if not isinstance(el, Tag):
            continue
        name = el.name
        if name in {"h2", "h3", "h4"}:
            heading = el.get_text(" ", strip=True)
            if heading and heading.lower() not in {"references", "gallery", "contents"}:
                level = {"h2": "##", "h3": "###", "h4": "####"}[name]
                lines.append(f"\n{level} {heading}\n")
        elif name == "p":
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(text)
        elif name in {"ul", "ol"}:
            for li in el.find_all("li", recursive=False):
                item = li.get_text(" ", strip=True)
                if item:
                    lines.append(f"- {item}")

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"

    return text


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    }
)
async def search_aesthetic(query: str, limit: int = 10) -> dict[str, Any]:
    """Search the Aesthetics Wiki for pages matching a query.

    Args:
        query: Free-text search (e.g. "cottagecore", "dark academia", "y2k").
        limit: Max number of results (1-50). Default 10.

    Returns:
        A dict with `results`: list of {title, pageid, snippet, url}.
    """
    limit = max(1, min(int(limit), 50))
    data = await _api_get({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "srprop": "snippet",
    })
    hits = data.get("query", {}).get("search", [])
    results = []
    for h in hits:
        snippet = re.sub(r"<[^>]+>", "", h.get("snippet", "")).strip()
        results.append({
            "title": h["title"],
            "pageid": h["pageid"],
            "snippet": snippet,
            "url": _page_url(h["title"]),
        })
    return {"query": query, "count": len(results), "results": results}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    }
)
async def get_aesthetic(name: str, max_chars: int = 6000) -> dict[str, Any]:
    """Fetch the cleaned content of an aesthetic's wiki page.

    Args:
        name: Page title (e.g. "Cottagecore", "Dark Academia"). Case-insensitive,
              underscores or spaces both work.
        max_chars: Soft cap on returned text length. Default 6000.

    Returns:
        A dict with `title`, `url`, `summary` (cleaned markdown-like text),
        and `main_image` (URL of the lead image if available).
    """
    data = await _api_get({
        "action": "parse",
        "page": name,
        "prop": "text|images|displaytitle",
        "redirects": 1,
    })

    if "error" in data:
        err = data["error"]
        return {
            "error": err.get("info", "Page not found"),
            "code": err.get("code", "unknown"),
            "suggestion": f"Try search_aesthetic(query='{name}') to find the correct title.",
        }

    parse = data.get("parse", {})
    title = parse.get("title", name)
    html = parse.get("text", "")
    summary = _clean_html_to_text(html, max_chars=max_chars)

    main_image: str | None = None
    images = parse.get("images", [])
    if images:
        first_image = images[0]
        img_data = await _api_get({
            "action": "query",
            "titles": f"File:{first_image}",
            "prop": "imageinfo",
            "iiprop": "url",
        })
        pages = img_data.get("query", {}).get("pages", [])
        if pages:
            info = pages[0].get("imageinfo", [])
            if info:
                main_image = info[0].get("url")

    return {
        "title": title,
        "url": _page_url(title),
        "summary": summary,
        "main_image": main_image,
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    }
)
async def list_related(name: str, limit: int = 20) -> dict[str, Any]:
    """List aesthetics linked from a given page — useful for discovering neighbors.

    Args:
        name: Source page title (e.g. "Cottagecore").
        limit: Max number of related pages (1-100). Default 20.

    Returns:
        A dict with `source` and `related`: list of {title, url}.
    """
    limit = max(1, min(int(limit), 100))
    data = await _api_get({
        "action": "query",
        "titles": name,
        "prop": "links",
        "pllimit": limit,
        "plnamespace": 0,
        "redirects": 1,
    })
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return {"source": name, "related": [], "error": "Page not found"}

    page = pages[0]
    if page.get("missing"):
        return {
            "source": name,
            "related": [],
            "error": f"Page '{name}' does not exist.",
            "suggestion": f"Try search_aesthetic(query='{name}').",
        }

    links = page.get("links", [])
    related = [{"title": l["title"], "url": _page_url(l["title"])} for l in links]
    return {"source": page.get("title", name), "count": len(related), "related": related}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    }
)
async def get_aesthetic_images(name: str, limit: int = 12) -> dict[str, Any]:
    """Get image URLs from an aesthetic's wiki page — perfect for moodboards.

    Args:
        name: Page title (e.g. "Cottagecore", "Dark Academia").
        limit: Max number of images (1-50). Default 12.

    Returns:
        A dict with `source`, `url`, and `images`: list of {filename, url, description_url}.
        Excludes tiny icons and SVG placeholders.
    """
    limit = max(1, min(int(limit), 50))
    data = await _api_get({
        "action": "query",
        "titles": name,
        "generator": "images",
        "gimlimit": limit * 2,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "redirects": 1,
    })

    query = data.get("query")
    if not query:
        return {
            "source": name,
            "images": [],
            "error": f"No images found for '{name}'.",
            "suggestion": f"Try search_aesthetic(query='{name}') to verify the title.",
        }

    pages = query.get("pages", [])
    images: list[dict[str, Any]] = []
    for p in pages:
        info_list = p.get("imageinfo") or []
        if not info_list:
            continue
        info = info_list[0]
        mime = info.get("mime", "")
        width = info.get("width", 0)
        if mime.startswith("image/svg"):
            continue
        if width and width < 100:
            continue
        images.append({
            "filename": p.get("title", "").replace("File:", ""),
            "url": info.get("url"),
            "description_url": info.get("descriptionurl"),
            "width": width,
            "height": info.get("height", 0),
        })
        if len(images) >= limit:
            break

    return {
        "source": name,
        "url": _page_url(name),
        "count": len(images),
        "images": images,
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
    }
)
async def random_aesthetic(count: int = 1) -> dict[str, Any]:
    """Get one or more random aesthetics from the wiki — great for inspiration.

    Args:
        count: Number of random pages (1-10). Default 1.

    Returns:
        A dict with `aesthetics`: list of {title, url}.
    """
    count = max(1, min(int(count), 10))
    data = await _api_get({
        "action": "query",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": count,
    })
    picks = data.get("query", {}).get("random", [])
    aesthetics = [{"title": p["title"], "url": _page_url(p["title"])} for p in picks]
    return {"count": len(aesthetics), "aesthetics": aesthetics}


def main() -> None:
    """Entry point for stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
