#!/usr/bin/env python3
"""Chain pair v3 — TRIMMED + BOOSTED wavs, fit to 2.3s cuts.
Line 1 (grandma, ~2.2s): 'Oh hush now, dear. Have a cookie.'
Line 2 (soul, ~2.2s): 'Lady, I am on fire!'
Whisper-gate before render; whisper-verify after; concat."""
import json, subprocess, re, os

RUN = "/home/straughter/wangp-dspy-fresh/runs/directpin/settings.json"
ST = "/home/straughter/speaker_test"
D = "/home/straughter/marathon/v2/dialogue"

CUT1 = ("integrated_multimodal_description:\n"
 "Same fiery torture chamber, continuing from the pinned frame. The same two people: "
 "the elderly grandmother with round glasses and cardigan, and the skinny tormented soul on the rack.\n"
 "(S1) The elderly grandmother, on-screen speaker: she speaks warm coaxing English, "
 "mouth in exact sync with the audio, gesturing with the cookie plate.\n"
 "(S2) The tormented soul shown in Picture 2 stays silent: his lips are pressed closed "
 "and motionless for the entire shot.\n"
 "Closed-mouth instruction: the man in Picture 2 keeps his mouth fully closed while "
 "the grandmother speaks.\n"
 "overall_soundscape: crackling fire, bubbling cauldron.\n"
 "non_diegetic_music: N/A")

CUT2 = ("integrated_multimodal_description:\n"
 "Same fiery torture chamber, continuing directly from the previous frame. The same two people: "
 "the elderly grandmother with round glasses and cardigan, and the skinny tormented soul on the rack.\n"
 "(S1) The tormented soul, on-screen speaker: he protests in exasperated English, "
 "mouth in exact sync with the audio.\n"
 "(S2) The elderly grandmother shown in Picture 2 stays silent: her lips are pressed "
 "closed and motionless for the entire shot.\n"
 "Closed-mouth instruction: the woman in Picture 2 keeps her mouth fully closed while "
 "the soul speaks.\n"
 "overall_soundscape: crackling fire, bubbling cauldron.\n"
 "non_diegetic_music: N/A")

def whisper_txt(wav):
    os.makedirs("/tmp/vfy", exist_ok=True)
    for f in os.listdir("/tmp/vfy"): os.remove(f"/tmp/vfy/{f}")
    subprocess.run(["/home/straughter/.local/bin/whisper",wav,"--model","small",
                    "--output_format","txt","--output_dir","/tmp/vfy"],capture_output=True)
    for f in os.listdir("/tmp/vfy"):
        if f.endswith(".txt"): return open(f"/tmp/vfy/{f}").read().strip().lower()
    return ""

def score(said, text):
    a=set(re.findall(r"[a-z']+",said)); b=set(re.findall(r"[a-z']+",text.lower()))
    return len(a&b)/len(b) if b else 0

def render(tag, seed_png, ref_png, wav, prompt):
    d=json.load(open(RUN))
    d.update({"model_type":"minimax_h3_ref2va_pruned","image_prompt_type":"S",
              "image_start":seed_png,"video_prompt_type":"I","image_refs":[seed_png,ref_png],
              "audio_prompt_type":"A","audio_guide":wav,
              "video_source":None,"video_guide":None,"keep_frames_video_source":"",
              "video_length":56,"resolution":"480x832","seed":904,"prompt":prompt})
    json.dump(d,open(RUN,"w"),indent=2)
    print(f"[{tag}] rendering...",flush=True)
    with open(f"{ST}/{tag}.log","w") as lf:
        rc=subprocess.run(["/home/straughter/Wan2GP/venv/bin/python","wgp.py","--process",RUN,
                           "--profile","2","--attention","sdpa"],
                          cwd="/home/straughter/Wan2GP",stdout=lf,stderr=subprocess.STDOUT).returncode
    if rc: return None
    new="/home/straughter/Wan2GP/outputs/"+subprocess.run(
        "ls -t /home/straughter/Wan2GP/outputs/ | head -1",shell=True,capture_output=True,text=True).stdout.strip()
    out=f"{ST}/{tag}.mp4"; subprocess.run(["cp",new,out],check=True); return out

