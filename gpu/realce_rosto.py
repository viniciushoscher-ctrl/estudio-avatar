"""Dentes e lábios nítidos no Hiroshi: 1080p + GFPGAN 1.4 (Apache-2.0) só na boca, na GPU da Modal.

Por que: no plano aberto (mesa, podcast) o rosto do Hiroshi tem ~120 px de largura no vídeo de 480p;
a boca fica com ~40 px e os dentes viram uma mancha quando o vídeo é ampliado para 1080p.
Aqui cada quadro é ampliado para 1920x1080, o rosto é alinhado em 512 px, o GFPGAN redesenha
dentes e lábios, e só a região da boca volta para o quadro (pele, rugas e manchas ficam originais).

Uso:
    modal run gpu/realce_rosto.py --entrada clipes --saida clipes      # pasta de .mp4 (em paralelo)
    modal run gpu/realce_rosto.py --entrada video.mp4 --saida video-hd.mp4
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import modal

app = modal.App("hiroshi-realce")
pesos = modal.Volume.from_name("realce-pesos", create_if_missing=True)
GFPGAN_URL = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0", "wget")
    .pip_install("torch==2.5.1", "torchvision==0.20.1", index_url="https://download.pytorch.org/whl/cu121")
    .pip_install("numpy==1.26.4", "opencv-python-headless==4.10.0.84", "basicsr==1.4.2", "facexlib==0.3.0",
                 "gfpgan==1.3.8", "tqdm")
)

LARG, ALT = 1920, 1080
FORCA = 0.85          # quanto da boca restaurada entra no quadro
PESO_GFP = 0.5        # mistura do GFPGAN com o rosto original (menos = mais natural)


@app.function(gpu="L4", image=image, volumes={"/pesos": pesos}, timeout=3600, memory=16384)
def realcar(video: bytes) -> bytes:
    import cv2
    import numpy as np
    import torch
    import torchvision.transforms.functional as _F
    sys.modules.setdefault("torchvision.transforms.functional_tensor", _F)
    os.makedirs("/pesos/gfpgan/weights", exist_ok=True)
    os.chdir("/pesos/gfpgan")  # facexlib baixa detector/parser em gfpgan/weights
    peso = "/pesos/GFPGANv1.4.pth"
    if not os.path.exists(peso):
        subprocess.run(["wget", "-q", "-O", peso, GFPGAN_URL], check=True)
    from gfpgan import GFPGANer
    r = GFPGANer(model_path=peso, upscale=1, arch="clean", channel_multiplier=2, bg_upsampler=None)
    pesos.commit()

    # máscara da boca no rosto alinhado (modelo FFHQ 512: boca por volta de y=365)
    m512 = np.zeros((512, 512), np.float32)
    cv2.ellipse(m512, (256, 362), (118, 82), 0, 0, 360, 1.0, -1)
    m512 = cv2.GaussianBlur(m512, (61, 61), 0)

    t = Path(tempfile.mkdtemp())
    (t / "in.mp4").write_bytes(video)
    cap = cv2.VideoCapture(str(t / "in.mp4"))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    out = cv2.VideoWriter(str(t / "v.avi"), cv2.VideoWriter_fourcc(*"MJPG"), fps, (LARG, ALT))
    fh = r.face_helper
    n = 0
    while True:
        ok, q = cap.read()
        if not ok:
            break
        h, w = q.shape[:2]
        s = max(LARG / w, ALT / h)
        q = cv2.resize(q, (round(w * s), round(h * s)), interpolation=cv2.INTER_LANCZOS4)
        y0, x0 = (q.shape[0] - ALT) // 2, (q.shape[1] - LARG) // 2
        q = np.ascontiguousarray(q[y0:y0 + ALT, x0:x0 + LARG])
        fh.clean_all()
        fh.read_image(q)
        fh.get_face_landmarks_5(only_center_face=True, eye_dist_threshold=5)
        if fh.all_landmarks_5:
            fh.align_warp_face()
            afim = fh.affine_matrices[0]
            rosto = fh.cropped_faces[0]
            x = torch.from_numpy(rosto[:, :, ::-1].copy()).permute(2, 0, 1).float().div(255).sub(0.5).div(0.5)[None].cuda()
            with torch.no_grad():
                y = r.gfpgan(x, return_rgb=False, weight=PESO_GFP)[0][0]
            y = ((y.clamp(-1, 1) + 1) / 2 * 255).permute(1, 2, 0).cpu().numpy()[:, :, ::-1]
            inv = cv2.invertAffineTransform(afim)
            volta = cv2.warpAffine(np.ascontiguousarray(y), inv, (LARG, ALT), flags=cv2.INTER_LANCZOS4)
            m = cv2.warpAffine(m512, inv, (LARG, ALT))[..., None] * FORCA
            q = (q * (1 - m) + volta * m).clip(0, 255).astype(np.uint8)
        out.write(q)
        n += 1
    out.release()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(t / "v.avi"), "-i", str(t / "in.mp4"),
                    "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", str(t / "out.mp4")], check=True)
    print(f"[realce] {n} quadros", flush=True)
    return (t / "out.mp4").read_bytes()


@app.local_entrypoint()
def main(entrada: str, saida: str):
    e = Path(entrada)
    if e.is_dir():
        arqs = sorted(e.glob("*.mp4"))
        destinos = [Path(saida) / a.name for a in arqs]
    else:
        arqs, destinos = [e], [Path(saida)]
    for d, v in zip(destinos, realcar.map([a.read_bytes() for a in arqs])):
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_bytes(v)
        print(f"[realce] {d}", flush=True)
