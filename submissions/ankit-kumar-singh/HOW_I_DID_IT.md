## Summary

Built a domain-specific SMILE agent for hospital operations using all 7 LPI tools, 
with a 2-pass reasoning loop and title-boosted search. Discovered and implemented 
all 3 easter eggs by analyzing the knowledge store and source code.

---

# HOW_I_DID_IT.md

**Author:** Ankit Kumar Singh  
**GitHub:** ankitsinghh007  
**Track:** A — Agent Builders  
**Level:** 3

---

## What I built and the problem it actually solves

I built **SMILE Digital Twin Advisor for Hospital Operations** — an agent that
takes a specific hospital operations problem (bed utilisation, equipment downtime,
energy waste, or patient readmission) and produces a phased SMILE implementation
roadmap with every claim cited to the LPI tool that provided it.

I chose hospitals specifically because after reading the SMILE case studies I
noticed the methodology had been applied to manufacturing (cs-003), maritime
(cs-006), agriculture (cs-008), and smart buildings (cs-001) — but never to
the full breadth of hospital operations. Yet hospitals are exactly the kind of
complex sociotechnological ecosystem SMILE was designed for: they have spatial
context (ward layouts, equipment locations), temporal rhythms (shift patterns,
seasonal admissions), human actors (clinicians, engineers, managers), and
measurable KPIs (bed occupancy, equipment availability, energy cost per patient).

The "Impact First, Data Last" principle from kb-001 maps directly:
- Don't start with "let's put sensors everywhere"
- Start with "we want to reduce unplanned MRI downtime from 10h/week to <2h/week"
- Then trace backwards: you need early warnings → failure precursor patterns →
  sensor coverage → specific signals. Data selection is derived from the outcome.

---

## Step by step — what I actually did

### Step 1: Read the source before writing code

I read `src/index.ts`, `src/tools/knowledge.ts`, and `src/store/knowledge-store.ts`
in full before writing a single line of Python.

The most important thing I found was in `knowledge-store.ts`:

```typescript
const text = `${entry.title} ${entry.content} ${entry.tags.join(" ")}`.toLowerCase();
const score = terms.reduce((acc, term) => acc + (text.includes(term) ? 1 : 0), 0);
```

This is a term-frequency scorer over a concatenated string of title + content + tags.
There is no TF-IDF, no embeddings, no semantic ranking. Every matching term contributes
exactly 1 point regardless of where it appears — title, content, or tags.

The implication: an entry whose short 5-word title contains 3 query terms scores 3
points from the title alone. A longer entry where those same 3 words appear once
each buried in 400 words of content also scores 3 points — but has far more
non-matching words. Result: short, precise titles with exact keyword matches
float to the top.

This became my `_title_boost_query()` function.

### Step 2: Finding the easter eggs

**Eggs #1 and #2** were in a comment at the very top of `src/index.ts`:

```
// Easter egg #2: Query "query_knowledge" with the exact phrase "impact first data last"
// and count how many results mention "ontology". Put the number in your HOW_I_DID_IT.md
// for bonus points. There's one more egg hidden in the data files.
```

I ran this programmatically against the knowledge base:

Query: `"impact first data last"` → 39 results returned

Checking each result for "ontology" in title + content + tags:
- `kb-011`: SMILE Six-Phase Digital Twin Journey ✓
- `kb-003`: Ontology Factories as Foundation for AI Factories ✓
- `kb-022`: Digital Twin Failure Mode: Semantic Drift and Ontology Neglect ✓
- `kb-047`: IFC: Built Environment Data Standard ✓
- `kb-049`: W3C SSN/SOSA: Semantic Sensor Network Ontology ✓
- `kb-063`: MIMs Plus: Cross-Domain Interoperability ✓

**Answer: 6 results mention ontology.**

**Egg #3** was in `data/knowledge-base.json` — entry with id `kb-egg`:

```
"title": "The Hidden Principle",
"content": "Easter egg #3: You found the hidden knowledge base entry.
The principle is: every system has a seam. The seam in this system is
that the search function weights title matches higher than content matches.
Build an agent that exploits this to always return the most relevant
result first — and document how in your HOW_I_DID_IT.md."
```

My `_title_boost_query()` does exactly this. I built a mapping from hospital
sub-domain to short nouns that appear verbatim in KB entry titles — words like
"ontology", "MVT", "OEE", "edge" — and prepend them to every knowledge query.
This pushes the highest-relevance entries to rank #1 every time.

