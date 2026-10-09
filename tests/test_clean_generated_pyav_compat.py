"""Local dependency fixtures, NOT real codec or new GPU-host evidence."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import record_clean_generated_proof as recorder


class LocalHost:
    def push_file(self, source, target):
        shutil.copyfile(source, target)
        return target

    def fetch_file(self, source, target):
        shutil.copyfile(source, target)

    def run_probe(self, argv, timeout=120):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr


def fixture_runtime(tmp_path, mode):
    runtime = tmp_path / "fixture-runtime"
    io = runtime / "torchvision/io"
    io.mkdir(parents=True)
    (runtime / "torch.py").write_text('__version__="fixture"\nuint8=0\ndef zeros(shape,dtype): return shape\n')
    (runtime / "av.py").write_text('__version__="fixture"\n')
    (runtime / "torchvision/__init__.py").write_text('from . import io\n__version__="fixture"\n')
    (io / "__init__.py").write_text('from .video import write_video\n')
    body = '''import os
from pathlib import Path
class Frame:
    def __setattr__(self, name, value):
        if type(value) is not int: raise TypeError("an integer is required")
def write_video(path, frames, fps):
    assert os.environ["HF_HUB_OFFLINE"] == os.environ["TRANSFORMERS_OFFLINE"] == "1"
    frame = Frame()
    frame.pict_type = "NONE"
    Path(path).write_bytes(b"fixture-video-not-real-codec")
'''
    if mode == "source":
        body = body.replace('frame.pict_type = "NONE"', 'frame.pict_type = "AUTO"')
    if mode == "write":
        body = body.replace('Path(path).write_bytes(b"fixture-video-not-real-codec")', 'raise OSError("fixture encoder failure")')
    (io / "video.py").write_text(body)
    if mode == "alias":
        with (io / "__init__.py").open("a") as handle:
            handle.write('import sys, types\nclass Locked(types.ModuleType):\n'
                         '    def __setattr__(self, name, value):\n'
                         '        if name != "write_video": super().__setattr__(name,value)\n'
                         'sys.modules[__name__].__class__ = Locked\n')
    if mode == "missing-source":
        with (io / "video.py").open("a") as handle:
            handle.write('exec("def write_video(path, frames, fps): pass")\n')
    config = {"remote_work_root": str(tmp_path / "remote"), "wgp_python": sys.executable,
              "runtime": {"python": sys.executable, "pythonpath": [str(runtime)], "environment": {}}}
    proof = tmp_path / "proof"
    recorder.record(proof / "inputs/resolved-host.json", config)
    return config, proof


@pytest.mark.parametrize("mode", ["success", "source", "missing-source", "alias", "write", "missing-shim", "changed-shim"])
def test_real_subprocess_shim_and_media_boundary(tmp_path, mode):
    config, proof = fixture_runtime(tmp_path, mode)
    host = LocalHost()
    config["pyav_compat"] = recorder.stage_pyav_compat(host, proof, config)
    shim = Path(config["pyav_compat"]["directory"]) / "sitecustomize.py"
    assert shim.read_text() == recorder.pyav_compat_sitecustomize()
    assert config["pyav_compat"]["sha256"] == recorder.sha(shim)
    if mode == "missing-shim":
        shim.unlink()
    if mode == "changed-shim":
        shim.write_text("# corrupted\n")
    if mode == "success":
        result = recorder.media_write_preflight(host, proof, config)
        assert result["passed"] and result["size_bytes"] > 0
        assert result["sha256"] == recorder.sha(Path(result["local_path"]))
        assert result["log_sha256"] == recorder.sha(Path(result["log_path"]))
    else:
        with pytest.raises(recorder.ProofError) as caught:
            recorder.media_write_preflight(host, proof, config)
        assert caught.value.code == "MEDIA_WRITE_PREFLIGHT_FAILED"
        result = recorder.load(proof / "preflight/media-write.json")
        assert not result["passed"]
        assert ("fixture encoder failure" if mode == "write" else "PYAV_COMPAT_FAILED") in result["stderr"]
    assert not (proof / "queue.db").exists()


def test_path_order_and_both_aliases(tmp_path):
    config, proof = fixture_runtime(tmp_path, "success")
    config["pyav_compat"] = recorder.stage_pyav_compat(LocalHost(), proof, config)
    wrapper = tmp_path / "wrapper.sh"
    wrapper.write_text(recorder.offline_wrapper_body(config))
    check = ('import os,sitecustomize,torchvision.io as io,torchvision.io.video as video; '
             'assert io.write_video is video.write_video; '
             'assert sitecustomize.PYAV_COMPAT_APPLIED; print(os.environ["PYTHONPATH"])')
    result = subprocess.run(["bash", str(wrapper), "-c", check], capture_output=True, text=True)
    expected = [config["pyav_compat"]["directory"], *config["runtime"]["pythonpath"]]
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().split(":") == expected
    # Startup itself fails if a caller reverses the actual environment ordering.
    result = subprocess.run([sys.executable, "-c", "raise AssertionError('must not execute')"],
                            env={**os.environ, "PYTHONPATH": ":".join(reversed(expected))}, capture_output=True, text=True)
    assert result.returncode == 78 and "must lead PYTHONPATH" in result.stderr
    config["pyav_compat"]["directory"] += "-wrong"
    with pytest.raises(recorder.ProofError, match="path ordering"):
        recorder.offline_wrapper_body(config)


def test_stage_failure_is_typed_and_recorded(tmp_path):
    config, proof = fixture_runtime(tmp_path, "success")
    class BrokenHost(LocalHost):
        def push_file(self, source, target):
            raise OSError("fixture transport failure")
    with pytest.raises(recorder.ProofError) as caught:
        recorder.stage_pyav_compat(BrokenHost(), proof, config)
    assert caught.value.code == "PYAV_COMPAT_FAILED"
    assert recorder.load(proof / "preflight/pyav-compat.json")["passed"] is False


def test_raw_host_proof_hash():
    assert recorder.sha(recorder.ROOT / "datasets/runs/maestro-parity/WD-pp86/pyav-compat-success.txt") == (
        "a356597b5a4954a3b9c0fa291604f6d6b523040f36e4ff92f651b5da3f08fafe")
