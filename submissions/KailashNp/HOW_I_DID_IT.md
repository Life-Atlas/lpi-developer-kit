# HOW I DID IT — Kailash Narayana Prasad
## What I did 
First, I ran the LPI sandbox using the provided commands to make sure everything was working correctly. All the tools returned PASS initially, so I knew the setup was fine.
After that, I opened the test-client.ts file to understand how the tools were being called. Once I saw the structure, I started modifying the inputs manually instead of using normal queries.

I added different types of inputs such as:
- very long strings
- special characters
- empty values
- null values
- incorrect data types like numbers

Then I ran the test client again using `npm run test-client` and observed the outputs for each case carefully.

## Problems I faced and how I solved them

At the beginning, I wasn’t sure where exactly to modify the inputs. I initially thought I had to change something in the backend, but after exploring the project structure, I realized everything I needed was inside test-client.ts.
Another issue was understanding the results. Some tests were showing PASS even when there were clear errors in the output. For example, when I passed a number instead of a string, it showed an error like "input.slice is not a function", but the system still marked it as PASS.
This confused me at first, but then I realized this itself is a bug — the system is not correctly reporting failures. After that, I started paying more attention not just to PASS/FAIL but also to the actual error messages printed.

## What I learned

Before this task, I used to think that if a system doesn’t crash, it’s working fine. But this exercise showed me that even if something looks like it’s working, there can still be hidden issues.
I learned how important input validation is, especially type checking. The system assumed inputs were always strings, which caused runtime errors when I passed numbers.
I also learned that proper error reporting is just as important as handling errors. If a system shows PASS even when something fails internally, it can mislead developers.
Overall, this task helped me think more like a tester — not just using the system normally, but actively trying to break it and understand how it behaves in edge cases.