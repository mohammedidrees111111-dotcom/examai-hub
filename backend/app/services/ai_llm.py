import os
import logging
from typing import Optional

logger = logging.getLogger("examai-hub")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_AVAILABLE = False
_client = None

if GROQ_API_KEY:
    try:
        from groq import Groq
        _client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        logger.info("Groq AI initialized successfully")
    except ImportError:
        logger.warning("Groq package not installed. Run: pip install groq")
    except Exception as e:
        logger.warning(f"Groq init failed: {e}")


def _call_groq(prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> Optional[str]:
    if not GROQ_AVAILABLE or not _client:
        return None
    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


def ai_summarize(text: str, target_length: str = "medium") -> Optional[str]:
    if not GROQ_AVAILABLE:
        return None
    lengths = {"short": "20-30%", "medium": "40-55%", "detailed": "60-80%"}
    prompt = f"""You are an academic summarizer. Summarize the following text at {lengths.get(target_length, '40-55%')} of original length.
PRESERVE: all definitions, key concepts, formulas, examples, comparisons, important notes, exam hints.
REMOVE ONLY: repeated sentences, filler words, decorative language.
DO NOT add any information not in the original text.

TEXT:
{text[:30000]}

SUMMARY:"""
    return _call_groq(prompt, max_tokens=3000)


def ai_exam_prep(text: str, num_questions: int = 10) -> Optional[str]:
    if not GROQ_AVAILABLE:
        return None
    prompt = f"""You are an expert exam creator. Based on the following text, generate {num_questions} exam questions.
Include a mix of: MCQ (with 4 options + correct answer), Short Answer, Essay, and Problem Solving.
For each question, provide: the question, answer, explanation, and difficulty level.
Focus on concepts that are repeated, emphasized, or defined in the text.
DO NOT invent questions about topics not in the text.

TEXT:
{text[:25000]}

EXAM QUESTIONS:"""
    return _call_groq(prompt, max_tokens=3000)


def ai_teacher_mode(text: str) -> Optional[str]:
    if not GROQ_AVAILABLE:
        return None
    prompt = f"""You are an experienced professor analyzing teaching materials. Based on the text, provide:
1. Teaching style (definition-heavy, application-focused, balanced, etc.)
2. Key concepts the teacher emphasizes (with reasons)
3. Question types the teacher likely prefers (MCQ, essay, problem-solving)
4. Difficulty level prediction
5. Topics most likely to appear on exams
6. Common student traps or tricky concepts
7. Recommended study strategy

TEXT:
{text[:25000]}

ANALYSIS:"""
    return _call_groq(prompt, max_tokens=2500)


def ai_qa_generate(text: str, num_qa: int = 10) -> Optional[str]:
    if not GROQ_AVAILABLE:
        return None
    prompt = f"""Convert the following study material into {num_qa} question-answer pairs.
Include: definition questions, concept explanation questions, comparison questions, and enumeration questions.
Each Q&A should have: a clear question, a complete answer from the text, and the type of question.
Format as: Q: [question] | A: [answer] | Type: [type]

TEXT:
{text[:25000]}

Q&A PAIRS:"""
    return _call_groq(prompt, max_tokens=3000)
