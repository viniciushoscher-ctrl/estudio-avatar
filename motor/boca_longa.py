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


@torch.no_grad()
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


class Realce:
    """GFPGAN 1.4 (Apache-2.0) só na boca: devolve a nitidez que o MuseTalk (rosto em 256 px) perde.

    O alinhamento do rosto de cada quadro da base é calculado uma vez e reaproveitado; a rede roda
    no rosto alinhado (512 px) e o resultado é colado de volta apenas na área da boca e do queixo.
    """

    def __init__(self, pesos, forca=0.85):
        import torchvision.transforms.functional as _F
        sys.modules.setdefault("torchvision.transforms.functional_tensor", _F)
        from gfpgan import GFPGANer
        self.r = GFPGANer(model_path=pesos, upscale=1, arch="clean", channel_multiplier=2,
                          bg_upsampler=None, device="cpu")
        self.forca = forca
        self.afins = {}

    def _afim(self, chave, quadro):
        if chave not in self.afins:
            fh = self.r.face_helper
            fh.clean_all()
            fh.read_image(quadro)
            fh.get_face_landmarks_5(only_center_face=True, eye_dist_threshold=5)
            if not fh.all_landmarks_5:
                self.afins[chave] = None
            else:
                fh.align_warp_face()
                self.afins[chave] = fh.affine_matrices[0].copy()
        return self.afins[chave]

    @torch.no_grad()
    def __call__(self, chave_base, quadro_base, quadro, mascara, caixa_mascara):
        afim = self._afim(chave_base, quadro_base)
        if afim is None:
            return quadro
        h, w = quadro.shape[:2]
        rosto = cv2.warpAffine(quadro, afim, (512, 512), borderMode=cv2.BORDER_CONSTANT, borderValue=(135, 133, 132))
        x = torch.from_numpy(rosto[:, :, ::-1].copy()).permute(2, 0, 1).float().div(255).sub(0.5).div(0.5)[None]
        y = self.r.gfpgan(x, return_rgb=False, weight=0.5)[0][0]
        y = ((y.clamp(-1, 1) + 1) / 2 * 255).permute(1, 2, 0).numpy()[:, :, ::-1]
        volta = cv2.warpAffine(np.ascontiguousarray(y), cv2.invertAffineTransform(afim), (w, h))
        m = np.zeros((h, w), np.float32)
        x1, y1, x2, y2 = caixa_mascara
        mm = mascara if mascara.ndim == 2 else mascara[..., 0]
        xa, ya, xb, yb = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        m[ya:yb, xa:xb] = mm[ya - y1:yb - y1, xa - x1:xb - x1] / 255.0
        m = cv2.GaussianBlur(m, (21, 21), 0)[..., None] * self.forca
        return (quadro * (1 - m) + volta * m).clip(0, 255).astype(np.uint8)


def roteiro_base(m, total, semente=7):
    """Ordem dos quadros da base para cada quadro do vídeo, sem repetição periódica.

    Anda pela base em trechos de 3 a 10 s, mudando de sentido ao acaso (e nas pontas), sempre
    quadro a quadro, sem pulos. É determinística: as máquinas paralelas calculam a mesma ordem.
    """
    rng = np.random.default_rng(semente)
    ordem, pos, sentido = [], 0, 1
    while len(ordem) < total:
        for _ in range(int(rng.integers(3 * FPS, 10 * FPS))):
            ordem.append(pos)
            if not 0 <= pos + sentido < m:
                sentido = -sentido
            pos += sentido
        if rng.random() < 0.5:
            sentido = -sentido
    return ordem[:total]


@torch.no_grad()
def falar(cache, audio, saida, de=0, ate=None, lote=4, so_video=False, realce=None):
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
    m = len(b["quadros"]) // 2  # o cache guarda ida + volta; usa só a ida
    ordem = roteiro_base(m, ate)
    h, w = b["quadros"][0].shape[:2]
    tmp = saida + ".sem_audio.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                           "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17",
                           "-preset", "medium", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    t = torch.tensor([0])
    rest = Realce(realce) if realce else None
    print(f"[fala] quadros {de}..{ate} de {len(pedacos)}", flush=True)
    for ini in range(de, ate, lote):
        idx = list(range(ini, min(ini + lote, ate)))
        aud = pe(torch.stack([pedacos[i] for i in idx]))
        lat = torch.cat([latentes[ordem[i]] for i in idx], dim=0)
        pred = unet.model(lat, t, encoder_hidden_states=aud).sample
        rostos = vae.decode_latents(pred)
        for i, r in zip(idx, rostos):
            k = ordem[i]
            x1, y1, x2, y2 = b["caixas"][k]
            r = cv2.resize(r.astype(np.uint8), (x2 - x1, y2 - y1))
            q = get_image_blending(b["quadros"][k].copy(), r, [x1, y1, x2, y2],
                                   b["mascaras"][k], b["caixas_mascara"][k])
            if rest is not None:
                q = rest(k, b["quadros"][k], q, b["mascaras"][k], b["caixas_mascara"][k])
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
    ap.add_argument("--lote", type=int, default=4, help="quadros por passo (4 cabe em 16 GB de RAM)")
    ap.add_argument("--realce", default=None, help="pesos do GFPGANv1.4.pth para nitidez da boca")
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
        falar(a.cache, a.audio, a.saida, a.de, a.ate, lote=a.lote, so_video=a.so_video,
              realce=os.path.abspath(a.realce) if a.realce else None)
