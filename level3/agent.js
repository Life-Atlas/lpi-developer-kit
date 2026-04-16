// level3/agent.js

import readline from "readline";

// Simulated LPI tools
const tools = {
  smile_overview: () => "Overview of SMILE methodology.",
  smile_phase_detail: (phase) => `Details about ${phase} phase.`,
  get_case_studies: () => "Relevant digital twin case studies.",
  get_insights: (query) => `Insights for: ${query}`,
  get_methodology_step: (phase) => `Steps for ${phase}`,
};

// Simple intent-based tool selector
function selectTools(query) {
  const selected = [];

  if (query.toLowerCase().includes("how") || query.toLowerCase().includes("build")) {
    selected.push("get_methodology_step");
  }

  if (query.toLowerCase().includes("example") || query.toLowerCase().includes("case")) {
    selected.push("get_case_studies");
  }

  if (query.toLowerCase().includes("explain") || query.toLowerCase().includes("what")) {
    selected.push("smile_overview");
  }

  // always include insights
  selected.push("get_insights");

  return selected;
}

// Agent execution
function runAgent(query) {
  console.log("\n=== LPI Smart Agent ===\n");
  console.log("Query:", query);

  const selectedTools = selectTools(query);
  console.log("\nSelected Tools:", selectedTools.join(", "));

  console.log("\n--- Results ---");

  selectedTools.forEach((tool) => {
    let result;

    if (tool === "get_insights") {
      result = tools[tool](query);
    } else if (tool === "get_methodology_step") {
      result = tools[tool]("concurrent-engineering");
    } else if (tool === "smile_phase_detail") {
      result = tools[tool]("reality-emulation");
    } else {
      result = tools[tool]();
    }

    console.log(`\n[${tool}]`);
    console.log(result);
  });

  console.log("\n=== Final Response ===");
  console.log("This response combines multiple tools to provide a structured answer.\n");
}

// CLI input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question("Enter your query: ", (query) => {
  runAgent(query);
  rl.close();
});