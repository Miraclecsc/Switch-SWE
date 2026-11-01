import test from "node:test"
import assert from "node:assert/strict"
import { mkdtemp, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { createServer } from "node:http"

test("the provider adapter makes bounded JSON analysis calls without forwarding the key as content", async () => {
  const exports = await import("../analyzer.mjs").catch(() => ({}))
  assert.equal(typeof exports.createAnalyzer, "function", "the analyzer adapter must exist")
  const requests = []
  const server = createServer(async (req, res) => {
    let body = ""
    for await (const chunk of req) body += chunk
    requests.push({ body: JSON.parse(body), authorization: req.headers.authorization, path: req.url })
    res.writeHead(200, { "content-type": "application/json" })
    res.end(JSON.stringify({ choices: [{ message: { content: JSON.stringify({
      context_id: "topic", title: "Topic", confidence: 0.95,
      related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [],
    }) } }], usage: { prompt_tokens: 20, completion_tokens: 10 } }))
  })
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve))
  try {
    const analyze = exports.createAnalyzer({
      configuration: () => ({ provider: { local: { options: {
        baseURL: `http://127.0.0.1:${server.address().port}/v1`, apiKey: "local-secret",
      } } } }),
    })
    const result = await analyze("route", { current: { id: "u1", text: "Investigate JSON parsing" } }, { providerID: "local", modelID: "local-model" })
    assert.equal(result.context_id, "topic")
    assert.equal(requests.length, 1)
    assert.equal(requests[0].path, "/v1/chat/completions")
    assert.equal(requests[0].authorization, "Bearer local-secret")
    assert.ok(!JSON.stringify(requests[0].body).includes("local-secret"))
    assert.equal(requests[0].body.model, "local-model")
  } finally {
    await new Promise(resolve => server.close(resolve))
  }
})

test("plugin compaction transform passes through, while its normal transform preserves array identity", async () => {
  const plugin = (await import("../plugin.mjs").catch(() => ({}))).default
  assert.equal(typeof plugin, "function", "the plugin entry must exist")
  const directory = await mkdtemp(join(tmpdir(), "context-plugin-test-"))
  try {
    const hooks = await plugin({ directory, project: { id: "project" }, client: {} }, { mode: "off", stateDirectory: directory })
    const messages = [{
      info: { id: "u1", sessionID: "s1", role: "user", model: { providerID: "local", modelID: "model" } },
      parts: [{ id: "p1", type: "text", text: "Original request" }],
    }]
    const output = { messages }
    await hooks["experimental.session.compacting"]({ sessionID: "s1" }, { context: [] })
    await hooks["experimental.chat.messages.transform"]({}, output)
    assert.equal(output.messages, messages)
    assert.equal(messages[0].parts[0].text, "Original request")
    await hooks["experimental.chat.messages.transform"]({}, output)
    assert.equal(output.messages, messages)
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
})
