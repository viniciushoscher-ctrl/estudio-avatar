"""Teddy Vlog: cena falada do Theodore Roosevelt feita 100% no ComfyUI (+ ComfyArt), na GPU da Modal.

Tudo open source, rodando como workflows do ComfyUI (nada de script próprio de inferência):
  1. chave  -> imagem inicial da cena: Qwen-Image 2512 (nós nativos do ComfyUI), 4 opções.
  2. video  -> Teddy falando com corpo, cabeça e mãos se mexendo + boca sincronizada:
               LongCat-Video-Avatar 1.5 pelo ComfyUI-WanVideoWrapper (workflow oficial de exemplo do kijai,
               comfy/longcat_avatar_ui.json), 720p, janelas de 93 quadros estendidas até cobrir o áudio.
O ComfyArt (canvas + agente + MCP + Timeline Render) fica instalado no mesmo ComfyUI, como custom node.

Uso:
  modal run gpu/teddy_comfy.py --modo baixar
  modal run gpu/teddy_comfy.py --modo chave --prompt-arquivo teddy/cena01-chave.txt --saida teddy/saida
  modal run gpu/teddy_comfy.py --modo video --imagem teddy/cena01.png --audio teddy/cena01.wav \
      --prompt-arquivo teddy/cena01-longcat.txt --saida teddy/saida
"""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import modal

GPU = os.environ.get("AVATAR_GPU", "H100,A100-80GB").split(",")
COMFY = "/comfy"
MODELOS = "/modelos"

VERSOES = {  # commits fixados (16/nov/2026)
    "https://github.com/comfyanonymous/ComfyUI": "e9afbccc2669",
    "https://github.com/kijai/ComfyUI-WanVideoWrapper": "a7439db30bed",
    "https://github.com/kijai/ComfyUI-KJNodes": "70701d2a11d4",
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite": "4d907bee61e9",
    "https://github.com/jtydhr88/ComfyArt": "2a990a741fcb",
}

# (repo HF, arquivo no repo, destino dentro de models/)
PESOS = [
    ("Kijai/LongCat-Video_comfy", "Avatar/LongCat-Avatar_comfy_bf16.safetensors", "diffusion_models/LongCat/LongCat-Avatar_bf16.safetensors"),
    ("Kijai/LongCat-Video_comfy", "LongCat_distill_lora_alpha64_bf16.safetensors", "loras/LongCat_distill_lora_alpha64_bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "Wan2_1_VAE_bf16.safetensors", "vae/Wan2_1_VAE_bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "umt5-xxl-enc-bf16.safetensors", "text_encoders/umt5-xxl-enc-bf16.safetensors"),
    ("Kijai/wav2vec2_safetensors", "wav2vec2-chinese-base_fp16.safetensors", "wav2vec2/wav2vec2-chinese-base_fp16.safetensors"),
    ("Comfy-Org/Qwen-Image", "split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors", "diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors"),
    ("Comfy-Org/Qwen-Image", "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors", "text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"),
    ("Comfy-Org/Qwen-Image", "split_files/vae/qwen_image_vae.safetensors", "vae/qwen_image_vae.safetensors"),
]

app = modal.App("teddy-comfy")
vol = modal.Volume.from_name("comfy-modelos", create_if_missing=True)


def _clones():
    cmds = []
    for url, commit in VERSOES.items():
        nome = url.rsplit("/", 1)[1]
        dest = COMFY if nome == "ComfyUI" else f"{COMFY}/custom_nodes/{nome}"
        cmds.append(f"git clone -q {url} {dest} && cd {dest} && git checkout -q {commit}")
    return cmds


TORCH = "https://download.pytorch.org/whl/cu128"
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.8.0", "torchvision==0.23.0", "torchaudio==2.8.0", index_url=TORCH)
    .run_commands(*_clones())
    .run_commands(
        f"pip install -q -r {COMFY}/requirements.txt",
        f"for d in {COMFY}/custom_nodes/*/; do [ -f $d/requirements.txt ] && pip install -q -r $d/requirements.txt || true; done",
    )
    .pip_install("huggingface_hub[hf_transfer]>=0.27", "requests")
    .run_commands(
        f"printf 'modal:\\n  base_path: {MODELOS}\\n  diffusion_models: diffusion_models\\n  loras: loras\\n"
        f"  vae: vae\\n  text_encoders: text_encoders\\n  clip: text_encoders\\n  wav2vec2: wav2vec2\\n' "
        f"> {COMFY}/extra_model_paths.yaml"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
)


# ---------------------------------------------------------------- ComfyUI headless

