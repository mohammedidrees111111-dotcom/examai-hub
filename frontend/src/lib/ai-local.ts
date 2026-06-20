import { CreateMLCEngine, MLCEngine } from "@mlc-ai/web-llm";

const MODEL_ID = "gemma-2-2b-it-q4f16_1-MLC";
const MODEL_SIZE_MB = 1200;

let engine: MLCEngine | null = null;
let loadingPromise: Promise<MLCEngine> | null = null;
let loadProgress = 0;
let loadStatus = "";

type ProgressCallback = (progress: number, status: string) => void;

export function getLoadProgress() {
  return { progress: loadProgress, status: loadStatus };
}

export function isEngineReady(): boolean {
  return engine !== null;
}

export async function initEngine(onProgress?: ProgressCallback): Promise<MLCEngine> {
  if (engine) return engine;
  
  if (loadingPromise) {
    const eng = await loadingPromise;
    return eng;
  }

  loadStatus = "Loading AI model...";
  loadProgress = 0;
  onProgress?.(0, loadStatus);

  loadingPromise = (async () => {
    const eng = await CreateMLCEngine(MODEL_ID, {
      initProgressCallback: (info) => {
        loadStatus = info.text;
        loadProgress = Math.round(info.progress * 100);
        onProgress?.(loadProgress, loadStatus);
      },
    });
    engine = eng;
    loadStatus = "AI Ready";
    loadProgress = 100;
    onProgress?.(100, "AI Ready");
    return eng;
  })();

  try {
    return await loadingPromise;
  } catch (e) {
    loadingPromise = null;
    loadStatus = "Failed to load AI model";
    throw e;
  }
}

export async function localChat(
  prompt: string,
  maxTokens: number = 1500,
  temperature: number = 0.3
): Promise<string> {
  if (!engine) {
    throw new Error("AI model not loaded");
  }

  const reply = await engine.chat.completions.create({
    messages: [
      {
        role: "system",
        content: "You are an expert academic AI assistant. Provide clear, accurate, educational responses based on the given material. For Arabic text, respond in Arabic. Be concise and focus on key concepts. DO NOT add information not present in the provided text.",
      },
      { role: "user", content: prompt },
    ],
    max_tokens: maxTokens,
    temperature: temperature,
  });

  return reply.choices[0]?.message?.content || "";
}

export async function localSummarize(text: string): Promise<string> {
  return localChat(
    `Summarize this text for exam study. Keep important definitions, concepts, examples. Remove only filler.\n\n${text.slice(0, 20000)}`
  );
}

export async function localExamPredict(text: string): Promise<string> {
  return localChat(
    `Generate exam questions from this text. Include MCQ with options+answer, Short Answer, and Essay questions. Base everything on the text.\n\n${text.slice(0, 20000)}`
  );
}

export async function localTeacherMode(text: string): Promise<string> {
  return localChat(
    `Analyze this teaching material like a professor. Provide: teaching style, key emphasized concepts, likely question types, exam strategy, and student traps.\n\n${text.slice(0, 20000)}`
  );
}

export async function localQA(text: string): Promise<string> {
  return localChat(
    `Convert this text into Q&A study pairs. Include: definition questions, concept comparison questions, and enumeration questions. Format as Q:/A: pairs.\n\n${text.slice(0, 20000)}`
  );
}
