"""Correção de cor só na boca do Hiroshi: dentes brancos e lábios naturais, sem redesenhar nada.

O LongCat às vezes puxa os dentes para o verde e os lábios para o magenta. Aqui cada quadro tem a
boca localizada (68 pontos do face-alignment, MIT), e só a cor (canais a/b do Lab) é ajustada:
- dentes (pixels claros dentro da boca): cor vai para um branco levemente quente; brilho e forma ficam;
- lábios: o excesso de magenta vira o tom de lábio tirado da pele em volta da boca.
Roda na CPU (grátis). Uso: python motor/boca_cor.py entrada.mp4 saida.mp4  (ou pastas de .mp4)
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

DETECTAR_CADA = 3      # landmarks a cada N quadros (interpolados entre eles)
LARG_DET = 640         # detecção numa cópia reduzida


def _modelo():
    import face_alignment
    import torch
    torch.set_num_threads(max(1, (__import__("os").cpu_count() or 2)))
    return face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, device="cpu", flip_input=False)


def pontos(fa, q):
    h, w = q.shape[:2]
    s = LARG_DET / max(w, h)
    p = fa.get_landmarks_from_image(cv2.cvtColor(cv2.resize(q, None, fx=s, fy=s), cv2.COLOR_BGR2RGB))
    if not p:
        return None
    p = max(p, key=lambda x: np.ptp(x[:, 0]))  # maior rosto
    return p / s


def corrigir(q, p):
    h, w = q.shape[:2]
    externo = p[48:60].astype(np.int32)
    interno = p[60:68].astype(np.int32)
    larg_boca = np.ptp(externo[:, 0])
    if larg_boca < 8:
        return q
    pena = max(3, int(larg_boca * 0.06)) | 1
    m_ext = np.zeros((h, w), np.float32)
    cv2.fillPoly(m_ext, [externo], 1.0)
    m_int = np.zeros((h, w), np.float32)
    cv2.fillPoly(m_int, [interno], 1.0)
    # boca aberta: a região interna cresce um pouco para pegar a borda dos dentes
    m_int = cv2.dilate(m_int, np.ones((pena, pena), np.uint8))
    m_lab = np.clip(m_ext - m_int, 0, 1)
    m_int = cv2.GaussianBlur(m_int, (pena * 2 + 1, pena * 2 + 1), 0)
    m_lab = cv2.GaussianBlur(m_lab, (pena * 2 + 1, pena * 2 + 1), 0)

    lab = cv2.cvtColor(q, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]

    # dentes: quanto mais claro, mais a cor vai para o branco quente (a≈129, b≈136 no Lab do OpenCV)
    claro = np.clip((L - 95) / 70, 0, 1)
    t = m_int * claro
    A[:] = A * (1 - t) + 129 * t
    B[:] = B * (1 - t) + 136 * t
    # interior escuro da boca: tira o verde/magenta sem clarear
    esc = m_int * (1 - claro) * 0.7
    A[:] = A * (1 - esc) + 140 * esc
    B[:] = B * (1 - esc) + 134 * esc

    # lábios: tom de referência = pele logo abaixo do lábio inferior, um pouco mais vermelho
    x0, x1 = int(externo[:, 0].min()), int(externo[:, 0].max())
    y1 = int(externo[:, 1].max())
    alt = max(4, int(larg_boca * 0.25))
    pele = lab[min(h - 1, y1 + alt // 2):min(h, y1 + alt), max(0, x0):min(w, x1)]
    if pele.size:
        pa, pb = np.median(pele[..., 1]), np.median(pele[..., 2])
        alvo_a, alvo_b = pa + 13, pb + 2
        exc = np.clip((A - alvo_a) / 12, 0, 1)  # só onde passou do natural (magenta)
        tl = m_lab * np.maximum(exc, 0.25)
        A[:] = A * (1 - tl) + alvo_a * tl
        B[:] = B * (1 - tl) + alvo_b * tl
    lab = np.clip(lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def video(fa, entrada, saida):
    cap = cv2.VideoCapture(str(entrada))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    quadros = []
    while True:
        ok, q = cap.read()
        if not ok:
            break
        quadros.append(q)
    n = len(quadros)
    if not n:
        return
    chaves = {}
    for i in list(range(0, n, DETECTAR_CADA)) + [n - 1]:
        chaves[i] = pontos(fa, quadros[i])
    idx = sorted(k for k, v in chaves.items() if v is not None)
    h, w = quadros[0].shape[:2]
    tmp = Path(str(saida) + ".avi")
    out = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    for i, q in enumerate(quadros):
        if idx:
            a = max([k for k in idx if k <= i], default=idx[0])
            b = min([k for k in idx if k >= i], default=idx[-1])
            p = chaves[a] if a == b else chaves[a] + (chaves[b] - chaves[a]) * ((i - a) / (b - a))
            q = corrigir(q, p)
        out.write(q)
    out.release()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp), "-i", str(entrada), "-map", "0:v",
                    "-map", "1:a?", "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    str(saida)], check=True)
    tmp.unlink()
    print(f"[boca_cor] {saida} ({n} quadros)", flush=True)


def main(entrada, saida):
    fa = _modelo()
    e = Path(entrada)
    if e.is_dir():
        Path(saida).mkdir(parents=True, exist_ok=True)
        for f in sorted(e.glob("*.mp4")):
            destino = Path(saida, f.name)
            video(fa, f, destino.with_suffix(".tmp.mp4"))
            destino.with_suffix(".tmp.mp4").replace(destino)
    else:
        video(fa, e, Path(saida))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
