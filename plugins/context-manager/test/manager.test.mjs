import test from "node:test"
import assert from "node:assert/strict"
import { mkdtemp, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"

async function api() {
  return import("../manager.mjs").catch(() => ({}))
}

const user = (id, text, sessionID = "session-one") => ({
  info: { id, sessionID, role: "user", agent: "build", model: { providerID: "local", modelID: "model" } },
  parts: [{ id: `${id}-text`, sessionID, messageID: id, type: "text", text }],
})
const assistant = (id, parentID, text) => ({
  info: { id, parentID, sessionID: "session-one", role: "assistant", finish: "stop", time: { completed: 1 } },
  parts: [{ id: `${id}-text`, type: "text", text }],
})
const tool = (id, parentID) => ({
  info: { id, parentID, sessionID: "session-one", role: "assistant", finish: "tool-calls" },
  parts: [{
    id: `${id}-tool`, type: "tool", callID: "call-7", tool: "bash",
    state: { status: "completed", input: { command: "run tests" }, output: "2 passed", time: { start: 1, end: 2 } },
  }],
})

async function fixture(fn) {
  const directory = await mkdtemp(join(tmpdir(), "context-manager-test-"))
  try {
    const exports = await api()
    assert.equal(typeof exports.createManager, "function", "the generic manager must exist")
    await fn(exports.createManager, directory)
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
}

test("off preserves all native messages exactly and performs no analysis", async () => fixture(async (create, directory) => {
  let calls = 0
  const manager = create({ stateDirectory: directory, mode: "off", analyze: async () => { calls++ } })
  const messages = [user("u1", "Fix authentication"), tool("a1", "u1"), user("u2", "Review CSV export")]
  assert.deepEqual(await manager.transform(messages), messages)
  assert.equal(calls, 0)
}))

test("returning to a context selects its original turns without rewriting the current request or tools", async () => fixture(async (create, directory) => {
  const analyze = async (kind, request) => {
    assert.equal(kind, "route")
    const text = request.current.text
    return {
      context_id: text.includes("CSV") ? "csv" : "login",
      title: text.includes("CSV") ? "CSV export" : "Authentication",
      confidence: 0.95, related_context_ids: [], shared_turn_ids: [],
      evidence_turn_ids: text.includes("Return") ? ["u1"] : [],
    }
  }
  const manager = create({ stateDirectory: directory, mode: "a", analyze })
  const messages = [user("u1", "Fix authentication")]
  await manager.transform(messages)
  messages.push(assistant("a1", "u1", "Checked the cookie parser"), user("u2", "Review CSV export"))
  await manager.transform(messages)
  messages.push(assistant("a2", "u2", "Checked CSV escaping"), user("u3", "Return to authentication"), tool("a3", "u3"))
  const before = structuredClone(messages)
  const output = await manager.transform(messages)
  assert.deepEqual(messages, before)
  assert.deepEqual(output.map(m => m.info.id), ["u1", "a1", "u3", "a3"])
  assert.deepEqual(output.at(-1), messages.at(-1))
  assert.deepEqual(output.find(m => m.info.id === "u3"), messages.find(m => m.info.id === "u3"))
}))

test("uncertain routing retains every original turn", async () => fixture(async (create, directory) => {
  const manager = create({ stateDirectory: directory, mode: "a", analyze: async () => ({
    context_id: "uncertain", title: "Unresolved", confidence: 0.2,
    evidence_turn_ids: [], related_context_ids: [], shared_turn_ids: [],
  }) })
  const messages = [user("u1", "Investigate the parser"), assistant("a1", "u1", "Started"), user("u2", "Do the other one")]
  assert.deepEqual(await manager.transform(messages), messages)
}))

test("CLI restarts reuse the same route and do not analyze a tool continuation twice", async () => fixture(async (create, directory) => {
  let calls = 0
  const analyze = async () => {
    calls++
    return { context_id: "parser", title: "Parser", confidence: 0.95, evidence_turn_ids: [], related_context_ids: [], shared_turn_ids: [] }
  }
  const first = create({ stateDirectory: directory, mode: "a", analyze })
  await first.transform([user("u1", "Fix the parser")])
  const second = create({ stateDirectory: directory, mode: "a", analyze })
  await second.transform([user("u1", "Fix the parser"), tool("a1", "u1")])
  assert.equal(calls, 1)
}))

test("X updates completed-state memory, while the current user and stored history remain unchanged", async () => fixture(async (create, directory) => {
  const kinds = []
  const analyze = async (kind) => {
    kinds.push(kind)
    if (kind === "memory") return {
      goal: "Fix the parser", constraints: [{ text: "Preserve whitespace", source_ids: ["u1"] }],
      progress: [{ text: "The earlier test reported 2 passed", source_ids: ["a1"] }],
      pending: ["Inspect empty input"], files: [], uncertainties: [],
    }
    return { context_id: "parser", title: "Parser", confidence: 0.95, evidence_turn_ids: [], related_context_ids: [], shared_turn_ids: [] }
  }
  const manager = create({ stateDirectory: directory, mode: "x", analyze })
  await manager.transform([user("u1", "Fix the parser. Preserve whitespace.")])
  const messages = [user("u1", "Fix the parser. Preserve whitespace."), tool("a1", "u1"), user("u2", "Now inspect empty input")]
  const before = structuredClone(messages)
  const output = await manager.transform(messages)
  assert.deepEqual(messages, before)
  assert.ok(kinds.includes("memory"))
  const current = output.find(m => m.info.id === "u2")
  assert.equal(current.parts.at(-1).text, "Now inspect empty input")
  assert.match(current.parts[0].text, /Preserve whitespace/)
  assert.match(current.parts[0].text, /historical/i)
}))

test("analysis errors preserve the input instead of losing context", async () => fixture(async (create, directory) => {
  const manager = create({ stateDirectory: directory, mode: "x", analyze: async () => { throw new Error("unavailable") } })
  const messages = [user("u1", "Continue working")]
  assert.deepEqual(await manager.transform(messages), messages)
}))

test("session identities remain isolated", async () => fixture(async (create, directory) => {
  let calls = 0
  const manager = create({ stateDirectory: directory, mode: "a", analyze: async () => {
    calls++
    return { context_id: "one", title: "One", confidence: 1, evidence_turn_ids: [], related_context_ids: [], shared_turn_ids: [] }
  } })
  await manager.transform([user("u1", "Task one", "session-one")])
  await manager.transform([user("u1", "Task two", "session-two")])
  assert.equal(calls, 2)
}))

test("A and X submit identical routing inputs; memory is the only additional semantic mechanism", async () => fixture(async (create, directory) => {
  const routed = { a: [], x: [] }
  for (const mode of ["a", "x"]) {
    const manager = create({
      stateDirectory: join(directory, mode), mode,
      analyze: async (kind, request) => {
        if (kind === "memory") return {
          goal: "Parser", constraints: [{ text: "Keep empty fields", source_ids: ["u1"] }],
          progress: [{ text: "Parser was inspected", source_ids: ["a1"] }],
          pending: [], files: [], uncertainties: [],
        }
        routed[mode].push(structuredClone(request))
        return { context_id: "parser", title: "Parser", confidence: 0.99, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
      },
    })
    await manager.transform([user("u1", "Fix parser; keep empty fields")])
    await manager.transform([
      user("u1", "Fix parser; keep empty fields"),
      assistant("a1", "u1", "Parser was inspected"),
      user("u2", "Continue with quoted fields"),
    ])
  }
  assert.deepEqual(routed.a, routed.x)
}))

test("long completed interactions are summarized in bounded batches without skipping messages", async () => fixture(async (create, directory) => {
  const seen = new Set()
  const sizes = []
  const manager = create({
    stateDirectory: directory, mode: "x", memoryInputChars: 24000,
    analyze: async (kind, request) => {
      if (kind === "route") return { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
      sizes.push(JSON.stringify(request).length)
      if (sizes.at(-1) > 24000) throw new Error("Analysis input exceeds bound")
      for (const turn of request.completed_interactions) for (const message of turn.messages) seen.add(message.id)
      return { goal: "Parser", constraints: [{ text: "Keep empty fields", source_ids: ["u1"] }], progress: [], pending: [], files: [], uncertainties: [] }
    },
  })
  const first = user("u1", "Fix parser; keep empty fields")
  await manager.transform([first])
  const earlier = Array.from({ length: 24 }, (_, i) => assistant("a" + i, "u1", "evidence ".repeat(650)))
  const output = await manager.transform([first, ...earlier, user("u2", "Continue the parser work")])
  assert.ok(sizes.length > 1)
  assert.ok(sizes.every(size => size <= 24000))
  assert.equal(seen.size, 25)
  assert.match(output.at(-1).parts[0].text, /Historical context state/)
}))

test("failed memory preparation is attempted once per user turn, not on every tool step", async () => fixture(async (create, directory) => {
  let calls = 0
  const manager = create({
    stateDirectory: directory, mode: "x",
    analyze: async kind => {
      if (kind === "memory") { calls++; throw new Error("Provider unavailable") }
      return { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
    },
  })
  const first = user("u1", "Inspect parser")
  await manager.transform([first])
  const history = [first, assistant("a1", "u1", "Inspected"), user("u2", "Continue")]
  await manager.transform(history)
  await manager.transform([...history, tool("a2", "u2")])
  assert.equal(calls, 1)
}))

test("failed routing is cached as an abstention and unassigned history survives later selection", async () => fixture(async (create, directory) => {
  let calls = 0
  const manager = create({
    stateDirectory: directory, mode: "a",
    analyze: async (_kind, request) => {
      calls++
      if (request.current.id === "u1") throw new Error("Provider unavailable")
      return { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
    },
  })
  const first = user("u1", "Preserve the earlier requirement")
  await manager.transform([first])
  await manager.transform([first, tool("a1", "u1")])
  const output = await manager.transform([first, assistant("a1", "u1", "Noted"), user("u2", "Work on the parser")])
  assert.equal(calls, 2)
  assert.ok(output.some(message => message.info.id === "u1"))
}))

test("memory compression retains original user requirements even when a summary omits them", async () => fixture(async (create, directory) => {
  const manager = create({
    stateDirectory: directory, mode: "x",
    analyze: async kind => kind === "route"
      ? { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
      : { goal: "Parser", constraints: [], progress: [], pending: [], files: [], uncertainties: [] },
  })
  const first = user("u1", "Preserve the public signature and accept empty strings.")
  const history = [first]
  await manager.transform(history)
  let output
  for (let i = 2; i <= 5; i++) {
    history.push(assistant("a" + (i - 1), "u" + (i - 1), "Inspected implementation"))
    history.push(user("u" + i, "Continue the parser work"))
    output = await manager.transform(history)
  }
  assert.deepEqual(output.find(message => message.info.id === "u1"), first)
  assert.ok(!output.some(message => message.info.id === "a1"))
}))

test("bounded tool evidence preserves the beginning and final outcome of long output", async () => fixture(async (create, directory) => {
  let evidence = ""
  const manager = create({
    stateDirectory: directory, mode: "x",
    analyze: async (kind, request) => {
      if (kind === "route") return { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
      evidence = JSON.stringify(request)
      return { goal: "Parser", constraints: [], progress: [], pending: [], files: [], uncertainties: [] }
    },
  })
  const first = user("u1", "Inspect the test output")
  await manager.transform([first])
  const execution = tool("a1", "u1")
  execution.parts[0].state.output = "START_OF_OUTPUT\n" + "x".repeat(18000) + "\nFINAL_TEST_FAILURE"
  await manager.transform([first, execution, user("u2", "Continue")])
  assert.match(evidence, /START_OF_OUTPUT/)
  assert.match(evidence, /FINAL_TEST_FAILURE/)
  assert.match(evidence, /omitted/)
}))

test("memory that exceeds the injection budget cannot replace its original evidence", async () => fixture(async (create, directory) => {
  const manager = create({
    stateDirectory: directory, mode: "x", memoryChars: 1000,
    analyze: async kind => kind === "route"
      ? { context_id: "parser", title: "Parser", confidence: 1, related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
      : { goal: "Parser", constraints: [], progress: [{ text: "Detailed earlier observation. ".repeat(100), source_ids: ["u1"] }],
        pending: ["A final unresolved observation must remain available"], files: [], uncertainties: [] },
  })
  const history = [user("u1", "Inspect the parser")]
  await manager.transform(history)
  let output
  for (let i = 2; i <= 5; i++) {
    history.push(tool("a" + (i - 1), "u" + (i - 1)))
    history.push(user("u" + i, "Continue the parser work"))
    output = await manager.transform(history)
  }
  assert.deepEqual(output, history, "retain the original exchanges when their complete memory does not fit")
}))
