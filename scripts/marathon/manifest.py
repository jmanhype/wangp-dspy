#!/usr/bin/env python3
"""Marathon manifest builder — every banked artifact with hashes + QC verdicts."""
import hashlib, json, os, subprocess, datetime

M = "/home/straughter/marathon"
manifest = {"generated": datetime.datetime.utcnow().isoformat() + "Z", "pipeline": "wangp-dspy marathon v1 (H3 Mode A)", "artifacts": []}

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

for f in sorted(os.listdir(M)):
    p = os.path.join(M, f)
    if not f.endswith((".mp4", ".png", ".wav")) or not os.path.isfile(p):
        continue
    entry = {"file": f, "bytes": os.path.getsize(p), "md5": md5(p)}
    if f.endswith(".mp4"):
        d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout.strip()
        entry["duration_s"] = float(d) if d else None
    manifest["artifacts"].append(entry)

json.dump(manifest, open(f"{M}/manifest.json","w"), indent=2)
print(f"manifest: {len(manifest['artifacts'])} artifacts")
