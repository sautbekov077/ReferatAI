import httpx
import time
from backend.core.config import settings

def supports_json_mode(model: str | None) -> bool:
    # qwen/qwen3-coder:free обычно без json_object режима
    return False

async def chat_complete(prompt: str, model: str | None = None) -> str:
    mdl = model or settings.DEFAULT_MODEL
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "DocGen Local",
    }
    messages = [
        {"role": "system", "content": "Output valid JSON object only. No markdown, no code fences, no extra text. Ensure JSON ends with '}'."},
        {"role": "user", "content": prompt.strip() + "\n\nReturn JSON only."}
    ]
    payload = {
        "model": mdl,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 25000
    }
    backoff = 2.0
    for _ in range(5):
        try:
            async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
                r = await client.post(f"{settings.OPENROUTER_BASE}/chat/completions", headers=headers, json=payload)
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(wait)
                backoff = min(backoff * 2, 30.0)
                continue
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(wait)
                backoff = min(backoff * 2, 30.0)
                continue
            raise
        except httpx.RequestError:
            time.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
    raise RuntimeError("API rate limited: 429 Too Many Requests. Try again later.")
