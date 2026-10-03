#!/usr/bin/env python3
"""Independent local-Qwen review for WD-28ac native outputs."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence


ENDPOINT = "http://127.0.0.1:8000/v1/chat/completions"
MODEL = "q"
THRESHOLD = 8.0
PROMPT = (
    "You are an independent video-output reviewer. Review the supplied visual "
    "evidence for obvious generation failure: severe anatomy distortion, "
    "unreadable frame, blank output, temporal collapse, or destructive artifacts. "
    'Return STRICT JSON only: {"score": 1-10, "verdict": "approve" or "reject", '
    '"summary": "one sentence", "artifacts": ["named visible issues"]}. '
    "Score 8 or higher with no blocking artifact is approve."
)


class ReviewError(ValueError):
    """Typed independent-review boundary."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _data_url(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")

def parse_review(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match is None:
            raise ReviewError("reviewer response is not JSON")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ReviewError("reviewer response root is not an object")
    score = value.get("score")
    verdict = value.get("verdict")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ReviewError("reviewer score is not numeric")
    if verdict not in {"approve", "reject"}:
        raise ReviewError("reviewer verdict is invalid")
    artifacts = value.get("artifacts", [])
    if not isinstance(artifacts, list) or any(not isinstance(item, str) for item in artifacts):
        raise ReviewError("reviewer artifacts must be a string array")
    score = float(score)
    if not 1.0 <= score <= 10.0:
        raise ReviewError("reviewer score is outside 1..10")
    approved = verdict == "approve" and score >= THRESHOLD and not artifacts
    return {
        "score": score,
        "requested_verdict": verdict,
        "artifacts": artifacts,
        "summary": str(value.get("summary", "")),
        "decision": "approved" if approved else "rejected",
    }

def request_review(
    contact_sheet: Path, *, endpoint: str = ENDPOINT, timeout: int = 300
) -> dict[str, Any]:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": _data_url(contact_sheet)}},
        ]}],
        "temperature": 0,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8", "replace"))
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ReviewError("reviewer response lacks choices[0].message.content") from exc
    return parse_review(text) | {
        "raw_response": text,
        "raw_response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "critic": "local:qwen38-27b-Q4_K_M.gguf",
        "threshold": THRESHOLD,
    }

def review_file(contact_sheet: Path, output: Path) -> dict[str, Any]:
    if not contact_sheet.is_file():
        raise ReviewError(f"contact sheet absent: {contact_sheet}")
    value = request_review(contact_sheet)
    value |= {
        "schema_version": "wangp-dspy.wd-28ac.independent-review/v1",
        "contact_sheet": str(contact_sheet),
        "contact_sheet_sha256": _sha256(contact_sheet),
        "independent": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("contact_sheet", type=Path)
    parser.add_argument("output", type=Path)
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = review_file(args.contact_sheet, args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["decision"] == "approved" else 2
    except (ReviewError, OSError, ValueError) as exc:
        print(json.dumps({
            "status": "failed_closed", "code": "INDEPENDENT_REVIEW_FAILED",
            "observed": str(exc), "remediation": "Preserve output and stop without retry.",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
