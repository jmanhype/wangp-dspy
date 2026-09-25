#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-$(git rev-parse --show-toplevel)}
BUNDLE="$ROOT/datasets/runs/maestro-parity/WD-bxhc"
WGP="$ROOT/.venv/bin/wgp"
PYTHON="$ROOT/.venv/bin/python"
cd "$BUNDLE"
mkdir -p packages planning/boundaries

"$PYTHON" - <<'PY'
import json
from pathlib import Path

bundle = Path.cwd()
request = json.loads(Path('planning/requests/vibevoice-clone-two.json').read_text())
alias = dict(request)
alias['output_path_planned'] = str(bundle / 'outputs/unused-ambiguous-witness.wav')
alias['character'] = {
    'character_id': 'Ambiguous Witness',
    'speaker_label': 'Witness',
    'voice_binding_id': 'ambiguous-witness-v1',
    'appearance': request['character']['appearance'],
}
Path('planning/requests/vibevoice-clone-two-alias.json').write_text(
    json.dumps(alias, indent=2, sort_keys=True) + '\n')

appearance = Path('inputs/appearance-native.png')
definitions = {
    'planning/character-definition.json': {
        'schema_version': 'wangp-dspy.character-package/v1',
        'character_id': 'Portable Witness',
        'speaker_label': 'Witness',
        'version': 1,
        'description': 'Operator-owned synthetic portable character for WD-bxhc evidence',
        'appearance': [{
            'path': str(bundle / appearance),
            'sha256': __import__('hashlib').sha256(appearance.read_bytes()).hexdigest(),
            'role': 'native', 'width': 260, 'height': 360,
            'source_path': 'inputs/appearance-native.png',
            'license': 'Operator-owned WD-m0r5/LF004 evaluation asset; authorized reference reuse only',
            'consent_ref': 'operator-authorization.md#operator-owned-appearance',
        }],
        'voice': {
            'path': str(bundle / 'packages/portable-witness.wgpvoice'),
            'voice_binding_id': 'portable-witness-v1',
        },
        'continuity': {
            'modes': ['image', 'video'],
            'constraints': [
                {'metric': 'face_embedding_cosine', 'threshold': 0.75},
                {'metric': 'cross_mode_binding', 'threshold': 1.0},
            ],
        },
        'recipe_seed': 9441,
    }
}
payload = dict(definitions['planning/character-definition.json'])
payload['character_id'] = 'Ambiguous Witness'
payload['description'] = 'Second operator-owned synthetic identity sharing the Witness alias'
payload['recipe_seed'] = 9442
payload['voice'] = {
    'path': str(bundle / 'packages/ambiguous-witness.wgpvoice'),
    'voice_binding_id': 'ambiguous-witness-v1',
}
definitions['planning/ambiguous-character-definition.json'] = payload
for name, document in definitions.items():
    Path(name).write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')
PY

"$WGP" voice export --request planning/requests/vibevoice-clone-two.json \
  --models planning/models.json --package packages/portable-witness.wgpvoice --json \
  > packages/voice-export.json
"$WGP" voice import --package packages/portable-witness.wgpvoice \
  --destination packages/imported-voice --json > packages/voice-import.json
"$WGP" voice export --request planning/requests/vibevoice-clone-two-alias.json \
  --models planning/models.json --package packages/ambiguous-witness.wgpvoice --json \
  > packages/ambiguous-voice-export.json

"$WGP" character create --definition planning/character-definition.json \
  --out planning/character-normalized.json --json > packages/character-create.json
"$WGP" character bind-voice --definition planning/character-normalized.json \
  --voice packages/portable-witness.wgpvoice --out planning/character-bound.json --json \
  > packages/character-bind-voice.json
"$WGP" character export --definition planning/character-bound.json \
  --package packages/portable-witness.wgpcharacter --json > packages/character-export.json
"$WGP" character show --package packages/portable-witness.wgpcharacter --json \
  > packages/character-show.json
"$WGP" character import --package packages/portable-witness.wgpcharacter \
  --destination packages/imported-character --json > packages/character-import.json
"$WGP" character export --definition planning/character-bound.json \
  --package packages/portable-witness.repeated.wgpcharacter --json \
  > packages/character-reexport.json
"$WGP" character recover --package packages/portable-witness.wgpcharacter \
  --destination packages/recovered-native.png --json > packages/native-recovery.json

"$WGP" character create --definition planning/ambiguous-character-definition.json \
  --out planning/ambiguous-character-normalized.json --json > packages/ambiguous-character-create.json
"$WGP" character bind-voice --definition planning/ambiguous-character-normalized.json \
  --voice packages/ambiguous-witness.wgpvoice --out planning/ambiguous-character-bound.json --json \
  > packages/ambiguous-character-bind-voice.json
"$WGP" character export --definition planning/ambiguous-character-bound.json \
  --package packages/ambiguous-witness.wgpcharacter --json > packages/ambiguous-character-export.json

