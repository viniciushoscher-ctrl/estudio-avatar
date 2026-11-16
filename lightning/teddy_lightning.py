"""Roda a cena do Teddy Vlog no ComfyUI (+ ComfyArt) numa GPU grátis da Lightning AI (créditos do plano Free).

Precisa de LIGHTNING_USER_ID e LIGHTNING_API_KEY no ambiente (segredos do GitHub).
  python lightning/teddy_lightning.py chave   -> saida/chave-*.png  (4 opções de imagem inicial)
  python lightning/teddy_lightning.py video   -> saida/teddy-*.mp4  (cena falada de ~15 s)
A máquina é desligada no fim, sempre (para não gastar crédito parada).
"""
import os
import sys
import time
from pathlib import Path

from lightning_sdk import Machine, Studio

ETAPA = sys.argv[1] if len(sys.argv) > 1 else "video"
GPU = os.environ.get("LIGHTNING_GPU", "L40S")
RAIZ = Path(__file__).resolve().parent.parent
REMOTO = "teddy"  # pasta dentro do Studio (home persistente)

kw = {}
if os.environ.get("LIGHTNING_TEAMSPACE"):
    kw["teamspace"] = os.environ["LIGHTNING_TEAMSPACE"]
st = Studio("teddy-comfy", create_ok=True, **kw)
print("[studio]", st.name, "| teamspace:", st.teamspace.name, flush=True)


def sh(cmd):
    t = time.time()
    out, code = st.run_with_exit_code(cmd)
    print(out[-12000:], flush=True)
    print(f"[run] {code} em {time.time() - t:.0f} s: {cmd[:90]}", flush=True)
    if code != 0:
        raise SystemExit(f"falhou: {cmd}")
    return out


try:
    inter = os.environ.get("LIGHTNING_INTERRUPTIBLE", "1") == "1"
    try:
        st.start(getattr(Machine, GPU), interruptible=inter)
    except Exception as e:
        print("[aviso] sem máquina interruptível, tentando normal:", e, flush=True)
        st.start(getattr(Machine, GPU), interruptible=False)
    print("[máquina]", st.machine, flush=True)
    sh(f"mkdir -p {REMOTO}/comfy {REMOTO}/teddy {REMOTO}/saida && rm -f {REMOTO}/saida/* && nvidia-smi --query-gpu=name,memory.total --format=csv && free -g | head -2")
    for f in ["comfy/teddy_run.py", "comfy/longcat_avatar_ui.json", "comfy/setup_lightning.sh",
              "teddy/cena01-chave.txt", "teddy/cena01-negativo.txt", "teddy/cena01-longcat.txt",
              "teddy/cena01.wav", "teddy/cena01.png"]:
        if (RAIZ / f).exists():
            st.upload_file(str(RAIZ / f), f"{REMOTO}/{f}", progress_bar=False)
    sh(f"bash {REMOTO}/comfy/setup_lightning.sh {ETAPA} 2>&1 | tail -40")
    if ETAPA == "chave":
        sh(f"cd {REMOTO} && python comfy/teddy_run.py chave --prompt teddy/cena01-chave.txt "
           f"--negativo teddy/cena01-negativo.txt --saida saida 2>&1 | tail -60")
    else:
        sh(f"cd {REMOTO} && python comfy/teddy_run.py video --imagem teddy/cena01.png --audio teddy/cena01.wav "
           f"--prompt teddy/cena01-longcat.txt --saida saida 2>&1 | tail -80")
    lista = sh(f"ls {REMOTO}/saida").split()
    Path("saida").mkdir(exist_ok=True)
    for nome in lista:
        if nome.endswith((".png", ".mp4")):
            st.download_file(f"{REMOTO}/saida/{nome}", f"saida/{nome}")
            print("[baixado]", nome, flush=True)
finally:
    try:
        st.stop()
        print("[máquina desligada]", flush=True)
    except Exception as e:
        print("[aviso] stop:", e)
