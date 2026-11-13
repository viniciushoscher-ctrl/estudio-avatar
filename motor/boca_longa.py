"""Vídeo longo do Hiroshi na CPU, de graça (o mesmo truque do HeyGen).

1. Um vídeo-base do avatar (gerado uma vez pelo LongCat) é preparado UMA vez: rosto, máscaras e
   latentes ficam salvos em cache.
2. Para qualquer fala (minutos ou horas), o vídeo-base roda em vai-e-volta e o MuseTalk 1.5
   (licença MIT) redesenha só a boca e o queixo, quadro a quadro, sincronizados com o áudio.

Uso:
  python motor/boca_longa.py preparar --base base.mp4 --cache cache_base
  python motor/boca_longa.py falar --cache cache_base --audio fala.wav --saida video.mp4 \
      [--de 0 --ate 9000]   # faixa de quadros, para dividir um vídeo longo em partes paralelas
Precisa do repositório MuseTalk em $MUSETALK (com a pasta models/).
"""
import argparse
import os
import pickle
import subprocess
import sys
import time

import cv2
import numpy as np
import torch

MUSETALK = os.environ.get("MUSETALK", "musetalk")
sys.path.insert(0, MUSETALK)
os.chdir(MUSETALK) if __name__ == "__main__" else None
torch.set_num_threads(os.cpu_count() or 4)
FPS = 25
MARGEM = 10  # extra_margin do MuseTalk 1.5


def caixa_do_rosto(fa, quadro):
    """Mesma regra do MuseTalk (preprocessing.get_landmark_and_bbox), com face_alignment no lugar do DWPose."""
    pts = fa.get_landmarks(quadro[:, :, ::-1])
    if not pts:
        return None
    lm = pts[0].astype(np.int32)
    meio = lm[29].copy()
    dist = np.max(lm[:, 1]) - meio[1]
    topo = max(0, meio[1] - dist)
    return [int(np.min(lm[:, 0])), int(topo), int(np.max(lm[:, 0])), int(np.max(lm[:, 1]))]