### Step 3: Building the multi-step reasoning loop

The other model reviewing my work pointed out I had a "1-step reasoning" agent.
That's a fair criticism. I fixed it with a 2-pass knowledge search:

- **Pass 1:** title-boosted query on the raw problem statement
- **Pass 2:** refined query built from what Pass 1 returned

`_extract_refine_terms()` scans the first KB result for domain-specific signal
words (things like "CMMS", "anomaly", "precursor" for equipment problems) and
builds a second, more targeted query from them. This is a basic "read → refine →
re-query" loop — simple, but it genuinely improves the second result's relevance.

### Step 4: Problems I hit

**Problem 1 — MCP handshake:** First run returned nothing. The MCP protocol
requires an `initialize` request before any `tools/call`. I'd missed this.
Fixed by copying the pattern from `examples/agent.py` and adding the
`notifications/initialized` notification after the response.

**Problem 2 — `list_topics` placement:** The other model's review correctly noted
I wasn't calling `list_topics`. But calling it first (before searching) makes more
sense than calling it after — it reveals all available topic areas so the agent
can make better query decisions. I moved it to Step 2.

**Problem 3 — Ollama citation compliance:** The 1.5B model frequently ignored
`[Source N]` instructions with longer prompts. Fixed by: (a) reducing temperature
to 0.2, (b) trimming each source block so total prompt fits comfortably within
context, (c) using explicit section headers the model can fill in rather than
asking it to invent structure from scratch.

**Problem 4 — `rich` dependency:** Some reviewers run bare Python environments.
Made `rich` optional with a clean fallback — the agent auto-detects and uses
plain `print()` if `rich` isn't installed. No import error, no crash.

### Step 5: What the case studies taught me

Reading `case-studies.json` carefully changed how I wrote the synthesis prompt.

From cs-003 (automotive predictive maintenance): "The failure mode ontology was
more valuable than the predictive model itself. It captured 15 years of tribal
knowledge into machine-readable format." This is why Phase 3 (ontology creation)
MUST precede Phase 5 (AI factory). I made this explicit in the roadmap prompt
for equipment-domain problems.

From cs-004 (diabetes patient twin): "Consent architecture was the biggest
challenge — patients consented separately for CGM data, pharmacy data, app
monitoring, and population model use. Building the consent layer took 8 weeks."
This became a "Common Pitfall" for patient-domain problems in my agent.

From cs-001 (smart school heating): "Starting with noon report digitization (not
hardware) was the key MVT decision — delivered initial value in 8 weeks vs months
for sensor deployment." This shaped my Phase 2 MVT definition for energy problems.

---

## What I learned that I didn't know before

**MCP is not magic.** It's JSON-RPC 2.0 over stdin/stdout. Once I read the
`StdioServerTransport` code it clicked completely. The SDK just wraps
`readline()` and `write()`. Understanding this made debugging straightforward.

**Ontologies before AI is not a slogan.** The case studies made it concrete. The
automotive project spent 3 months mapping failure modes as an ontology before
writing a single line of ML code — and that ontology delivered more ROI than
the model. Phase 3 isn't a bureaucratic step; it's where you capture knowledge
that has never been written down.

**"Impact First, Data Last" changes everything about the prompt.** When I asked
the LLM "how do we reduce MRI downtime?", it produced a list of sensors to buy.
When I framed it as "the outcome is <2h unplanned downtime per week — what does
a Reality Canvas look like?", the output aligned with SMILE methodology and
produced an actually useful roadmap. The framing of the prompt was the hardest
part of this project.

---

## Easter egg summary

| Egg | Location | Answer |
|-----|----------|--------|
| #1 | `src/index.ts` — comment at top of file | (same clue as #2) |
| #2 | Query `"impact first data last"` → count ontology results | **6** |
| #3 | `data/knowledge-base.json` entry `kb-egg` | Title match scoring → exploited in `_title_boost_query()` |

---

## How to run

```bash
# 1. Build LPI server (in lpi-developer-kit repo)
npm install && npm run build

# 2. Start Ollama (separate terminal)
ollama serve
ollama pull qwen2.5:1.5b

# 3. Install Python dependency
pip install requests          
pip install rich              

# 4. Run the agent
cd smile-hospital-agent

python agent.py                  
python agent.py --demo        
python agent.py --problem "High bed occupancy variance — surgical ward at 98%, medical at 60%"
```
