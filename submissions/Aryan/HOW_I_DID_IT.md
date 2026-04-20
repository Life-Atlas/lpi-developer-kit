# How I Did It - Level 3

### What I did, step by step

After completing level 2, I moved to Track A and focused on building a real agent instead of just demonstrating tool calls. My goal was to create something that actually answers a meaningful question by combining multiple sources rather than returning raw outputs.

I started by exploring the LPI developer kit and understanding how the MCP-style communication works. The example agent helped me see how subprocess communication and JSON-RPC requests are structured, but it wasn’t immediately clear how real tool execution works beyond the demo.

Then I defined a clear use case instead of keeping it generic. I chose a specific query: “How are digital twins used in healthcare?” This helped me design the agent around combining conceptual understanding and real-world examples.

For tool selection, I intentionally kept it minimal and focused. I used `smile_overview` for methodology and `get_case_studies` for practical implementations. The idea was to combine theory and application instead of relying on a single source.

Next, I implemented the MCP connection using Python subprocess. I tested each tool call individually to confirm that the responses were coming back correctly. Initially, I used `test-client.js`, but I realized it only runs demo tests and does not return actual tool outputs. I switched to `dist/src/index.js` and added the required initialization step (`notifications/initialized`) to make real tool calls work.

Once tool calls were working, I handled response parsing. The outputs were nested JSON structures, so I extracted the actual content from `result → content → text`. After that, I added logic to filter the case studies so that only healthcare-related content is returned instead of unrelated examples.

Finally, I structured the output into clear sections — SMILE summary, case study summary, analysis, and conclusion — so that the response is readable and explainable instead of just dumping raw text.

---

### What problems I hit and how I solved them

The first major issue was that tool calls were not returning real data. This happened because I was using `test-client.js`, which only executes predefined test cases. I fixed this by switching to the actual LPI server (`dist/src/index.js`).

The second issue was that even after switching, the agent returned empty outputs. This was because I had not sent the initialization message. Once I added the JSON-RPC initialization step, the tool calls started working correctly.

Another problem was incomplete or empty responses. Initially, I used `readline()` to capture output, which only reads partial data. I replaced it with `process.communicate()` to capture the full response.

I also faced an issue where the agent returned irrelevant case studies (like smart buildings instead of healthcare). To fix this, I modified the tool query to `"healthcare digital twin"` and added filtering logic to extract only the relevant section.

Finally, summarization was breaking structured headings like `# S.M.I.L.E.` because I was splitting text by sentences. I switched to simple truncation (`text[:400]`) to preserve formatting.

---

### What I learned that I didn't know before

I didn’t fully understand how MCP-style communication works before this. Going through the JSON-RPC flow manually — initialization, notifications, and tool calls — made it clear that it’s essentially structured communication over stdin/stdout.

I also realized that connecting tools correctly is more important than the complexity of the agent itself. Most of the work was not in building logic, but in making sure data flows correctly between systems.

Another key learning was that raw tool output is not useful by default. Without filtering and structuring, the responses are noisy and hard to interpret. Once I filtered and structured the output, the quality improved significantly.

I also learned that relevance matters more than volume. Returning fewer but targeted results (like healthcare-specific case studies) is much better than returning everything.

Finally, I understood that simplicity is effective. The final agent only uses two tools with basic parsing and structuring, but it produces reliable and meaningful results.
