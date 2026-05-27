// Remote HTTP entrypoint — Streamable HTTP transport for the Claude apps
// (web / desktop / mobile) via a custom connector. Protected by an unguessable
// secret path: the connector URL is  https://<host>/mcp/<MCP_SECRET>.
import express from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { buildServer, summary } from "./server.js";

const PORT = Number(process.env.PORT) || 8080;
const SECRET = process.env.MCP_SECRET;

if (!SECRET) {
  console.error("FATAL: MCP_SECRET env var is required (the secret path segment). Set it and restart.");
  process.exit(1);
}

const app = express();
app.use(express.json({ limit: "4mb" }));

// Public health endpoints (no secret, no data) — for humans and Railway checks.
app.get(["/", "/healthz"], (_req, res) => {
  res.json({ ok: true, server: "music-library", summary });
});

// MCP endpoint behind the secret path. Stateless: a fresh server + transport per
// request (no sessions), with JSON responses — exactly what Claude connectors use.
app.post("/mcp/:token", async (req, res) => {
  if (req.params.token !== SECRET) {
    res.status(404).json({ error: "not found" }); // don't confirm the path exists
    return;
  }
  try {
    const server = buildServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });
    res.on("close", () => {
      transport.close();
      server.close();
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (e) {
    console.error("MCP request error:", e);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal server error" },
        id: null,
      });
    }
  }
});

// Streamable HTTP stateless mode only needs POST.
app.all("/mcp/:token", (_req, res) => res.status(405).json({ error: "method not allowed" }));

app.listen(PORT, () => {
  console.error(`music-library MCP (HTTP) on :${PORT} — ${summary}`);
  console.error(`Connector URL: <https-host>/mcp/${"*".repeat(Math.min(SECRET.length, 8))}…`);
});
