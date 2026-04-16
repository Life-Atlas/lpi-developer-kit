# HOW I DID IT - level 2

## WHAT I DID STEP BY STEP 
1) I Forked the repository and cloned it to my local system . 
2) then I installed the dependencies using npm install also check my node version 
3) When I tried to follow the instructions (npm run build and npm run test-client ) they didnt work 
4) then I checked the project files and realized those scripts were not present 
5) then I install ollama using "irm https://ollama.com/install.ps1 | iex" and run the command "ollama run llama3" 

### PROBLEMS I FACED 
Initially, the given commands didn’t work because the repository didn’t have the expected scripts.This confused me, but I checked package.json and confirmed it.
Then I faced errors like "Cannot find module" and "Unknown file extension .ts".
I realized this was due to missing compiled files and Node.js version differences. I solved this by compiling the TypeScript code manually using npx tsc.
I also made mistakes like running commands in the wrong directory, which caused file not found errors. Once I switched to the correct folder, it worked.
Overall, I had to debug step by step instead of relying only on instructions.


## WHAT I LEARNT 
I learned that real world problems dont always match the documentation and its very much important to explore and understand the codefirst 
Node.js version ad module system can affect execution 
I learned how to debug errors logically instead of getting stuck 
