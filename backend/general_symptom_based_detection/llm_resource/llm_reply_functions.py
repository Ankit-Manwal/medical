import json
import re
from typing import List, Dict, Any


def _extract_json_block(text: str) -> str:
    """Extract the largest JSON-like block from text (handles code fences)."""
    if not text:
        return ""
    # Remove code fences if present
    text = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", text.strip())
    # Greedy match outermost braces
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text


def parse_llm_reply_to_dict(ai_reply: str) -> Dict[str, Any]:
    """Parse model reply into dict; return {} on failure."""
    try:
        raw = _extract_json_block(ai_reply)
        return json.loads(raw)
    except Exception:
        return {}


def _ensure_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        flat: List[str] = []
        for item in value:
            if isinstance(item, list):
                flat.extend([str(x).strip() for x in item if str(x).strip()])
            else:
                s = str(item).strip()
                if s:
                    flat.append(s)
        return flat
    if isinstance(value, str):
        if not value.strip():
            return []
        return [s.strip() for s in value.split(',') if s.strip()]
    s = str(value).strip()
    return [s] if s else []


def normalize_llm_reply(reply: Dict[str, Any], known_symptoms_list: List[str], known_tests_list: List[str]) -> Dict[str, Any]:
    """Coerce LLM reply to normalized schema with lists and filtered values."""
    known_symptoms_set = {s.strip() for s in known_symptoms_list}
    known_tests_set = {t.strip() for t in known_tests_list}

    symptoms_to_add = [s for s in _ensure_list(reply.get("symptoms_to_add")) if s in known_symptoms_set]
    symptoms_to_removed = [s for s in _ensure_list(reply.get("symptoms_to_removed")) if s in known_symptoms_set]

    tests_raw = _ensure_list(reply.get("specific_tests_to_run"))
    specific_tests_to_run: List[str] = []
    for t in tests_raw:
        if t in known_tests_set:
            specific_tests_to_run.append(t)
        else:
            specific_tests_to_run.append(t)

    def dedupe(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    specific_tests_to_run = dedupe(specific_tests_to_run)
    symptoms_to_add = dedupe(symptoms_to_add)
    symptoms_to_removed = dedupe(symptoms_to_removed)

    diseases_detail_value = reply.get("specific_diseases_detail")
    specific_diseases_detail: List[Dict[str, Any]] = []
    if isinstance(diseases_detail_value, list):
        for item in diseases_detail_value:
            if isinstance(item, dict):
                specific_diseases_detail.append({
                    "disease": str(item.get("disease", "")).strip(),
                    "description": str(item.get("description", "")).strip(),
                    "likely_causes": _ensure_list(item.get("likely_causes")),
                    "precautions": _ensure_list(item.get("precautions")),
                })
    elif isinstance(diseases_detail_value, str) and diseases_detail_value.strip():
        specific_diseases_detail.append({
            "disease": "",
            "description": diseases_detail_value.strip(),
            "likely_causes": [],
            "precautions": [],
        })

    priority_order = _ensure_list(reply.get("priority_order"))
    valid_keys = {"specific_tests_to_run", "symptoms_to_add", "symptoms_to_removed", "specific_diseases_detail"}
    priority_order = [k for k in priority_order if k in valid_keys]
    if not priority_order:
        priority_order = ["specific_tests_to_run", "symptoms_to_add", "symptoms_to_removed", "specific_diseases_detail"]

    invalid_input = str(reply.get("invalid_input", "")).strip()

    return {
        "symptoms_to_add": symptoms_to_add,
        "symptoms_to_removed": symptoms_to_removed,
        "specific_tests_to_run": specific_tests_to_run,
        "specific_diseases_detail": specific_diseases_detail,
        "invalid_input": invalid_input,
        "priority_order": priority_order,
    }


