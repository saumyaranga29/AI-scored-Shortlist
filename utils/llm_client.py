"""
LLM client using Groq's free API (OpenAI-compatible).
Free tier: 30 RPM, 14,400 requests/day — no credit card required.
Fast inference on Llama 3.3 70B and other top-tier models.
"""
import os
import json
import re
import time
from openai import OpenAI, APIStatusError
from dotenv import load_dotenv

load_dotenv()

# Groq models (all free on free tier)
AVAILABLE_MODELS = {
    "⭐ Llama 3.3 70B (FREE - Best)": "llama-3.3-70b-versatile",
    "⭐ Llama 3.1 8B (FREE - Fast)": "llama-3.1-8b-instant",
    "⭐ Gemma 2 9B (FREE)": "gemma2-9b-it",
    "⭐ Llama 3.1 70B (FREE)": "llama-3.1-70b-versatile",
    "⭐ Mixtral 8x7B (FREE)": "mixtral-8x7b-32768",
}

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Fallback chain on rate-limit
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_llm_client(api_key: str = None) -> OpenAI:
    """Create a Groq-backed OpenAI-compatible client."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError(
            "GROQ_API_KEY not set. "
            "Get a free key at https://console.groq.com and add GROQ_API_KEY to your .env file."
        )
    return OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=key,
    )


def extract_json(text: str) -> dict:
    """Robustly extract JSON from LLM response text."""
    # 1. Try markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 2. Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 3. Find outermost JSON object / array
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract valid JSON from response:\n{text[:300]}")


def chat_completion(
    messages: list,
    model: str = None,
    api_key: str = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """
    Send a chat completion request via Groq.
    Automatically retries with exponential backoff on 429,
    and falls back through FALLBACK_MODELS on persistent failures.
    """
    primary = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    chain = [primary] + [m for m in FALLBACK_MODELS if m != primary]

    last_error = None
    for attempt_model in chain:
        for retry in range(3):
            try:
                client = get_llm_client(api_key)
                response = client.chat.completions.create(
                    model=attempt_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if attempt_model != primary:
                    print(f"[llm_client] Fell back to: {attempt_model}")
                return response.choices[0].message.content

            except APIStatusError as e:
                last_error = e
                status = e.status_code
                if status == 429:
                    wait = 2 ** retry   # 1s → 2s → 4s
                    print(f"[llm_client] 429 on {attempt_model}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                elif status in (404, 400):
                    print(f"[llm_client] {status} on {attempt_model}, trying next model...")
                    break
                else:
                    raise
        else:
            print(f"[llm_client] All retries failed for {attempt_model}, trying next...")
            continue

    raise RuntimeError(
        f"All models in fallback chain failed. Last error: {last_error}"
    )
