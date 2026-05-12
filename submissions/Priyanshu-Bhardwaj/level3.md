# Track A

Github Repo Link - https://github.com/PriyanshuBHardwaj20/lpi-agent

### What I did,step by step for L3

1) Set up a virtual environment to manage dependencies like requests.

2) Integrated the LPI Developer Kit's Node.js server into a Python script using the subprocess module to establish a JSON-RPC connection over stdio.

3) Programmed the agent to query multiple LPI tools, specifically smile_overview and smile_phase_detail , to gather grounded methodology data.

4) Connected the agent to a local LLM via Ollama (Qwen 2.5:1.5b) to perform a Gap Analysis that compares a user's project state with the SMILE framework.

5) Engineered a system prompt that forces the LLM to provide citations for every claim, ensuring the user can trace the answer back to the specific LPI tool used.

6) Implemented a streaming response logic to provide real time feedback and prevent timeouts during long analysis generations.

### Problems I Hit & How I Solved Them For L3

I initially couldn't activate my virtual environment in PowerShell due to execution policies. I solved this by switching to the Command Prompt, which bypassed the script restriction. The Qwen 3.5 model was too heavy for my Laptop, causing the script to hang or timeout. I solved this by switching to the Qwen 2.5:1.5b model, which is much faster.

### What I Learned That I Didn't Know Before L3

I learned how to use MCP to bridge different programming environments to create a unified AI system.

### Output of the live run of agent

```

PS C:\Users\G15\Documents\GitHub\lpi-agent> python agent.py "I have made a digital twin concept of a hospital room in Unity which shows patient changing colours based on its vitals. How does this align with SMILE?"
[LPI Sandbox] Server started — 7 read-only tools available
[*] Accessing LPI Methodology...
[DEBUG] Tool Call Evidence (Overview): # S.M.I.L.E. â€” Sustainable Methodology for Impact Lifecycl...
[DEBUG] Tool Call Evidence (Phase Detail): # Phase 1: Reality Emulation

## Duration
Days to Weeks

## ...

--- AUDIT ANALYSIS START ---

### Step 1: Determine Which SMILE Phase the User is Currently in

Based on the provided context, the user has created a digital twin concept of a hospital room in Unity which shows patient changing colors based on its vitals.

This indicates that the user is currently **Phase 1: Reality Emulation**. The reasoning is:
- **Reality Canvas**: The user has established a shared reality canvas for their project.
- **Duration and Description**: This phase describes creating a shared reality canvas with an emphasis on spatial-temporal understanding.
- **Key Activities and Deliverables**: These activities align well with the "Create a shared reality canvas" described in Source 1.

### Step 2: Explain Why, Using Specific Definitions from the Sources

The user has created a digital twin concept for a hospital room using Unity. This project is aligned closely with the first phase of SMILE methodology because it involves creating a shared reality canvas to establish where, when, and who on the planet.

Here’s how this aligns:

- **Source 1 Context**: "Create a shared reality canvas â€” establishing where, when, and who." The user has done just that by using Unity to visualize their concept in a shared environment.
- **Source 2 Context**: "Define the scope (as-is to to-be), invite stakeholders to innovate together, validate hypotheses virtually before committing resources." This phase is similar as it involves defining scope, inviting innovation, and validating ideas before physical implementation.

### Step 3: Identify What Technical Steps Are Needed to Reach the Next Phase

To progress from **Phase 1: Reality Emulation** to **Phase 2: Concurrent Engineering**, several technical steps are needed:

1. **Define the Scope (As-is to To-be)**:
   - Establish the current state of the hospital room and define its future improvements or changes.
   
2. **Inviting Stakeholders to Innovate Together and Validate Hypotheses Virtually**:
   - Collaborate with stakeholders through virtual user interaction, scenario planning, and validation exercises.
   
3. **Define a Minimal Viable Twin (MVT) for Validation**:
   - Develop a digital twin model that closely mirrors the hospital room concept to validate hypotheses before physical implementation.

4. **Emulate Virtual Scenarios**:
   - Create and simulate different scenarios using the MVT to test out ideas without physically modifying anything.
   
5. **Create an As-Is/To-BE Scope Document and Validation Hints**:
   - Document the current state of the room and prepare for future changes, ensuring validation is performed before physical implementation.

### Step 4: Mandatory Citations

This should be done at the end of each sentence to adhere to the audit requirement. The user can now reference specific parts from their project and its context with these citations:

- Reality Emulation (Source 1): Establish shared reality canvas
- Concurrent Engineering (Source 2): Define scope, invite innovation, validate hypotheses virtually

The final summary for clarity:
- "In order to think outside the box, one has to define the box first. What is the starting point and boundary of your sociotechnological ecosystem?" [Source 1]
- "What does the Minimal Viable Twin look like, and how do we validate it virtually before investing in physical implementation?" [Source 2]

============================================================
PROVENANCE: Data grounded via LPI MCP Server toolsets.
============================================================

```
### Evidence of Tool Calls

The agent now logs the first 60 characters of the raw data retrieved from the LPI server. During the live run, the following data was successfully fetched and used for reasoning:

Tool Call (Overview): # S.M.I.L.E. — Sustainable Methodology for Impact Lifecycl...

Tool Call (Phase Detail): # Phase 1: Reality Emulation. Duration: Days to Weeks...
This confirms that the Python agent is successfully communicating with the Node.js MCP server via JSON-RPC.

### Explainability & Citations

As shown in the analysis, the agent anchors its recommendations to the LPI sources. For example:

It identified the project as Phase 1: Reality Emulation because the Unity hospital room functions as a 'Shared Reality Canvas' [Source 1].

It explicitly defined the path to Phase 2 (Concurrent Engineering) by citing the requirement to 'Define a Minimal Viable Twin (MVT) for Validation' [Source 2].

### Error Handling

Server/Input Safety: I added a proc.poll() health check and an empty-input validation. If the LPI server is offline or the input is empty, the agent provides a clear error instead of failing silently.

Architectural Trade-off: I chose the Qwen 2.5:1.5b model to ensure the entire auditing process runs locally on a standard developer laptop (6GB VRAM) with streaming enabled. This makes the tool practical for real-time development workflows.

# Track D

Github Repo Link - https://github.com/PriyanshuBHardwaj20/digital-twin

### What I did,step by step for L3

1) created a new unity project with standard 3D URP template.

2) then created a 3d hospital room for digital twin concept using primitive 3D shapes.

3) inside the room I created Bed, Patient and Patient Monitor game_objects using primitive 3D shapes.

4) Using Unity's UI system I created a screen for Patient Monitor and Patient Vitals UI which has sliders for changing different patient vitals for simulating Patient health.

5) Finally i created a C# script for changing the Patient's colour based on its Vitals. 

### Problems I Hit & How I Solved Them For L3

The main problem I faced was to decide what digital twin concept I should choose and how it would look like in Unity, to solve this I googled existing digital twin concepts made in Unity, and I found "Introduction to Digital Twins with Unity"
on Unity learn website which helped me a lot to decide the digital twin concept. I hardly faced any technical challenge as I have worked with Unity for a long time. 

### What I Learned That I Didn't Know Before L3

I learned a lot about digital twins and how I can implement them using Unity.


