# Connecting the Music Library to Claude

The MCP server exposes the same tools over two transports. Connect whichever
surfaces you want.

Tools available everywhere: `find_music`, `suggest_by_vibe`, `get_song`,
`get_book`, `list_books`, `random_pick`, `list_vocabulary`.

---

## 1. Claude apps (web · desktop · mobile) — remote connector

The server is deployed to Railway. Add it once on the web and it syncs to
desktop and mobile.

**Connector URL** (the secret path is the auth — keep it private; the real
`MCP_SECRET` lives in Railway, not in this repo):

```
https://music-library-mcp-production.up.railway.app/mcp/<MCP_SECRET>
```

Steps (on **claude.ai**, web):
1. Settings → **Connectors** → **Add custom connector**.
2. Name: `Music Library`. URL: paste the connector URL above.
3. Leave Advanced settings (OAuth) empty — auth is the secret path.
4. Save. It now appears on desktop and mobile too (mobile inherits; it can't add
   connectors itself).

Then in any chat, enable the **Music Library** connector and ask:
> "Find me something wistful for a rainy night."
> "Upbeat cocktail-party jazz I can play — give me book and page."

If you ever need to rotate the secret: change `MCP_SECRET` on Railway
(`railway variables --set "MCP_SECRET=…"`) and update the connector URL.

---

## 2. Claude Code — local stdio

Registered at user scope (available in every project):

```bash
claude mcp add music-library --scope user -- node /Users/alex/Code/projects/music-library/dist/index.js
```

Rebuild after any data/code change: `npm run build` (the server reads
`data/library.json` at startup).

---

## 3. Kit (iMessage assistant) — local stdio

Kit runs on the Anthropic Agent SDK with its own MCP config in
`~/Code/system/imessage`. Add an entry pointing at the same stdio entrypoint:

```json
{
  "music-library": {
    "command": "node",
    "args": ["/Users/alex/Code/projects/music-library/dist/index.js"]
  }
}
```

Then Kit can answer "what should I play tonight?" with a book + page from your
phone.

---

## Operations

- **Logs:** `railway logs`
- **Redeploy after data changes:** rebuild data (`python3 scripts/*.py`), commit,
  then `railway up`. `data/library.json` ships with the deploy.
- **Health:** `GET https://music-library-mcp-production.up.railway.app/healthz`
- **Local HTTP test:** `MCP_SECRET=dev PORT=8090 npm start`, then POST to
  `http://localhost:8090/mcp/dev`.
