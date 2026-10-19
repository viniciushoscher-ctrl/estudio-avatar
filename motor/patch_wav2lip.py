"""Ajusta o Wav2Lip (2020) para rodar com as bibliotecas atuais. Idempotente.

Uso: python patch_wav2lip.py pasta_wav2lip
"""
import sys
from pathlib import Path

TROCAS = [
    ("audio.py",
     "librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels,",
     "librosa.filters.mel(sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels,"),
    ("audio.py", "librosa.core.load(path, sr=sr)", "librosa.load(path, sr=sr)"),
]


def main():
    raiz = Path(sys.argv[1])
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
