"""Avatar falante a partir de UMA imagem (clone open source do HeyGen "Photo Avatar").

Modelo: LongCat-Video-Avatar 1.5 (Meituan, licença MIT, uso comercial liberado).
A imagem do avatar + o áudio da fala viram um vídeo do peito para cima, com boca sincronizada,
piscadas, cabeça, ombros e mãos se mexendo. Nenhum vídeo de pessoa real é usado.

Roda na GPU da Modal (plano grátis: US$ 5 de crédito por mês, sem cartão).
O código de inferência é o mesmo do Space oficial do Hugging Face
(victor/LongCat-Video-Avatar-1.5, commit fixado abaixo), com uma diferença:
clipes de mais de 5 s são estendidos com a continuação oficial do LongCat (generate_avc),
sem cortes nem troca de pose.

Uso (no GitHub Actions ou no PC):
    modal run gpu/kenji_longcat.py --imagem avatares/rosto-japones.png --audio voz.wav --saida kenji.mp4
"""
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import modal

SPACE = "https://huggingface.co/spaces/victor/LongCat-Video-Avatar-1.5"
SPACE_COMMIT = "daeb7c18bdfd051b5f94a2e88287a50ccf2988e3"
# L40S (48 GB) cabe tudo na GPU. Em GPUs de 24 GB (A10G/L4) o codificador de texto (T5, 11 GB,
# roda uma vez por clipe) fica na CPU automaticamente.
GPU = os.environ.get("AVATAR_GPU", "L40S").split(",")

app = modal.App("kenji-avatar")
pesos = modal.Volume.from_name("longcat-pesos", create_if_missing=True)

