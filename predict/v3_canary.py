"""Pinned-artifact regression gate; not a general audiovisual quality judge.

Run with python -m predict.v3_canary. It reads completed artifacts only, never
renders, replaces audio, or changes queue/verdict state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import subprocess

from predict.v3_recipe import V3_RECIPE


class GoldenCanaryError(ValueError):
    pass


def _probe(path: Path) -> list[dict]:
    proc = subprocess.run([
        'ffprobe', '-v', 'error', '-count_frames', '-show_entries',
        'stream=codec_type,nb_read_frames,start_time,r_frame_rate,duration',
        '-of', 'json', str(path)], capture_output=True, text=True, timeout=60)
    if proc.returncode:
        raise GoldenCanaryError(f'ffprobe failed: {proc.stderr[-200:]}')
    return json.loads(proc.stdout)['streams']


def verify_v3_canary(*, cut1, cut2, pair, seed, report_path) -> dict:
    paths = {key: Path(value).resolve() for key, value in
             dict(cut1=cut1, cut2=cut2, pair=pair, seed=seed).items()}
    report_path = Path(report_path).resolve()
    if report_path in paths.values():
        raise GoldenCanaryError('canary report must not overwrite an input artifact')
    expected = dict(V3_RECIPE.golden_sha256)
    artifacts, errors = {}, []
    for key, path in paths.items():
        try:
            data = path.read_bytes()
            artifacts[key] = {'path':str(path), 'sha256':hashlib.sha256(data).hexdigest(),
                              'md5':hashlib.md5(data).hexdigest(), 'bytes':len(data)}
            if artifacts[key]['sha256'] != expected[key]:
                errors.append(f'{key}: golden SHA256 mismatch')
        except OSError as exc:
            errors.append(f'{key}: unreadable artifact: {exc}')
    # Hash mismatches fail immediately; never turn a similar-looking result
    # into a golden pass by weakening the media checks or reseeding.
    if not errors:
        for key in ('cut1', 'cut2', 'pair'):
            try:
                streams = _probe(paths[key])
                artifacts[key]['streams'] = streams
                video = [s for s in streams if s.get('codec_type') == 'video']
                audio = [s for s in streams if s.get('codec_type') == 'audio']
                if len(video) != 1 or len(audio) != 1:
                    raise ValueError('one video and one audio stream required')
                frames = V3_RECIPE.frames * (2 if key == 'pair' else 1)
                if int(video[0]['nb_read_frames']) != frames:
                    raise ValueError('frame count differs from golden contract')
                if Fraction(video[0]['r_frame_rate']) != V3_RECIPE.fps:
                    raise ValueError('FPS differs from golden contract')
                for stream in (video[0], audio[0]):
                    start = float(stream['start_time'])
                    if not math.isfinite(start) or abs(start) > 0.000001:
                        raise ValueError('audio/video start timestamp must be zero')
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                errors.append(f'{key}: {exc}')
    report = {'schema':'wangp-dspy.v3-golden-canary/v1', 'recipe_version':V3_RECIPE.version,
              'passed':not errors, 'artifacts':artifacts, 'errors':errors,
              'scope':'Exact original two-cut artifacts and chain seed on the pinned environment; not new-premise quality or fresh-clone acceptance.'}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    if errors:
        raise GoldenCanaryError('; '.join(errors))
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('cut1','cut2','pair','seed','report'):
        parser.add_argument('--'+name, required=True)
    args=parser.parse_args(argv)
    try:
        report=verify_v3_canary(cut1=args.cut1, cut2=args.cut2, pair=args.pair,
                                seed=args.seed, report_path=args.report)
    except GoldenCanaryError as exc:
        print(f'golden canary refused: {exc}')
        return 2
    print(json.dumps({'passed':report['passed'],'report_path':str(Path(args.report).resolve()),
                      'md5':{k:v['md5'] for k,v in report['artifacts'].items()}}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
