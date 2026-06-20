const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://examai-hub-api.onrender.com";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    register: (data: { email: string; username: string; password: string; full_name?: string }) =>
      request<{ access_token: string; user: User }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  },
  ai: {
    examPredict: (text: string, numQuestions = 5, documentId?: string) =>
      request<{ questions: Question[]; total: number }>("/ai/exam-predict", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, num_questions: numQuestions } : { text, num_questions: numQuestions }),
      }),
    teacherMode: (text: string, topic?: string, documentId?: string) =>
      request<TeacherResult>("/ai/teacher-mode", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, topic } : { text, topic }),
      }),
    summarize: (text: string, maxLength = 200, documentId?: string) =>
      request<SummaryResult>("/ai/summarize", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, max_length: maxLength } : { text, max_length: maxLength }),
      }),
    analyze: (text: string, documentId?: string) =>
      request<StructuredAnalysis>("/ai/analyze", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    flashcards: (text: string, count = 10, documentId?: string) =>
      request<{ flashcards: Flashcard[]; total: number }>("/ai/flashcards", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, count } : { text, count }),
      }),
    studyPlan: (text: string, days = 7, documentId?: string) =>
      request<StudyPlan>("/ai/study-plan", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, days } : { text, days }),
      }),
    cheatsheet: (text: string, documentId?: string) =>
      request<Cheatsheet>("/ai/cheatsheet", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    examPrep: (text: string, documentId?: string) =>
      request<ExamPrepResult>("/ai/exam-prep", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    teacherExam: (text: string, documentId?: string) =>
      request<TeacherFingerprintResult>("/ai/teacher-exam", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    examReconstruct: (textbook: string, pastExams?: string, lectureNotes?: string) =>
      request<ExamReconstructResult>("/ai/exam-reconstruct", {
        method: "POST",
        body: JSON.stringify({ textbook, past_exams: pastExams, lecture_notes: lectureNotes }),
      }),
    examPredictLearn: (textbook: string, pastExams?: string, feedback?: object[]) =>
      request<ExamLearnResult>("/ai/exam-predict-learn", {
        method: "POST",
        body: JSON.stringify({ textbook, past_exams: pastExams, feedback }),
      }),
    unified: (textbook: string, pastExams?: string, lectureNotes?: string) =>
      request<UnifiedResult>("/ai/unified", {
        method: "POST",
        body: JSON.stringify({ textbook, past_exams: pastExams, lecture_notes: lectureNotes }),
      }),
    hierarchicalSummarize: (text: string, targetRatio?: number, documentId?: string) =>
      request<HierarchicalSummaryResult>("/ai/hierarchical-summarize", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId, target_ratio: targetRatio } : { text, target_ratio: targetRatio }),
      }),
    multiPassPredict: (textbook: string, pastExams?: string, lectureNotes?: string) =>
      request<MultiPassResult>("/ai/multi-pass-predict", {
        method: "POST",
        body: JSON.stringify({ textbook, past_exams: pastExams, lecture_notes: lectureNotes }),
      }),
    qaSummarize: (text: string, documentId?: string) =>
      request<QaResult>("/ai/qa-summarize", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    fullExam: (text: string, documentId?: string) =>
      request<FullExamResult>("/ai/full-exam", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
    globalAnalyze: (text: string, documentId?: string) =>
      request<GlobalAnalysisResult>("/ai/global-analyze", {
        method: "POST",
        body: JSON.stringify(documentId ? { document_id: documentId } : { text }),
      }),
  },
  feedback: {
    submit: (data: { analysis_type: string; rating: number; helpful?: string; comment?: string; document_id?: string }) =>
      request<{ status: string; id: number }>("/feedback/submit", { method: "POST", body: JSON.stringify(data) }),
    stats: () => request<FeedbackStats>("/feedback/stats"),
    credits: () => request<Credits>("/feedback/credits"),
    buyCredits: (tokens: number) =>
      request<{ balance_tokens: number; added: number }>("/feedback/credits/buy", { method: "POST", body: JSON.stringify({ tokens }) }),
    usageHistory: () => request<UsageLogEntry[]>("/feedback/usage/history"),
  },
  upload: {
    pdf: async (file: File) => {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const formData = new FormData();
      formData.append("file", file);
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API_BASE}/upload/pdf`, { method: "POST", headers, body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return res.json() as Promise<PdfUploadResult>;
    },
    text: (text: string) =>
      request<{ document_id: string; text: string; full_text_length: number; words: number }>("/upload/text", {
        method: "POST",
        body: JSON.stringify({ text }),
      }),
    getDocument: (docId: string) => request<DocumentInfo>(`/upload/document/${docId}`),
    getFullDocument: (docId: string) => request<{ document_id: string; text: string; total_chars: number }>(`/upload/document/${docId}/full`),
    getStructured: (docId: string) => request<DocumentStructured>(`/upload/document/${docId}/structured`),
  },
  payments: {
    createOrder: (plan = "monthly") =>
      request<{ order_id: string; approval_url: string; status: string }>("/payments/create-order", { method: "POST", body: JSON.stringify({ plan }) }),
    captureOrder: (orderId: string) =>
      request<{ status: string; capture_id: string; premium_activated: boolean }>("/payments/capture-order", { method: "POST", body: JSON.stringify({ order_id: orderId }) }),
    activateDemo: (plan = "monthly") =>
      request<{ status: string; premium_activated: boolean; plan: string; message: string }>("/payments/activate-demo", { method: "POST", body: JSON.stringify({ plan }) }),
    history: () => request<PaymentHistoryEntry[]>("/payments/history"),
    verifyPremium: () => request<{ is_premium: boolean; user_id: number }>("/payments/verify-premium"),
  },
  user: {
    me: () => request<User>("/user/me"),
    stats: () => request<Stats>("/user/stats"),
    update: (data: { full_name?: string; username?: string }) =>
      request<User>("/user/me", { method: "PUT", body: JSON.stringify(data) }),
  },
  health: () => request<{ status: string }>("/health"),
  growth: {
    referral: () => request<ReferralInfo>("/growth/referral"),
    applyReferral: (code: string) => request<{ status: string; bonus: number; message: string }>(`/growth/referral/apply/${code}`, { method: "POST" }),
    share: (data: { title: string; subject: string; course: string; data: object }) =>
      request<{ share_token: string; share_url: string; message: string }>("/growth/share", { method: "POST", body: JSON.stringify(data) }),
    achievements: () => request<AchievementList>("/growth/achievements"),
    checkAchievements: () => request<{ new_achievements: AchievementBadge[]; total: number }>("/growth/achievements/check", { method: "POST" }),
    score: () => request<UserScore>("/growth/score"),
    leaderboard: () => request<{ leaderboard: LeaderboardEntry[]; total_participants: number }>("/growth/leaderboard"),
    dailyChallenge: () => request<{ questions: DailyQuestion[]; date: string }>("/growth/daily-challenge"),
  },
};

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  is_premium: boolean;
  is_admin: boolean;
  is_active: boolean;
  created_at?: string;
}

export interface Stats {
  exams_predicted: number;
  files_uploaded: number;
  summaries_generated: number;
  teacher_mode_sessions: number;
  is_premium: boolean;
}

export interface Question {
  question: string;
  options: string[];
  answer: string;
  type?: string;
}

export interface TeacherResult {
  summary: string;
  key_concepts: string[];
  difficulty_level: string;
  suggested_study_time: string;
  topic: string;
  bullet_points: string[];
  recommended_resources: string[];
  sections?: { number: number; preview: string; word_count: number; sentences: number }[];
  total_words?: number;
  total_chunks?: number;
  language?: string;
}

export interface SummaryResult {
  original_length: number;
  summary_length: number;
  summary: string;
  keywords: string[];
  compression_ratio: string;
  sections?: number;
  total_chunks?: number;
  language?: string;
}

export interface PdfUploadResult {
  filename: string;
  document_id: string;
  text: string;
  full_text_length: number;
  characters: number;
  words: number;
  pages: number;
  extraction_method: string;
  has_full_text: boolean;
}

export interface DocumentInfo {
  document_id: string;
  filename: string;
  total_chars: number;
  total_words: number;
  total_chunks: number;
  chunks: { index: number; word_count: number; sentences: number; keywords: string[] }[];
}

export interface StructuredAnalysis {
  document_info: { total_words: number; total_chapters: number; language: string; difficulty_level: string };
  chapters: { number: number; title: string; word_count: number; keywords: string[]; preview: string }[];
  main_topics: string[];
  subtopics: string[];
  key_definitions: { term: string; definition: string }[];
  importance_ranking: { concept: string; frequency: number; importance: string; context: string[] }[];
  possible_exam_questions: { question: string; importance: string; concept: string }[];
}

export interface Flashcard {
  id: number;
  front: string;
  back: string;
  concept: string;
  difficulty: string;
}

export interface StudyPlan {
  total_days: number;
  total_chapters: number;
  total_words: number;
  plan: { day: number; title: string; chapters: string[]; estimated_words: number; tasks: string[] }[];
}

export interface Cheatsheet {
  title: string;
  must_know_terms: string[];
  high_importance: { concept: string; importance: string }[];
  definitions: { term: string; definition: string }[];
  study_tips: string[];
}

export interface Credits {
  user_id: number;
  balance_tokens: number;
  total_tokens_used: number;
  total_words_analyzed: number;
  plan_type: string;
  free_credits_given: number;
}

export interface UsageLogEntry {
  id: number;
  analysis_type: string;
  words_processed: number;
  tokens_charged: number;
  cost_cents: number;
  created_at: string;
}

export interface FeedbackStats {
  total: number;
  helpful: number;
  avg_rating: number;
  by_type: Record<string, number>;
}

export interface PaymentHistoryEntry {
  id: number;
  paypal_order_id: string;
  amount: number;
  currency: string;
  status: string;
  plan: string;
  created_at: string;
}

export interface DocumentStructured {
  title: string;
  chapters: { title: string; word_count: number; style: string; preview: string }[];
  total_chapters: number;
  total_words: number;
  total_chars: number;
}

export interface ExamPrepResult { document_stats: object; high_yield_topics: string[]; definition_focus_list: object[]; likely_exam_questions: object[]; essay_questions: object[]; problem_solving_questions: object[]; tricky_questions: object[]; teacher_trap_patterns: object[]; difficulty_map: object; revision_sheet: object }

export interface TeacherFingerprintResult { teacher_profile: object; emphasis_map: object; hidden_exam_signals: object[]; exam_pattern_reconstruction: object; high_probability_questions: object[]; predicted_exam: object }

export interface ExamReconstructResult { exam_prediction_confidence: number; source_analysis: object; source_alignment: object; exam_patterns_mined: object; teacher_behavior_model: object; predicted_exam: object[]; last_minute_revision_sheet: object }

export interface ExamLearnResult { exam_prediction: object; confidence_score: number; learning_updates: object; teacher_fingerprint_update: object; iteration: number }

export interface UnifiedResult { exam_study_material: object; teacher_fingerprint: object; predicted_exam: object[]; confidence_score: number; cross_validation: object }

export interface HierarchicalSummaryResult { original_words: number; summary_words: number; compression_ratio: string; target_ratio: string; chapters_count: number; chapters: object[]; global_keywords: string[]; full_summary: string; information_preservation: object }

export interface MultiPassResult { passes_completed: number; topics_extracted: number; importance_ranking: object[]; teacher_style: string; exam_blueprint: object; exam_questions: object[]; quality_assurance: object }

export interface QaResult { format: string; total_questions: number; chapters_covered: number; total_words: number; chapters: QaChapter[]; all_definitions: { term: string; definition: string }[]; language: string }

export interface QaChapter { chapter: number; title: string; qa_pairs: QaPair[] }

export interface QaPair { type: string; question: string; answer: string }

export interface ReferralInfo { referral_code: string; referral_link: string; total_referrals: number; credits_earned: number }

export interface AchievementList { achievements: AchievementBadge[]; total_earned: number }

export interface AchievementBadge { id: string; name: string; icon: string; desc: string; earned: boolean }

export interface UserScore { study_readiness: number; exam_confidence: string; total_analyses: number; uploads: number; predictions: number; achievements: number; share_text: string }

export interface LeaderboardEntry { username: string; score: number; analyses: number }

export interface DailyQuestion { q: string; options: string[]; answer: number }

export interface FullExamResult {
  exam_id: string; title: string; subject: string; total_marks: number; time_minutes: number; language: string;
  instructions: string[];
  sections: FullExamSection[];
  marking_scheme: object;
  answer_key: object;
  chapter_coverage: { chapter: number; title: string; questions: number }[];
  statistics: { total_concepts_analyzed: number; prediction_confidence: number };
}

export interface FullExamSection {
  section: string; title: string; marks: string; questions: FullExamQuestion[]; instructions?: string;
}

export interface FullExamQuestion {
  number: number; question: string; marks: number;
  options?: string[]; correct?: string; correct_answer?: string; explanation?: string | object;
  model_answer?: string; marking_points?: string[];
  marking_criteria?: string[]; topic?: string; spans_chapters?: number;
  context?: string; solution_approach?: string[];
}

export interface GlobalAnalysisResult {
  global_context: object; teacher_insights: object; full_exam: object;
  contextual_summary: { text: string; word_count: number }; language: string;
}
