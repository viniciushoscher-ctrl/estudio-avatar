"""Voz fixa do Hiroshi com o Qwen3-TTS (Apache-2.0), na CPU.

A voz nasceu no Qwen3-TTS VoiceDesign (descrição em texto); o trecho aprovado está em
vozes/hiroshi.wav (+ vozes/hiroshi.txt). O modelo Base clona essa referência, então todas as falas
de todos os vídeos saem com a mesma voz.

Uso:
  python motor/voz_hiroshi.py roteiro.txt pasta/                 # um wav por linha (clipes)
  python motor/voz_hiroshi.py roteiro.txt parte.wav --parte 0 --partes 8   # vídeo longo: um wav
      só com as linhas desta parte, emendadas com pausas naturais
"""
import argparse
import json
import random
import re
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

AQUI = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("roteiro")
ap.add_argument("saida")
ap.add_argument("--parte", type=int, default=None)
ap.add_argument("--partes", type=int, default=1)
a = ap.parse_args()

torch.manual_seed(1); random.seed(1); np.random.seed(1)
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
VOZ = __import__("os").environ.get("VOZ", "hiroshi").strip() or "hiroshi"  # vozes/<VOZ>.wav + .txt
prompt = m.create_voice_clone_prompt(ref_audio=str(AQUI / "vozes" / f"{VOZ}.wav"),
                                     ref_text=(AQUI / "vozes" / f"{VOZ}.txt").read_text(encoding="utf-8").strip())
# "[broll: ...]" / "[split: ...]" / "[avatar]" no começo da linha são instruções de edição (motor/montar.py)
falas = [re.sub(r"^\s*\[[^\]]*\]\s*", "", l).strip()
         for l in Path(a.roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]


def dizer(texto):
    wavs, sr = m.generate_voice_clone(text=texto, language="English", voice_clone_prompt=prompt)
    return wavs[0].astype(np.float32), sr


if a.parte is None:
    pasta = Path(a.saida); pasta.mkdir(parents=True, exist_ok=True)
    for i, fala in enumerate(falas, 1):
        w, sr = dizer(fala)
        p = np.zeros(int(sr * 0.25), dtype=np.float32)
        sf.write(pasta / f"fala-{i:02d}.wav", np.concatenate([p, w, p]), sr)
        print(f"fala-{i:02d}.wav: {(len(w) / sr) + 0.5:.1f}s", flush=True)
else:
    minhas = np.array_split(np.array(falas, dtype=object), a.partes)[a.parte]
    partes, sr, tempos = [], 24000, []
    for fala in minhas:
        w, sr = dizer(str(fala))
        partes += [w, np.zeros(int(sr * 0.45), dtype=np.float32)]
        tempos.append(len(w) + int(sr * 0.45))
        print(f"{len(w) / sr:.1f}s  {str(fala)[:40]}", flush=True)
    if partes:
        sf.write(a.saida, np.concatenate(partes), sr)
    # duração (em amostras de 24 kHz) de cada linha desta parte, para a montagem saber quando cada frase começa
    Path(a.saida).with_suffix(".json").write_text(json.dumps({"sr": sr, "amostras": tempos}))
