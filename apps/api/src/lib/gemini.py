"""LLM client for the FactCheck pipeline.

Named `gemini` for the default provider, but kept provider-agnostic: the model
is env-driven so swapping to another LangChain chat model (Grok via ChatXAI,
Claude via ChatAnthropic, etc.) is a config change, not a code change. See the
LLM-provider decision in PROJECT.md.

Env:
    GEMINI_API_KEY   required for the default Google provider
    GEMINI_MODEL     default "gemini-2.5-flash" (overridable)
    LLM_TEMPERATURE  default "0.1"
"""

import json
import os
import re
import time

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# gemini-2.5-flash (not flash-lite): stronger instruction-following and
# calibration for the synthesis/critic agents, still on Gemini's free tier
# (~1.5k requests/day). Overridable via GEMINI_MODEL.
DEFAULT_MODEL = "gemini-2.5-flash"

_llm: ChatGoogleGenerativeAI | None = None


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a lazily-initialized singleton chat model."""
    global _llm
    if _llm is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _llm = ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
            google_api_key=api_key,
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.1")),
        )
    return _llm


def _is_transient(msg: str) -> bool:
    return any(s in msg for s in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"))


def invoke(prompt: str, max_attempts: int = 5) -> str:
    """Call the LLM with exponential backoff on transient 429/503 errors."""
    llm = get_llm()
    for attempt in range(max_attempts):
        try:
            return llm.invoke([HumanMessage(content=prompt)]).content.strip()
        except Exception as e:  # noqa: BLE001 — retry on any transient API error
            if _is_transient(str(e)) and attempt < max_attempts - 1:
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


def invoke_json(prompt: str, max_attempts: int = 5) -> dict | list:
    """Call the LLM and parse a JSON object/array, stripping markdown fences."""
    text = invoke(prompt, max_attempts=max_attempts)
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(text)
