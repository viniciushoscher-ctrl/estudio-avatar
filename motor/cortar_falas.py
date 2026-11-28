"""Corta a fala completa nos trechos em que o Hiroshi aparece (linhas sem marca e [split:]).

Cada trecho vira um .wav com o nome da 1ª linha (falas/linha-NNN.wav). O LongCat gera o Hiroshi
falando exatamente esse áudio (motor/montar.py depois encaixa cada clipe no seu lugar).
Uso: python motor/cortar_falas.py --roteiro r.txt --tempos tempos.json --audio fala.wav --saida falas
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar import FPS, trechos  # noqa: E402

ap = argparse.ArgumentParser()
for a in ["roteiro", "tempos", "audio", "saida"]:
    ap.add_argument(f"--{a}", required=True)
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
total = 0.0
for t in trechos(a.roteiro, json.load(open(a.tempos))):
    if t["tipo"] in ("avatar", "split") and t["q1"] > t["q0"]:
        ini, dur = t["q0"] / FPS, (t["q1"] - t["q0"]) / FPS
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", a.audio,
                        "-ac", "1", "-ar", "24000", os.path.join(a.saida, f"linha-{t['linha']:03d}.wav")], check=True)
        total += dur
        print(f"linha {t['linha']:3d} {t['tipo']:6s} {dur:5.1f}s", flush=True)
print(f"Hiroshi na tela: {total:.0f}s (~US$ {total / 37 * 1.5:.2f} de GPU na Modal, 480p)", flush=True)
