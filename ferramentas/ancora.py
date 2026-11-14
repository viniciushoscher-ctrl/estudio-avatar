# ancora.py — âncora de IA (avatar ancora65, aprovado 2026-11-14) falando trechos da narração do vídeo.
# Padrão (Vinicius 14/11): ~5 s no início, ~2 s no meio, ~5 s perto do fim (+ 1 batida extra), 15-20 s no total.
# Passos (rodar na pasta de trabalho do vídeo; precisa do repo viniciushoscher-ctrl/estudio-avatar clonado em $EA,
#  branch claude/project-thread-f10yr5, onde roda o LongCat na GPU grátis da Modal):
#   python3 ancora.py prep  words-NN.json NN-slug-narracao.mp3 <id>     -> ancora-<id>/segs.json + wavs, push p/ estudio-avatar
#   python3 ancora.py wait  <id>                                        -> espera o workflow e baixa os clipes em ancora-<id>/
#   python3 ancora.py insert out/NN.mp4 <id> out/NN-ancora.mp4          -> põe o âncora em tela cheia nesses trechos (áudio intacto)
# Depois: thumbframes_add.sh como sempre (os trechos evitam 25/50/75% do vídeo).
import json, os, re, subprocess, sys, time
EA = os.environ.get("EA", "/home/user/estudio-avatar"); REPO = "viniciushoscher-ctrl/estudio-avatar"
BR = "claude/project-thread-f10yr5"; AV = os.environ.get("ANCORA", "ancora65")
def sh(*a, **k): return subprocess.run(list(a), check=True, capture_output=True, text=True, **k).stdout
def dur(f): return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f))
def sentences(w):
    out, cur = [], []
    for x in w:
        cur.append(x)
        if re.search(r"[.?!][\"”']?$", x["w"].strip()): out.append(cur); cur = []
    if cur: out.append(cur)
    return [dict(s=c[0]["s"], e=c[-1]["e"], n=len(c), t=" ".join(x["w"].strip() for x in c)) for c in out]
def pick(S, D, target, lo, hi, used, avoid):
    """span of whole consecutive sentences starting near `target`, length in [lo,hi] (else best cut by words)"""
    best = None
    for i, s in enumerate(S):
        for j in range(i, min(i + 4, len(S))):
            a, b = S[i]["s"], S[j]["e"]; L = b - a
            if L > hi: break
            if L < lo: continue
            if any(not (b + 1 < u0 or a - 1 > u1) for u0, u1 in used): continue
            if any(a - 2 < f * D < b + 2 for f in avoid): continue
            sc = abs(a - target) + 0.5 * abs(L - (lo + hi) / 2)
            if best is None or sc < best[0]: best = (sc, a, b, " ".join(x["t"] for x in S[i:j + 1]))
    return best
