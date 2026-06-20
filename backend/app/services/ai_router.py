import os
import time
import logging
from typing import Optional

logger = logging.getLogger("examai-hub")

_clients = {}
_available = {}

# --- Groq ---
def _init_groq():
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return False
    try:
        from groq import Groq
        _clients["groq"] = Groq(api_key=key)
        _user_clients["groq"] = {}
        logger.info("Groq initialized (platform key)")
        return True
    except Exception as e:
        logger.warning(f"Groq init failed: {e}")
        return False


_user_clients = {}


def _get_or_create_user_client(provider: str, user_id: int, db_session=None):
    if provider not in _user_clients:
        _user_clients[provider] = {}

    if user_id in _user_clients[provider]:
        return _user_clients[provider][user_id]

    user_key = _get_user_api_key(user_id, provider)
    if not user_key:
        return None

    try:
        if provider == "groq":
            from groq import Groq
            client = Groq(api_key=user_key)
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=user_key)
        else:
            return None

        _user_clients[provider][user_id] = client
        return client
    except Exception:
        return None


def _get_user_api_key(user_id: int, provider: str) -> str:
    from app.database import SessionLocal
    from app.routers.settings import get_user_api_key
    db = SessionLocal()
    try:
        return get_user_api_key(db, user_id, provider)
    finally:
        db.close()


def route_ai(text: str, mode: str, max_tokens: int = 2000, user_id: int = 0) -> dict:
    prompt = _build_prompt(text, mode)

    for name in MODEL_ORDER:
        result = None

        if user_id > 0:
            user_client = _get_or_create_user_client(name, user_id)
            if user_client:
                if name == "groq":
                    result = _call_groq_with_client(user_client, prompt, max_tokens)
                elif name == "openai":
                    result = _call_openai_with_client(user_client, prompt, max_tokens)
                if result:
                    return {"result": result, "model": f"user-{name}", "ai_powered": True}

        if _available.get(name):
            if name == "groq":
                result = _call_groq(prompt, max_tokens)
            elif name == "gemini":
                result = _call_gemini(prompt, max_tokens)
            elif name == "deepseek":
                result = _call_deepseek(prompt, max_tokens)
            elif name == "local_ollama":
                result = _call_ollama(prompt, max_tokens)
            elif name == "huggingface":
                result = _call_hf(prompt, max_tokens)
            if result:
                return {"result": result, "model": name, "ai_powered": True}

    return {"result": None, "model": "rule_based", "ai_powered": False}


def _call_groq_with_client(client, prompt: str, max_tokens: int = 2000) -> Optional[str]:
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.warning(f"User Groq call failed: {e}")
        return None


def _call_openai_with_client(client, prompt: str, max_tokens: int = 2000) -> Optional[str]:
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.warning(f"User OpenAI call failed: {e}")
        return None


