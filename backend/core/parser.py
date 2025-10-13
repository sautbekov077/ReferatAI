import json
import re
from backend.models.schemas import Section

CODE_FENCE_RE = re.compile(r"^``````$", flags=re.IGNORECASE | re.MULTILINE)

def _strip_code_fences(text: str) -> str:
    return CODE_FENCE_RE.sub("", text).strip()

def _trim_to_balanced_braces(s: str) -> str:
    depth = 0
    last_good = -1
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last_good = i
    if last_good != -1:
        return s[: last_good + 1]
    return s

def _fix_trailing_commas(s: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", s)

def _extract_json_maybe(text: str) -> str:
    s = (text or "").strip()
    if not s:
        raise ValueError("Пустой ответ модели")
    if len(s) >= 3 and s[:3] == "```":
        s = _strip_code_fences(s)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    s = _fix_trailing_commas(s)
    s = _trim_to_balanced_braces(s)
    return s.strip()

def _normalize(node: dict) -> Section:
    title = str(node.get("title", "Документ")).strip()
    paragraphs = []
    for p in (node.get("paragraphs") or []):
        if isinstance(p, str):
            t = p.strip()
            if t:
                paragraphs.append(t)
    subsections = []
    for sub in (node.get("subsections") or []):
        if isinstance(sub, dict):
            subsections.append(_normalize(sub))
    return Section(title=title, paragraphs=paragraphs, subsections=subsections)

def parse_essay(text: str) -> Section:
    raw = _extract_json_maybe(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("\u0000", "").replace("\ufeff", "")
        cleaned = _fix_trailing_commas(cleaned)
        data = json.loads(cleaned)
    return _normalize(data)
