import sitecustomize
if getattr(sitecustomize, "PYAV_COMPAT_APPLIED", False) is not True:
    raise RuntimeError("PYAV_COMPAT_FAILED: patch not applied")
import hashlib, json, platform, sys
from pathlib import Path
import torch, torchvision, av
versions = {"python": platform.python_version(), "torch": torch.__version__,
            "torchvision": torchvision.__version__, "av": av.__version__}
print(json.dumps({"versions": versions}), flush=True)
output = Path(sys.argv[1])
if output.exists():
    raise RuntimeError("media-write output must be fresh")
torchvision.io.write_video(str(output), torch.zeros((1, 8, 8, 3), dtype=torch.uint8), fps=24)
print(json.dumps({"size_bytes": output.stat().st_size,
                  "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}), flush=True)
