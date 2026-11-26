"""Montagem final do vídeo do Walt em 4K.

Entradas (pasta de trabalho): linha.json, narracao.wav, palco.mp4 (telas 3840x2160) e walt.mp4 (LongCat, já com
a cor da boca corrigida). Cada aparição do Walt é o trecho [off, off+dur] do walt.mp4 colocado em [ini, fim].
Uso: python montar.py pasta saida.mp4
"""
import json, subprocess, sys
from pathlib import Path

d = Path(sys.argv[1]); out = sys.argv[2]
L = json.load(open(d / "linha.json"))
W = L["walt"]
# Walt sobe para 4K: lanczos + nitidez leve, preenchendo 16:9
pre = "scale=3840:2160:force_original_aspect_ratio=increase:flags=lanczos,crop=3840:2160,unsharp=5:5:0.6:5:5:0.0,setsar=1,fps=30"
fc = [f"[1:v]{pre},split={len(W)}" + "".join(f"[w{i}]" for i in range(len(W)))]
base = "[0:v]"
for i, w in enumerate(W):
    a0 = max(0, w["off"] - 0.10); a1 = w["off"] + (w["fim"] - w["ini"]) + 0.15
    t0 = max(0, w["ini"] - 0.10)
    fc.append(f"[w{i}]trim=start={a0:.3f}:end={a1:.3f},setpts=PTS-STARTPTS+{t0:.3f}/TB[s{i}]")
    nxt = f"[v{i}]" if i < len(W) - 1 else "[vout]"
    fc.append(f"{base}[s{i}]overlay=eof_action=pass:enable='between(t,{t0:.3f},{t0 + a1 - a0:.3f})'{nxt}")
    base = f"[v{i}]"
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats", "-i", str(d / "palco.mp4"), "-i", str(d / "walt.mp4"), "-i", str(d / "narracao.wav"),
       "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "2:a",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{L['duracao']:.3f}", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print("ok", out)
