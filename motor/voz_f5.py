"""Fala cada trecho do roteiro com a voz clonada em português do BRASIL (F5-TTS pt-br).

O Chatterbox tem um "português" só, que puxa para o sotaque de Portugal. Este modelo
(firstpixel/F5-TTS-pt-br, ajustado com ~3.500 falantes brasileiros do Common Voice) clona a voz a
partir da gravação e mantém o sotaque brasileiro. Licença CC-BY-NC: só uso pessoal, como o Wav2Lip.

Uso (igual ao voz.py): python voz_f5.py referencia.wav trechos.json pasta_saida idioma [exagero] [cfg]
Roda num ambiente Python separado (o workflow cria), para não conflitar com o Chatterbox.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from f5_tts.api import F5TTS
from huggingface_hub import hf_hub_download
from num2words import num2words

REPO, ARQUIVO = "firstpixel/F5-TTS-pt-br", "pt-br/model_last.safetensors"
PAUSA_S = 0.30


def preparar_texto(texto: str) -> str:
    """O modelo foi treinado com texto minúsculo e números por extenso (recomendação do autor)."""
    texto = re.sub(r"\s*%", " por cento", texto)
    texto = re.sub(r"\d+(?:[.,]\d+)?",
                   lambda m: num2words(float(m.group().replace(",", ".")) if re.search(r"[.,]", m.group())
                                       else int(m.group()), lang="pt_BR"), texto)
    return re.sub(r"\s+", " ", texto).strip().lower()


def main():
    ref, trechos_json, saida = sys.argv[1:4]
    # exagero (0 a 1) -> força de condicionamento; mais = fala mais marcada e expressiva.
    exagero = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    trechos = json.loads(Path(trechos_json).read_text(encoding="utf-8"))

    print("voz (F5 pt-br): carregando o modelo", flush=True)
    tts = F5TTS(model="F5TTS_Base", ckpt_file=hf_hub_download(REPO, ARQUIVO), device="cpu")
    ref_texto = ""  # vazio: o próprio F5 transcreve a gravação de referência
    for i, pecas in enumerate(trechos):
        partes, sr = [], 24000
        for j, texto in enumerate(pecas):
            wav, sr, _ = tts.infer(ref_file=ref, ref_text=ref_texto, gen_text=preparar_texto(texto),
                                   cfg_strength=1.5 + exagero, nfe_step=32, show_info=lambda *a: None)
            partes += [np.asarray(wav, np.float32), np.zeros(int(sr * PAUSA_S), np.float32)]
            print(f"voz (F5 pt-br): trecho {i + 1}/{len(trechos)}, pedaço {j + 1}/{len(pecas)}", flush=True)
        sf.write(str(saida / f"trecho_{i:03d}.wav"), np.concatenate(partes), sr)


if __name__ == "__main__":
    main()
