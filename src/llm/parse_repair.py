import json
import re
from pathlib import Path
from datetime import datetime, timezone
from pydantic import ValidationError
from src.llm.schema import TriageResponse

QUARANTINE_DIR = Path(__file__).parent.parent.parent / "logs"


def strip_code_fence(text: str) -> str:
    text = text.strip()
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def find_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_model_output(raw: str) -> dict:
    cleaned = strip_code_fence(raw)
    cleaned = find_json_object(cleaned)
    return json.loads(cleaned)


def validate_output(data: dict) -> TriageResponse:
    return TriageResponse.model_validate(data)


def log_quarantine(raw: str, error: str, prompt_version: str, input_text: str):
    QUARANTINE_DIR.mkdir(exist_ok=True)
    quarantine_file = QUARANTINE_DIR / "quarantine.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_text,
        "raw_output": raw,
        "error": error,
        "prompt_version": prompt_version,
    }
    with open(quarantine_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def parse_and_validate(raw: str, input_text: str, prompt_version: str = "v1"):
    try:
        data = parse_model_output(raw)
        return validate_output(data), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, str(e)
