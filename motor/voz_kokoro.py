"""Fala em inglês com o Kokoro-82M (Apache-2.0), rápido na CPU.

Uso: python motor/voz_kokoro.py roteiro.txt saida/ [voz] [velocidade]
Cada linha não vazia do roteiro vira um arquivo saida/fala-01.wav, fala-02.wav...
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

roteiro, pasta = Path(sys.argv[1]), Path(sys.argv[2])
voz = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
velocidade = float(sys.argv[4]) if len(sys.argv) > 4 else 0.9
pasta.mkdir(parents=True, exist_ok=True)
pipe = KPipeline(lang_code=voz[0])
pausa = np.zeros(int(24000 * 0.25), dtype=np.float32)  # respiro no começo e no fim

falas = [l.strip() for l in roteiro.read_text(encoding="utf-8").splitlines() if l.strip()]
for i, fala in enumerate(falas, 1):
    audio = np.concatenate([a for _, _, a in pipe(fala, voice=voz, speed=velocidade)])
    audio = np.concatenate([pausa, audio, pausa])
    destino = pasta / f"fala-{i:02d}.wav"
    sf.write(destino, audio, 24000)
    print(f"{destino.name}: {len(audio) / 24000:.1f}s")
