"""Junta os clipes do Walt (LongCat) num só walt.mp4 alinhado com walt-falas.wav.

O LongCat perde o rosto em clipes longos, então as falas são geradas em grupos curtos (cortes.json).
Cada pedaço é cortado no tempo exato do seu trecho de áudio e tudo é reencodado a 25 fps, para que
o tempo t de walt.mp4 corresponda ao tempo t de walt-falas.wav (é o que montar.py espera).
Uso: python juntar_walt.py cortes.json saida.mp4 inicio.mp4 g1.mp4 g2.mp4 ...
"""
import json, subprocess, sys, tempfile
from pathlib import Path

C = json.load(open(sys.argv[1])); out = sys.argv[2]; clipes = sys.argv[3:]
trechos = ([C["inicio_reaproveitado"]] if "inicio_reaproveitado" in C else []) + C["grupos"]
assert len(trechos) == len(clipes), (len(trechos), len(clipes))
tmp = Path(tempfile.mkdtemp()); lista = []
for k, ((s, e), c) in enumerate(zip(trechos, clipes)):
    f = tmp / f"{k:02d}.mp4"
    # o primeiro trecho vem de um clipe que começa em 0; os grupos começam no próprio s
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", c, "-t", f"{e - s:.4f}", "-an",
                    "-vf", "fps=25,tpad=stop_mode=clone:stop_duration=1", "-frames:v", str(round((e - s) * 25)),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", str(f)], check=True)
    lista.append(f)
(tmp / "l.txt").write_text("".join(f"file '{p}'\n" for p in lista))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"),
                "-c", "copy", out], check=True)
print("ok", out)
