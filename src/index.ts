#!/usr/bin/env node
// Local stdio entrypoint — for Claude Code and Kit (the iMessage assistant).
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { buildServer, summary } from "./server.js";

const server = buildServer();
const transport = new StdioServerTransport();
await server.connect(transport);
// stderr is safe with stdio transport (stdout carries the protocol).
process.stderr.write(`music-library MCP (stdio) ready — ${summary}\n`);
