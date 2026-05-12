# Threat Model

## My Approach

My approach was to analyze security risks based on how users interact with the system.

---

## Threats Considered

1. Prompt Injection  
User input attempting to override logic  

2. Invalid Input  
Malformed or missing values  

3. Data Leakage  
Exposure of internal system behavior  

4. Tool Failure  
Unexpected or invalid responses from LPI  

---

## Mitigation

- input validation  
- fallback responses  
- structured JSON flow  
- controlled output handling  