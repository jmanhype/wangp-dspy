from __future__ import annotations

import json
from pathlib import Path

import tokenizers
import transformers

from models.ltx2.ltx_core.text_encoders.gemma.tokenizer import LTXVGemmaTokenizer


TOKENIZER_PATH = Path("/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1")


def load(label: str, **kwargs: object) -> None:
    try:
        tokenizer = LTXVGemmaTokenizer(str(TOKENIZER_PATH), 1024, **kwargs)
    except Exception as error:
        print(f"{label}: FAIL {type(error).__name__}: {error}")
        return

    video_id = tokenizer.tokenizer.convert_tokens_to_ids("<|video|>")
    sample = tokenizer.tokenizer(
        "<|video|> a cat walks through rain",
        add_special_tokens=False,
    )["input_ids"]
    video_only = tokenizer.tokenizer("<|video|>")["input_ids"]
    print(f"{label}: OK vocab={tokenizer.tokenizer.vocab_size} video_token_id={video_id}")
    print(f"{label}: ids={sample}")
    print(f"{label}: video_only_ids={video_only}")


print(f"transformers={transformers.__version__} tokenizers={tokenizers.__version__}")
print(f"tokenizer_path={TOKENIZER_PATH}")
with (TOKENIZER_PATH / "config.json").open(encoding="utf-8") as handle:
    model_type = json.load(handle).get("model_type")
gemma4 = model_type == "gemma4_unified_text"
print(f"model_type={model_type} gemma4={gemma4}")

load(
    "old_conflation",
    fix_mistral_regex=True,
    extra_special_tokens={"video_token": "<|video|>"},
)
load("no_override")
load(
    "real_gemma4_path",
    **({"extra_special_tokens": {"video_token": "<|video|>"}} if gemma4 else {}),
)
