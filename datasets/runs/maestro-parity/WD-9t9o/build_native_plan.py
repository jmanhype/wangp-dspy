#!/usr/bin/env python3
"""Generate native Wan2GP settings for the WD-9t9o VDN operation batch."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = "/home/straughter/Wan2GP/wd-9t9o/inputs/source.mp4"
FIRST_FRAME = "/home/straughter/Wan2GP/wd-9t9o/inputs/first-frame.png"
MASK = "/home/straughter/Wan2GP/wd-9t9o/inputs/repaint-mask.mp4"
RECAST_REFERENCE = "/home/straughter/Wan2GP/wd-9t9o/inputs/recast-reference.png"


def base(seed: int, *, length: int = 56) -> dict:
    return {
        "model_type": "minimax_h3_fl2va_pruned",
        "resolution": "480x832",
        "seed": seed,
        "video_length": length,
        "num_inference_steps": 8,
        "guidance_scale": 1.0,
        "embedded_guidance_scale": 6.0,
        "force_fps": "24",
        "sample_solver": "euler",
        "image_prompt_type": "",
        "image_start": None,
        "image_end": None,
        "image_refs": [],
        "video_source": None,
        "video_guide": None,
        "video_guide2": None,
        "video_mask": None,
        "video_prompt_type": "T",
        "audio_prompt_type": "",
        "denoising_strength": 1.0,
        "masking_strength": 1.0,
        "override_attention": "sol",
        "attention_sparsity": 1.0,
    }


def write(name: str, settings: dict) -> None:
    target = ROOT / "native-settings" / f"{name}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")


def main() -> int:
    extend = base(2961, length=120)
    extend.update({
        "image_prompt_type": "V",
        "video_source": SOURCE,
        "sliding_window_size": 362,
        "sliding_window_overlap": 18,
        "prompt": "Continue the VDN crane-and-compass scene naturally: the crane turns once, cool light shifts, and paper sounds settle.",
    })
    retake = base(2962)
    retake.update({
        "image_prompt_type": "S",
        "image_start": FIRST_FRAME,
        "prompt": "Retake from the supplied VDN first frame with a slower crane turn, softer light, and one clear paper click.",
    })
    edit = base(2963)
    edit.update({
        "video_guide": SOURCE,
        "video_prompt_type": "GV",
        "audio_prompt_type": "K",
        "denoising_strength": 0.45,
        "prompt": "Edit the VDN crane scene: warm the light, refine the brass compass, and preserve motion and soundtrack.",
    })
    repaint = base(2964)
    repaint.update({
        "video_guide": SOURCE,
        "video_mask": MASK,
        "video_prompt_type": "GVA",
        "audio_prompt_type": "K",
        "masking_strength": 0.5,
        "custom_settings": {"h3_mask_mode": "shared_timestep"},
        "prompt": "Repaint only the central compass region with cleaner brass; preserve the surrounding crane, map, and soundtrack.",
    })
    blend = base(2965)
    blend.update({
        "video_guide": SOURCE,
        "video_guide2": SOURCE,
        "video_prompt_type": "GV+-U",
        "prompt": "Blend the two supplied VDN takes while preserving continuity.",
    })
    recast = base(2966)
    recast.update({
        "image_prompt_type": "I",
        "image_refs": [RECAST_REFERENCE],
        "video_prompt_type": "I",
        "prompt": "Recast the visual subject using the supplied contextual reference while preserving the VDN scene.",
    })
    outpaint = base(2967)
    outpaint.update({
        "video_guide": SOURCE,
        "video_prompt_type": "GV",
        "video_guide_outpainting": "20 20 20 20",
        "video_guide_outpainting_ratio": "",
        "prompt": "Widen the VDN scene with additional paper map and soft window light.",
    })
    for name, settings in {
        "extend": extend,
        "retake": retake,
        "edit": edit,
        "repaint": repaint,
        "blend-probe": blend,
        "recast-probe": recast,
        "outpaint-probe": outpaint,
    }.items():
        write(name, settings)
    write("upscale", {
        "mode": "edit_postprocessing",
        "prompt": "Media postprocessing",
        "image_mode": 0,
        "video_source": SOURCE,
        "temporal_upsampling": "",
        "spatial_upsampling": "lanczos2",
        "spatial_upsampler_prompt": "",
        "spatial_upsampler_reference_images": [],
        "spatial_upsampler_face_count": 1,
        "film_grain_intensity": 0,
        "film_grain_saturation": 0.5,
        "postprocess_audio": "",
        "repeat_generation": 1,
        "batch_size": 1,
        "seed": 2968,
    })
    print(json.dumps({"settings": 8, "source": SOURCE}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
