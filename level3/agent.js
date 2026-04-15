const { execSync } = require("child_process");

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

  return [...new Set(tools)];
}

function runTool(tool) {
  try {
    const result = execSync(`node ../dist/test-client.js ${tool}`, {
      encoding: "utf-8"
    });
    return result;
  } catch (err) {
    return `Error running ${tool}`;
  }
}

function agent(query) {
  const tools = chooseTools(query);

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

// TEST
const query = "How to implement digital twin with examples?";
console.log(JSON.stringify(agent(query), null, 2));