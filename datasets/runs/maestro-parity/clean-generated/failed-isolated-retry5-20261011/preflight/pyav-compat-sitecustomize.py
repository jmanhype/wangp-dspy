import inspect, os, sys
from pathlib import Path
try:
    if os.environ.get("PYTHONPATH", "").split(":")[0] != str(Path(__file__).parent):
        raise RuntimeError("compatibility directory must lead PYTHONPATH")
    import torchvision.io as io
    import torchvision.io.video as video
    original = video.write_video
    if io.write_video is not original or original.__module__ != "torchvision.io.video" or original.__name__ != "write_video":
        raise RuntimeError("unexpected writer alias")
    source = inspect.getsource(original)
    legacy = 'frame.pict_type = "NONE"'
    if source.count(legacy) != 1 or sum(line.strip() == legacy for line in source.splitlines()) != 1:
        raise RuntimeError("missing or unexpected legacy writer source")
    namespace = dict(video.__dict__)
    exec(compile(source.replace(legacy, "frame.pict_type = 0"), "<WD-pp86-pyav-compat>", "exec"), namespace)
    patched = namespace["write_video"]
    video.write_video = patched
    io.write_video = patched
    if video.write_video is not patched or io.write_video is not patched:
        raise RuntimeError("writer alias patch failed")
    PYAV_COMPAT_APPLIED = True
except BaseException as exc:
    sys.stderr.write("PYAV_COMPAT_FAILED: " + type(exc).__name__ + ": " + str(exc) + "\n")
    sys.stderr.flush()
    os._exit(78)  # Ordinary sitecustomize exceptions are swallowed by Python.
