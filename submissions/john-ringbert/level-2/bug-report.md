**Bug report**

**What I tested**

I ran the LPI sandbox locally and tested it with empty inputs, whitespace-only inputs, invalid values, special characters, emoji, long queries, and some light stress testing.

**What worked**

The sandbox was stable overall and nothing fully crashed.

Most of the tools kept working even when I sent unusual input.

Some required fields were also handled clearly for example when `phase` or `query` were empty.

**What did not work as expected**

Some invalid input was still accepted instead of being rejected more clearly.

A query with only spaces returned results instead of being treated as empty input.

In `get_insights` both an empty `tier` and an invalid value like `skumtomte` still returned normal output.

When I tested wrong data types I also got internal error messages such as `input.slice is not a function` which feels like something users probably should not see.

**Error messages I got**

Some of the error messages I got were:

* `Error: 'phase' parameter is required.`
* `Error: 'query' parameter is required.`
* `input.slice is not a function`
* `input.slice(...).replace is not a function`
* `MaxListenersExceededWarning: Possible EventEmitter memory leak detected`


