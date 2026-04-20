# Aesthetics Wiki MCP

An [MCP](https://modelcontextprotocol.io) server that lets LLMs search, read, and discover aesthetics from the [Aesthetics Wiki](https://aesthetics.fandom.com) (cottagecore, dark academia, y2k, goblincore, and thousands more).

Backed by the MediaWiki API. No API key required.

## Tools

| Tool | Description |
| --- | --- |
| `search_aesthetic(query, limit=10)` | Full-text search across the wiki. |
| `get_aesthetic(name, max_chars=6000)` | Fetch a page's cleaned content + main image URL. |
| `get_aesthetic_images(name, limit=12)` | Gallery of image URLs from a page — perfect for moodboards. |
| `list_related(name, limit=20)` | List aesthetics linked from a page (neighbors/related). |
| `random_aesthetic(count=1)` | Pick random aesthetics for inspiration. |

All tools are read-only.

## Install

Requires Python 3.10+.

```bash
# With uv (recommended)
uv tool install aesthetics-wiki-mcp

# Or with pipx
pipx install aesthetics-wiki-mcp

# Or from source
git clone https://github.com/leonardoca1/aesthetics-wiki-mcp.git
cd aesthetics-wiki-mcp
uv sync
```

## Use with Claude Code

Add to your MCP config (`~/.claude/settings.json` or project `.mcp.json`):

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

Or, if installed from source:

```json
{
  "mcpServers": {
    "aesthetics-wiki": {
      "command": "uv",
      "args": ["--directory", "/path/to/aesthetics-wiki-mcp", "run", "aesthetics-wiki-mcp"]
    }
  }
}
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) with the same shape as above.

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
