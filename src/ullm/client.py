from __future__ import annotations

import asyncio
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ChatResult:
    text: str
    model_returned: str | None
    usage: dict[str, Any] | None
    raw: dict[str, Any]
    latency_s: float
    request_id: str | None
    http_status: int
    attempts_used: int


class OpenAICompatibleClient:
    """Small resilient client for an OpenAI-compatible chat-completions gateway.

    One AsyncClient is reused across requests so a 10k+ call experiment does not
    repeatedly create TCP/TLS pools. API keys are read only from the environment.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 120,
        max_retries: int = 5,
        user_agent: str = "ULLM-research/0.4",
    ) -> None:
        self.api_key = api_key or os.getenv("ZZZ_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("ZZZ_BASE_URL")
            or "https://api.zhizengzeng.com/v1"
        ).rstrip("/")
        if not self.api_key:
            raise RuntimeError(
                "ZZZ_API_KEY is not set. Keep the key only in your shell/.env; never commit it."
            )
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s),
            limits=httpx.Limits(max_keepalive_connections=32, max_connections=64),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 300,
        seed: int | None = None,
        request_overrides: dict[str, Any] | None = None,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed

        # Model-specific compatibility controls are frozen in experiment.yaml and
        # recorded in every request artifact. They may add provider-supported fields
        # (for example DeepSeek's `thinking` toggle), but may never silently replace
        # the common scientific controls above.
        if request_overrides:
            collisions = sorted(set(request_overrides) & set(payload))
            if collisions:
                raise ValueError(
                    "request_overrides may not replace common request fields: "
                    + ", ".join(collisions)
                )
            payload.update(request_overrides)

        url = f"{self.base_url}/chat/completions"
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                response = await self._client.post(url, headers=self._headers, json=payload)
                latency_s = time.perf_counter() - started
                if response.status_code in {408, 409, 425, 429} or response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "retryable gateway response",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                request_id = (
                    response.headers.get("x-request-id")
                    or response.headers.get("request-id")
                    or data.get("id")
                )
                return ChatResult(
                    text=text,
                    model_returned=data.get("model"),
                    usage=data.get("usage"),
                    raw=data,
                    latency_s=latency_s,
                    request_id=request_id,
                    http_status=response.status_code,
                    attempts_used=attempt + 1,
                )
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                if attempt >= self.max_retries:
                    status = None
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                        status = exc.response.status_code
                    raise RuntimeError(
                        f"Request failed for {model} after {self.max_retries + 1} attempts"
                        + (f"; last_http_status={status}" if status is not None else "")
                    ) from exc
                # Exponential backoff + jitter; respect Retry-After when present.
                retry_after = None
                if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                    retry_after = exc.response.headers.get("retry-after")
                try:
                    wait_s = float(retry_after) if retry_after is not None else None
                except ValueError:
                    wait_s = None
                if wait_s is None:
                    wait_s = min(60.0, (2**attempt) + random.random())
                await asyncio.sleep(max(0.0, wait_s))

        raise AssertionError("unreachable")
