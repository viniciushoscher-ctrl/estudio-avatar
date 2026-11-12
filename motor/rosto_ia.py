"""Gera rostos de um personagem de IA (CPU, Stable Diffusion 1.5) para servir de avatar."""
import sys
from pathlib import Path

import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

saida = Path(sys.argv[1])
quantos = int(sys.argv[2])
descricao = sys.argv[3]
saida.mkdir(parents=True, exist_ok=True)

pipe = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5", torch_dtype=torch.float32, safety_checker=None)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)

negativo = ("cartoon, anime, illustration, painting, deformed, blurry, lowres, extra fingers, "
            "closed eyes, smiling too wide, sunglasses, hat, text, watermark, side view, profile")
for i in range(quantos):
    g = torch.Generator("cpu").manual_seed(1000 + i)
    img = pipe(descricao, negative_prompt=negativo, width=512, height=640,
               num_inference_steps=28, guidance_scale=7.0, generator=g).images[0]
    img.save(saida / f"rosto-{i + 1}.png")
    print(f"rosto {i + 1}/{quantos} pronto", flush=True)
