"""Transforma a imagem de IA de cada linha [broll: ...] em VÍDEO com movimento real (LTX-Video 0.9.7 distilled).

Licença LTX-Video Open Weights: uso comercial grátis para quem fatura menos de US$ 10 milhões/ano.
Roda na GPU da Modal (crédito grátis). Só anima as linhas que ficaram sem vídeo real (Coverr/Mixkit).
Linhas longas ganham 2 ou 3 clipes com movimentos de câmera diferentes (sem repetir o mesmo clipe).

Uso: modal run gpu/broll_animar.py --roteiro roteiro.txt --tempos tempos.json --broll broll
Saída: broll/linha-NNN-1.mp4, linha-NNN-2.mp4 ...
"""
import io
import json
import math
import re
import sys
from pathlib import Path

import modal

app = modal.App("hiroshi-broll-video")
pesos = modal.Volume.from_name("ltx-pesos", create_if_missing=True)
MODELO = "Lightricks/LTX-Video-0.9.7-distilled"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("diffusers==0.34.0", "transformers==4.51.3", "accelerate>=1.0", "sentencepiece", "imageio",
                 "imageio-ffmpeg", "Pillow", "numpy<2", "hf_transfer", "huggingface_hub>=0.30,<1.0")
    .env({"HF_HOME": "/pesos", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

LARG, ALT, QUADROS, FPS_LTX = 1216, 704, 121, 24   # ~5 s por clipe
MOVIMENTOS = [
    "slow cinematic push in, gentle natural motion",
    "slow camera pan from left to right, gentle natural motion",
    "slow camera pull back, gentle natural motion",
]
NEGATIVO = "worst quality, blurry, jittery, distorted, deformed hands, deformed face, text, watermark, cartoon"


@app.cls(gpu="H100", image=image, volumes={"/pesos": pesos}, memory=65536, timeout=3600, scaledown_window=60)
class Animador:
    @modal.enter()
    def carregar(self):
        import torch
        from diffusers import LTXConditionPipeline
        self.pipe = LTXConditionPipeline.from_pretrained(MODELO, torch_dtype=torch.bfloat16).to("cuda")
        self.pipe.vae.enable_tiling()
        pesos.commit()

    @modal.method()
    def animar(self, jpg: bytes, prompt: str, movimento: str, semente: int) -> bytes:
        import tempfile

        import torch
        from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
        from diffusers.utils import export_to_video
        from PIL import Image, ImageOps

        img = ImageOps.fit(Image.open(io.BytesIO(jpg)).convert("RGB"), (LARG, ALT), Image.LANCZOS)
        cond = LTXVideoCondition(image=img, frame_index=0)
        quadros = self.pipe(
            conditions=[cond], prompt=f"{prompt}. {movimento}, photorealistic documentary footage",
            negative_prompt=NEGATIVO, width=LARG, height=ALT, num_frames=QUADROS,
            timesteps=[1000, 993, 987, 981, 975, 909, 725, 0.03], decode_timestep=0.05, decode_noise_scale=0.025,
            image_cond_noise_scale=0.0, guidance_scale=1.0, guidance_rescale=0.7,
            generator=torch.Generator("cuda").manual_seed(semente), output_type="pil",
        ).frames[0]
        f = tempfile.mktemp(suffix=".mp4")
        export_to_video(quadros, f, fps=FPS_LTX)
        return Path(f).read_bytes()


@app.local_entrypoint()
def main(roteiro: str, tempos: str, broll: str = "broll"):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "motor"))
    from montar import FPS, trechos

    linhas = [l for l in Path(roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]
    t = json.loads(Path(tempos).read_text())
    tarefas, destinos = [], []
    for tr in trechos(roteiro, t):
        if tr["tipo"] not in ("broll", "split"):
            continue
        i = tr["linha"]
        if list(Path(broll).glob(f"linha-{i:03d}-*.mp4")):
            continue  # já tem vídeo real
        img = Path(broll, f"linha-{i:03d}.jpg")
        m = re.match(r"^\s*\[(?:broll|split)\s*:\s*([^\]|]*)", linhas[i], re.I)
        if not img.exists() or not m:
            continue
        n = max(1, min(3, math.ceil(((tr["q1"] - tr["q0"]) / FPS) / 5.0)))
        for k in range(n):
            tarefas.append((img.read_bytes(), m.group(1).strip(), MOVIMENTOS[(i + k) % 3], 1000 * i + k))
            destinos.append(Path(broll, f"linha-{i:03d}-{k + 1}.mp4"))
    print(f"[animar] {len(tarefas)} clipe(s)", flush=True)
    if not tarefas:
        return
    a = Animador()
    for d, v in zip(destinos, a.animar.starmap(tarefas)):
        d.write_bytes(v)
        print(f"[animar] {d}", flush=True)
