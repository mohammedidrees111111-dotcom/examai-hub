import { isEngineReady, localChat, localSummarize, localExamPredict, localTeacherMode, localQA } from "./ai-local";

const API_BASE = "https://examai-hub-api.onrender.com";

type AIMode = "summarize" | "exam_predict" | "teacher_mode" | "qa_generate" | "chat";

interface AIResult {
  text: string;
  model: string;
  aiPowered: boolean;
}

async function callRemoteAPI(endpoint: string, body: object): Promise<string | null> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) return null;
    const data = await res.json();
    if (data.ai_powered && data.result) return data.result;
    if (data.summary) return data.summary;
    if (data.full_summary) return data.full_summary;
    return null;
  } catch {
    return null;
  }
}

export async function routeAI(text: string, mode: AIMode): Promise<AIResult> {
  // Layer 1: Remote APIs via backend (Groq → Gemini → DeepSeek → Rule-based)
  const remoteResult = await callRemoteAPI(endpointMap[mode], body);
  if (remoteResult) {
    return { text: remoteResult, model: "cloud-ai", aiPowered: true };
  }

  // Layer 2: WebLLM (local browser - unlimited + free)
  if (isEngineReady()) {
    try {
      let result: string;
      const prompt = buildPrompt(text, mode);
      
      switch (mode) {
        case "summarize": result = await localSummarize(text); break;
        case "exam_predict": result = await localExamPredict(text); break;
        case "teacher_mode": result = await localTeacherMode(text); break;
        case "qa_generate": result = await localQA(text); break;
        default: result = await localChat(prompt); break;
      }
      
      if (result) return { text: result, model: "local-gemma-2b", aiPowered: true };
    } catch { /* fall through */ }
  }

  // Layer 2: Remote APIs via backend
  const endpointMap: Record<AIMode, string> = {
    summarize: "/ai/summarize",
    exam_predict: "/ai/exam-predict",
    teacher_mode: "/ai/teacher-mode",
    qa_generate: "/ai/qa-summarize",
    chat: "/ai/summarize",
  };

  const body = mode === "exam_predict"
    ? { text, num_questions: 5 }
    : { text };

  const remoteResult = await callRemoteAPI(endpointMap[mode], body);
  if (remoteResult) {
    return { text: remoteResult, model: "remote-api", aiPowered: true };
  }

  // Layer 3: Return simple rule-based fallback
  return { text: fallbackResponse(text, mode), model: "rule-based", aiPowered: false };
}

function buildPrompt(text: string, mode: AIMode): string {
  const t = text.slice(0, 15000);
  const prompts: Record<AIMode, string> = {
    summarize: `Summarize this study material. Keep definitions, concepts, examples. Remove filler.\n\n${t}`,
    exam_predict: `Generate 5 exam questions from this text with answers:\n\n${t}`,
    teacher_mode: `Analyze this like a professor: teaching style, key concepts, exam strategy:\n\n${t}`,
    qa_generate: `Create Q&A study pairs from this text:\n\n${t}`,
    chat: t,
  };
  return prompts[mode] || t;
}

function fallbackResponse(text: string, mode: AIMode): string {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20);
  const preview = sentences.slice(0, 5).join(". ") + ".";
  
  switch (mode) {
    case "summarize": return preview;
    case "exam_predict": return "AI models unavailable. Try again or use basic prediction mode.";
    case "teacher_mode": return "AI models unavailable. Key concepts: " + extractKeywords(text).join(", ");
    case "qa_generate": return "AI models unavailable. Review the key concepts: " + extractKeywords(text).join(", ");
    default: return preview;
  }
}

function extractKeywords(text: string): string[] {
  const words = text.toLowerCase().match(/\b[a-z]{4,}\b/g) || [];
  const stop = new Set(["this","that","with","from","they","have","been","were","which","their","about","would","could","should","what","when","where","there","these","those"]);
  const filtered = words.filter(w => !stop.has(w));
  const freq: Record<string, number> = {};
  filtered.forEach(w => freq[w] = (freq[w] || 0) + 1);
  return Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 10).map(e => e[0]);
}