def prep(words, audio, vid):
    w = json.load(open(words)); D = dur(audio); S = sentences(w); used = []; segs = []
    avoid = [0.25, 0.5, 0.75]  # thumb frames
    # 1) open: from 0, whole sentences up to ~5 s (accept 3.5-7 s; else cut at the word nearest 5 s)
    e = 0
    for s in S:
        if s["e"] <= 7.0: e = s["e"]
        else: break
    if e < 3.5: e = min((x["e"] for x in w), key=lambda t: abs(t - 5.0))
    segs.append(dict(a=0.0, b=e)); used.append((0.0, e))
    for target, lo, hi in [(0.45 * D, 1.6, 3.4), (D - 40, 3.5, 6.5), (0.62 * D, 2.5, 4.5)]:
        p = pick(S, D, target, lo, hi, used, avoid)
        if p: segs.append(dict(a=p[1], b=p[2])); used.append((p[1], p[2]))
    segs.sort(key=lambda s: s["a"])
    d = f"ancora-{vid}"; os.makedirs(d, exist_ok=True); tot = 0
    for k, s in enumerate(segs):
        a, b = max(0, s["a"] - 0.12), min(D, s["b"] + 0.25); s.update(a=round(a, 2), b=round(b, 2), wav=f"{k:02d}.wav"); tot += b - a
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", audio, "-ac", "1", "-ar", "16000", f"{d}/{s['wav']}")
    json.dump(dict(id=vid, avatar=AV, total=round(tot, 1), segs=segs), open(f"{d}/segs.json", "w"), indent=1)
    print("segs", [(s["a"], s["b"]) for s in segs], "total", round(tot, 1), "s")
    # push to estudio-avatar -> workflow "Âncora trechos"
    t = f"{EA}/trechos/{vid}"; os.makedirs(t, exist_ok=True)
    for s in segs: sh("cp", f"{d}/{s['wav']}", t)
    open(f"{t}/avatar.txt", "w").write(AV + "\n"); open(f"{t}/pronto.txt", "w").write(time.strftime("%FT%TZ", time.gmtime()) + "\n")
    sh("git", "-C", EA, "pull", "-q", "--rebase", "origin", BR)
    sh("git", "-C", EA, "add", f"trechos/{vid}")
    sh("git", "-C", EA, "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m", f"Âncora: trechos do vídeo {vid}")
    for i in range(4):
        try: sh("git", "-C", EA, "-c", "push.negotiate=true", "push", "-q", "origin", BR); break
        except subprocess.CalledProcessError: time.sleep(5 * 2 ** i)
    print("pushed", t)
def wait(vid):
    d = f"ancora-{vid}"; t0 = time.time(); run = None
    while time.time() - t0 < 7200:
        rs = json.loads(sh("gh", "api", f"repos/{REPO}/actions/runs?branch={BR}&per_page=15"))["workflow_runs"]
        rs = [r for r in rs if r["name"].startswith("Âncora trechos")]
        for r in rs:
            arts = json.loads(sh("gh", "api", r["artifacts_url"]))["artifacts"] if r["status"] == "completed" else []
            if any(a["name"] == f"ancora-{vid}" for a in arts): run = (r, [a for a in arts if a["name"] == f"ancora-{vid}"][0]); break
        if run: break
        time.sleep(60)
    if not run: sys.exit("timeout: nenhum artefato ancora-" + vid)
    sh("gh", "api", run[1]["archive_download_url"], "-H", "Accept: application/vnd.github+json", "--output", f"{d}/clipes.zip") if False else \
        subprocess.run(["gh", "api", run[1]["archive_download_url"]], check=True, stdout=open(f"{d}/clipes.zip", "wb"))
    sh("unzip", "-o", "-q", f"{d}/clipes.zip", "-d", d); print("ok", sorted(os.listdir(d)))
def insert(src, vid, out):
    d = f"ancora-{vid}"; J = json.load(open(f"{d}/segs.json")); segs = [s for s in J["segs"] if os.path.exists(f"{d}/{s['wav'][:-4]}.mp4")]
    if not segs: sys.exit("sem clipes do âncora")
    ins = ["-i", src]; fc = []; last = "0:v"
    for k, s in enumerate(segs):
        ins += ["-i", f"{d}/{s['wav'][:-4]}.mp4"]; L = s["b"] - s["a"]
        fc.append(f"[{k+1}:v]trim=0:{L:.3f},setpts=PTS-STARTPTS+{s['a']:.3f}/TB,scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,unsharp=5:5:0.5[a{k}]")
        fc.append(f"[{last}][a{k}]overlay=0:0:eof_action=pass:enable='between(t,{s['a']:.3f},{s['b']:.3f})'[v{k}]"); last = f"v{k}"
    sh("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium",
       "-crf", "23", "-maxrate", "1800k", "-bufsize", "3600k", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out)
    print("done", out, "anchor seconds", round(sum(s["b"] - s["a"] for s in segs), 1))
if __name__ == "__main__":
    c = sys.argv[1]
    if c == "prep": prep(*sys.argv[2:5])
    elif c == "wait": wait(sys.argv[2])
    elif c == "insert": insert(*sys.argv[2:5])
