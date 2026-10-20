"""Ajusta o Wav2Lip (2020) para rodar com as bibliotecas atuais. Idempotente.

Uso: python patch_wav2lip.py pasta_wav2lip
"""
import shutil
import sys
from pathlib import Path

TROCAS = [
    ("audio.py",
     "librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels,",
     "librosa.filters.mel(sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels,"),
    ("audio.py", "librosa.core.load(path, sr=sr)", "librosa.load(path, sr=sr)"),
    # Cola só a boca, com borda suave e cor igualada, em vez do quadrado do rosto inteiro.
    ("inference.py", "import json, subprocess, random, string\n",
     "import json, subprocess, random, string\nfrom boca import colar_boca\n"),
    ("inference.py", "\t\t\tf[y1:y2, x1:x2] = p\n", "\t\t\tf[y1:y2, x1:x2] = colar_boca(f[y1:y2, x1:x2], p)\n"),
]


def main():
    raiz = Path(sys.argv[1])
    # Sempre recopia o boca.py: a pasta do Wav2Lip vem do cache e pode ter uma versão antiga.
    shutil.copy(Path(__file__).with_name("boca.py"), raiz / "boca.py")
    for arquivo, antigo, novo in TROCAS:
        p = raiz / arquivo
        texto = p.read_text()
        if novo in texto:
            continue
        if antigo not in texto:
            sys.exit(f"patch: trecho não encontrado em {arquivo}: {antigo!r}")
        p.write_text(texto.replace(antigo, novo))
    print("patch: ok")


if __name__ == "__main__":
    main()
