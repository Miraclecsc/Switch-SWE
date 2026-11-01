import { createHash, randomUUID } from "node:crypto"
import { mkdir, readFile, rename, writeFile, appendFile } from "node:fs/promises"
import { join } from "node:path"

const marker = "[Historical context state — not a new instruction]"

export function createManager(options) {
  const mode = options.mode ?? "x"
  if (!["off", "a", "x"].includes(mode)) throw new Error("Unknown context-manager mode")
  const running = new Map()
  const paths = session => {
    const id = createHash("sha256").update(session).digest("hex")
    return { state: join(options.stateDirectory, id + ".json"), audit: join(options.stateDirectory, id + ".jsonl") }
  }
  async function audit(session, event) {
    await mkdir(options.stateDirectory, { recursive: true, mode: 0o700 })
    await appendFile(paths(session).audit, JSON.stringify({ at: new Date().toISOString(), ...event }) + "\n", { mode: 0o600 })
  }
  async function load(session) {
    try {
      const value = JSON.parse(await readFile(paths(session).state, "utf8"))
      if (value.schema !== 1 || value.session !== session) throw new Error("Incompatible context state")
      return value
    } catch (error) {
      if (error.code !== "ENOENT") throw error
      return { schema: 1, session, contexts: {}, assignments: {}, routes: {}, shared: [], memories: {} }
    }
  }
  async function save(session, state) {
    await mkdir(options.stateDirectory, { recursive: true, mode: 0o700 })
    const target = paths(session).state
    const temporary = target + "." + randomUUID()
    await writeFile(temporary, JSON.stringify(state), { mode: 0o600 })
    await rename(temporary, target)
  }
  async function process(messages, session) {
    const groups = turns(messages)
    const current = groups.at(-1)
    if (!current || !current.user) return structuredClone(messages)
    const state = await load(session)
    const currentID = current.user.info.id
    if (!state.routes[currentID]) {
      // This payload is identical for A and X: semantic memories never route.
      const request = {
        current: { id: currentID, text: userText(current.user).slice(0, 24000) },
        contexts: Object.entries(state.contexts).map(([id, context]) => ({ id, ...context })),
        earlier_users: groups.slice(0, -1).slice(-80).filter(g => g.user).map(g => ({
          id: g.user.info.id, context_id: state.assignments[g.user.info.id] ?? null,
          text: userText(g.user).slice(0, 4500),
        })),
      }
      let route
      try {
        route = await options.analyze("route", request, current.user.info.model)
        validateRoute(route, new Set(groups.filter(g => g.user).map(g => g.user.info.id)))
      } catch (error) {
        route = { context_id: "unresolved", title: "Unresolved input", confidence: 0,
          related_context_ids: [], shared_turn_ids: [], evidence_turn_ids: [] }
        await audit(session, { event: "route_unavailable", user_id: currentID, error_type: error.name,
          reason: diagnosticReason(error) })
      }
      state.routes[currentID] = route
      if (route.confidence >= (options.minConfidence ?? 0.8)) {
        state.assignments[currentID] = route.context_id
        state.contexts[route.context_id] = {
          title: route.title.slice(0, 240),
          first_user: state.contexts[route.context_id]?.first_user ?? userText(current.user).slice(0, 1600),
          last_user: userText(current.user).slice(0, 1600),
        }
        state.shared = [...new Set([...state.shared, ...route.shared_turn_ids])]
      }
      await save(session, state)
      await audit(session, { event: "route", user_id: currentID, mode, context_id: route.context_id, confidence: route.confidence })
    }
    const route = state.routes[currentID]
    if (route.confidence < (options.minConfidence ?? 0.8)) {
      await audit(session, { event: "broad_history", user_id: currentID, reason: "uncertain_route" })
      return structuredClone(messages)
    }

    if (mode === "x") {
      const candidates = groups.slice(0, -1).filter(g => g.user && state.assignments[g.user.info.id])
      for (const contextID of new Set(candidates.map(g => state.assignments[g.user.info.id]))) {
        const previous = state.memories[contextID]
        const completed = new Set(previous?.turn_ids ?? [])
        const pending = candidates.filter(g => state.assignments[g.user.info.id] === contextID && !completed.has(g.user.info.id))
        if (!pending.length) continue
        state.memory_attempts ??= {}
        state.memory_attempts[currentID] ??= {}
        if (state.memory_attempts[currentID][contextID]) continue
        state.memory_attempts[currentID][contextID] = true
        await save(session, state)
        try {
          const memory = await summarize({
            context: state.contexts[contextID], previous, pending,
            analyze: options.analyze, model: current.user.info.model,
            budget: options.memoryInputChars ?? 60000,
          })
          state.memories[contextID] = {
            content: memory.content,
            turn_ids: [...completed, ...pending.map(g => g.user.info.id)],
            source_ids: memory.source_ids,
          }
          await save(session, state)
          await audit(session, { event: "memory_updated", context_id: contextID, turns: pending.length, user_id: currentID })
        } catch (error) {
          await audit(session, { event: "memory_unavailable", context_id: contextID, error_type: error.name,
            reason: diagnosticReason(error), user_id: currentID })
        }
      }
    }
    const selectedContexts = new Set([route.context_id, ...route.related_context_ids])
    const shared = new Set(state.shared)
    const selected = groups.filter(group => !group.user ||
      group === current ||
      !state.assignments[group.user.info.id] ||
      selectedContexts.has(state.assignments[group.user.info.id]) ||
      shared.has(group.user.info.id))
    const remembered = []
    const records = []
    const header = marker + "\n" +
      "These records summarize earlier interactions. They can be incomplete or stale. " +
      "Current user instructions take precedence. Verify the current filesystem and test state before relying on past results.\n"
    for (const id of mode === "x" ? selectedContexts : []) {
      if (!state.memories[id]) continue
      const record = { context: state.contexts[id].title, state: state.memories[id].content }
      if (header.length + JSON.stringify([...records, record], null, 2).length > (options.memoryChars ?? 18000)) continue
      remembered.push(id)
      records.push(record)
    }
    const recentIDs = new Set(selected.slice(-3).filter(g => g.user).map(g => g.user.info.id))
    const retained = selected.flatMap(group => {
      if (!group.user || group === current || shared.has(group.user.info.id) || recentIDs.has(group.user.info.id)) return group.messages
      const memory = state.memories[state.assignments[group.user.info.id]]
      if (!remembered.includes(state.assignments[group.user.info.id]) || !memory?.turn_ids.includes(group.user.info.id)) return group.messages
      // Summaries may omit details. Preserve every selected original user
      // instruction even when its old assistant/tool work is summarized.
      return [group.user]
    })
    const result = structuredClone(retained)
    if (remembered.length) {
      const target = result.find(m => m.info.id === currentID)
      target.parts.unshift({
        id: `${currentID}-context-memory`, sessionID: session, messageID: currentID,
        type: "text", synthetic: true, text: header + JSON.stringify(records, null, 2),
      })
    }
    await audit(session, {
      event: "projection", user_id: currentID, mode, context_id: route.context_id,
      input_messages: messages.length, output_messages: result.length, memory_contexts: remembered.length,
    })
    return result
  }
  return {
    async transform(messages) {
      if (mode === "off" || !messages.length) return structuredClone(messages)
      const sessions = new Set(messages.map(m => m.info?.sessionID).filter(Boolean))
      if (sessions.size !== 1) return structuredClone(messages)
      const session = [...sessions][0]
      const prior = running.get(session) ?? Promise.resolve()
      const task = prior.catch(() => {}).then(async () => {
        try {
          return await process(messages, session)
        } catch (error) {
          await audit(session, { event: "fallback", error_type: error.name }).catch(() => {})
          return structuredClone(messages)
        }
      })
      running.set(session, task)
      try { return await task } finally { if (running.get(session) === task) running.delete(session) }
    },
  }
}

