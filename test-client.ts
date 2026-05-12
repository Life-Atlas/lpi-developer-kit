#!/usr/bin/env node

/**
 * LPI Sandbox Test Client
 *
 * Connects to the LPI sandbox MCP server and calls each tool.
 * Use this to verify your setup works before building on top of it.
 *
 * Usage:
 *   npm run build
 *   npm run test-client
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  console.log("=== LPI Sandbox Test Client ===\n");

  // Connect to the sandbox server
  const transport = new StdioClientTransport({
    command: "node",
    args: ["dist/src/index.js"],
  });

  const client = new Client(
    { name: "lpi-test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);
  console.log("Connected to LPI Sandbox\n");

  // List available tools
  const tools = await client.listTools();
  console.log(`Available tools (${tools.tools.length}):`);
  for (const tool of tools.tools) {
    console.log(`  - ${tool.name}: ${(tool.description ?? "").slice(0, 80)}...`);
  }
  console.log();

  // Test each tool
  const tests: Array<{ name: string; args: Record<string, string> }> = [
    { name: "smile_overview", args: {} },
    { name: "smile_phase_detail", args: { phase: "reality-emulation" } },
    { name: "list_topics", args: {} },
    { name: "query_knowledge", args: { query: "explainable AI" } },
    { name: "get_case_studies", args: {} },
    { name: "get_case_studies", args: { query: "smart buildings" } },
    { name: "get_insights", args: { scenario: "personal health digital twin", tier: "free" } },
    { name: "get_methodology_step", args: { phase: "concurrent-engineering" } },
    // Invalid input
{ name: "query_knowledge", args: { query: "!!!!!!!" } },

// Long input (DoS style)
{ name: "query_knowledge", args: { query: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" } },

// SQL injection attempt
{ name: "query_knowledge", args: { query: "' OR 1=1 --" } },

// Script injection attempt
{ name: "query_knowledge", args: { query: "<script>alert(1)</script>" } },

// Empty input
{ name: "query_knowledge", args: { query: "" } },
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      const result = await client.callTool({
        name: test.name,
        arguments: test.args,
      });
      const text = (result.content as Array<{ type: string; text: string }>)[0]?.text || "";
      const preview = text.slice(0, 120).replace(/\n/g, " ");
      console.log(`[PASS] ${test.name}(${JSON.stringify(test.args)})`);
      console.log(`       ${preview}...\n`);
      passed++;
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      console.log(`[FAIL] ${test.name}(${JSON.stringify(test.args)})`);
      console.log(`       Error: ${msg}\n`);
      failed++;
    }
  }

  console.log("=== Results ===");
  console.log(`Passed: ${passed}/${tests.length}`);
  console.log(`Failed: ${failed}/${tests.length}`);

  if (failed === 0) {
    console.log("\nAll tools working. Your LPI Sandbox is ready.");
    console.log("You can now build agents that connect to this server.");
  }

  await client.close();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((error) => {
  console.error("Test client error:", error);
  process.exit(1);
});
