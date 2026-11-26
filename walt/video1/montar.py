"""Montagem final do vídeo do Walt em 4K, por pedaços (pouca memória).

Entradas (pasta de trabalho): linha.json, narracao.wav, palco.mp4 (telas 3840x2160, 30 fps) e walt.mp4 (LongCat, já com
a cor da boca corrigida). Cada aparição do Walt é o trecho [off, off+dur] do walt.mp4 colocado em [ini, fim]; entre
elas entra o palco. Todos os pedaços saem com o mesmo codificador e são emendados sem recodificar.
Uso: python montar.py pasta saida.mp4
"""
import json, subprocess, sys
from pathlib import Path

d = Path(sys.argv[1]); out = sys.argv[2]
L = json.load(open(d / "linha.json"))
FPS = 30
q = lambda t: round(t * FPS) / FPS
tmp = d / "pedacos"; tmp.mkdir(exist_ok=True)
ENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-profile:v", "high", "-video_track_timescale", "15360"]
PRE = "scale=3840:2160:force_original_aspect_ratio=increase:flags=lanczos,crop=3840:2160,unsharp=5:5:0.6:5:5:0.0,setsar=1"
pecas, t = [], 0.0
total = q(L["duracao"])
for i, w in enumerate(L["walt"]):
    ini = q(max(0, w["ini"] - 0.10)); fim = q(w["fim"] + 0.15)
    if ini > t:
        pecas.append(("palco", t, ini - t, None))
    pecas.append(("walt", ini, fim - ini, q(max(0, w["off"] - 0.10))))
    t = fim
if t < total:
    pecas.append(("palco", t, total - t, None))
lista = []
for k, (tipo, ini, dur, off) in enumerate(pecas):
    f = tmp / f"{k:03d}.mp4"; lista.append(f)
    if tipo == "palco":
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{ini:.4f}", "-i", str(d / "palco.mp4"), "-t", f"{dur:.4f}",
               "-vf", f"fps={FPS},setsar=1"] + ENC + [str(f)]
    else:
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{off:.4f}", "-i", str(d / "walt.mp4"), "-t", f"{dur:.4f}",
               "-vf", f"{PRE},fps={FPS},tpad=stop_mode=clone:stop_duration=1"] + ENC + ["-frames:v", str(round(dur * FPS)), str(f)]
    subprocess.run(cmd, check=True)
    print(f"{k:02d} {tipo} {ini:7.2f} +{dur:5.2f}", flush=True)
(tmp / "lista.txt").write_text("".join(f"file '{p.name}'\n" for p in lista))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
                "-i", str(d / "narracao.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", out], check=True)
print("ok", out)