def preparar(base, cache):
    import face_alignment
    from musetalk.utils.blending import get_image_prepare_material
    from musetalk.utils.face_parsing import FaceParsing
    from musetalk.utils.utils import load_all_model

    vae, _, _ = load_all_model(device="cpu")
    fa = face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, device="cpu")
    fp = FaceParsing(left_cheek_width=90, right_cheek_width=90)
    cap = cv2.VideoCapture(base)
    quadros = []
    while True:
        ok, q = cap.read()
        if not ok:
            break
        quadros.append(q)
    print(f"[base] {len(quadros)} quadros", flush=True)
    caixas, ultima = [], None
    for q in quadros:
        c = caixa_do_rosto(fa, q) or ultima
        c[3] = min(c[3] + MARGEM, q.shape[0])
        caixas.append(c)
        ultima = list(c)
    # suaviza a caixa no tempo para a boca não tremer
    arr = np.array(caixas, dtype=np.float32)
    k = 5
    pad = np.pad(arr, ((k // 2, k // 2), (0, 0)), mode="edge")
    arr = np.stack([pad[i:i + k].mean(0) for i in range(len(arr))]).round().astype(int)
    caixas = [list(map(int, c)) for c in arr]
    latentes, mascaras, caixas_mascara = [], [], []
    for i, (q, (x1, y1, x2, y2)) in enumerate(zip(quadros, caixas)):
        rosto = cv2.resize(q[y1:y2, x1:x2], (256, 256), interpolation=cv2.INTER_LANCZOS4)
        latentes.append(vae.get_latents_for_unet(rosto))
        m, cb = get_image_prepare_material(q, [x1, y1, x2, y2], fp=fp, mode="jaw")
        mascaras.append(m)
        caixas_mascara.append(cb)
        if i % 100 == 0:
            print(f"[base] preparado {i}/{len(quadros)}", flush=True)
    os.makedirs(cache, exist_ok=True)
    # vai-e-volta: o fim emenda no começo sem pulo
    ida_volta = lambda l: l + l[::-1]
    with open(os.path.join(cache, "base.pkl"), "wb") as f:
        pickle.dump({"quadros": ida_volta(quadros), "caixas": ida_volta(caixas),
                     "mascaras": ida_volta(mascaras), "caixas_mascara": ida_volta(caixas_mascara)}, f)
    torch.save(ida_volta(latentes), os.path.join(cache, "latentes.pt"))
    print("[base] cache pronto", flush=True)


@torch.no_grad()
def falar(cache, audio, saida, de=0, ate=None, lote=8, so_video=False):
    from transformers import WhisperModel
    from musetalk.utils.audio_processor import AudioProcessor
    from musetalk.utils.blending import get_image_blending
    from musetalk.utils.utils import load_all_model

    t0 = time.time()
    with open(os.path.join(cache, "base.pkl"), "rb") as f:
        b = pickle.load(f)
    latentes = torch.load(os.path.join(cache, "latentes.pt"))
    vae, unet, pe = load_all_model(device="cpu")
    ap = AudioProcessor(feature_extractor_path="models/whisper")
    whisper = WhisperModel.from_pretrained("models/whisper").eval()
    feats, comp = ap.get_audio_feature(audio, weight_dtype=torch.float32)
    pedacos = ap.get_whisper_chunk(feats, "cpu", torch.float32, whisper, comp, fps=FPS,
                                   audio_padding_length_left=2, audio_padding_length_right=2)
    ate = len(pedacos) if ate is None else min(ate, len(pedacos))
    n = len(b["quadros"])
    h, w = b["quadros"][0].shape[:2]
    tmp = saida + ".sem_audio.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                           "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17",
                           "-preset", "medium", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    t = torch.tensor([0])
    print(f"[fala] quadros {de}..{ate} de {len(pedacos)}", flush=True)
    for ini in range(de, ate, lote):
        idx = list(range(ini, min(ini + lote, ate)))
        aud = pe(torch.stack([pedacos[i] for i in idx]))
        lat = torch.cat([latentes[i % n] for i in idx], dim=0)
        pred = unet.model(lat, t, encoder_hidden_states=aud).sample
        rostos = vae.decode_latents(pred)
        for i, r in zip(idx, rostos):
            x1, y1, x2, y2 = b["caixas"][i % n]
            r = cv2.resize(r.astype(np.uint8), (x2 - x1, y2 - y1))
            q = get_image_blending(b["quadros"][i % n].copy(), r, [x1, y1, x2, y2],
                                   b["mascaras"][i % n], b["caixas_mascara"][i % n])
            ff.stdin.write(np.ascontiguousarray(q).tobytes())
        if (ini - de) % (lote * 25) == 0:
            feito = min(ini + lote, ate) - de
            print(f"[fala] {feito}/{ate - de} quadros, {feito / (time.time() - t0):.2f} q/s", flush=True)
    ff.stdin.close()
    ff.wait()
    if so_video:  # parte de um vídeo longo: o áudio inteiro entra na junção final
        os.replace(tmp, saida)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-ss", f"{de / FPS:.3f}",
                        "-t", f"{(ate - de) / FPS:.3f}", "-i", audio, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", saida], check=True)
        os.remove(tmp)
    print(f"[fala] {saida} pronto em {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["preparar", "falar"])
    ap.add_argument("--base")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--saida")
    ap.add_argument("--de", type=int, default=0)
    ap.add_argument("--ate", type=int, default=None)
    ap.add_argument("--so-video", action="store_true")
    ap.add_argument("--parte", type=int, default=None, help="índice da parte (0..partes-1)")
    ap.add_argument("--partes", type=int, default=1)
    a = ap.parse_args()
    if a.acao == "preparar":
        preparar(os.path.abspath(a.base) if not os.path.isabs(a.base) else a.base, a.cache)
    else:
        if a.parte is not None:  # divide o total de quadros do áudio em partes iguais
            import soundfile as sf
            total = int(sf.info(a.audio).duration * FPS)
            passo = -(-total // a.partes)
            a.de, a.ate = a.parte * passo, min(total + 2, (a.parte + 1) * passo)
            a.so_video = True
        falar(a.cache, a.audio, a.saida, a.de, a.ate, so_video=a.so_video)
