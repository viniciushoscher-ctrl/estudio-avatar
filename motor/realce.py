"""Restaura o rosto (GFPGAN) quadro a quadro depois do Wav2Lip, para dar nitidez à boca.

Uso: python realce.py entrada.mp4 saida_sem_audio.mp4 pesos/GFPGANv1.4.pth [forca 0-1]
Só o rosto é refeito e colado de volta; o resto do quadro fica como está.
"""
import sys
import time

import cv2
import numpy as np
import torchvision.transforms.functional as _F

# O basicsr (usado pelo GFPGAN) ainda procura um módulo que o torchvision novo removeu.
sys.modules.setdefault("torchvision.transforms.functional_tensor", _F)

from gfpgan import GFPGANer  # noqa: E402


def _mascara_boca(rest, formato) -> np.ndarray:
    """Máscara suave (0 a 1, com 3 canais) em volta da boca e do queixo; zeros se não achar o rosto."""
    h, w = formato[:2]
    m = np.zeros((h, w), np.float32)
    pts = getattr(rest.face_helper, "all_landmarks_5", None)
    if pts is not None and len(pts):
        p = np.asarray(pts[0], np.float32)  # olho E, olho D, nariz, canto E da boca, canto D da boca
        boca = (p[3] + p[4]) / 2
        larg = float(np.linalg.norm(p[4] - p[3]))
        centro = (int(boca[0]), int(boca[1] + larg * 0.25))
        cv2.ellipse(m, centro, (int(larg * 1.0), int(larg * 0.95)), 0, 0, 360, 1.0, -1)
        k = max(3, int(larg * 0.9) | 1)
        m = cv2.GaussianBlur(m, (k, k), 0)
    return m[..., None]


def main():
    entrada, saida, pesos = sys.argv[1:4]
    forca = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
    rest = GFPGANer(model_path=pesos, upscale=1, arch="clean", channel_multiplier=2,
                    bg_upsampler=None, device="cpu")
    cap = cv2.VideoCapture(entrada)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = cv2.VideoWriter(saida, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    t0, i = time.time(), 0
    while True:
        ok, quadro = cap.read()
        if not ok:
            break
        try:
            _, _, melhor = rest.enhance(quadro, has_aligned=False, only_center_face=True,
                                        paste_back=True, weight=forca)
        except Exception:  # noqa: BLE001
            melhor = None
        if melhor is not None and melhor.shape == quadro.shape:
            # O GFPGAN "clean" (v1.4) ignora o `weight` e sempre redesenha o rosto 100%: pele
            # lisa, "cara de IA". Então a mistura é feita aqui: o rosto fica `forca` restaurado
            # (mantém a textura da pele), mas a boca e o queixo são restaurados por inteiro,
            # porque é onde o Wav2Lip deixa a imagem borrada.
            peso = forca + (1 - forca) * _mascara_boca(rest, quadro.shape)
            melhor = (quadro * (1 - peso) + melhor * peso).clip(0, 255).astype("uint8")
        else:
            melhor = quadro
        out.write(melhor)
        i += 1
        if i % 25 == 0:
            print(f"realce: {i}/{total} quadros ({time.time() - t0:.0f} s)", flush=True)
    out.release()


if __name__ == "__main__":
    main()
