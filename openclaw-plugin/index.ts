import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const DEFAULT_PROJECT_PATH = resolve(
  process.env.HOME ?? process.env.USERPROFILE ?? "~",
  ".claude/agents/digital-persona"
);

function runPython(projectPath: string, pythonPath: string, script: string): string {
  const cmd = `${pythonPath} -c "${script}"`;
  try {
    const output = execSync(cmd, {
      cwd: projectPath,
      env: { ...process.env },
      encoding: "utf-8",
      timeout: 30_000,
    });
    return output.trim();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Python error: ${msg}`);
  }
}

export default definePluginEntry({
  id: "digital-persona",
  name: "Digital Persona",
  description: "Chat with your digital persona — responds using your memories, values, and emotional state.",
  register(api) {
    const config = (api.config ?? {}) as {
      personaId?: number;
      pythonPath?: string;
      projectPath?: string;
    };
    const personaId = config.personaId ?? 1;
    const pythonPath = config.pythonPath ?? "python";
    const projectPath = config.projectPath ?? DEFAULT_PROJECT_PATH;

    // Tool: chat with the persona
    api.registerTool({
      name: "persona_chat",
      description:
        "Send a message to your digital persona and get a reply. " +
        "The persona responds using your stored memories, values, and current emotional state. " +
        "Use this for every user message when acting as the digital persona.",
      parameters: Type.Object({
        message: Type.String({ description: "The user's message to the persona" }),
      }),
      async execute(_id, { message }) {
        if (!existsSync(projectPath)) {
          return {
            content: [
              {
                type: "text" as const,
                text: `[Digital Persona] 项目目录不存在：${projectPath}\n请先配置 projectPath。`,
              },
            ],
          };
        }

        const script = [
          "import sys",
          `sys.path.insert(0, '${projectPath.replace(/\\/g, "\\\\")}')`,
          "from scripts.db import Database",
          "from scripts.memory_manager import MemoryManager",
          "from scripts.respond import ResponsePipeline",
          "from scripts.emotion_engine import EmotionEngine",
          "import json",
          `persona_id = ${personaId}`,
          "db = Database()",
          "persona = db.get_persona(persona_id)",
          "if not persona: print(json.dumps({'error': 'no_persona'})); sys.exit(0)",
          "values = db.get_values_profile(persona_id)",
          "state = db.get_emotion_state(persona_id)",
          "mm = MemoryManager(persona_id=persona_id)",
          `memories = mm.recall(${JSON.stringify(message)}, top_k=5)`,
          "pipeline = ResponsePipeline()",
          "pipeline.load(persona, values, state)",
          `result = pipeline.run(${JSON.stringify(message)}, memories)`,
          // Update emotion after reply
          "if not result['blocked']:",
          "  engine = EmotionEngine()",
          `  new_state = engine.apply_event(state, result['anger_delta'], result['topic_sentiment'])`,
          "  db.update_emotion_state(persona_id, new_state['instant_emotion'], new_state['sadness'], new_state['anger'])",
          "  db.save_conversation(persona_id, " + JSON.stringify(message) + ", result['reply'])",
          "print(result['reply'])",
        ].join("; ");

        const reply = runPython(projectPath, pythonPath, script);
        return {
          content: [{ type: "text" as const, text: reply }],
        };
      },
    });

    // Tool: get persona status (emotion + memory count)
    api.registerTool({
      name: "persona_status",
      description: "Get the current emotional state and memory count of your digital persona.",
      parameters: Type.Object({}),
      async execute(_id, _params) {
        const script = [
          "import sys, json",
          `sys.path.insert(0, '${projectPath.replace(/\\/g, "\\\\")}')`,
          "from scripts.db import Database",
          "from scripts.memory_manager import MemoryManager",
          `db = Database(); mm = MemoryManager(persona_id=${personaId})`,
          `p = db.get_persona(${personaId})`,
          `s = db.get_emotion_state(${personaId})`,
          "print(json.dumps({'name': p['name'], 'instant_emotion': s['instant_emotion'], 'sadness': s['sadness'], 'anger': s['anger'], 'memories': mm.count()}))",
        ].join("; ");

        const raw = runPython(projectPath, pythonPath, script);
        const data = JSON.parse(raw) as {
          name: string;
          instant_emotion: number;
          sadness: number;
          anger: number;
          memories: number;
        };
        const text = [
          `副本：${data.name}`,
          `即时情绪：${data.instant_emotion}/100`,
          `悲伤程度：${data.sadness}/100`,
          `愤怒程度：${data.anger}/100`,
          `记忆条数：${data.memories}`,
        ].join("\n");
        return { content: [{ type: "text" as const, text }] };
      },
    });
  },
});