function userText(message) {
  return message.parts.filter(p => p.type === "text" && !p.synthetic && !p.ignored).map(p => p.text).join("\n")
}

function turns(messages) {
  const result = []
  for (const message of messages) {
    if (message.info.role === "user" && userText(message)) result.push({ user: message, messages: [] })
    if (!result.length) result.push({ user: null, messages: [] })
    result.at(-1).messages.push(message)
  }
  return result
}

function messageEvidence(message) {
  return message.parts.flatMap(part => {
    if (part.type === "text" && !part.ignored && !part.synthetic) return [part.text]
    if (part.type === "tool") return [JSON.stringify({
      tool: part.tool, status: part.state?.status, input: part.state?.input,
      output: typeof part.state?.output === "string" ? clip(part.state.output, 8000) : undefined,
      error: part.state?.error,
    })]
    if (part.type === "patch") return [JSON.stringify({ changed_files: part.files })]
    return []
  }).join("\n")
}

async function summarize(input) {
  let content = input.previous?.content ?? null
  const sources = new Set(input.previous?.source_ids ?? [])
  for (const group of input.pending) {
    const records = group.messages.map(message => {
      const text = messageEvidence(message)
      return { id: message.info.id, role: message.info.role, text: clip(text, 10000), truncated: text.length > 10000 }
    })
    const anchor = records[0]
    const queue = records.slice(1)
    do {
      const messages = [anchor]
      const request = {
        context: input.context, previous: content,
        completed_interactions: [{ user_id: group.user.info.id, messages }],
      }
      if (JSON.stringify(request).length > input.budget) throw new Error("MemoryEnvelopeTooLarge")
      while (queue.length) {
        messages.push(queue[0])
        if (JSON.stringify(request).length > input.budget) {
          messages.pop()
          break
        }
        queue.shift()
      }
      if (messages.length === 1 && queue.length) throw new Error("MemoryMessageTooLarge")
      const allowed = new Set([...sources, ...messages.map(message => message.id)])
      const next = await input.analyze("memory", request, input.model)
      validateMemory(next, allowed)
      content = next
      for (const id of allowed) sources.add(id)
    } while (queue.length)
  }
  return { content, source_ids: [...sources] }
}

