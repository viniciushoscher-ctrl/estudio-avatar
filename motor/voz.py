"""Fala cada trecho do roteiro com a voz clonada (Chatterbox Multilingual, MIT).

Uso: python voz.py referencia.wav trechos.json pasta_saida idioma [exagero] [cfg]
trechos.json = lista de trechos; cada trecho é uma lista de pedaços de fala.
Gera pasta_saida/trecho_000.wav, trecho_001.wav, ... (usa GPU se houver, senão CPU)
"""
import inspect
import json
import random
import sys
from pathlib import Path

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Pausa entre pedaços: depois de ponto é mais longa que depois de vírgula, e varia um pouco,
# porque pausas sempre iguais denunciam a voz sintética.
PAUSA_FRASE_S = (0.30, 0.45)
PAUSA_VIRGULA_S = (0.12, 0.20)
TEMPERATURA = 0.85  # um pouco acima do padrão (0.8): entonação menos monótona


def pausa(sr: int, texto: str) -> torch.Tensor:
    lo, hi = PAUSA_FRASE_S if texto.rstrip()[-1:] in ".!?…" else PAUSA_VIRGULA_S
    return torch.zeros(1, int(sr * random.uniform(lo, hi)))


def main():
    ref, trechos_json, saida, idioma = sys.argv[1:5]
    exagero = float(sys.argv[5]) if len(sys.argv) > 5 else 0.85
    cfg = float(sys.argv[6]) if len(sys.argv) > 6 else 0.3
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    trechos = json.loads(Path(trechos_json).read_text(encoding="utf-8"))
    random.seed(0)  # mesmas pausas a cada execução do mesmo roteiro

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"voz: usando {device}, exagero {exagero}, cfg {cfg}", flush=True)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    model.prepare_conditionals(ref, exaggeration=exagero)
    extra = {"temperature": TEMPERATURA} if "temperature" in inspect.signature(model.generate).parameters else {}

    for i, pecas in enumerate(trechos):
        partes = []
        for j, texto in enumerate(pecas):
            wav = model.generate(texto, language_id=idioma, exaggeration=exagero, cfg_weight=cfg, **extra)
            partes += [wav.cpu(), pausa(model.sr, texto)]
            print(f"voz: trecho {i + 1}/{len(trechos)}, pedaço {j + 1}/{len(pecas)}", flush=True)
        ta.save(str(saida / f"trecho_{i:03d}.wav"), torch.cat(partes, dim=1), model.sr)


if __name__ == "__main__":
    main()
