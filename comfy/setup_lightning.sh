#!/usr/bin/env bash
# Instala ComfyUI + WanVideoWrapper + KJNodes + VideoHelperSuite + ComfyArt (commits fixados) e baixa os pesos
# da etapa pedida ($1 = chave | video). Idempotente: na 2ª vez só confere.
set -euo pipefail
ETAPA=${1:-video}
COMFY=${COMFY_DIR:-$HOME/comfy}
clonar() { [ -d "$2/.git" ] || git clone -q "$1" "$2"; (cd "$2" && git fetch -q --depth 50 origin && git checkout -q "$3" 2>/dev/null || git checkout -q "$3"); }
clonar https://github.com/comfyanonymous/ComfyUI "$COMFY" e9afbccc2669
clonar https://github.com/kijai/ComfyUI-WanVideoWrapper "$COMFY/custom_nodes/ComfyUI-WanVideoWrapper" a7439db30bed
clonar https://github.com/kijai/ComfyUI-KJNodes "$COMFY/custom_nodes/ComfyUI-KJNodes" 70701d2a11d4
clonar https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite "$COMFY/custom_nodes/ComfyUI-VideoHelperSuite" 4d907bee61e9
clonar https://github.com/jtydhr88/ComfyArt "$COMFY/custom_nodes/ComfyArt" 2a990a741fcb
if [ ! -f "$COMFY/.instalado" ]; then
  python -m pip install -q -r "$COMFY/requirements.txt"
  for d in "$COMFY"/custom_nodes/*/; do [ -f "$d/requirements.txt" ] && python -m pip install -q -r "$d/requirements.txt" || true; done
  python -m pip install -q "huggingface_hub[hf_transfer]>=0.27"
  command -v ffmpeg >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg) || true
  touch "$COMFY/.instalado"
fi
# pesos: na pasta com mais espaço livre (home persistente se couber, senão disco local)
LIVRE_HOME=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9)
MODELOS=${MODELOS:-$([ "$LIVRE_HOME" -gt 90 ] && echo "$HOME/modelos" || echo /tmp/modelos)}
mkdir -p "$MODELOS"; df -h "$HOME" /tmp | sed 's/^/[disco] /'
printf "lightning:\n  base_path: %s\n  diffusion_models: diffusion_models\n  loras: loras\n  vae: vae\n  text_encoders: text_encoders\n  clip: text_encoders\n  wav2vec2: wav2vec2\n" "$MODELOS" > "$COMFY/extra_model_paths.yaml"
HF_HUB_ENABLE_HF_TRANSFER=1 MODELOS="$MODELOS" ETAPA="$ETAPA" python - <<'PY'
import os, time
from pathlib import Path
from huggingface_hub import hf_hub_download
M = Path(os.environ["MODELOS"])
pesos = {
  "chave": [
    ("Comfy-Org/Qwen-Image", "split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors", "diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors"),
    ("Comfy-Org/Qwen-Image", "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors", "text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"),
    ("Comfy-Org/Qwen-Image", "split_files/vae/qwen_image_vae.safetensors", "vae/qwen_image_vae.safetensors"),
  ],
  "video": [
    ("Kijai/LongCat-Video_comfy", "Avatar/LongCat-Avatar_comfy_bf16.safetensors", "diffusion_models/LongCat/LongCat-Avatar_bf16.safetensors"),
    ("Kijai/LongCat-Video_comfy", "LongCat_distill_lora_alpha64_bf16.safetensors", "loras/LongCat_distill_lora_alpha64_bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "Wan2_1_VAE_bf16.safetensors", "vae/Wan2_1_VAE_bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "umt5-xxl-enc-bf16.safetensors", "text_encoders/umt5-xxl-enc-bf16.safetensors"),
    ("Kijai/wav2vec2_safetensors", "wav2vec2-chinese-base_fp16.safetensors", "wav2vec2/wav2vec2-chinese-base_fp16.safetensors"),
  ],
}[os.environ["ETAPA"]]
for repo, arq, dest in pesos:
    alvo = M / dest
    if alvo.exists():
        print("[ok]", dest); continue
    alvo.parent.mkdir(parents=True, exist_ok=True)
    t = time.time()
    p = hf_hub_download(repo, arq, local_dir=str(M / ".hf"))
    os.replace(p, alvo)
    print(f"[baixado] {dest} {alvo.stat().st_size/1e9:.1f} GB em {time.time()-t:.0f} s", flush=True)
PY
echo "[setup] pronto ($ETAPA)"
