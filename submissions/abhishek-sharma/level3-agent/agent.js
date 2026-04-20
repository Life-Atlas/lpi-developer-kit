import { spawn } from "child_process";

// start MCP server
const mcp = spawn("cmd.exe", ["/c", "echo MCP Server Mock Running"]);

mcp.stdout.on("data", (data) => {
  console.log("MCP Response:", data.toString());
});

mcp.stderr.on("data", (data) => {
  console.error("Error:", data.toString());
});

// send a tool call
setTimeout(() => {
  const request = {
    type: "tool_call",
    tool: "time",
    args: {}
  };

  mcp.stdin.write(JSON.stringify(request) + "\n");
}, 2000);