mkdir -p packages/registry-valid packages/registry-duplicate packages/registry-ambiguous
cp packages/portable-witness.wgpcharacter packages/registry-valid/one.wgpcharacter
cp packages/portable-witness.wgpcharacter packages/registry-duplicate/one.wgpcharacter
cp packages/portable-witness.wgpcharacter packages/registry-duplicate/two.wgpcharacter
cp packages/portable-witness.wgpcharacter packages/registry-ambiguous/one.wgpcharacter
cp packages/ambiguous-witness.wgpcharacter packages/registry-ambiguous/two.wgpcharacter

"$WGP" character resolve --registry packages/registry-valid --identity 'Portable Witness' --json \
  > packages/registry-resolve-id.json
"$WGP" character resolve --registry packages/registry-valid --identity witness --json \
  > packages/registry-resolve-alias.json

"$PYTHON" - <<'PY'
import json
from pathlib import Path

shown = json.loads(Path('packages/character-show.json').read_text())
manifest = shown['manifest']
appearance = manifest['appearance'][0]
base = {
    'schema_version': 'wangp-dspy.character-continuity-request/v1',
    'prompt': 'Preserve the bound Portable Witness identity while producing the WD-bxhc mode artifact.',
    'character': {
        'package_path': str(Path.cwd() / 'packages/portable-witness.wgpcharacter'),
        'package_sha256': shown['package_sha256'],
        'character_id': manifest['character_id'],
        'speaker_label': manifest['speaker_label'],
        'appearance_member': appearance['member'],
        'appearance_sha256': appearance['sha256'],
        'voice_member': manifest['voice']['member'],
        'voice_binding_id': manifest['voice']['voice_binding_id'],
        'voice_sha256': manifest['voice']['sha256'],
        'modes': manifest['continuity']['modes'],
    },
    'recipe_seed': 9441,
}
for mode, operation in (('image', 'identity_edit'), ('video', 'create')):
    payload = dict(base, mode=mode, operation=operation)
    Path(f'planning/requests/character-{mode}.json').write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n')

variants = {}
for name, field, value in (
    ('package-hash', ('character', 'package_sha256'), 'b' * 64),
    ('appearance-binding', ('character', 'appearance_sha256'), 'c' * 64),
    ('voice-binding', ('character', 'voice_binding_id'), 'unbound-voice-v1'),
):
    payload = json.loads(json.dumps(base), object_pairs_hook=dict)
    target = payload
    for key in field[:-1]:
        target = target[key]
    target[field[-1]] = value
    variants[f'character-{name}'] = payload
for name, payload in variants.items():
    Path(f'planning/requests/{name}.json').write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n')
PY

"$WGP" character plan --request planning/requests/character-image.json \
  --db planning/databases/character-image.db --json > planning/cli/character-image.json
"$WGP" character plan --request planning/requests/character-video.json \
  --db planning/databases/character-video.db --json > planning/cli/character-video.json
"$WGP" character plan --reconstruct --db planning/databases/character-image.db --json \
  > planning/cli/character-image.reconstruct.json
"$WGP" character plan --reconstruct --db planning/databases/character-video.db --json \
  > planning/cli/character-video.reconstruct.json

run_negative() {
  local name=$1
  shift
  set +e
  "$@" > "planning/boundaries/$name.stdout.json" 2> "planning/boundaries/$name.stderr.txt"
  local code=$?
  set -e
  printf '%s\n' "$code" > "planning/boundaries/$name.exit"
}
mkdir -p planning/boundaries
run_negative package-mismatch "$WGP" character plan --request planning/requests/character-package-hash.json --dry-run --json
run_negative appearance-mismatch "$WGP" character plan --request planning/requests/character-appearance-binding.json --dry-run --json
run_negative voice-mismatch "$WGP" character plan --request planning/requests/character-voice-binding.json --dry-run --json
run_negative registry-duplicate "$WGP" character resolve --registry packages/registry-duplicate --identity 'Portable Witness' --json
run_negative registry-ambiguous "$WGP" character resolve --registry packages/registry-ambiguous --identity witness --json

sha256sum packages/portable-witness.wgpvoice packages/portable-witness.wgpcharacter \
  packages/portable-witness.repeated.wgpcharacter packages/recovered-native.png \
  > packages/package-hashes.txt
"$PYTHON" - <<'PY'
import json
from pathlib import Path

results = {
    'round_trip_package_hashes_equal': (
        Path('packages/portable-witness.wgpcharacter').read_bytes()
        == Path('packages/portable-witness.repeated.wgpcharacter').read_bytes()
    ),
    'native_recovery_hash_equal': (
        Path('inputs/appearance-native.png').read_bytes()
        == Path('packages/recovered-native.png').read_bytes()
    ),
}
for name in ('registry-duplicate', 'registry-ambiguous', 'package-mismatch',
             'appearance-mismatch', 'voice-mismatch'):
    results[name + '_exit'] = int(Path(f'planning/boundaries/{name}.exit').read_text().strip())
for name in ('character-image', 'character-video'):
    reconstruct = json.loads(Path(f'planning/cli/{name}.reconstruct.json').read_text())
    results[name + '_reconstruction_all_match'] = reconstruct['all_match']
    results[name + '_reconstruction_hidden_mutation'] = reconstruct['hidden_mutation']
Path('packages/character-operation-results.json').write_text(
    json.dumps(results, indent=2, sort_keys=True) + '\n')
print(json.dumps(results, sort_keys=True))
PY
