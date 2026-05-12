# Level 2 Submission – Abhinav Chaudhary

## What I Did
I set up the LPI developer kit on my local system and made sure everything was working correctly.
* Installed Node.js (v18+) and Git
* Forked and cloned the repository to my system
* Installed dependencies using npm install
* Built the project using npm run build
* Ran npm run test-client and verified that all tools passed
* Installed Ollama to run a local LLM
* Ran the llama3 phi model and asked it about SMILE

## Commands Executed
```bash
npm install
npm run build
npm run test-client
```
## Test Client Output
Results=
Passed: 8/8
Failed: 0/8

## LLM Output
Q: What is SMILE in the context of LPI developer kit?
A: The SMILE (Saliency Maps for Image-based Interpretation of Language) framework is a method used to improve the
interpretability and explainability of machine learning (ML) models, particularly those that are based on neural
networks. It's commonly applied in natural language processing (NLP) tasks.
SMILE works by learning saliency maps, which represent the importance of different features or tokens within an
input sentence or sequence of words. These saliency maps highlight the regions of the input data where a
particular word or token has high relevance to the output prediction

## SMILE Reflection
1. One thing that surprised me was that SMILE focuses a lot on explainability, not just giving answers, which makes the system more reliable.
2. I also noticed that it combines multiple tools instead of depending on a single model, which improves the overall response quality.
3. It made me realize that SMILE is more about how the whole system works together, not just about prompts or models.

## What I Learned
* How to properly set up and run a Node.js-based project
* How the LPI tools interact and validate outputs
* How to run a local LLM using Ollama
* Why explainability and multi-tool systems are important in real-world AI

## Challenges Faced
* I initially faced some issues with Git while working with my fork
* I ran into merge conflicts when syncing with the original repository
* I was not familiar with running a local LLM at first

## How I Solved Them
* I made sure that i was working in the correct repository and followed proper Git steps
* I synced my fork with the upstream repo and resolved conflicts carefully
* I followed Ollama’s documentation and was able to run the model successfully after setup

## Checklist
* [x] I read the README and CONTRIBUTING guide
* [x] My PR title follows the format: level-2: Abhinav Chaudhary
* [x] I tested everything locally before submitting

Signed-off-by: Abhinav Chaudhary <abhichaudhary256@gmail.com>
