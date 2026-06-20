"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { api, Question, TeacherResult, SummaryResult, PdfUploadResult, Credits, QaResult, FullExamResult, GlobalAnalysisResult } from "@/lib/api";
import AdBanner from "@/components/AdBanner";

type Tab = "predict" | "upload";
type Mode = "teacher" | "summarize" | "predict" | "qa" | "fullexam" | "global";

export default function AILabPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) api.feedback.credits().then(setCredits).catch(() => {});
  }, [user]);

  const sendRating = async (type: string, helpful: string) => {
    if (ratingSent) return;
    setRatingSent(true);
    try {
      await api.feedback.submit({ analysis_type: type, rating: helpful === "yes" ? 5 : 2, helpful, document_id: documentId || undefined });
    } catch { /* silent */ }
  };

  const [activeTab, setActiveTab] = useState<Tab>("predict");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState("");

  // Text input
  const [textInput, setTextInput] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);

  // File upload
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [extractedText, setExtractedText] = useState("");
  const [extractMeta, setExtractMeta] = useState<PdfUploadResult | null>(null);
  const [analyzeMode, setAnalyzeMode] = useState<Mode>("teacher");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Document ID for large files
  const [documentId, setDocumentId] = useState<string | null>(null);

  // Credits & rating
  const [credits, setCredits] = useState<Credits | null>(null);
  const [ratingSent, setRatingSent] = useState(false);

  // Results
  const [questions, setQuestions] = useState<Question[]>([]);
  const [teacherResult, setTeacherResult] = useState<TeacherResult | null>(null);
  const [summaryResult, setSummaryResult] = useState<SummaryResult | null>(null);
  const [qaResult, setQaResult] = useState<QaResult | null>(null);
  const [fullExamResult, setFullExamResult] = useState<FullExamResult | null>(null);
  const [globalResult, setGlobalResult] = useState<GlobalAnalysisResult | null>(null);
  const [lastAnalysisType, setLastAnalysisType] = useState("");

  const clearResults = () => {
    setQuestions([]);
    setTeacherResult(null);
    setSummaryResult(null);
    setQaResult(null);
    setFullExamResult(null);
    setGlobalResult(null);
    setError("");
    setRatingSent(false);
  };

  const handlePredict = async () => {
    setError("");
    clearResults();
    setLoading(true);
    setProgress("Generating questions...");
    try {
      const res = await api.ai.examPredict(textInput, numQuestions);
      setQuestions(res.questions);
      setLastAnalysisType("exam_predict");
      setRatingSent(false);
      api.feedback.credits().then(setCredits).catch(() => {});
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
      setProgress("");
    }
  };

  const handleFile = (f: File | null) => {
    setFile(f);
    setExtractedText("");
    setExtractMeta(null);
    setDocumentId(null);
    clearResults();
  };

  const handleUpload = async () => {
    if (!file) return;
    setError("");
    clearResults();
    setLoading(true);
    setProgress(`Extracting ${file.name}...`);
    try {
      const res = await api.upload.pdf(file);
      setExtractMeta(res);
      setExtractedText(res.text);
      setDocumentId(res.document_id);

      const wc = res.words;
      const modeLabel = analyzeMode === "teacher" ? "Teacher Mode" : analyzeMode === "summarize" ? "Summarizer" : "Exam Predict";
      setProgress(`Analyzing ${res.pages} pages (${wc.toLocaleString()} words) with ${modeLabel}...`);

      let result;
      if (analyzeMode === "teacher") {
        result = await api.ai.teacherMode(res.text, undefined, res.document_id);
        setTeacherResult(result);
        setLastAnalysisType("teacher_mode");
      } else if (analyzeMode === "summarize") {
        result = await api.ai.summarize(res.text, 200, res.document_id);
        setSummaryResult(result);
        setLastAnalysisType("summarize");
      } else if (analyzeMode === "qa") {
        result = await api.ai.qaSummarize(res.text, res.document_id);
        setQaResult(result);
        setLastAnalysisType("qa");
      } else if (analyzeMode === "fullexam") {
        result = await api.ai.fullExam(res.text, res.document_id);
        setFullExamResult(result);
        setLastAnalysisType("fullexam");
      } else if (analyzeMode === "global") {
        result = await api.ai.globalAnalyze(res.text, res.document_id);
        setGlobalResult(result);
        setLastAnalysisType("global");
      } else {
        result = await api.ai.examPredict(res.text, numQuestions, res.document_id);
        setQuestions(result.questions);
        setLastAnalysisType("exam_predict");
      }
      setRatingSent(false);
      api.feedback.credits().then(setCredits).catch(() => {});
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload or analysis failed");
      setFile(null);
    } finally {
      setLoading(false);
      setProgress("");
    }
  };

  if (authLoading || !user) return <div className="p-8 text-center text-gray-500">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">AI Lab</h1>
            <p className="text-gray-600 mt-1">Paste text or upload PDFs. AI predicts questions, explains concepts, and summarizes.</p>
          </div>
          {credits && !user?.is_premium && (
            <div className="text-right text-sm bg-gray-50 rounded-xl px-4 py-2 border">
              <span className="text-gray-500">Credits: </span>
              <span className={`font-bold ${credits.balance_tokens < 1000 ? 'text-red-500' : 'text-green-600'}`}>
                {credits.balance_tokens.toLocaleString()}
              </span>
              <span className="text-gray-400 text-xs block">~{Math.floor(credits.balance_tokens / 2).toLocaleString()} words</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-8">
        {[
          { id: "predict" as Tab, label: "Write / Paste Text", icon: "✍️" },
          { id: "upload" as Tab, label: "Upload PDF", icon: "📄" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => { setActiveTab(t.id); clearResults(); setError(""); }}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition flex items-center gap-2 ${
              activeTab === t.id ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* Progress */}
      {progress && (
        <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-700 px-4 py-3 rounded-xl text-sm flex items-center gap-3">
          <div className="animate-spin h-4 w-4 border-2 border-indigo-600 border-t-transparent rounded-full" />
          {progress}
        </div>
      )}

      {/* TAB: TEXT INPUT */}
      {activeTab === "predict" && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Study Material</label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={10}
            placeholder="Paste your notes, textbook content, or any study material... Works with Arabic & English. Supports up to 1M+ characters."
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-y text-sm"
          />
          <div className="flex items-center gap-4 mt-4 flex-wrap">
            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1">Questions</label>
              <select value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
                {[3, 5, 7, 10, 15, 20].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <span className="text-xs text-gray-400">
              {textInput.length.toLocaleString()} chars | ~{textInput.split(/\s+/).filter(Boolean).length.toLocaleString()} words
            </span>
            <button onClick={handlePredict} disabled={loading || textInput.length < 20} className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-40 transition text-sm ml-auto">
              {loading ? "Generating..." : "Generate Exam Questions"}
            </button>
          </div>
        </div>
      )}

      {/* TAB: PDF UPLOAD */}
      {activeTab === "upload" && (
        <div>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0] || null); }}
            className={`border-2 border-dashed rounded-2xl p-10 text-center transition cursor-pointer ${
              dragOver ? "border-indigo-400 bg-indigo-50" : file ? "border-green-300 bg-green-50" : "border-gray-300 hover:border-indigo-300"
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" onChange={(e) => handleFile(e.target.files?.[0] || null)} className="hidden" />
            <div className="text-5xl mb-4">{file ? "✅" : "📁"}</div>
            <p className="text-gray-700 font-medium mb-1">
              {file ? file.name : "Drop your PDF here or click to browse"}
            </p>
            <p className="text-gray-400 text-sm">
              {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "Supports large PDFs up to 300 MB / 1000+ pages"}
            </p>
          </div>

          <div className="flex gap-3 mt-4">
            <button onClick={() => fileInputRef.current?.click()} className="border border-gray-300 text-gray-700 px-5 py-2 rounded-xl font-medium hover:bg-gray-50 text-sm">
              Browse Files
            </button>
            <button onClick={handleUpload} disabled={!file || loading} className="bg-indigo-600 text-white px-5 py-2 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-40 transition text-sm">
              {loading && !extractMeta ? "Extracting..." : "Extract Text"}
            </button>
            {file && <button onClick={() => handleFile(null)} className="text-red-500 text-sm hover:underline self-center">Remove</button>}
          </div>

          {extractMeta && (
            <div className="mt-4 flex flex-wrap gap-2 text-sm text-gray-500">
              <span className="bg-gray-100 px-3 py-1 rounded-full">Pages: {extractMeta.pages}</span>
              <span className="bg-gray-100 px-3 py-1 rounded-full">Words: {extractMeta.words.toLocaleString()}</span>
              <span className="bg-gray-100 px-3 py-1 rounded-full">Engine: {extractMeta.extraction_method}</span>
              {extractMeta.has_full_text && (
                <span className="bg-amber-100 text-amber-700 px-3 py-1 rounded-full">
                  Large doc: {(extractMeta.full_text_length / 1024).toFixed(0)} KB stored
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">{error}</div>
      )}

      {/* Analysis Mode Toggle (visible after upload or while picking mode) */}
      {(extractedText || documentId) && (
        <div className="mt-4 flex items-center gap-2 text-sm">
          <span className="text-gray-500">Analysis mode:</span>
          <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
              {([
                { id: "teacher" as Mode, label: "Teacher" },
                { id: "summarize" as Mode, label: "Summarize" },
                { id: "qa" as Mode, label: "Q&A" },
                { id: "fullexam" as Mode, label: "Full Exam" },
                { id: "global" as Mode, label: "Global" },
                { id: "predict" as Mode, label: "Predict" },
              ]).map((m) => (
              <button
                key={m.id}
                onClick={() => { setAnalyzeMode(m.id); clearResults(); }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  analyzeMode === m.id ? "bg-white shadow text-indigo-600" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <AdBanner slot="ai-lab-mid" format="auto" className="mt-6" />

      {/* Results go directly here after upload */}
      {extractMeta?.has_full_text && (
        <div className="mt-3 bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-700">
          Large document ({extractMeta.pages} pages). Processing in chunks automatically.
        </div>
      )}

      {/* Questions Result */}
      {questions.length > 0 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-xl font-bold">Generated Questions ({questions.length})</h2>
          {questions.map((q, i) => (
            <div key={i} className="border border-gray-200 rounded-2xl p-6 bg-white shadow-sm">
              <div className="flex items-start gap-3">
                <span className="bg-indigo-100 text-indigo-700 font-bold rounded-full w-8 h-8 flex items-center justify-center text-sm shrink-0">{i + 1}</span>
                <div className="flex-1">
                  <p className="font-semibold mb-1">{q.question}</p>
                  {q.type && <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded mb-3 inline-block">{q.type}</span>}
                  {q.options.length > 0 && (
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      {q.options.map((opt, j) => (
                        <div key={j} className="border border-gray-200 rounded-lg px-4 py-2 text-sm bg-gray-50">
                          <span className="font-medium text-indigo-500">{String.fromCharCode(65 + j)}.</span> {opt}
                        </div>
                      ))}
                    </div>
                  )}
                  <details>
                    <summary className="text-green-600 cursor-pointer font-medium text-sm hover:underline">Reveal Answer</summary>
                    <p className="mt-2 text-green-700 bg-green-50 p-3 rounded-lg text-sm">{q.answer}</p>
                  </details>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Teacher Mode Result */}
      {teacherResult && (
        <div className="mt-8 border border-indigo-200 rounded-2xl overflow-hidden">
          <div className="bg-indigo-600 text-white px-6 py-4">
            <h3 className="text-xl font-bold">Teacher Mode Analysis</h3>
            <p className="text-indigo-100 text-sm">
              {teacherResult.topic} · {teacherResult.difficulty_level} · {teacherResult.suggested_study_time}
              {teacherResult.total_words ? ` · ${teacherResult.total_words.toLocaleString()} words` : ""}
              {teacherResult.total_chunks && teacherResult.total_chunks > 1 ? ` · ${teacherResult.total_chunks} sections` : ""}
            </p>
          </div>
          <div className="p-6 space-y-5 bg-white">
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">Overview</h4>
              <p className="text-gray-600">{teacherResult.summary}</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Key Concepts</h4>
              <div className="flex flex-wrap gap-2">
                {teacherResult.key_concepts.map((k) => (
                  <span key={k} className="bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-full text-sm font-medium border border-indigo-100">{k}</span>
                ))}
              </div>
            </div>
            {teacherResult.sections && teacherResult.sections.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Document Structure ({teacherResult.sections.length} sections)</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {teacherResult.sections.map((s) => (
                    <div key={s.number} className="flex items-center gap-3 text-sm">
                      <span className="bg-gray-100 text-gray-500 w-7 h-7 rounded-full flex items-center justify-center font-medium text-xs shrink-0">{s.number}</span>
                      <span className="flex-1 text-gray-600 truncate">{s.preview}</span>
                      <span className="text-gray-400 text-xs whitespace-nowrap">{s.word_count}w · {s.sentences}s</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Study Points</h4>
              <ul className="space-y-1.5">
                {teacherResult.bullet_points.map((b, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-600 text-sm">
                    <span className="text-indigo-400 mt-0.5">•</span> {b}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Next Steps</h4>
              <ul className="space-y-1.5">
                {teacherResult.recommended_resources.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-600 text-sm">
                    <span className="text-green-500 mt-0.5">✓</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Rating */}
      {teacherResult && (
        <div className="mt-4 flex items-center gap-2 text-sm">
          <span className="text-gray-400">Was this helpful?</span>
          <button onClick={() => sendRating("teacher_mode", "yes")} disabled={ratingSent} className="px-3 py-1 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 disabled:opacity-50">Yes</button>
          <button onClick={() => sendRating("teacher_mode", "no")} disabled={ratingSent} className="px-3 py-1 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 disabled:opacity-50">No</button>
          {ratingSent && <span className="text-gray-400">Thanks!</span>}
        </div>
      )}

      {/* Summarizer Result */}
      {summaryResult && (
        <div className="mt-8 border border-purple-200 rounded-2xl overflow-hidden">
          <div className="bg-purple-600 text-white px-6 py-4">
            <h3 className="text-xl font-bold">AI Summary</h3>
            <p className="text-purple-100 text-sm">
              {summaryResult.original_length.toLocaleString()} → {summaryResult.summary_length.toLocaleString()} words ({summaryResult.compression_ratio})
              {summaryResult.total_chunks && summaryResult.total_chunks > 1 ? ` · ${summaryResult.total_chunks} chunks` : ""}
            </p>
          </div>
          <div className="p-6 bg-white">
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">{summaryResult.summary}</p>
            {summaryResult.keywords.length > 0 && (
              <div className="mt-6 pt-4 border-t border-gray-100">
                <h4 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">Keywords</h4>
                <div className="flex flex-wrap gap-2">
                  {summaryResult.keywords.map((k) => (
                    <span key={k} className="bg-purple-50 text-purple-700 px-3 py-1.5 rounded-full text-sm font-medium border border-purple-100">{k}</span>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
              <div className="bg-gray-50 rounded-xl p-3">
                <div className="text-lg font-bold text-gray-700">{summaryResult.original_length.toLocaleString()}</div>
                <div className="text-gray-500">Original Words</div>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <div className="text-lg font-bold text-gray-700">{summaryResult.summary_length.toLocaleString()}</div>
                <div className="text-gray-500">Summary Words</div>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <div className="text-lg font-bold text-gray-700">{summaryResult.compression_ratio}</div>
                <div className="text-gray-500">Compression</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Q&A Result */}
      {qaResult && (
        <div className="mt-8 border border-emerald-200 rounded-2xl overflow-hidden">
          <div className="bg-emerald-600 text-white px-6 py-4">
            <h3 className="text-xl font-bold">Q&A Study Guide</h3>
            <p className="text-emerald-100 text-sm">
              {qaResult.total_questions} questions across {qaResult.chapters_covered} chapters · {qaResult.total_words.toLocaleString()} words
            </p>
          </div>
          <div className="p-6 bg-white space-y-6">
            {qaResult.chapters.map((ch) => (
              <div key={ch.chapter}>
                <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="bg-emerald-100 text-emerald-700 rounded-full w-6 h-6 flex items-center justify-center text-xs">{ch.chapter}</span>
                  {ch.title}
                </h4>
                <div className="space-y-3 ml-8">
                  {ch.qa_pairs.map((qa, i) => (
                    <div key={i} className="border border-gray-100 rounded-xl p-4 bg-gray-50">
                      <div className="flex items-start gap-2">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded mt-0.5 ${
                          qa.type === "definition" ? "bg-blue-100 text-blue-700" :
                          qa.type === "concept" ? "bg-emerald-100 text-emerald-700" :
                          qa.type === "comparison" ? "bg-amber-100 text-amber-700" :
                          "bg-purple-100 text-purple-700"
                        }`}>{qa.type}</span>
                        <div className="flex-1">
                          <p className="font-semibold text-gray-800">Q: {qa.question}</p>
                          <p className="text-gray-600 mt-1 text-sm whitespace-pre-line">A: {qa.answer}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {qaResult.all_definitions.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h4 className="font-semibold text-gray-700 mb-3">Key Definitions</h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {qaResult.all_definitions.map((d, i) => (
                    <div key={i} className="bg-gray-50 rounded-xl p-3 text-sm">
                      <span className="font-semibold text-indigo-600">{d.term}</span>
                      <p className="text-gray-600 mt-1">{d.definition}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Full Exam Result */}
      {fullExamResult && (
        <div className="mt-8 space-y-6">
          <div className="bg-gradient-to-r from-gray-900 to-gray-700 text-white rounded-2xl p-8">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-2xl font-bold">{fullExamResult.title}</h3>
                <p className="text-gray-300 text-sm mt-1">Subject: {fullExamResult.subject}</p>
              </div>
              <div className="text-right text-sm">
                <div className="bg-white/20 rounded-lg px-3 py-1 inline-block mb-1">{fullExamResult.exam_id}</div>
                <div className="text-gray-300">Total: {fullExamResult.total_marks} marks</div>
                <div className="text-gray-300">Time: {fullExamResult.time_minutes} minutes</div>
              </div>
            </div>
            <div className="mt-4 bg-white/10 rounded-xl p-4 text-sm space-y-1">
              <p className="font-semibold text-white">Instructions:</p>
              {fullExamResult.instructions.map((inst, i) => (
                <p key={i} className="text-gray-300">{i+1}. {inst}</p>
              ))}
            </div>
          </div>

          {fullExamResult.sections.map((section) => (
            <div key={section.section} className="border border-gray-200 rounded-2xl overflow-hidden bg-white">
              <div className="bg-indigo-50 px-6 py-3 border-b border-gray-200">
                <h4 className="font-bold text-indigo-700">
                  Section {section.section}: {section.title} — {section.marks}
                </h4>
                {section.instructions && <p className="text-sm text-gray-600 mt-1">{section.instructions}</p>}
              </div>
              <div className="p-6 space-y-6">
                {section.questions.map((q) => (
                  <div key={q.number} className="border-b border-gray-100 pb-5 last:border-0 last:pb-0">
                    <div className="flex items-start gap-3">
                      <span className="bg-indigo-100 text-indigo-700 font-bold rounded-full w-7 h-7 flex items-center justify-center text-sm shrink-0">{q.number}</span>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-800">{q.question}</p>
                        <span className="text-xs text-gray-400 mt-1 inline-block">[{q.marks} marks]</span>

                        {/* MCQs */}
                        {q.options && (
                          <div className="grid grid-cols-2 gap-2 mt-3">
                            {q.options.map((opt, j) => (
                              <div key={j} className={`border rounded-lg px-3 py-2 text-sm ${q.correct === String.fromCharCode(65+j) ? 'bg-green-50 border-green-300' : 'bg-gray-50'}`}>
                                {opt}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Show correct answer reveal */}
                        {q.correct && (
                          <details className="mt-2">
                            <summary className="text-green-600 cursor-pointer text-sm font-medium">Show Answer</summary>
                            <div className="mt-2 text-sm bg-green-50 rounded-lg p-3">
                              <p className="font-semibold">Answer: {q.correct}) {q.correct_answer}</p>
                              {q.explanation && <p className="text-gray-600 mt-1">{(q.explanation as {why_correct: string}).why_correct}</p>}
                            </div>
                          </details>
                        )}

                        {/* Model answer for short */}
                        {q.model_answer && (
                          <details className="mt-2">
                            <summary className="text-green-600 cursor-pointer text-sm font-medium">Model Answer</summary>
                            <div className="mt-2 text-sm bg-green-50 rounded-lg p-3">
                              <p className="text-gray-700">{q.model_answer}</p>
                              {q.marking_points && (
                                <div className="mt-2">
                                  <span className="font-semibold text-xs text-gray-500">Marking Points:</span>
                                  <ul className="list-disc pl-4 text-xs text-gray-600 mt-1">
                                    {q.marking_points.map((p, i) => <li key={i}>{p}</li>)}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </details>
                        )}

                        {/* Marking criteria for essay */}
                        {q.marking_criteria && (
                          <div className="mt-2 text-xs text-gray-500">
                            <span className="font-semibold">Criteria:</span>
                            <ul className="list-disc pl-4 mt-1">
                              {q.marking_criteria.map((c, i) => <li key={i}>{c}</li>)}
                            </ul>
                          </div>
                        )}

                        {/* Approach for problems */}
                        {q.solution_approach && (
                          <div className="mt-2 text-xs text-gray-500">
                            <span className="font-semibold">Approach:</span>
                            <ol className="list-decimal pl-4 mt-1">
                              {q.solution_approach.map((s, i) => <li key={i}>{s}</li>)}
                            </ol>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Chapter Coverage */}
          {fullExamResult.chapter_coverage && (
            <div className="bg-gray-50 rounded-xl p-5 text-sm">
              <h4 className="font-semibold text-gray-700 mb-2">Chapter Coverage</h4>
              <div className="flex flex-wrap gap-2">
                {fullExamResult.chapter_coverage.map((ch) => (
                  <span key={ch.chapter} className="bg-white border px-3 py-1 rounded-full text-xs text-gray-600">
                    Ch.{ch.chapter}: {ch.title.slice(0, 30)} ({ch.questions} Qs)
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Stats */}
          <div className="bg-gray-50 rounded-xl p-5 text-sm text-gray-600">
            <span className="font-semibold">Confidence: {fullExamResult.statistics.prediction_confidence}%</span>
            <span className="mx-2">·</span>
            <span>{fullExamResult.statistics.total_concepts_analyzed} concepts analyzed</span>
          </div>
        </div>
      )}
    </div>
  );
}
