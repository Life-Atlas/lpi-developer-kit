# Security Audit

## What I Tried

I tried breaking the system using:

- empty input  
- random strings  
- incomplete data  

---

## Observations

The system initially failed on missing inputs.

---

## Fixes

I added:

- default fallback values  
- error handling  
- output sanitization  

---

## Result

The system now handles invalid inputs and tool failures without crashing.