# 1. VibeVoice: short lines
def gen(name, ref, text):
    wav=f"{D}/{name}"
    conv=[{"role":"0","content":[{"type":"audio","url":ref},{"type":"text","text":text}]}]
    code=("from transformers import AutoProcessor, AutoModelForTextToWaveform, set_seed\n"
     "p=AutoProcessor.from_pretrained('/home/straughter/models/VibeVoice-7B-hf')\n"
     "m=AutoModelForTextToWaveform.from_pretrained('/home/straughter/models/VibeVoice-7B-hf',device_map='auto')\n"
     "set_seed(42)\n"
     f"conv={json.dumps(conv)}\n"
     "inputs=p.apply_chat_template(conv,return_dict=True,tokenize=True,add_generation_prompt=True).to(m.device,m.dtype)\n"
     "audio=m.generate(**inputs)\n"
     f"p.save_audio(audio,'{wav}_raw')\nprint('OK')")
    open(f"/tmp/g_{name}.py","w").write(code)
    subprocess.run(["/home/straughter/vb7-venv/bin/python","-u",f"/tmp/g_{name}.py"],
                   capture_output=True,text=True,cwd="/home/straughter")
    # trim silence + boost + ensure 2.0-2.5s
    subprocess.run(["ffmpeg","-y","-v","error","-i",f"{wav}_raw",
                    "-af","silenceremove=start_periods=1:start_threshold=-40dB,highpass=f=100,volume=9dB,atrim=0:2.4",
                    "-c:a","pcm_s16le",wav],check=True)
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",wav],
            capture_output=True,text=True).stdout.strip())
    if d<2.0:
        subprocess.run(["ffmpeg","-y","-v","error","-i",wav,"-af","apad=pad_dur=0.5","-c:a","pcm_s16le","/tmp/p.wav"],check=True)
        subprocess.run(["cp","/tmp/p.wav",wav],check=True)
    return wav

W1=gen("dgshort_g.wav","/home/straughter/grandma_2s.wav","Oh hush now, dear. Have a cookie.")
W2=gen("dgshort_s.wav","/home/straughter/good_prisoner.wav","Lady, I am on fire!")
s1=score(whisper_txt(W1),"Oh hush now, dear. Have a cookie.")
s2=score(whisper_txt(W2),"Lady, I am on fire!")
print(f"gate: cut1 {s1:.2f}, cut2 {s2:.2f}",flush=True)
if s1<0.6 or s2<0.6: print("GATE FAIL",flush=True); exit(1)

c1=render("v3_c1",f"{ST}/grandma_frame2.png",f"{ST}/soul_frame.png",W1,CUT1)
if c1:
    said=whisper_txt(c1); post=score(said,"Oh hush now, dear. Have a cookie.")
    print(f"post-render c1: {post:.2f} — {said[:60]}",flush=True)
    subprocess.run(["ffmpeg","-y","-v","error","-sseof","-0.05","-i",c1,
                    "-update","1","-frames:v","1",f"{ST}/v3_c2seed.png"],check=True)
    c2=render("v3_c2",f"{ST}/v3_c2seed.png",f"{ST}/grandma_frame.png",W2,CUT2)
    if c2:
        said2=whisper_txt(c2); post2=score(said2,"Lady, I am on fire!")
        print(f"post-render c2: {post2:.2f} — {said2[:60]}",flush=True)
        subprocess.run(["ffmpeg","-y","-v","error","-i",c1,"-i",c2,
                        "-filter_complex","[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                        "-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-c:a","aac",
                        f"{ST}/v3_pair.mp4"],check=True)
        print("FILM: v3_pair.mp4",flush=True)
