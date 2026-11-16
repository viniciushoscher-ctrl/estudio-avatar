"""Vídeo-base do avatar com o CORPO se mexendo e a BOCA FECHADA, gerado na CPU do GitHub (grátis, sem GPU).

Modelo: LTX-Video 2B 0.9.6 distilled (Lightricks; uso comercial grátis abaixo de US$ 10 mi/ano), imagem -> vídeo.
Roda uma vez por avatar e por semente; depois o Ditto (motor/ditto_cpu.sh) põe a boca falando o áudio
novo em cima desse vídeo. Com a boca fechada na base, a fala nova não briga com uma fala antiga.

Uso: python motor/base_cpu.py avatares/hiroshi-mesa.png saida.mp4 --semente 1
"""
import argparse
import gc
import time

import torch
from diffusers import AutoencoderKLLTXVideo, LTXConditionPipeline, LTXVideoTransformer3DModel
from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
from diffusers.utils import export_to_video
from PIL import Image, ImageOps
from transformers import T5EncoderModel

# versão de 2 bilhões de parâmetros (a de 13 bi não cabe na CPU grátis); texto/tokenizador da 0.9.5 em diffusers
PESOS = "https://huggingface.co/Lightricks/LTX-Video/blob/main/ltxv-2b-0.9.6-distilled-04-25.safetensors"
MODELO = "Lightricks/LTX-Video-0.9.5"
PROMPT = ("A real elderly man sitting at a wooden desk, facing the camera, listening calmly with his mouth "
          "closed and lips together. He breathes naturally, gently nods and tilts his head, shifts his shoulders "
          "and makes small relaxed hand gestures on the desk, then rests his hands again. Static camera, "
          "same room, soft natural window light, photorealistic documentary footage.")
NEGATIVO = ("talking, open mouth, teeth, worst quality, blurry, jittery, distorted, deformed hands, extra fingers, "
            "deformed face, text, watermark, cartoon, camera movement, zoom")

ap = argparse.ArgumentParser()
ap.add_argument("imagem")
ap.add_argument("saida")
ap.add_argument("--semente", type=int, default=1)
ap.add_argument("--largura", type=int, default=1216)
ap.add_argument("--altura", type=int, default=704)
ap.add_argument("--quadros", type=int, default=97)  # 8k+1; 97 = 4 s a 24 fps
ap.add_argument("--prompt", default=PROMPT)
a = ap.parse_args()
torch.set_num_threads(max(1, torch.get_num_threads()))
t0 = time.time()

transformer = LTXVideoTransformer3DModel.from_single_file(PESOS, torch_dtype=torch.float32)
vae = AutoencoderKLLTXVideo.from_single_file(PESOS, torch_dtype=torch.float32)
pipe = LTXConditionPipeline.from_pretrained(MODELO, transformer=transformer, vae=vae, text_encoder=None,
                                            torch_dtype=torch.float32)
# o T5 em float32 não cabe nos 16 GB da máquina grátis: carrega em bfloat16 só para ler o texto e solta
pipe.text_encoder = T5EncoderModel.from_pretrained(MODELO, subfolder="text_encoder", torch_dtype=torch.bfloat16)
with torch.no_grad():
    pe, pm, _, _ = pipe.encode_prompt(a.prompt, None, do_classifier_free_guidance=False, device="cpu")
pipe.text_encoder = None
gc.collect()
pe = pe.float()
print(f"[base] texto pronto em {time.time() - t0:.0f} s", flush=True)

pipe.vae.enable_tiling()
img = ImageOps.fit(Image.open(a.imagem).convert("RGB"), (a.largura, a.altura), Image.LANCZOS)
quadros = pipe(
    conditions=[LTXVideoCondition(image=img, frame_index=0)],
    prompt_embeds=pe, prompt_attention_mask=pm,
    width=a.largura, height=a.altura, num_frames=a.quadros,
    num_inference_steps=8, decode_timestep=0.05, decode_noise_scale=0.025, guidance_scale=1.0,
    generator=torch.Generator("cpu").manual_seed(a.semente), output_type="pil",
).frames[0]
export_to_video(quadros, a.saida, fps=24)
print(f"[base] {a.saida}: {len(quadros)} quadros em {time.time() - t0:.0f} s", flush=True)
