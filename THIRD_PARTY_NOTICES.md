# Third-party notices and model constraints

This notice identifies third-party material that Wangp references, adapts, downloads, or invokes. It is factual attribution, not legal advice. **The Apache-2.0 licence for this repository covers only repository-owned code and documentation. It does not licence, relicence, or waive conditions for third-party models, weights, datasets, hosted services, or their outputs.**

## Maestro and Wan2GP / H3 stack

- Wangp's Director architecture was pattern-matched from Maestro as an idea/spec reference. The repository records Maestro as licensed under **WanGP Non-Commercial Evaluation 1.1**. No Maestro source is vendored or copied verbatim; `tests/test_no_maestro_verbatim.py` continuously rejects shared verbatim code runs.
- The production renderer targets the external Wan2GP environment and MiniMax H3 / Ref2VA handler/checkpoints under `/home/straughter/Wan2GP`. Wan2GP, Maestro, MiniMax H3 models, model settings, and generated media remain subject to their respective upstream licences, terms, and use policies.
- Do not assume commercial redistribution rights for H3/Wan2GP artifacts. Obtain and record the applicable current terms before redistribution or commercial use.

## SyncNet v2

- `qc/audio_critic/syncnet_model.py` adapts the PyTorch model definition from Joon Son Chung's MIT-licensed SyncNet demo. The adaptation is attributed at the source file.
- SyncNet v2 weights are **not committed**. The runtime downloads the Oxford VGG weight file only by its pinned URL and SHA-256 (`961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442`). Those weights remain external assets under their upstream terms.
- SyncNet evidence measures audio/lip embedding synchrony. It does not grant phonetic correctness or any model-rights licence.

## Whisper

- Whisper transcript gates invoke an external Whisper runtime/model supplied by the operator or render host. Whisper code and model files are not vendored by Wangp.
- Obtain the applicable OpenAI Whisper licence/terms for the exact package and model artifact in use. Model availability or licensing in one deployment does not transfer to another artifact version.

## Qwen-family models

- Wangp can invoke Qwen2-Audio, Qwen-VL/ModelScope, and local Qwen-family vision deployments through explicit adapters. No Qwen model or credential is included.
- Qwen model cards, weights, hosted endpoints, and outputs are governed by Alibaba/Qwen and the selected deployment provider's then-current terms. Those terms may differ by model, region, and API deployment.
- A configured endpoint is not a licence grant. Operators must ensure the selected model and use case satisfy the upstream terms and retain the model identity recorded in evidence.

## Other external assets

- VibeVoice audio models, MiniMax/H3 checkpoints, ModelScope or other hosted services, FFmpeg, Python packages, committed reference images, and generated media retain their upstream or creator rights. Dependency licences are available through the locked package metadata.
- External methodology documents under `docs/` carry source and licence attribution where adapted. Their inclusion as citation does not transfer rights to underlying models or creative works.

Before adding a model, weight, corpus, or hosted service, add its identity, licence, acquisition path, and output constraints here and in the relevant story evidence.