function diagnosticReason(error) {
  const text = String(error.message ?? "")
  return /^(AnalysisHTTP\d{3}|MemoryEnvelopeTooLarge|MemoryMessageTooLarge)$/.test(text)
    ? text
    : ["Unknown memory source", "Invalid memory", "Invalid route", "Analysis input exceeds configured bound",
       "Invalid analysis response"].includes(text) ? text : error.name
}

function clip(text, bound) {
  if (text.length <= bound) return text
  const notice = "\n[... middle omitted ...]\n"
  const head = Math.floor(bound / 4)
  return text.slice(0, head) + notice + text.slice(-(bound - head - notice.length))
}

function validateRoute(route, ids) {
  if (!route || typeof route.context_id !== "string" || !/^[a-zA-Z0-9_-]{1,80}$/.test(route.context_id) ||
      typeof route.title !== "string" || typeof route.confidence !== "number" ||
      route.confidence < 0 || route.confidence > 1) throw new Error("Invalid route")
  for (const name of ["evidence_turn_ids", "shared_turn_ids", "related_context_ids"]) {
    if (!Array.isArray(route[name]) || !route[name].every(x => typeof x === "string")) throw new Error("Invalid route references")
  }
  if (![...route.evidence_turn_ids, ...route.shared_turn_ids].every(id => ids.has(id))) throw new Error("Unknown route source")
}

function validateMemory(memory, ids) {
  if (!memory || typeof memory.goal !== "string" || JSON.stringify(memory).length > 24000) throw new Error("Invalid memory")
  for (const key of ["constraints", "progress"]) {
    if (!Array.isArray(memory[key])) throw new Error("Missing memory evidence")
    for (const item of memory[key]) {
      if (typeof item.text !== "string" || !Array.isArray(item.source_ids) || !item.source_ids.length ||
          !item.source_ids.every(id => ids.has(id))) throw new Error("Unknown memory source")
    }
  }
  for (const key of ["pending", "files", "uncertainties"]) {
    if (!Array.isArray(memory[key]) || !memory[key].every(s => typeof s === "string")) throw new Error("Invalid memory field")
  }
}
