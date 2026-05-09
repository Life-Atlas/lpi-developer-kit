# LPI API Advisor Agent — Level 3 Submission

An advanced AI advisor that streamlines API strategy and digital twin implementation using the SMILE methodology. Built with LangGraph and Groq, this agent transforms raw LPI tool data into structured, explainable recommendations.

Github link - https://github.com/yashm0910/LPI-Agent
 

---

## What I Built

I developed a **LPI API Advisor Agent** that uses a dynamic **"Research-and-Summarize" workflow**. The agent performs **intent-based routing** to select the most relevant LPI tools, ensuring that advice is backed by real-world case studies and methodology-specific insights.

The primary goal was to create an agent capable of **multi-source reasoning** while maintaining a strict **provenance log** for total transparency.

---

## Setup Instructions

To run the LPI API Advisor:

1. **Clone the repository** and navigate to your project folder.

2. **Build the LPI Server:**
   ```bash
   npm install
   npm run build
````

3. **Configure Environment:**
   Create a `.env` file in the root directory and add:

   ```
   GROQ_API_KEY=your_api_key_here
   ```

4. **Run the Workflow:**
   Execute the LangGraph cells in:

   ```
   testl3.ipynb
   ```

---

## LPI Tools Used

The agent dynamically orchestrates calls to several LPI tools based on user intent:

* **query_knowledge**
  Baseline conceptual data for all queries.

* **smile_overview**
  Used for overview or explanatory requests.

* **get_case_studies**
  Triggered when the user asks for examples or real-world cases.

* **get_methodology_step & get_insights**
  Activated for implementation-focused "how-to" questions.

---

## Explainability

The agent is designed for **Explainable AI (XAI)** using structured outputs.

### Workflow

```
User Input → Intent Detection → Dynamic Tool Selection → Data Aggregation → Structured Synthesis
```

### Traceability

Users can see exactly which tools contributed to the answer via the `sources` field in the final response.

---

## Example Output

```
--- RESEARCHING FOR: What are the core phases of the SMILE methodology? ---
Running tool: query_knowledge
Running tool: smile_overview
--- GENERATING FINAL ANSWER ---

>> Tool Outputs: [
  'Tool Used: query_knowledge | Data: ...',
  'Tool Used: smile_overview | Data: ...'
]

>> Sources Cited: ["query_knowledge", "smile_overview"]
```

---
