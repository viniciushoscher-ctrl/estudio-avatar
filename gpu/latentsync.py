"""Hiroshi falando o vídeo INTEIRO (estilo "avatar o tempo todo", como o canal Thomas Becker).

Como funciona (tudo open source, Apache-2.0):
1. Uma base curta do Hiroshi feita pelo LongCat (gpu/kenji_longcat.py, 480p) traz o corpo vivo:
   cabeça, piscadas, ombros, mãos.
2. A base é esticada até o tamanho do áudio andando para a frente e para trás em trechos de
   duração aleatória (sem repetição periódica, que o olho percebe).
3. O LatentSync 1.6 (ByteDance) redesenha só a boca em 512 px sincronizada com a voz.
4. O áudio é dividido em pedaços de ~60 s que rodam em paralelo em várias GPUs e são
   colados no fim, com a trilha original inteira (sem emendas no som).

Uso:
    modal run gpu/latentsync.py --base bases/base-hiroshi-podcast.mp4 --audio fala.wav --saida hiroshi.mp4
"""
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

import modal

REPO = "https://github.com/bytedance/LatentSync"
COMMIT = "a229c3948406bc2cf6eaf4873e662e70c6a04746"
GPU = os.environ.get("LIPSYNC_GPU", "L40S").split(",")
FPS = 25
PEDACO = 60  # segundos de áudio por GPU

app = modal.App("hiroshi-latentsync")
pesos = modal.Volume.from_name("latentsync-pesos", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.5.1", "torchvision==0.20.1", index_url="https://download.pytorch.org/whl/cu121")
    .pip_install(
        "diffusers==0.32.2", "transformers==4.48.0", "decord==0.6.0", "accelerate==0.26.1",
        "einops==0.7.0", "omegaconf==2.3.0", "opencv-python-headless==4.9.0.80", "mediapipe==0.10.11",
        "python_speech_features==0.6", "librosa==0.10.1", "scenedetect==0.6.1", "ffmpeg-python==0.2.0",
        "imageio==2.31.1", "imageio-ffmpeg==0.5.1", "lpips==0.1.4", "face-alignment==1.4.1",
        "huggingface-hub==0.30.2", "numpy==1.26.4", "kornia==0.8.0", "insightface==0.7.3",
        "onnxruntime-gpu==1.21.0", "DeepCache==0.1.1", "hf_transfer",
    )
    .run_commands(f"git clone {REPO} /LatentSync && cd /LatentSync && git checkout {COMMIT}")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


def ordem_base(n, total, semente=7):
    """Índices dos quadros da base para `total` quadros: vai e volta em trechos de 3 a 10 s."""
    rnd = random.Random(semente)
    i, d, ordem = rnd.randrange(n), 1, []
    while len(ordem) < total:
        for _ in range(rnd.randint(3 * FPS, 10 * FPS)):
            ordem.append(i)
            if not 0 <= i + d < n:
                d = -d
            i += d
        d = rnd.choice((1, -1))
    return ordem[:total]


@app.function(gpu=GPU, image=image, volumes={"/pesos": pesos}, memory=32768, timeout=3600)
def sincronizar(base: bytes, audio: bytes, ordem: list, passos: int = 20, guia: float = 1.5) -> bytes:
    import cv2

    ck = Path("/pesos/checkpoints")
    if not (ck / "latentsync_unet.pt").exists():
        from huggingface_hub import hf_hub_download
        for f in ("latentsync_unet.pt", "whisper/tiny.pt"):
            hf_hub_download("ByteDance/LatentSync-1.6", f, local_dir=str(ck))
        pesos.commit()
    os.chdir("/LatentSync")
    if not Path("checkpoints").exists():
        os.symlink(ck, "checkpoints")

    t = Path(tempfile.mkdtemp())
    (t / "base.mp4").write_bytes(base)
    (t / "fala.wav").write_bytes(audio)
    cap = cv2.VideoCapture(str(t / "base.mp4"))
    quadros = []
    while True:
        ok, q = cap.read()
        if not ok:
            break
        quadros.append(q)
    h, w = quadros[0].shape[:2]
    out = cv2.VideoWriter(str(t / "esticada.avi"), cv2.VideoWriter_fourcc(*"MJPG"), FPS, (w, h))
    for i in ordem:
        out.write(quadros[min(i, len(quadros) - 1)])
    out.release()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(t / "esticada.avi"), "-c:v", "libx264",
                    "-crf", "16", "-pix_fmt", "yuv420p", str(t / "esticada.mp4")], check=True)
    subprocess.run([
        "python", "-m", "scripts.inference",
        "--unet_config_path", "configs/unet/stage2_512.yaml",
        "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
        "--inference_steps", str(passos), "--guidance_scale", str(guia), "--enable_deepcache",
        "--video_path", str(t / "esticada.mp4"), "--audio_path", str(t / "fala.wav"),
        "--video_out_path", str(t / "saida.mp4"),
    ], check=True)
    return (t / "saida.mp4").read_bytes()


def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def _quadros(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


@app.local_entrypoint()
def main(base: str, audio: str, saida: str = "hiroshi-falando.mp4", passos: int = 20, semente: int = 7):
    t = Path(tempfile.mkdtemp())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", base, "-r", str(FPS), "-an", "-c:v", "libx264",
                    "-crf", "16", "-pix_fmt", "yuv420p", str(t / "base.mp4")], check=True)
    n = _quadros(str(t / "base.mp4"))
    dur = _dur(audio)
    total = int(round(dur * FPS))
    ordem = ordem_base(n, total + FPS, semente)
    pedacos, cargas = [], []
    k = 0
    while k * PEDACO < dur:
        ini, fim = k * PEDACO, min((k + 1) * PEDACO, dur)
        wav = t / f"a{k:03d}.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(ini), "-t", str(fim - ini), "-i", audio,
                        "-ar", "16000", "-ac", "1", str(wav)], check=True)
        q0, q1 = int(round(ini * FPS)), int(round(fim * FPS)) + FPS // 2
        cargas.append((wav.read_bytes(), ordem[q0:q1]))
        pedacos.append(t / f"v{k:03d}.mp4")
        k += 1
    print(f"Base {n} quadros; áudio {dur:.1f} s em {len(pedacos)} pedaço(s) paralelos")
    b = (t / "base.mp4").read_bytes()
    for p, video in zip(pedacos, sincronizar.starmap([(b, a, o, passos) for a, o in cargas])):
        p.write_bytes(video)
    lista = t / "lista.txt"
    lista.write_text("".join(f"file '{p}'\n" for p in pedacos))
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", saida], check=True)
    print(json.dumps({"saida": saida, "segundos": round(dur, 1)}))