def _subir_comfy():
    log = open("/tmp/comfy.log", "w")
    p = subprocess.Popen(
        ["python", "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch",
         "--output-directory", "/tmp/out", "--input-directory", "/tmp/in"],
        cwd=COMFY, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(600):
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
            print("[comfy] no ar", flush=True)
            return p
        except Exception:
            if p.poll() is not None:
                break
            time.sleep(1)
    print(open("/tmp/comfy.log").read()[-6000:])
    raise RuntimeError("ComfyUI não subiu")


def _get(caminho):
    return json.loads(urllib.request.urlopen("http://127.0.0.1:8188" + caminho, timeout=60).read())


def _rodar(prompt, rotulo):
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": prompt}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    except urllib.error.HTTPError as e:
        print(e.read().decode()[:8000])
        raise
    t = time.time()
    while True:
        h = _get(f"/history/{pid}")
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                print(json.dumps(st, indent=1)[:8000])
                print(open("/tmp/comfy.log").read()[-8000:])
                raise RuntimeError(f"{rotulo}: erro no ComfyUI")
            if st.get("completed"):
                print(f"[{rotulo}] pronto em {time.time() - t:.0f} s", flush=True)
                return h[pid]["outputs"]
        time.sleep(3)


VIRTUAIS = {"Note", "MarkdownNote", "PrimitiveNode", "PreviewAny"}
CONTROLES = {"fixed", "increment", "decrement", "randomize"}


def ui_para_api(ui, info):
    """Converte um workflow salvo pela interface (formato UI) no formato da API, resolvendo
    Reroute/SetNode/GetNode e casando widgets_values com os nomes vindos de /object_info."""
    nos = {n["id"]: n for n in ui["nodes"] if n.get("mode", 0) == 0}
    links = {l[0]: (l[1], l[2]) for l in ui["links"]}
    setters = {n["widgets_values"][0]: n for n in nos.values() if n["type"] == "SetNode"}

    def origem(link_id):
        nid, slot = links[link_id]
        n = nos[nid]
        if n["type"] == "Reroute":
            return origem(n["inputs"][0]["link"])
        if n["type"] == "GetNode":
            s = setters[n["widgets_values"][0]]
            return origem(s["inputs"][0]["link"])
        if n["type"] == "SetNode":
            return origem(n["inputs"][0]["link"])
        return (str(nid), slot)

    api = {}
    for nid, n in nos.items():
        tipo = n["type"]
        if tipo in VIRTUAIS or tipo in ("Reroute", "SetNode", "GetNode") or tipo not in info:
            if tipo not in info and tipo not in VIRTUAIS and tipo not in ("Reroute", "SetNode", "GetNode"):
                print(f"[aviso] nó sem definição: {tipo}")
            continue
        defs = info[tipo]["input"]
        ordem = list(defs.get("required", {}).items()) + list(defs.get("optional", {}).items())
        entradas = {}
        ligados = {i["name"]: i["link"] for i in n.get("inputs", []) if i.get("link") is not None}
        wv = n.get("widgets_values")
        if isinstance(wv, dict):
            for k, v in wv.items():
                if k != "videopreview":
                    entradas[k] = v
        else:
            wv = list(wv or [])
            i = 0
            for nome, spec in ordem:
                t = spec[0]
                eh_widget = isinstance(t, list) or t in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO")
                if not eh_widget:
                    continue
                if i < len(wv):
                    entradas[nome] = wv[i]
                    i += 1
                    if t == "INT" and i < len(wv) and wv[i] in CONTROLES:
                        i += 1
        for nome, lid in ligados.items():
            if lid in links and links[lid][0] in nos:
                entradas[nome] = list(origem(lid))
        api[str(nid)] = {"class_type": tipo, "inputs": entradas}
    # remove saídas de prévia de nós que não existem mais
    return api


def _saidas(outputs, chave="gifs"):
    arqs = []
    for nid, o in outputs.items():
        for item in o.get(chave, []) + o.get("images", []):
            p = Path("/tmp/out") / item.get("subfolder", "") / item["filename"]
            if p.exists():
                arqs.append(p)
    return arqs


# ---------------------------------------------------------------- funções da Modal

@app.function(image=image, volumes={MODELOS: vol}, timeout=3600, cpu=4, memory=8192)
def baixar():
    from huggingface_hub import hf_hub_download
    for repo, arq, dest in PESOS:
        alvo = Path(MODELOS) / dest
        if alvo.exists():
            print("[ok]", dest)
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        t = time.time()
        p = hf_hub_download(repo, arq, local_dir="/tmp/hf")
        os.replace(p, alvo)
        print(f"[baixado] {dest} {alvo.stat().st_size / 1e9:.1f} GB em {time.time() - t:.0f} s", flush=True)
        vol.commit()
    vol.commit()


@app.function(image=image, volumes={MODELOS: vol}, gpu=GPU, timeout=3600)
def chave(prompt: str, negativo: str, largura: int = 1280, altura: int = 720, sementes=(11, 22, 33, 44)):
    os.makedirs("/tmp/in", exist_ok=True)
    _subir_comfy()
    res = {}
    for s in sementes:
        p = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2512_fp8_e4m3fn.safetensors", "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}},
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
            "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.1}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": negativo}},
            "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": largura, "height": altura, "batch_size": 1}},
            "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "seed": s, "steps": 40, "cfg": 4.0,
                                                        "sampler_name": "euler", "scheduler": "simple",
                                                        "positive": ["5", 0], "negative": ["6", 0],
                                                        "latent_image": ["7", 0], "denoise": 1.0}},
            "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
            "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": f"chave-{s}"}},
        }
        out = _rodar(p, f"chave {s}")
        for a in _saidas(out):
            res[f"chave-{s}.png"] = a.read_bytes()
    return res


