"""Fala cada trecho do roteiro com a voz clonada (Chatterbox Multilingual, MIT).

Uso: python voz.py referencia.wav trechos.json pasta_saida idioma [exagero] [cfg]
trechos.json = lista de trechos; cada trecho é uma lista de frases curtas.
Gera pasta_saida/trecho_000.wav, trecho_001.wav, ... (usa GPU se houver, senão CPU)
"""
import json
import sys
from pathlib import Path

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

PAUSA_S = 0.25


def main():
    ref, trechos_json, saida, idioma = sys.argv[1:5]
    exagero = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
    cfg = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    trechos = json.loads(Path(trechos_json).read_text())

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"voz: usando {device}", flush=True)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    model.prepare_conditionals(ref, exaggeration=exagero)
    pausa = torch.zeros(1, int(model.sr * PAUSA_S))

    for i, frases in enumerate(trechos):
        partes = []
        for j, frase in enumerate(frases):
            wav = model.generate(frase, language_id=idioma, exaggeration=exagero, cfg_weight=cfg)
            partes += [wav.cpu(), pausa]
            print(f"voz: trecho {i + 1}/{len(trechos)}, frase {j + 1}/{len(frases)}", flush=True)
        ta.save(str(saida / f"trecho_{i:03d}.wav"), torch.cat(partes, dim=1), model.sr)


if __name__ == "__main__":
    main()
