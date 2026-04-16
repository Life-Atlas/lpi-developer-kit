#!/usr/bin/env node

// 🥚 Easter egg #2: Query "query_knowledge" with the exact phrase "impact first data last"
// and count how many results mention "ontology". Put the number in your HOW_I_DID_IT.md
// for bonus points. There's one more egg hidden in the data files.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { smileOverview, smilePhaseDetail, listTopics } from "./tools/smile.js";
import { queryKnowledge, getInsights } from "./tools/knowledge.js";
import { listCaseStudies, getCaseStudyDetails } from "./tools/cases.js";

const MAX_INPUT_LENGTH = 500;

function sanitizeInput(input: string | undefined): string {
  if (!input) return "";
  // Strip to max length, remove control characters
  return input.slice(0, MAX_INPUT_LENGTH).replace(/[\x00-\x1f\x7f]/g, "");
}

const server = new Server(
  {
    name: "lpi-sandbox",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions — ALL read-only, no tier gating
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "smile_overview",
        description:
          "Get an overview of the S.M.I.L.E. methodology (Sustainable Methodology for Impact Lifecycle Enablement) — a benefits-driven digital twin implementation framework. Returns the 6 phases, 3 perspectives, AI journey, and core principles.",
        inputSchema: {
          type: "object" as const,
          properties: {},
        },
      },
      {
        name: "smile_phase_detail",
        description:
          "Deep dive into a specific SMILE phase. Returns activities, deliverables, key questions, duration, and related concepts.",
        inputSchema: {
          type: "object" as const,
          properties: {
            phase: {
              type: "string",
              description:
                "Phase ID or name. Options: reality-emulation, concurrent-engineering, collective-intelligence, contextual-intelligence, continuous-intelligence, perpetual-wisdom",
            },
          },
          required: ["phase"],
        },
      },
      {
        name: "query_knowledge",
        description:
          "Search the LPI knowledge base for digital twin implementation knowledge, methodology guidance, and best practices. Returns relevant knowledge entries ranked by relevance.",
        inputSchema: {
          type: "object" as const,
          properties: {
            query: {
              type: "string",
              description:
                "Search query — keywords, topics, or questions about digital twins, SMILE, interoperability, manufacturing, healthcare, energy, security, etc.",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_case_studies",
        description:
          "Browse or search anonymized digital twin implementation case studies across industries including smart buildings, manufacturing, healthcare, energy, maritime, and more.",
        inputSchema: {
          type: "object" as const,
          properties: {
            query: {
              type: "string",
              description:
                "Search query — industry, challenge type, or topic. Leave empty to list all available cases.",
              default: "",
            },
          },
        },
      },
      {
        name: "get_insights",
        description:
          "Get digital twin implementation advice for a specific scenario. Provides scenario-specific SMILE recommendations, relevant knowledge, and common pitfalls.",
        inputSchema: {
          type: "object" as const,
          properties: {
            scenario: {
              type: "string",
              description:
                "Describe your digital twin implementation scenario — industry, challenge, current state, desired outcome.",
            },
          },
          required: ["scenario"],
        },
      },
      {
        name: "list_topics",
        description:
          "Browse all available topics in the LPI knowledge base — SMILE phases, key concepts, perspectives, AI journey stages, and interoperability layers.",
        inputSchema: {
          type: "object" as const,
          properties: {},
        },
      },
      {
        name: "get_methodology_step",
        description:
          "Get step-by-step guidance for implementing a specific SMILE phase. Returns practical activities, deliverables, and the key question to answer.",
        inputSchema: {
          type: "object" as const,
          properties: {
            phase: {
              type: "string",
              description:
                "Phase ID or name to get implementation steps for.",
            },
          },
          required: ["phase"],
        },
      },
    ],
  };
});

// Tool execution — ALL read-only, no writes, all inputs sanitized
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "smile_overview": {
        return {
          content: [{ type: "text" as const, text: smileOverview() }],
        };
      }

      case "smile_phase_detail": {
        const phase = sanitizeInput((args as Record<string, string>)?.phase);
        if (!phase) {
          return {
            content: [
              { type: "text" as const, text: "Error: 'phase' parameter is required." },
            ],
            isError: true,
          };
        }
        const result = smilePhaseDetail(phase);
        return {
          content: [
            { type: "text" as const, text: result || "Phase not found." },
          ],
        };
      }

      case "query_knowledge": {
        const query = sanitizeInput((args as Record<string, string>)?.query);
        if (!query) {
          return {
            content: [
              { type: "text" as const, text: "Error: 'query' parameter is required." },
            ],
            isError: true,
          };
        }
        return {
          content: [{ type: "text" as const, text: queryKnowledge(query) }],
        };
      }

      case "get_case_studies": {
        const query = sanitizeInput((args as Record<string, string>)?.query || "");
        if (query) {
          return {
            content: [
              { type: "text" as const, text: getCaseStudyDetails(query) },
            ],
          };
        }
        return {
          content: [
            { type: "text" as const, text: listCaseStudies() },
          ],
        };
      }

      case "get_insights": {
        const scenario = sanitizeInput((args as Record<string, string>)?.scenario);
        if (!scenario) {
          return {
            content: [
              { type: "text" as const, text: "Error: 'scenario' parameter is required." },
            ],
            isError: true,
          };
        }
        return {
          content: [
            { type: "text" as const, text: getInsights(scenario) },
          ],
        };
      }

      case "list_topics": {
        return {
          content: [{ type: "text" as const, text: listTopics() }],
        };
      }

      case "get_methodology_step": {
        const phase = sanitizeInput((args as Record<string, string>)?.phase);
        if (!phase) {
          return {
            content: [
              { type: "text" as const, text: "Error: 'phase' parameter is required." },
            ],
            isError: true,
          };
        }
        const result = smilePhaseDetail(phase);
        return {
          content: [
            { type: "text" as const, text: result || "Phase not found." },
          ],
        };
      }

      default:
        return {
          content: [{ type: "text" as const, text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[LPI Sandbox] Error in tool ${name}:`, message);
    return {
      content: [{ type: "text" as const, text: `Error: ${message}` }],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[LPI Sandbox] Server started — 7 read-only tools available");
}

main().catch((error) => {
  console.error("[LPI Sandbox] Fatal error:", error);
  process.exit(1);
});
