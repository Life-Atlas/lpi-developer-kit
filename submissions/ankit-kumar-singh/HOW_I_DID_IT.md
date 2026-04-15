# HOW I DID IT — Level 2

## Steps I followed

I started by cloning the repository to my local system and installing all the required dependencies using npm.

After that, I built the project using the TypeScript compiler and ran the test client to verify if everything was working correctly. The output showed that all the tools were running successfully, which confirmed that the setup was done properly.

Next, I used Ollama to run a local language model. I pulled the qwen2.5:1.5b model and tested it by interacting with it through the terminal, which confirmed that the model was working correctly.

---

## Problems I faced

While setting up the project, I initially wanted to confirm whether dependency isolation was required, as I am more familiar with Python environments. After going through the setup, I understood that npm manages dependencies locally within the project.

---

## What I learned

I gained a clearer understanding of how MCP-based systems allow querying specific tools instead of relying only on raw LLM responses, making outputs more structured and explainable.

---

## SMILE Reflection

1. I was surprised by how the SMILE methodology is divided into clear phases, which makes complex implementations easier to understand.

2. The inclusion of case studies and insights makes the system feel practical and connected to real-world use cases.

3. The most interesting part for me was how the system combines structured tools with AI to produce more reliable and explainable results.
