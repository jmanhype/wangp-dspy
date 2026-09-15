"""Explicit recovery after native rendering succeeded but transport failed.

No rerender, guessing, or QC waiver. Original evidence stays read-only; normal
runtime/QC continue in a newly allocated attempt directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def recover_completed_render(*, host, recovery, wire, conditioning,
                             settings_local, raw_local, wgp_root, outputs_dir):
    from host.wangp_adapter import WanGPError, _host_path, _host_frame_count, verify_denoise_steps

    def reject(message):
        raise WanGPError(f'completed-render recovery refused: {message}')

    def probe(argv):
        rc, out, err = host.run_probe(argv, timeout=120)
        if rc:
            reject(f'{argv[0]} failed: {(err or "")[-200:]}')
        return out or ''

    if not isinstance(recovery, dict) or not str(recovery.get('reason', '')).strip():
        reject('explicit source directory, SHA256 and operator reason required')
    expected_hash = recovery.get('native_sha256', '')
    if not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
        reject('expected native SHA256 required')
    source_dir = Path(recovery.get('source_dir', '')).resolve()
    run_root = settings_local.parent.parent.resolve()
    if source_dir.parent != run_root or source_dir == settings_local.parent.resolve():
        reject('source must be a separate prior attempt in the same render namespace')
    try:
        old_wire = json.loads((source_dir / 'wgp-settings.json').read_text())
        old_evidence = json.loads((source_dir / 'conditioning-evidence.json').read_text())
        log = (source_dir / 'render.log').read_text()
    except (OSError, ValueError) as exc:
        reject(f'original evidence missing or invalid: {exc}')
    if old_wire != wire:
        reject('original wire settings differ from current job')
    for field in ('mapped_asset_sha256', 'wgp_code_sha256', 'wire_settings_sha256'):
        if not old_evidence.get(field) or old_evidence[field] != conditioning.get(field):
            reject(f'{field} changed since render')
    if ('[MULTISHOT]' in log or 'Encoding H3 prompt and references' not in log
            or not re.search(r'(?m)^\s*Queue completed:\s*1/1\s+tasks\b', log)
            or not verify_denoise_steps(log, int(wire.get('num_inference_steps') or 20))):
        reject('no verified completed native Ref2VA render')
    names = re.findall(r'(?m)^Video file saved to Path:[ \t]*(.+\.mp4)[ \t]*$', log)
    if len(names) != 1:
        reject('exactly one authoritative saved-output line required')
    name = names[0].strip()
    if any(ord(c) < 32 for c in name) or '..' in PurePosixPath(name).parts:
        reject('invalid output path in completion line')
    source = PurePosixPath(name)
    if not source.is_absolute():
        source = PurePosixPath(wgp_root) / source
    if source.parent != PurePosixPath(outputs_dir):
        reject('completed output outside configured outputs directory')
    canonical_root = probe(['readlink', '-f', outputs_dir]).strip()
    canonical_source = probe(['readlink', '-f', str(source)]).strip()
    if PurePosixPath(canonical_source).parent != PurePosixPath(canonical_root):
        reject('completed output resolves outside configured outputs directory')
    probe(['test', '-f', str(source)])
    if probe(['sha256sum', str(source)]).split()[0] != expected_hash:
        reject('completed output SHA256 does not match requested native artifact')
    if _host_frame_count(host, str(source)) != wire['video_length']:
        reject('native frame count mismatch')
    raw_host = _host_path(host, str(raw_local.parent)).rstrip('/') + '/' + raw_local.name
    probe(['cp', str(source), raw_host])
    host.fetch_file(raw_host, str(raw_local))
    if hashlib.sha256(raw_local.read_bytes()).hexdigest() != expected_hash:
        reject('pulled native artifact SHA256 mismatch')
    (settings_local.parent / 'render.log').write_text(log)
    # The executor's independent log gate reads the host mirror. Publish the
    # same verified log there too, rather than claiming a new render occurred.
    host.write_text(_host_path(host, str(settings_local.parent / 'render.log')), log)
    proof = {**recovery, 'source_dir': str(source_dir), 'remote_native_path': str(source),
             'source_log_sha256': hashlib.sha256(log.encode()).hexdigest(),
             'wire_settings_sha256': conditioning['wire_settings_sha256'],
             're_rendered': False, 'qc_waived': False}
    (settings_local.parent / 'recovery-evidence.json').write_text(json.dumps(proof, indent=2)+'\n')
    return raw_local
