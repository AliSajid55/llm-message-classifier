import os
import time
import random
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIStatusError

load_dotenv(override=True)

LOG_DIR = Path(__file__).parent.parent.parent / "logs"


def get_client():
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0,
    )


def get_model():
    return os.environ.get("LLM_MODEL", "openrouter/free")


def is_retryable_error(error: Exception) -> bool:
    if isinstance(error, APITimeoutError):
        return True
    if isinstance(error, APIStatusError):
        return error.status_code in (429, 500, 502, 503, 504)
    return False


def get_retry_after(error: APIStatusError) -> float:
    if hasattr(error, "response") and error.response is not None:
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return 1.0


def call_with_retry(client: OpenAI, model: str, messages: list, attempt: int = 0) -> tuple:
    start = time.time()
    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=messages,
        )
        duration_ms = (time.time() - start) * 1000
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        return {
            "content": content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "duration_ms": round(duration_ms, 2),
            "repaired": False,
            "error": None,
        }, None
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        if is_retryable_error(e) and attempt < 2:
            if isinstance(e, APIStatusError) and e.status_code == 429:
                wait = get_retry_after(e)
            else:
                wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
            return call_with_retry(client, model, messages, attempt + 1)
        return None, str(e)


def log_call(model: str, input_tokens: int, output_tokens: int, duration_ms: float, repaired: bool, error: str | None = None):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "calls.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "repaired": repaired,
        "error": error,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
