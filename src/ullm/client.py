from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ChatResult:
    text: str
    model_returned: str | None
    usage: dict[str, Any] | None
    raw: dict[str, Any]


class OpenAICompatibleClient:
    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, timeout_s: float = 120, max_retries: int = 5) -> None:
        self.api_key = api_key or os.getenv("ZZZ_API_KEY")
        self.base_url = (base_url or os.getenv("ZZZ_BASE_URL") or "https://api.zhizengzeng.com/v1").rstrip("/")
        if not self.api_key:
            raise RuntimeError("ZZZ_API_KEY is not set. Copy .env.example to .env locally; never commit the key.")
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    async def chat(self, *, model: str, messages: list[dict[str, str]], temperature: float = 0.0, max_tokens: int = 300, seed: int | None = None) -> ChatResult:
        payload: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if seed is not None:
            payload["seed"] = seed
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code in {408, 409, 429} or response.status_code >= 500:
                        raise httpx.HTTPStatusError("retryable", request=response.request, response=response)
                    response.raise_for_status()
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    return ChatResult(text=text, model_returned=data.get("model"), usage=data.get("usage"), raw=data)
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    if attempt >= self.max_retries:
                        raise RuntimeError(f"Request failed for {model} after retries") from exc
                    await asyncio.sleep(min(30.0, (2**attempt) + random.random()))
        raise AssertionError("unreachable")
