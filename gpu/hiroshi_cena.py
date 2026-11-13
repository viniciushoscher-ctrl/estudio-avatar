"""Cria novas cenas do Hiroshi a partir da imagem original, mantendo o mesmo rosto.

Modelo: Qwen-Image-Edit-2509 (Alibaba, licença Apache-2.0, uso comercial liberado), na GPU da Modal.
Uso:
    modal run gpu/hiroshi_cena.py --imagem avatares/rosto-japones.png --saida cenas --variacoes 4
"""
import io
import os
from pathlib import Path

import modal

app = modal.App("hiroshi-cena")
pesos = modal.Volume.from_name("qwen-image-pesos", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("diffusers>=0.36", "transformers>=4.51,<5", "accelerate>=1.0", "safetensors",
                 "huggingface_hub[hf_transfer]<1.0", "Pillow", "sentencepiece")
    .env({"HF_HOME": "/pesos", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
MODELO = "Qwen/Qwen-Image-Edit-2509"
CENA_MESA = (
    "Show this exact same man, same face, same gray hair, same age and same navy shirt, sitting at a "
    "wooden desk in a calm traditional Japanese home study. Wide horizontal medium shot from the waist "
    "up, centered, both hands resting folded on the desk, looking straight at the camera with a gentle "
    "expression, mouth closed. Behind him a low bookshelf and a shoji paper window with soft daylight, "
    "a small bonsai and a cup of green tea on the desk. Photorealistic, natural skin texture, 35mm "
    "documentary photo, shallow depth of field."
)
CENA_PODCAST = (
    "Show this exact same man, same face, same gray hair, same age and same navy shirt, sitting at a "
    "wooden desk in a calm traditional Japanese room, recording a podcast. Wide horizontal 16:9 medium "
    "shot from the waist up, centered, hands folded on the desk. A black podcast microphone on a boom "
    "arm stands at the LEFT edge of the desk, low at chest height and far to the side of his body, "
    "pointing toward him; the microphone never covers his face: his whole face, lips, mouth and chin "
    "are completely clear and unobstructed. Looking straight at the camera, gentle expression, mouth "
    "closed. Behind him shoji paper screens with warm soft light, a low wooden shelf with a few "
    "ceramics and a small bonsai, warm lamp glow. Photorealistic, natural skin texture, 35mm "
    "documentary photo, shallow depth of field."
)
CENA_PERTO = (
    "Show this exact same man in this exact same room, same face, same gray hair, same navy shirt, same "
    "shoji window, wooden shelf, bonsai and tea, but the camera is closer: a horizontal 16:9 medium "
    "close-up from the middle of the chest up, his head and shoulders large in the frame, face centered "
    "in the upper half, looking straight at the camera with a gentle expression, mouth closed. "
    "Photorealistic, sharp natural skin texture, 50mm documentary photo, shallow depth of field."
)
NEGATIVO = "microphone in front of the face, microphone covering the mouth, cartoon, illustration, 3d render, blurry, deformed hands, extra fingers, text, watermark"


@app.cls(gpu="A100-80GB", image=image, volumes={"/pesos": pesos}, memory=65536, timeout=3600,
         scaledown_window=60)
class Cena:
    @modal.enter()
    def carregar(self):
        import torch
        from diffusers import QwenImageEditPlusPipeline
        self.pipe = QwenImageEditPlusPipeline.from_pretrained(MODELO, torch_dtype=torch.bfloat16).to("cuda")
        pesos.commit()

    @modal.method()
    def gerar(self, imagem: bytes, prompt: str, seed: int, largura: int, altura: int) -> bytes:
        import torch
        from PIL import Image
        foto = Image.open(io.BytesIO(imagem)).convert("RGB")
        out = self.pipe(image=[foto], prompt=prompt, negative_prompt=NEGATIVO, true_cfg_scale=4.0,
                        num_inference_steps=40, width=largura, height=altura,
                        generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        buf = io.BytesIO()
        out.save(buf, "PNG")
        return buf.getvalue()


@app.local_entrypoint()
def main(imagem: str = "avatares/rosto-japones.png", saida: str = "cenas", prompt: str = "",
         variacoes: int = 4, largura: int = 1344, altura: int = 768):
    Path(saida).mkdir(parents=True, exist_ok=True)
    foto = Path(imagem).read_bytes()
    c = Cena()
    for s in range(1, variacoes + 1):
        png = c.gerar.remote(foto, prompt.strip() or CENA_PERTO, s, largura, altura)
        Path(saida, f"cena-{s}.png").write_bytes(png)
        print(f"[cena] {saida}/cena-{s}.png", flush=True)
