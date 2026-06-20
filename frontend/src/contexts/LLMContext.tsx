"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { initEngine, isEngineReady, getLoadProgress } from "@/lib/ai-local";

interface LLMContextType {
  engineReady: boolean;
  loadProgress: number;
  loadStatus: string;
  isLoading: boolean;
  initLLM: () => Promise<void>;
}

const LLMContext = createContext<LLMContextType | null>(null);

export function LLMProvider({ children }: { children: ReactNode }) {
  const [engineReady, setEngineReady] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadStatus, setLoadStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const updateProgress = useCallback((progress: number, status: string) => {
    setLoadProgress(progress);
    setLoadStatus(status);
  }, []);

  const initLLM = useCallback(async () => {
    if (engineReady || isLoading) return;
    setIsLoading(true);
    try {
      await initEngine(updateProgress);
      setEngineReady(true);
    } catch {
      setLoadStatus("WebLLM not supported on this device");
    } finally {
      setIsLoading(false);
    }
  }, [engineReady, isLoading, updateProgress]);

  useEffect(() => {
    const ready = isEngineReady();
    if (ready) {
      setEngineReady(true);
      setLoadProgress(100);
      setLoadStatus("AI Ready");
      return;
    }
    
    const saved = localStorage.getItem("llm_loaded");
    if (saved === "true") {
      initLLM();
    }
  }, [initLLM]);

  useEffect(() => {
    if (engineReady) {
      localStorage.setItem("llm_loaded", "true");
    }
  }, [engineReady]);

  return (
    <LLMContext.Provider value={{ engineReady, loadProgress, loadStatus, isLoading, initLLM }}>
      {children}
    </LLMContext.Provider>
  );
}

export function useLLM() {
  const ctx = useContext(LLMContext);
  if (!ctx) throw new Error("useLLM must be used within LLMProvider");
  return ctx;
}
