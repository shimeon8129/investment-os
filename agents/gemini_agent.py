# =========================================================
# agents/gemini_agent.py
# Google Gemini API wrapper for narrative scoring (free tier)
# =========================================================

import os
import json
from google import genai
from google.genai import types

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


SYSTEM_PROMPT = """\
You are a Taiwan stock market analyst specializing in AI supply chain narrative analysis.

Given a list of Taiwan stock tickers (with names), analyze each stock's narrative strength \
in the context of the current AI supply chain / semiconductor theme.

You MUST output ONLY a valid JSON array. No explanation. No markdown. No extra text.

Each element must have exactly these fields:
{
  "ticker": "<ticker>",
  "name": "<company name in Chinese>",
  "narrative_score": <integer 0-100>,
  "narrative_strength": "<HIGH|MID|LOW>",
  "theme": "<main theme driving this stock>",
  "summary": "<one sentence in Traditional Chinese>",
  "confidence": <integer 0-100>
}

Scoring rules:
- narrative_score 80-100: strong AI/semiconductor tailwind, hot money flow, clear catalyst
- narrative_score 60-79: moderate relevance, sector rotation potential
- narrative_score below 60: weak or no narrative fit
- narrative_strength: HIGH if score>=80, MID if 60-79, LOW if <60
"""


def call_gemini_narrative(tickers_with_names: list[dict], perspective: str = "主流") -> list[dict]:
    """
    Call Gemini API to score narrative strength for given tickers.

    Args:
        tickers_with_names: list of {"ticker": ..., "name": ...}
        perspective: analysis angle label

    Returns:
        list of narrative score dicts
    """
    client = _get_client()

    ticker_lines = "\n".join(
        f"- {t['ticker']} ({t['name']})" for t in tickers_with_names
    )

    user_prompt = f"""\
分析視角：{perspective}
今日日期：{__import__('datetime').date.today()}

請分析以下台灣股票在 AI 供應鏈敘事中的強度：

{ticker_lines}

輸出 JSON array，包含所有上述股票。
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        contents=user_prompt
    )

    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    start = raw.index("[")
    end = raw.rindex("]") + 1
    return json.loads(raw[start:end])
