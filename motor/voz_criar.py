"""Cria a voz de um avatar novo com o Qwen3-TTS VoiceDesign (Apache-2.0), na CPU, a partir de descrições em texto.

Lê avatares/novos/<nome>.json e grava uma amostra por descrição em vozes-<nome>/<letra>.wav.
Depois que o usuário escolhe, a escolhida vira vozes/<nome>.wav (+ vozes/<nome>.txt com a frase falada),
e o motor/voz_hiroshi.py (VOZ=<nome>) clona essa referência em todos os vídeos.

Uso: python motor/voz_criar.py avatares/novos/<nome>.json saida/
"""
import json
import sys
import time
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
saida = Path(sys.argv[2])
saida.mkdir(parents=True, exist_ok=True)
torch.set_num_threads(4)
torch.manual_seed(1)
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", dtype=torch.float32, device_map="cpu")
frase = cfg["frase"].strip()
(saida / "frase.txt").write_text(frase + "\n", encoding="utf-8")
for letra, instr in zip("ABCDEFGH", cfg["vozes"]):
    t = time.time()
    wavs, sr = m.generate_voice_design(text=frase, language=cfg.get("idioma", "English"), instruct=instr)
    sf.write(saida / f"{letra}.wav", wavs[0], sr)
    (saida / f"{letra}.txt").write_text(instr + "\n", encoding="utf-8")
    print(f"[voz] {letra}: {len(wavs[0]) / sr:.1f} s em {time.time() - t:.0f} s", flush=True)
