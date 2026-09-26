from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

from tokenizers import Regex, Tokenizer, models, pre_tokenizers

from models.ltx2.ltx_core.text_encoders.gemma.tokenizer import LTXVGemmaTokenizer


REAL_TOKENIZER_PATH = Path("/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1")


class LTXVGemmaTokenizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.tokenizer_path = Path(self._temporary_directory.name)
        self._write_synthetic_tokenizer(self.tokenizer_path)

    def _write_synthetic_tokenizer(self, path: Path) -> None:
        """Build a local fast tokenizer exhibiting both deployed-config edge cases."""
        vocabulary = {
            "<pad>": 0,
            "<eos>": 1,
            "a": 2,
            "cat": 3,
            "<|video|>": 4,
        }
        # transformers only invokes its Mistral regex patch for vocabularies over 100k.
        for index in range(5, 100_001):
            vocabulary[f"__wd_i7qs_{index}"] = index

        backend = Tokenizer(models.BPE(vocab=vocabulary, merges=[]))
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

    def test_extra_special_tokens_load_without_the_mistral_patch(self) -> None:
        tokenizer = LTXVGemmaTokenizer(
            str(self.tokenizer_path),
            max_length=16,
            extra_special_tokens={"video_token": "<|video|>"},
        )

        self.assertEqual(tokenizer.tokenizer.model_max_length, 16)
        self.assertIn(
            4,
            tokenizer.tokenizer("<|video|> a cat", add_special_tokens=False)["input_ids"],
        )

    def test_wrapper_defaults_keep_the_two_options_independent(self) -> None:
        parameters = inspect.signature(LTXVGemmaTokenizer.__init__).parameters

        self.assertFalse(parameters["fix_mistral_regex"].default)
        self.assertIsNone(parameters["extra_special_tokens"].default)

    def test_list_only_extra_special_tokens_still_need_the_dict_override(self) -> None:
        with self.assertRaises(AttributeError) as raised:
            LTXVGemmaTokenizer(str(self.tokenizer_path), max_length=16)

        self.assertIn("'list' object has no attribute 'keys'", str(raised.exception))

    def test_enabling_the_mistral_patch_still_fails_on_bare_split(self) -> None:
        with self.assertRaises(TypeError) as raised:
            LTXVGemmaTokenizer(
                str(self.tokenizer_path),
                max_length=16,
                fix_mistral_regex=True,
                extra_special_tokens={"video_token": "<|video|>"},
            )

        self.assertIn("does not support item assignment", str(raised.exception))

    @unittest.skipUnless(REAL_TOKENIZER_PATH.is_dir(), "deployed gemma4 tokenizer is unavailable")
    def test_deployed_gemma4_video_token(self) -> None:
        tokenizer = LTXVGemmaTokenizer(
            str(REAL_TOKENIZER_PATH),
            max_length=1024,
            extra_special_tokens={"video_token": "<|video|>"},
        )
        encoded = tokenizer.tokenizer(
            "<|video|> a cat walks through rain",
            add_special_tokens=False,
        )["input_ids"]

        self.assertEqual(tokenizer.tokenizer.convert_tokens_to_ids("<|video|>"), 258884)
        self.assertIn(258884, encoded)


if __name__ == "__main__":
    unittest.main()
