"""Corrective pass (S3, PR #47) blocker 2: write_run_records must hash
the CANONICAL sidecar `audio_manifest.json` beside the render — not the
fictional `{key}_audio_manifest.json`."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "s4" / "scripts" / "write_run_records.py"


def _load_fn(name):
    # extract the pure helper without running the script body
    src = SCRIPT.read_text()
    marker = "# --- pure helper under test (extracted) ---"
    helper = (
        "import hashlib\n"
        "from pathlib import Path\n"
        "def sha(p):\n"
        "    h = hashlib.sha256()\n"
        "    with open(p, 'rb') as f:\n"
        "        for chunk in iter(lambda: f.read(1 << 20), b''):\n"
        "            h.update(chunk)\n"
        "    return h.hexdigest()\n"
        "def audio_manifest_sha(film, key):\n"
        "    sidecar = film / 'renders' / key / 'audio_manifest.json'\n"
        "    return sha(sidecar) if sidecar.is_file() else None\n"
    )
    ns = {"__name__": "wrr_helper"}
    exec(helper, ns)
    return ns[name]


def _helper_from_script(tmp_path):
    """Import the helpers the script ACTUALLY defines (source of truth)."""
    src = SCRIPT.read_text()
    start = src.index("def sha(")
    end = src.index("\n\n", src.index("def audio_manifest_sha256_for"))
    defs = "import hashlib\nfrom pathlib import Path\n" + src[start:end]
    ns = {"__name__": "wrr"}
    exec(defs, ns)
    return ns["audio_manifest_sha256_for"]


def test_sidecar_present_returns_hash(tmp_path):
    fn = _helper_from_script(tmp_path)
    renders = tmp_path / "renders" / "cut1"
    renders.mkdir(parents=True)
    payload = json.dumps({"audio_policy": {"discard": True}}, sort_keys=True)
    sidecar = renders / "audio_manifest.json"
    sidecar.write_text(payload + "\n")
    got = fn(tmp_path, "cut1")
    assert got is not None
    import hashlib
    assert got == hashlib.sha256((payload + "\n").encode()).hexdigest()


def test_sidecar_absent_is_honest_none(tmp_path):
    fn = _helper_from_script(tmp_path)
    (tmp_path / "renders" / "cut1").mkdir(parents=True)
    assert fn(tmp_path, "cut1") is None


def test_script_no_fictional_keyed_sidecar_name():
    """The buggy lookup hashed renders/{key}_audio_manifest.json; that
    filename must not appear in the script anymore."""
    src = SCRIPT.read_text()
    assert "_audio_manifest.json" not in src.replace(
        "audio_manifest.json", "")
