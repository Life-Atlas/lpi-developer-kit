import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { writeFileSync } from "fs";

const transport = new StdioClientTransport({
  command: "node",
  args: ["dist/src/index.js"],
});

const client = new Client({ name: "extractor", version: "1.0.0" }, {});

await client.connect(transport);

let output = "";

// Tool 1: SMILE Overview
console.log("Fetching smile_overview...");
const overview = await client.callTool({ name: "smile_overview", arguments: {} });
output += "=== SMILE OVERVIEW ===\n";
output += JSON.stringify(overview, null, 2) + "\n\n";

// Tool 2: Case Studies
console.log("Fetching case studies...");
const cases = await client.callTool({ name: "get_case_studies", arguments: {} });
output += "=== CASE STUDIES ===\n";
output += JSON.stringify(cases, null, 2) + "\n\n";

// Tool 3: List Topics
console.log("Fetching topics...");
const topics = await client.callTool({ name: "list_topics", arguments: {} });
output += "=== TOPICS ===\n";
output += JSON.stringify(topics, null, 2) + "\n\n";

writeFileSync("smile-content.txt", output);
console.log("✅ Done! Open smile-content.txt");

await client.close();