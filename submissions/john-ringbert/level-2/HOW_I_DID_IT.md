**How I did it**

I first ran the sandbox the normal way just to see that everything worked before I started messing with it.

After that I used the test client and changed the inputs to see how the different tools reacted when I sent unusual or clearly wrong input.

I tried things I have come across in earlier courses like empty values, spaces only, wrong values, special characters, emojis, and long strings.

I mostly focused on `query_knowledge`, `get_case_studies`, `get_insights`, `smile_phase_detail` and `get_methodology_step` because they felt like the most relevant ones to test from a QA and security angle.

What stood out to me was that the sandbox felt pretty stable overall. I was not able to make it crash even when I sent a lot of unusual input.

At the same time I noticed that the validation was a bit uneven. Some inputs gave clear error messages while others were accepted even though they probably should have been rejected more clearly.

