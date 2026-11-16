#!/usr/bin/env bash
# Instala o Ditto (Ant Group, Apache-2.0) para rodar 100% na CPU (GitHub Actions, grátis, sem GPU).
# Uso: bash motor/ditto_cpu.sh            (instala em ./ditto)
#      bash motor/ditto_cpu.sh fala.wav imagem.png saida.mp4
# O Ditto anima rosto, boca, olhos e cabeça a partir do áudio; o resto da imagem fica parado.
set -euo pipefail
D=${DITTO_DIR:-ditto}

if [ ! -f "$D/.pronto" ]; then
  rm -rf "$D"
  git clone -q https://github.com/antgroup/ditto-talkinghead "$D"
  git -C "$D" checkout -q c3e47eee2e626500017a0556b470d6d4182f85e8
  # tudo na CPU
  grep -rl '"cuda"' "$D/core" "$D/inference.py" | xargs sed -i 's/"cuda"/"cpu"/g'
  sed -i "s/device='cuda'/device='cpu'/" "$D/core/models/modules/LMDM.py"
  # float16 na CPU dá NaN (o rosto saía branco): na CPU roda em float32
  sed -i 's/dtype=torch.float16, enabled=True/dtype=torch.float16, enabled=self.device.startswith("cuda")/' \
    "$D"/core/models/*.py
  touch "$D/.pronto"
fi

if ! python -c "import mediapipe, onnxruntime, librosa" 2>/dev/null; then
  pip install -q torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
  pip install -q "numpy<2" librosa tqdm filetype imageio imageio-ffmpeg opencv-python-headless scikit-image \
    cython einops onnxruntime==1.20.1 mediapipe==0.10.14 scipy huggingface_hub
fi

CFG="$D/checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl"
if [ ! -f "$D/checkpoints/.cpu" ]; then
  python - "$D" <<'PY'
import pickle, sys
from huggingface_hub import snapshot_download
d = sys.argv[1]
snapshot_download("digital-avatar/ditto-talkinghead", local_dir=f"{d}/checkpoints",
                  allow_patterns=["ditto_pytorch/*", "ditto_pytorch/**", "ditto_cfg/*"])
# a configuração do modelo também pede "cuda": troca por "cpu"
p = f"{d}/checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl"
def cpu(x):
    if isinstance(x, dict): return {k: cpu(v) for k, v in x.items()}
    if isinstance(x, list): return [cpu(v) for v in x]
    if isinstance(x, tuple): return tuple(cpu(v) for v in x)
    return "cpu" if isinstance(x, str) and x.startswith("cuda") else x
pickle.dump(cpu(pickle.load(open(p, "rb"))), open(p, "wb"))
PY
  touch "$D/checkpoints/.cpu"
fi

if [ $# -ge 3 ]; then
  AUDIO=$(realpath "$1"); IMG=$(realpath "$2"); SAIDA=$(realpath -m "$3")
  mkdir -p "$(dirname "$SAIDA")"
  T0=$(date +%s)
  (cd "$D" && python inference.py --data_root ./checkpoints/ditto_pytorch --cfg_pkl "./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl" \
     --audio_path "$AUDIO" --source_path "$IMG" --output_path "$SAIDA" 2>&1 | grep -v Warning | tail -5)
  rm -f "$SAIDA.tmp.mp4"
  echo "[ditto] $SAIDA em $(( $(date +%s) - T0 )) s"
fi
