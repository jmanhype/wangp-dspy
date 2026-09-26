from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from tokenizers import Regex, Tokenizer, models, pre_tokenizers
from transformers import AutoTokenizer


def build(path: Path) -> None:
    vocab = {
        "<pad>": 0,
        "<eos>": 1,
        "a": 2,
        "cat": 3,
        "<|video|>": 4,
    }
    for index in range(5, 100_001):
        vocab[f"__wd_i7qs_{index}"] = index
    backend = Tokenizer(models.BPE(vocab=vocab, merges=[]))
    backend.pre_tokenizer = pre_tokenizers.Split(Regex(" "), behavior="isolated")
    backend.save(str(path / "tokenizer.json"), pretty=True)
    (path / "tokenizer_config.json").write_text(
        json.dumps(
            {
                "tokenizer_class": "PreTrainedTokenizerFast",
                "extra_special_tokens": ["<|video|>"],
                "is_local": True,
                "local_files_only": True,
                "model_max_length": 16,
                "pad_token": "<pad>",
                "eos_token": "<eos>",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (path / "config.json").write_text(
        json.dumps({"model_type": "gemma4_unified_text"}),
        encoding="utf-8",
    )


with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary)
    build(path)
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            path,
            local_files_only=True,
            model_max_length=16,
            fix_mistral_regex=True,
            extra_special_tokens={"video_token": "<|video|>"},
        )
    except Exception as error:
        print(f"LOAD_ERROR={type(error).__name__}: {error}")
        sys.exit(2)
    print(f"vocab_size={tokenizer.vocab_size}")
    print(f"fix_mistral_regex={getattr(tokenizer, 'fix_mistral_regex', None)}")
    print(f"pre_tokenizer={type(tokenizer.backend_tokenizer.pre_tokenizer).__name__}")
    try:
        tokenizer.backend_tokenizer.pre_tokenizer[0] = tokenizer.backend_tokenizer.pre_tokenizer
    except Exception as error:
        print(f"DIRECT_ASSIGN_ERROR={type(error).__name__}: {error}")
    print(f"ids={tokenizer('<|video|> a cat', add_special_tokens=False)['input_ids']}")
