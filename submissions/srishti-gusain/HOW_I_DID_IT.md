# How I Built the Smart Health Advisor Agent

## Objective
To build a structured AI agent that uses LPI tools to provide meaningful health recommendations.

---

## Approach
- Used the LPI agent framework (agent.py)
- Built a wrapper agent (health_agent.py)
- Combined multiple tool outputs into a single response

---

## Tools Used
- smile_overview → structured framework
- query_knowledge → health-related insights
- get_case_studies → contextual understanding

---

## Explainability Strategy
The agent explains:
- Why suggestions are given
- What knowledge sources were used
- How conclusions were formed

---

## Challenges
- Understanding how to integrate tool outputs
- Structuring output clearly for users

---

## Future Improvements
- Add personalization
- Integrate real-time health data
- Improve response formatting
