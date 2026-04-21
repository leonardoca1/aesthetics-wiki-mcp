# Aesthetics Wiki MCP

[![PyPI version](https://img.shields.io/pypi/v/aesthetics-wiki-mcp.svg)](https://pypi.org/project/aesthetics-wiki-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/aesthetics-wiki-mcp.svg)](https://pypi.org/project/aesthetics-wiki-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An [MCP](https://modelcontextprotocol.io) server that lets LLMs search, read, and discover aesthetics from the [Aesthetics Wiki](https://aesthetics.fandom.com) (cottagecore, dark academia, y2k, goblincore, and thousands more).

Backed by the MediaWiki API. No API key required. Zero setup: run it straight with `uvx`.

## Tools

| Tool | Description |
| --- | --- |
| `search_aesthetic(query, limit=10)` | Full-text search across the wiki. |
| `get_aesthetic(name, max_chars=6000)` | Fetch a page's cleaned content + main image URL. |
| `get_aesthetic_images(name, limit=12)` | Gallery of image URLs from a page — perfect for moodboards. |
| `list_related(name, limit=20)` | List aesthetics linked from a page (neighbors/related). |
| `random_aesthetic(count=1)` | Pick random aesthetics for inspiration. |

All tools are read-only.

## Quick start

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/). Nothing to install manually — `uvx` fetches and runs it on demand.

### Claude Code / Claude Desktop

Add this to your MCP config (`~/.claude/settings.json`, project `.mcp.json`, or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "aesthetics-wiki": {
      "command": "uvx",
      "args": ["aesthetics-wiki-mcp"]
    }
  }
}
```

Restart your client and the 5 tools show up automatically.

### Other MCP clients

Any client that speaks stdio works. Just run `uvx aesthetics-wiki-mcp` as the transport command.

### Manual install

```bash
uv tool install aesthetics-wiki-mcp      # or: pipx install aesthetics-wiki-mcp
aesthetics-wiki-mcp                       # starts the stdio server
```

## Example prompts

- "Find aesthetics related to dark academia and show me a visual moodboard."
- "Give me 5 random aesthetics and a one-sentence vibe for each."
- "What are the core elements of cottagecore? Any adjacent aesthetics I should know?"
- "Compare y2k and 2014 Tumblr aesthetically."

## Development

```bash
uv sync
uv run aesthetics-wiki-mcp        # start stdio server
uv run python -m py_compile src/aesthetics_wiki_mcp/server.py
```

Test interactively with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run aesthetics-wiki-mcp
```

## License

MIT. Content from the Aesthetics Wiki is licensed CC-BY-SA 3.0 by its contributors; this project only proxies read access and attributes the source in every response URL.

## Credits

Built by [Leonardo Cametti](https://github.com/leonardoca1). Data © [Aesthetics Wiki](https://aesthetics.fandom.com) contributors.
