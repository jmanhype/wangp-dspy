#!/bin/bash
set -euo pipefail
LIVE=/home/straughter/Wan2GP
printf "asset_count=%d\n" 15
fail=0
expected=b4bb89c54e025d834f0c6138dbf80c245e8196c27c8bff8dd47db4c03412c72f
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b-distilled_diffusion_model_int8_convrot.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b-distilled_diffusion_model_int8_convrot.safetensors" "$actual"
expected=685b06ee3d9b2039647698fc4ea33175112462fc374e2777312c907897dfce8d
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_video_vae_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_video_vae_bf16.safetensors" "$actual"
expected=847e14ca7f3355debca0cea4eaa24ac0fbcdf0061da054ac89ca638a869ddba3
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_diffusion_video_vae_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_diffusion_video_vae_bf16.safetensors" "$actual"
expected=43ed048b9a5aa7eac181cf1b5bf68382aa4fb9d98627575d01d9b187d3462028
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_audio_vae_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_audio_vae_bf16.safetensors" "$actual"
expected=a865b27a492fea788dc35bed29b333103ca1fb9c280f4fd77976ad19a3b13435
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_vocoder_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_vocoder_bf16.safetensors" "$actual"
expected=06b7017692b2d0d42a863d609cf40e7672243eb3d13ae7a19650a7a8294ac494
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_text_embedding_projection_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_text_embedding_projection_bf16.safetensors" "$actual"
expected=9559f09ff6fb1b3dca10617722df7133838ea0fee6f1457c90e992447796d765
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_video_embeddings_connector_int8_convrot.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_video_embeddings_connector_int8_convrot.safetensors" "$actual"
expected=80270afb795fdac363dcd8329e6b375f6ca93f6a3d74a25b2bb440d342095362
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-22b_audio_embeddings_connector_int8_convrot.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-22b_audio_embeddings_connector_int8_convrot.safetensors" "$actual"
expected=eb5a71fe4068ee87ccdb1c3aa635e547ca76bd2d30ae20ae889f2c325c0677e8
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-spatial-upscaler-x2-1.0_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-spatial-upscaler-x2-1.0_bf16.safetensors" "$actual"
expected=2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors" "$actual"
expected=6a23b673266b65a318e26cad27fabd5c67609f4ecf51aa13996feb07d0060903
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/gemma4-12b-ltx-v1_int8_convrot.safetensors | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-gemma4-gemma4-12b-ltx-v1_int8_convrot.safetensors" "$actual"
expected=cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/tokenizer.json | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-gemma4-tokenizer.json" "$actual"
expected=82ec29063791629eac6a023c662f4edc2a811e479343ae79f21b8453357caeb0
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/config.json | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-gemma4-config.json" "$actual"
expected=ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/chat_template.jinja | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-gemma4-chat_template.jinja" "$actual"
expected=794a39f8330ce05020774c70c091225bc5f031b9cacf41fc20e52eb54b4b52d8
actual=$(sha256sum /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/tokenizer_config.json | awk '{print $1}')
if test "$actual" = "$expected"; then status=MATCH; else status=MISMATCH; fail=1; fi
printf "%s %s %s\n" "$status" "ltx25-gemma4-tokenizer_config.json" "$actual"
test "$fail" = 0
printf "all_ltx25_assets=PASS\n"
