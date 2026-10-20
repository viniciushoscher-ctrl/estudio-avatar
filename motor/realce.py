"""Restaura o rosto (GFPGAN) quadro a quadro depois do Wav2Lip, para dar nitidez à boca.

Uso: python realce.py entrada.mp4 saida_sem_audio.mp4 pesos/GFPGANv1.4.pth [forca 0-1]
Só o rosto é refeito e colado de volta; o resto do quadro fica como está.
"""
import sys
import time

import cv2
import torchvision.transforms.functional as _F

# O basicsr (usado pelo GFPGAN) ainda procura um módulo que o torchvision novo removeu.
sys.modules.setdefault("torchvision.transforms.functional_tensor", _F)

from gfpgan import GFPGANer  # noqa: E402


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
        out.write(melhor if melhor is not None and melhor.shape == quadro.shape else quadro)
        i += 1
        if i % 25 == 0:
            print(f"realce: {i}/{total} quadros ({time.time() - t0:.0f} s)", flush=True)
    out.release()


if __name__ == "__main__":
    main()
