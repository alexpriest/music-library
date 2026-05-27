import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerTools } from "./tools.js";
import { library } from "./library.js";

export function buildServer(): McpServer {
  const server = new McpServer({
    name: "music-library",
    version: "1.0.0",
  });
  registerTools(server);
  return server;
}

export const summary = `${library.title}: ${library.book_count} books, ${library.song_count} songs`;
