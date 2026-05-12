What I did
I cloned the project, opened it in VS Code, and ran npm install to install dependencies. Then I ran npm run build to compile the project and npm run test-client to check if everything was working. The tests ran successfully.

For the LLM setup, I installed Ollama. Instead of trying heavier models, I directly used a lightweight model (TinyLlama), which ran smoothly on my system. I verified it with a simple prompt.

Problems I faced and how I solved them
I faced path-related issues while running npm commands locally. Some scripts were not executing properly due to incorrect paths. I fixed this by adjusting the project directory structure and ensuring commands were run from the correct root folder.

What I learned
I learned how to set up and run a project end-to-end using npm. I also understood how small environment issues like incorrect paths can affect execution. Additionally, I gained basic experience running a local LLM and choosing a model that fits system constraints.