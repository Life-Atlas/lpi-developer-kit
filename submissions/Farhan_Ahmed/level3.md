# Level 3 Submission — Farhan Ahmed Siddique

**Track:** A — Agent Builders  
**GitHub:** [Farhan-Ahmed-code](https://github.com/Farhan-Ahmed-code)

---

## Agent

Code is in `submissions/Farhan_Ahmed/level3-agent/`.  
*(Also available as a standalone repo — link below once pushed)*

### What the agent does
- Accepts any question about SMILE / digital twins
- Queries **4 LPI tools**: `smile_overview`, `smile_phase_detail`, `query_knowledge`, `get_case_studies`
- Sends combined context to `qwen2.5:1.5b` via Ollama
- Returns a cited, provenance-tracked answer

### How to run
```bash
pip install requests
python submissions/Farhan_Ahmed/level3-agent/agent.py "What is SMILE?"
python submissions/Farhan_Ahmed/level3-agent/agent.py --interactive
```

---

## Checklist

- [x] Accepts user input (CLI arg or interactive)
- [x] Queries 4 LPI tools (≥ 2 required)
- [x] Cites which tools provided which parts of the answer
- [x] Uses local LLM via Ollama (`qwen2.5:1.5b`)
- [x] Provenance section printed after every answer
- [x] HOW_I_DID_IT.md included
