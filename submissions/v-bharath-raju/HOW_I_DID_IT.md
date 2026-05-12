# HOW I DID IT

## Approach

I started by running the vulnerable API locally using Flask. I explored all endpoints manually using a browser and tested them with different types of inputs such as:

- SQL injection payloads
- Command execution inputs
- Script injection
- Invalid and empty values

## Tools Used

I used the LPI sandbox tools to understand digital twin concepts and validate system behavior:

- query_knowledge("explainable AI")
- get_insights("personal health digital twin")

These tools helped me understand how secure systems should behave and how data should be handled properly.

## Observations

While testing, I identified multiple vulnerabilities including:

- SQL Injection
- Command Injection
- XSS
- Hardcoded secrets
- Debug data exposure

## Challenges

- Understanding how inputs break backend logic
- Interpreting error messages and linking them to vulnerabilities

## What I would improve

- Automate testing using scripts instead of manual testing
- Add input validation layer
- Improve logging and error handling