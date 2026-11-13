"""Imagens de b-roll para os vídeos do Hiroshi (uma por instrução [broll: ...] / [split: ...] do roteiro).

Modelo: FLUX.1-schnell (Black Forest Labs, licença Apache-2.0, uso comercial liberado), 4 passos,
na GPU da Modal. Cada imagem leva ~1-2 s numa L40S.
Uso:
    modal run gpu/broll_imagens.py --roteiro roteiros/x.txt --saida broll
"""
import io
import re
from pathlib import Path

import modal

app = modal.App("hiroshi-broll")
pesos = modal.Volume.from_name("flux-pesos", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("diffusers>=0.32", "transformers>=4.48,<5", "accelerate>=1.0", "safetensors",
                 "sentencepiece", "protobuf", "huggingface_hub[hf_transfer]<1.0", "Pillow")
    .env({"HF_HOME": "/pesos", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
ESTILO = (", photorealistic documentary photo, natural light, Japan, candid, 35mm lens, "
          "realistic skin texture, no text")


def instrucoes(roteiro):
    """[(linha, tipo, prompt)] para cada linha com [broll: ...] ou [split: ...]."""
    saida = []
    linhas = [l for l in Path(roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, l in enumerate(linhas):
        m = re.match(r"^\s*\[(broll|split)\s*:\s*([^\]]+)\]", l, re.I)
        if m:
            saida.append((i, m.group(1).lower(), m.group(2).strip()))
    return saida


@app.cls(gpu="L40S", image=image, volumes={"/pesos": pesos}, memory=32768, timeout=3600, scaledown_window=60)
class Broll:
    @modal.enter()
    def carregar(self):
        import torch
        from diffusers import FluxPipeline
        self.pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell",
                                                 torch_dtype=torch.bfloat16).to("cuda")
        pesos.commit()

    @modal.method()
    def gerar(self, prompts: list, largura: int = 1344, altura: int = 768) -> list:
        import torch
        pngs = []
        for i, p in enumerate(prompts):
            img = self.pipe(p + ESTILO, num_inference_steps=4, guidance_scale=0.0, width=largura,
                            height=altura, max_sequence_length=256,
                            generator=torch.Generator("cuda").manual_seed(100 + i)).images[0]
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=93)
            pngs.append(buf.getvalue())
        return pngs


@app.local_entrypoint()
def main(roteiro: str, saida: str = "broll"):
    Path(saida).mkdir(parents=True, exist_ok=True)
    pedidos = instrucoes(roteiro)
    if not pedidos:
        print("[broll] roteiro sem [broll:]/[split:]", flush=True)
        return
    imgs = Broll().gerar.remote([p for _, _, p in pedidos])
    for (linha, _, _), jpg in zip(pedidos, imgs):
        Path(saida, f"linha-{linha:03d}.jpg").write_bytes(jpg)
    print(f"[broll] {len(imgs)} imagens em {saida}/", flush=True)