TORCH = "https://download.pytorch.org/whl/cu124"
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", "torchaudio==2.6.0", index_url=TORCH)
    .pip_install("xformers==0.0.29.post3", index_url=TORCH)
    .pip_install(
        "gradio==6.10.0", "spaces>=0.30", "huggingface_hub>=0.27,<1.0", "hf_transfer",
        "transformers==4.49.0", "diffusers==0.32.2", "accelerate>=1.0", "safetensors>=0.4",
        "einops>=0.8", "loguru", "ftfy", "regex", "imageio", "imageio-ffmpeg",
        "opencv-python-headless", "Pillow", "numpy==1.26.4", "scipy==1.15.3",
        "scikit-image==0.25.2", "soundfile==0.13.1", "librosa==0.11.0", "pyloudnorm==0.1.1",
        "audio-separator==0.30.2", "onnx==1.18.0", "onnxruntime==1.20.1",
    )
    .run_commands(
        f"GIT_LFS_SKIP_SMUDGE=1 git clone {SPACE} /longcat",
        f"cd /longcat && git checkout {SPACE_COMMIT} && rm -rf assets",
        # pesos completos em bf16 em vez do INT8 do Space: o INT8 deixava dentes verdes e lábios roxos
        # quando a boca ocupa mais pixels (câmera perto / 720p)
        "cd /longcat && python - <<'PY'\n"
        "import re\n"
        "s = open('app.py').read()\n"
        "s = s.replace('\"base_model_int8/*\",', '\"base_model_int8/*\", \"base_model/*\",')\n"
        "s = s.replace('dit = load_quantized_dit(str(AVATAR_DIR), subfolder=\"base_model_int8\", cp_split_hw=CP_SPLIT_HW)',"
        " 'from longcat_video.modules.avatar.longcat_video_dit_avatar import LongCatVideoAvatarTransformer3DModel as _M\\n"
        "dit = (load_quantized_dit(str(AVATAR_DIR), subfolder=\"base_model_int8\", cp_split_hw=CP_SPLIT_HW) "
        "if os.environ.get(\"AVATAR_PESOS\", \"bf16\") == \"int8\" else _M.from_pretrained(str(AVATAR_DIR), "
        "subfolder=\"base_model\", cp_split_hw=CP_SPLIT_HW, torch_dtype=torch_dtype, enable_flashattn2=False, "
        "enable_flashattn3=False, enable_bsa=False, enable_xformers=True))')\n"
        "s = s.replace('if not (AVATAR_DIR / \"base_model_int8\" / \"config.json\").exists():',"
        " 'if not (AVATAR_DIR / \"base_model\" / \"config.json\").exists():')\n"
        "assert '_M.from_pretrained' in s and '\"base_model/*\"' in s\n"
        "open('app.py', 'w').write(s)\n"
        "PY",
    )
    .env({"WEIGHTS_DIR": "/pesos", "HF_HUB_ENABLE_HF_TRANSFER": "1",
          "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
)

FPS = 25
QUADROS = 125          # 5 s por trecho (igual ao Space); falas longas usam vários trechos
COND = 13              # quadros de continuidade entre trechos (igual ao demo oficial)
PROMPT_PADRAO = (
    "A real elderly Japanese man in his sixties, filmed from the chest up, talking warmly and "
    "naturally to the camera like a YouTuber sharing life advice. Natural blinking, subtle head "
    "nods and tilts, relaxed shoulders, occasional gentle hand gestures, realistic skin texture, "
    "soft natural window light, documentary realism."
)


def _sem_progresso(*_a, **_k):
    return None


@app.cls(gpu=GPU, image=image, volumes={"/pesos": pesos}, memory=65536, timeout=7200, scaledown_window=60)
class Avatar:
    @modal.enter()
    def carregar(self):
        os.chdir("/longcat")
        sys.path.insert(0, "/longcat")
        t = time.time()
        import torch
        import longcat_video.pipeline_longcat_video_avatar as P

        class TextoNaCPU:
            def __init__(self, m):
                self.m, self.config, self.dtype = m.eval(), m.config, m.dtype

            def to(self, *_a, **_k):
                return self

            def __call__(self, ids, mask):
                with torch.no_grad():
                    return self.m(ids.cpu(), mask.cpu())

        mover = P.LongCatVideoAvatarPipeline.to

        def mover_sem_t5(pipe, device):
            t5, pipe.text_encoder = pipe.text_encoder, None
            mover(pipe, device)
            pipe.text_encoder = t5 if isinstance(t5, TextoNaCPU) else TextoNaCPU(t5)
            return pipe

        # T5 (11 GB, roda uma vez por clipe) fica na CPU: sobra memória para a continuação dos
        # clipes longos (vários trechos de 5 s com cache de atenção).
        P.LongCatVideoAvatarPipeline.to = mover_sem_t5
        import app as lc  # baixa os pesos no volume na 1ª vez (~30 GB) e monta o pipeline na GPU
        self.lc = lc
        pesos.commit()
        print(f"[kenji] modelo pronto em {time.time() - t:.0f}s", flush=True)

    @modal.method()
    def gerar(self, imagem: bytes, sufixo_imagem: str, audio: bytes, prompt: str = PROMPT_PADRAO,
              seed: int = 42, resolucao: str = "480p", aceleracao: str = "Exact 8-step") -> bytes:
        import numpy as np
        import torch
        from PIL import Image

        lc = self.lc
        tmp = Path(tempfile.mkdtemp())
        img_path = tmp / f"avatar{sufixo_imagem}"
        img_path.write_bytes(imagem)
        aud_path = tmp / "fala.wav"
        aud_path.write_bytes(audio)

        fala, sr = lc._load_audio_16k(str(aud_path))
        dur = len(fala) / sr
        quadros_fala = math.ceil(dur * FPS)
        trechos = 1 + max(0, math.ceil((quadros_fala - QUADROS) / (QUADROS - COND)))
        total = QUADROS + (trechos - 1) * (QUADROS - COND)
        print(f"[kenji] fala {dur:.1f}s -> {trechos} trecho(s), {total} quadros", flush=True)

        t0 = time.time()
        emb = lc._prepare_audio_embedding(str(aud_path), lc.VOCAL_MODE_FAST, total, FPS, 1, _sem_progresso)
        lc._configure_dit_acceleration(aceleracao)
        gen = torch.Generator(device=lc.device).manual_seed(int(seed))
        foto = Image.open(img_path).convert("RGB")

        with torch.inference_mode():
            saida, latente = lc.pipe.generate_ai2v(
                image=foto, prompt=prompt, negative_prompt=lc.NEGATIVE_PROMPT, resolution=resolucao,
                num_frames=QUADROS, num_inference_steps=8, text_guidance_scale=1.0,
                audio_guidance_scale=1.0, output_type="both", generator=gen,
                audio_emb=emb[:, :QUADROS], use_distill=True,
            )
            atual = [Image.fromarray((q * 255).astype(np.uint8)) for q in saida[0]]
            todos = list(atual)
            ref = latente[:, :, :1].clone()
            largura, altura = atual[0].size
            inicio = 0
            del saida
            torch.cuda.empty_cache()
            for i in range(1, trechos):
                inicio += QUADROS - COND
                print(f"[kenji] trecho {i + 1}/{trechos}", flush=True)
                saida, latente = lc.pipe.generate_avc(
                    video=atual, video_latent=latente, prompt=prompt,
                    negative_prompt=lc.NEGATIVE_PROMPT, height=altura, width=largura,
                    num_frames=QUADROS, num_cond_frames=COND, num_inference_steps=8,
                    text_guidance_scale=1.0, audio_guidance_scale=1.0, generator=gen,
                    output_type="both", use_kv_cache=True, offload_kv_cache=True,
                    enhance_hf=False, audio_emb=emb[:, inicio:inicio + QUADROS],
                    ref_latent=ref, ref_img_index=10, mask_frame_range=3, use_distill=True,
                )
                atual = [Image.fromarray((q * 255).astype(np.uint8)) for q in saida[0]]
                todos.extend(atual[COND:])
                del saida
                torch.cuda.empty_cache()
        print(f"[kenji] geração {time.time() - t0:.0f}s", flush=True)

        quadros = np.stack([np.asarray(q) for q in todos[:quadros_fala]])
        final = lc._save_video_ffmpeg_fast(quadros, tmp / "kenji", str(aud_path), fps=FPS, quality=8)
        return Path(final).read_bytes()


@app.local_entrypoint()
def main(imagem: str, audio: str, saida: str = "kenji.mp4", prompt: str = "", seed: int = 42,
         resolucao: str = "480p"):
    """audio pode ser um .wav ou uma pasta de .wav; com pasta, saida é a pasta dos clipes e o
    modelo é carregado uma vez só para todos (o mesmo contêiner atende os clipes em sequência)."""
    t = time.time()
    foto = Path(imagem).read_bytes()
    avatar = Avatar()
    if Path(audio).is_dir():
        falas = sorted(Path(audio).glob("*.wav"))
        Path(saida).mkdir(parents=True, exist_ok=True)
        destinos = [Path(saida) / f.with_suffix(".mp4").name for f in falas]
    else:
        falas, destinos = [Path(audio)], [Path(saida)]
    for fala, destino in zip(falas, destinos):
        video = avatar.gerar.remote(foto, Path(imagem).suffix, fala.read_bytes(),
                                    prompt.strip() or PROMPT_PADRAO, seed, resolucao)
        destino.write_bytes(video)
        print(f"[kenji] {destino} pronto ({len(video) / 1e6:.1f} MB) em {time.time() - t:.0f}s", flush=True)
