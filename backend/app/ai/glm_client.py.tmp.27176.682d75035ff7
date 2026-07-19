"""GLM client using httpx (no zhipuai SDK)."""
import os
import httpx
from typing import Dict, Any, Iterator, Optional


class GLMClientError(Exception):
    """GLM API error."""


class GLMClient:
    """Client for GLM chat and image generation (httpx direct)."""

    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
        )

    def chat(
        self,
        model: str,
        messages: list,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> Dict[str, Any]:
        """Chat completion (non-streaming)."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def chat_stream(
        self,
        model: str,
        messages: list,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        """Chat completion (streaming)."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    # Parse SSE line
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: "
                        if data == "[DONE]":
                            break
                        try:
                            chunk = httpx.utils.json_loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except Exception:
                            continue

    def generate_image(
        self, model: str, prompt: str, size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """Generate image from prompt."""
        payload = {"model": model, "prompt": prompt, "size": size}
        response = self.client.post("/images/generations", json=payload)
        response.raise_for_status()
        return response.json()