def _call_groq(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    if "groq" not in _clients:
        return None
    try:
        r = _clients["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.warning(f"Groq call failed: {e}")
        return None


# --- Gemini ---
def _init_gemini():
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return False
    try:
        from google import genai
        _clients["gemini"] = genai.Client(api_key=key)
        logger.info("Gemini initialized")
        return True
    except Exception as e:
        logger.warning(f"Gemini init failed: {e}")
        return False


def _call_gemini(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    if "gemini" not in _clients:
        return None
    try:
        r = _clients["gemini"].models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"max_output_tokens": max_tokens, "temperature": 0.3},
        )
        return r.text
    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
        return None


# --- DeepSeek ---
def _init_deepseek():
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        return False
    try:
        from openai import OpenAI
        _clients["deepseek"] = OpenAI(api_key=key, base_url="https://api.deepseek.com")
        logger.info("DeepSeek initialized")
        return True
    except Exception as e:
        logger.warning(f"DeepSeek init failed: {e}")
        return False


def _call_deepseek(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    if "deepseek" not in _clients:
        return None
    try:
        r = _clients["deepseek"].chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.warning(f"DeepSeek call failed: {e}")
        return None


# --- HuggingFace ---
def _init_hf():
    key = os.getenv("HF_TOKEN", "")
    if not key:
        return False
    try:
        logger.info("HuggingFace initialized (token present)")
        return True
    except Exception:
        return False


def _call_hf(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    key = os.getenv("HF_TOKEN", "")
    if not key:
        return None
    try:
        import httpx
        r = httpx.post(
            "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-1.5B-Instruct",
            headers={"Authorization": f"Bearer {key}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "temperature": 0.3}},
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("generated_text", "")
            if isinstance(data, dict):
                return data.get("generated_text", "")
    except Exception as e:
        logger.warning(f"HuggingFace call failed: {e}")
    return None


# --- Ollama (stub - requires Cloudflare tunnel) ---
def _call_ollama(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    return None


# --- Init all ---
_available["groq"] = _init_groq()
_available["gemini"] = _init_gemini()
_available["deepseek"] = _init_deepseek()
_available["huggingface"] = _init_hf()
_available["ollama"] = False

# First route_ai MODEL_ORDER
MODEL_ORDER = ["huggingface", "groq", "gemini", "deepseek"]


def route_ai(text: str, mode: str, max_tokens: int = 2000) -> dict:
    prompt = _build_prompt(text, mode)

    for name in MODEL_ORDER:
        if name == "hf_space" and _available.get("hf_space"):
            result = _call_hf_space(prompt, max_tokens)
        elif name == "local_ollama" and _available.get("ollama"):
            result = _call_ollama(prompt, max_tokens)
        elif name == "huggingface" and _available.get("huggingface"):
            result = _call_hf(prompt, max_tokens)
        elif name == "groq" and _available.get("groq"):
            result = _call_groq(prompt, max_tokens)
        elif name == "gemini" and _available.get("gemini"):
            result = _call_gemini(prompt, max_tokens)
        elif name == "deepseek" and _available.get("deepseek"):
            result = _call_deepseek(prompt, max_tokens)
        else:
            continue
        if result:
            return {"result": result, "model": name, "ai_powered": True}

    return {"result": None, "model": "rule_based", "ai_powered": False}


def _init_hf_space():
    url = os.getenv("HF_SPACE_URL", "https://mohammedid99-ollama.hf.space")
    try:
        import httpx
        r = httpx.get(f"{url}/health", timeout=10)
        if r.status_code == 200 and r.json().get("status") == "ok":
            logger.info(f"HF Space connected: {url}")
            return True
    except Exception:
        pass
    return False


def _call_hf_space(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    url = os.getenv("HF_SPACE_URL", "https://mohammedid99-ollama.hf.space")
    try:
        import httpx
        r = httpx.post(f"{url}/generate", json={"prompt": prompt, "max_tokens": max_tokens, "temperature": 0.3}, timeout=90)
        if r.status_code == 200:
            return r.json().get("text", "")
    except Exception as e:
        logger.warning(f"HF Space call failed: {e}")
    return None


_available["hf_space"] = _init_hf_space()


def _build_prompt(text: str, mode: str) -> str:
    text = text[:30000]
    prompts = {
        "summarize": f"""Summarize this text for exam study. Keep 40-55% of original length.
PRESERVE: definitions, key concepts, formulas, examples, comparisons, exam hints.
REMOVE ONLY: filler words, repeated sentences.
DO NOT add anything not in the text.

TEXT: {text}
SUMMARY:""",

        "exam_predict": f"""Generate 5 exam questions from this text.
Include: MCQ (with options+answer), Short Answer, Essay.
Base all questions on the text. Provide correct answers.

TEXT: {text}
QUESTIONS:""",

        "teacher_mode": f"""Analyze this teaching material like a professor.
Provide: teaching style, emphasized concepts, likely question types, difficulty level, exam topics, student traps, study strategy.

TEXT: {text}
ANALYSIS:""",

        "qa_generate": f"""Convert this text into Q&A study pairs. 
Generate 8-10 pairs covering: definitions, comparisons, key concepts, lists.
Format: Q: [question] | A: [answer] | Type: [type]

TEXT: {text}
Q&A:""",

        "full_exam": f"""Create a complete exam from this text. Include all question types. Provide answer key.

TEXT: {text}
EXAM:""",
    }
    return prompts.get(mode, prompts["summarize"])


def is_any_ai_available() -> bool:
    return any(_available.values())
