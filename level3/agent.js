import { execSync } from "child_process";

function chooseTool(query) {
  query = query.toLowerCase();
  let tools = [];

  if (query.includes("how") || query.includes("implement")) {
    tools.push("get_methodology_step", "get_insights");
  }

  if (query.includes("example") || query.includes("case")) {
    tools.push("get_case_studies");
  }

  if (query.includes("what") || query.includes("explain") || query.includes("overview")) {
    tools.push("smile_overview");
  }

  if (!tools.includes("get_insights")) {
    tools.push("get_insights");
  }

  return [...new Set(tools)];
}

function runTool(tool) {
  try {
    const result = execSync(
ode ../dist/test-client.js , {
      encoding: "utf-8",
    });
    return result;
  } catch (err) {
    return Error running ;
  }
}

function agent(query) {
  const tools = chooseTool(query);
  let outputs = {};

  tools.forEach(tool => {
    outputs[tool] = runTool(tool);
  });

  return {
    query,
    tools_used: tools,
    outputs
  };
}

const query = "How to implement digital twin with examples?";
console.log(JSON.stringify(agent(query), null, 2));
