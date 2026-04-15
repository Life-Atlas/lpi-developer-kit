import { execSync } from "child_process";

// Decide which tools to use based on query
function chooseTools(query) {
  query = query.toLowerCase();

  let tools = [];

  if (query.includes("how") || query.includes("implement")) {
    tools.push("get_insights", "get_methodology_step");
  }

  if (query.includes("example") || query.includes("case")) {
    tools.push("get_case_studies");
  }

  if (query.includes("overview")) {
    tools.push("smile_overview");
  }

  if (tools.length === 0) {
    tools.push("query_knowledge");
  }

  return [...new Set(tools)];
}

// Simulate tool execution
function runTool(tool) {
  try {
    execSync(`node ../dist/test-client.js`, {
      encoding: "utf-8"
    });

    return `[${tool}] used to contribute to the final answer`;
  } catch (err) {
    return `[${tool}] failed to execute`;
  }
}

// Format final response
function buildResponse(query, tools) {
  let response = `Query: ${query}\n\n`;

  response += `Tools Selected:\n`;
  tools.forEach(t => {
    response += `- ${t}\n`;
  });

  response += `\nFinal Response:\n`;

  if (tools.includes("get_insights")) {
    response += "- Provided implementation guidance\n";
  }

  if (tools.includes("get_methodology_step")) {
    response += "- Included step-by-step methodology\n";
  }

  if (tools.includes("get_case_studies")) {
    response += "- Added real-world examples\n";
  }

  if (tools.includes("smile_overview")) {
    response += "- Included SMILE framework overview\n";
  }

  if (tools.includes("query_knowledge")) {
    response += "- Retrieved relevant knowledge base information\n";
  }

  return response;
}

// Main agent
function agent(query) {
  const tools = chooseTools(query);

  tools.forEach(tool => runTool(tool));

  return buildResponse(query, tools);
}

// CLI input
const query = process.argv[2] || "How to implement digital twin with examples?";

console.log(agent(query));