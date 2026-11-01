Complete the text-mode contract for UTF-16, the configured errors policy, and newline='', '\n', '\r', and '\r\n' as well as newline=None. Rollover must preserve the stored encoded bytes and text behavior without decoding/re-encoding damage or repeated newline translation. Preserve tell()/seek() cookies, including after partial reads. Text write()/writelines() must also retain data and cursor across allocation failure and retry, and honor max_size=0. document the behavior and add regression tests.

That should be enough. Send the complete patch.

Respond with strict JSON:
{"task_id": "task_4ea4b4c28d9514ca1020995da71d3790", "analysis": "...", "patch": "<unified diff>"}
The patch must be a standalone unified diff applying at the original base commit.