@app.function(image=image, volumes={MODELOS: vol}, gpu=GPU, timeout=3600)
def video(img: bytes, wav: bytes, prompt: str, ui_json: str, largura: int = 1280, altura: int = 720):
    os.makedirs("/tmp/in", exist_ok=True)
    Path("/tmp/in/teddy.png").write_bytes(img)
    Path("/tmp/in/teddy.wav").write_bytes(wav)
    _subir_comfy()
    info = _get("/object_info")
    ui = json.loads(ui_json)
    api = ui_para_api(ui, info)

    def por_tipo(t):
        return [k for k, v in api.items() if v["class_type"] == t]

    # entradas da cena
    for k in por_tipo("LoadImage"):
        api[k]["inputs"]["image"] = "teddy.png"
    for k in por_tipo("LoadAudio"):
        api[k]["inputs"]["audio"] = "teddy.wav"
    api["245"]["inputs"]["value"] = largura
    api["246"]["inputs"]["value"] = altura
    api["241"]["inputs"]["positive_prompt"] = prompt
    for k in por_tipo("WanVideoModelLoader"):
        api[k]["inputs"]["model"] = "LongCat/LongCat-Avatar_bf16.safetensors"
        api[k]["inputs"]["attention_mode"] = "sdpa"
    for k in por_tipo("WanVideoLoraSelect"):
        api[k]["inputs"]["lora"] = "LongCat_distill_lora_alpha64_bf16.safetensors"
    # áudio já é voz limpa (TTS): pula o separador de vocal MelBandRoFormer
    api["194"]["inputs"]["audio_1"] = ["317", 0]
    for k in ("301", "302"):
        api.pop(k, None)
    # wav2vec local em vez de baixar na hora
    api["194"]["inputs"]["wav2vec_model"] = ["300", 0]
    api.pop("137", None)
    for k in por_tipo("VHS_VideoCombine"):
        api[k]["inputs"]["save_output"] = True
        api[k]["inputs"]["filename_prefix"] = f"teddy-{k}"
    print(json.dumps({k: v["class_type"] for k, v in api.items()}), flush=True)

    out = _rodar(api, "longcat")
    res = {}
    for a in _saidas(out):
        if a.suffix == ".mp4":
            res[a.name] = a.read_bytes()
    return res


@app.local_entrypoint()
def main(modo: str = "video", imagem: str = "", audio: str = "", prompt_arquivo: str = "",
         negativo_arquivo: str = "", saida: str = "teddy/saida"):
    Path(saida).mkdir(parents=True, exist_ok=True)
    if modo == "baixar":
        baixar.remote()
        return
    prompt = Path(prompt_arquivo).read_text(encoding="utf-8").strip()
    if modo == "chave":
        neg = Path(negativo_arquivo).read_text(encoding="utf-8").strip() if negativo_arquivo else ""
        res = chave.remote(prompt, neg)
    else:
        ui = Path(__file__).resolve().parent.parent.joinpath("comfy/longcat_avatar_ui.json").read_text()
        res = video.remote(Path(imagem).read_bytes(), Path(audio).read_bytes(), prompt, ui)
    for nome, dados in res.items():
        Path(saida, nome).write_bytes(dados)
        print("[salvo]", Path(saida, nome), len(dados) // 1024, "KB")
