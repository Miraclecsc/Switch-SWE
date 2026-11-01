import { createHash } from "node:crypto"
import { mkdir, appendFile } from "node:fs/promises"
import { join } from "node:path"
import { homedir } from "node:os"
import { createManager } from "./manager.mjs"
import { createAnalyzer } from "./analyzer.mjs"

export default async function contextManager(input, options = {}) {
  const project = createHash("sha256").update(input.project?.id ?? input.directory).digest("hex").slice(0, 24)
  const stateDirectory = options.stateDirectory ?? process.env.OPENCODE_CONTEXT_STATE_DIR ??
    join(process.env.XDG_STATE_HOME ?? join(homedir(), ".local/state"), "opencode-context-manager", project)
  let configuration = {}
  const compacting = new Set()
  const mode = options.mode ?? process.env.OPENCODE_CONTEXT_MODE ?? "x"
  const analyze = createAnalyzer({
    configuration: () => configuration,
    ...options.analyzer,
    async onUsage(event) {
      await mkdir(stateDirectory, { recursive: true, mode: 0o700 })
      await appendFile(join(stateDirectory, "usage.jsonl"), JSON.stringify({
        at: new Date().toISOString(), ...event,
      }) + "\n", { mode: 0o600 })
    },
  })
  const manager = createManager({ stateDirectory, analyze, mode, minConfidence: 0.8 })
  return {
    async config(value) {
      configuration = value
      await mkdir(stateDirectory, { recursive: true, mode: 0o700 })
      await appendFile(join(stateDirectory, "lifecycle.jsonl"), JSON.stringify({
        at: new Date().toISOString(), event: "loaded", version: "v003", mode, pid: process.pid,
      }) + "\n", { mode: 0o600 })
    },
    async "experimental.session.compacting"(info, output) {
      compacting.add(info.sessionID)
      if (mode !== "off") output.context.push(
        "Preserve the goals, explicit constraints, observed progress, and unresolved work for every distinct work topic. " +
        "Keep topics distinguishable; do not discard suspended topics merely because another topic was most recent.",
      )
    },
    async "experimental.chat.messages.transform"(_info, output) {
      const sessions = new Set(output.messages.map(m => m.info?.sessionID).filter(Boolean))
      // The compactor shares this hook with ordinary provider turns. Never
      // filter its input down to one topic.
      if ([...sessions].some(id => compacting.has(id))) {
        for (const id of sessions) compacting.delete(id)
        return
      }
      const messages = await manager.transform(output.messages)
      // The upstream caller retains this array: replacing output.messages
      // would silently discard the projection.
      output.messages.splice(0, output.messages.length, ...messages)
    },
  }
}
