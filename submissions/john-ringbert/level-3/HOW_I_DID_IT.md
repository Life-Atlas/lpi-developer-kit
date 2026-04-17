How I did it

For this part I ran the vulnerable API locally in the sandbox and tested the endpoints manually.

I used a mix of curl, simple manual request testing and basic fuzzing-style tests to see how the API responded to different kinds of input. That helped me find several weaknesses in how the API handled input, exposed information and let certain actions happen.

After that I reviewed the code in examples/vulnerable-api.py to confirm what was causing the issues and understand them better.

Once I had the main findings I matched them with OWASP and also read more about the impact and possible fixes for each one.

That made it easier to connect what I found during testing with the actual problems in the file like command injection, SQL injection risk, hardcoded secrets, debug information leakage, weak admin authentication and reflected XSS.

