"""Mede e corrige o atraso entre a boca e a voz de qualquer vídeo gerado.

Compara o quanto a região da boca muda a cada quadro com o volume do áudio no mesmo instante
e procura o deslocamento (em quadros) em que os dois mais combinam. Devolve segundos:
positivo = atrasar a imagem (a boca se mexia antes do som); negativo = atrasar o som.
"""
import subprocess

import cv2
import numpy as np

FPS = 25
MAX_QUADROS = 6
CORRELACAO_MINIMA = 0.12  # abaixo disso a medida não é confiável e não mexemos


def _z(v):
    return (v - v.mean()) / (v.std() + 1e-9)


def medir_atraso(video: str) -> tuple[float, float]:
    audio = np.frombuffer(subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True).stdout, np.int16).astype(float)
    n = len(audio) // (16000 // FPS)
    env = np.sqrt((audio[:n * 640].reshape(n, 640) ** 2).mean(1))
    cap = cv2.VideoCapture(video)
    mov = []
    while True:
        ok, q = cap.read()
        if not ok:
            break
        h, w = q.shape[:2]
        reg = cv2.cvtColor(q[int(h * .38):int(h * .62), int(w * .25):int(w * .75)], cv2.COLOR_BGR2GRAY)
        mov.append(float(reg.astype(np.float32).std()))
    mov = np.abs(np.diff(np.array(mov), prepend=mov[0]))
    m = min(len(mov), len(env))
    if m < 50:
        return 0.0, 0.0
    mov, env = mov[:m], env[:m]
    melhor, corr = 0, -1.0
    for lag in range(-MAX_QUADROS, MAX_QUADROS + 1):
        c = (np.corrcoef(_z(mov[lag:]), _z(env[:m - lag]))[0, 1] if lag >= 0
             else np.corrcoef(_z(mov[:m + lag]), _z(env[-lag:]))[0, 1])
        if c > corr:
            melhor, corr = lag, c
    if corr < CORRELACAO_MINIMA:
        return 0.0, corr
    return -melhor / FPS, corr
