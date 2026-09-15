"""Measured conditioning provenance at the production host boundary."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess


def measure_conditioning(host, wire: dict, *, wgp_root: str) -> dict:
    def probe(argv):
        rc, out, err = host.run_probe(argv, timeout=120)
        if rc:
            raise ValueError(f'conditioning probe failed: {argv[0]}: {(err or "")[-200:]}')
        return out

    paths = list(dict.fromkeys([wire.get('image_start'), *wire['image_refs'], wire['audio_guide']]))
    assets = {}
    for path in filter(None, paths):
        digest = probe(['sha256sum', path]).split()[0]
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError(f'no SHA256 for mapped conditioning asset {path}')
        assets[path] = digest
    audio = json.loads(probe([
        'ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
        'stream=duration,sample_rate,channels', '-of', 'json', wire['audio_guide']]))
    streams = audio.get('streams', [])
    if len(streams) != 1:
        raise ValueError('one audio guide stream required')
    stream = streams[0]
    duration = float(stream['duration'])
    cut_s = wire['video_length'] / 24
    if not math.isfinite(duration) or not 2 <= duration <= cut_s + 0.1:
        raise ValueError(f'measured audio duration {duration}s outside 2s..{cut_s + 0.1}s')
    if int(stream['channels']) != 1:
        raise ValueError('single-speaker guide must be mono (speaker identity still requires source verification)')
    # Fingerprint the actual dirty dispatch/model code, not only a nominal SHA.
    code = {}
    for relative in ('wgp.py', 'models/minimax_h3/multishot.py',
                     'models/minimax_h3/minimax_h3_handler.py',
                     'models/minimax_h3/transformer.py'):
        code[relative] = probe(['sha256sum', f'{wgp_root}/{relative}']).split()[0]
    root = Path(__file__).resolve().parents[1]
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    diff = subprocess.check_output(['git', 'diff', '--binary'], cwd=root)
    source_hashes = {}
    for package in ('predict', 'host', 'qc', 'services', 'scripts'):
        for path in sorted((root / package).rglob('*.py')):
            source_hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'schema_version': 1, 'expected_dispatch': 'native_ref2va',
            'mapped_asset_sha256': assets, 'guide_probe': stream,
            'guide_duration_s': duration, 'cut_duration_s': cut_s,
            'wgp_code_sha256': code, 'repo_sha': sha,
            'repo_tracked_diff_sha256': hashlib.sha256(diff).hexdigest(),
            'effective_repo_source_sha256': source_hashes,
            'wire_settings_sha256': hashlib.sha256(
                json.dumps(wire, sort_keys=True).encode()).hexdigest(),
            'limitations': ['model/checkpoint hashes and full environment lock not captured']}
