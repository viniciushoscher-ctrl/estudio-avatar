"""Troca o rosto do vídeo pelo rosto de uma imagem (inswapper), mantendo corpo, cabeça e boca reais.

Uso: python trocar_rosto.py rosto.png entrada.mp4 saida_sem_audio.mp4 inswapper_128.onnx GFPGANv1.4.pth [forca]
A boca continua sendo a de quem gravou, então a fala fica sincronizada sem Wav2Lip.
"""
import sys
import time

import cv2
import numpy as np
import torchvision.transforms.functional as _F

sys.modules.setdefault("torchvision.transforms.functional_tensor", _F)

import insightface  # noqa: E402
from gfpgan import GFPGANer  # noqa: E402
from insightface.app import FaceAnalysis  # noqa: E402


def maior(rostos):
    return max(rostos, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])) if rostos else None


def main():
    imagem, entrada, saida, modelo, pesos = sys.argv[1:6]
    forca = float(sys.argv[6]) if len(sys.argv) > 6 else 0.6
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    troca = insightface.model_zoo.get_model(modelo, providers=["CPUExecutionProvider"])
    rest = GFPGANer(model_path=pesos, upscale=1, arch="clean", channel_multiplier=2,
                    bg_upsampler=None, device="cpu")
    alvo = maior(app.get(cv2.imread(imagem)))
    if alvo is None:
        sys.exit("não achei rosto na imagem do avatar")

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
        rosto = maior(app.get(quadro))
        if rosto is not None:
            trocado = troca.get(quadro, rosto, alvo, paste_back=True)
            # O inswapper trabalha em 128 px: o GFPGAN devolve nitidez, misturado para não ficar "pele de IA".
            try:
                _, _, melhor = rest.enhance(trocado, has_aligned=False, only_center_face=True, paste_back=True)
            except Exception:  # noqa: BLE001
                melhor = None
            if melhor is not None and melhor.shape == trocado.shape:
                trocado = (trocado * (1 - forca) + melhor * forca).clip(0, 255).astype(np.uint8)
            quadro = trocado
        out.write(quadro)
        i += 1
        if i % 25 == 0:
            print(f"{i}/{total} quadros, {time.time() - t0:.0f} s", flush=True)
    out.release()


if __name__ == "__main__":
    main()
