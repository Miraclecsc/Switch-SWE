Extend the CR/LF rejection requirement to all serialized fields, including shapes, emitted attribute names/values and other emitted tokens. make_qstr must reject literal CR or LF. Validate the entire graph before generate_pajek yields its first line or write_pajek writes any bytes to a caller-owned stream, even if the invalid field is on the last edge. Preserve the existing warnings/omission policy for ignored optional attributes. The no-partial-output guarantee applies to these invalid fields; general I/O failures and concurrent mutation are outside its scope.

That should be enough. Send the complete patch.

Respond with strict JSON:
{"task_id": "task_efe550fa0d2fce865afc950971e46389", "analysis": "...", "patch": "<unified diff>"}
The patch must be a standalone unified diff applying at the original base commit.