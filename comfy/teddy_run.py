"""Roda a cena do Teddy Vlog dentro de uma máquina que já tem o ComfyUI instalado (Lightning AI, PC, etc.).

Usa só workflows do ComfyUI: Qwen-Image 2512 (imagem inicial) e LongCat-Video-Avatar 1.5 pelo
ComfyUI-WanVideoWrapper (fala com corpo, cabeça e mãos se mexendo). O ComfyArt fica instalado no mesmo ComfyUI.

  python comfy/teddy_run.py chave  --prompt p.txt --negativo n.txt --saida out/
  python comfy/teddy_run.py video  --imagem cena.png --audio voz.wav --prompt p.txt --saida out/
Variáveis: COMFY_DIR (pasta do ComfyUI), LONGCAT_MODELO, LONGCAT_LORA, UMT5.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

COMFY = os.environ.get("COMFY_DIR", str(Path.home() / "comfy"))
os.makedirs("/tmp/in", exist_ok=True)
os.makedirs("/tmp/out", exist_ok=True)

# ---------------------------------------------------------------- ComfyUI headless

def _subir_comfy():
    log = open("/tmp/comfy.log", "w")
    p = subprocess.Popen(
        [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch",
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




def chave(prompt, negativo, saida, largura=1280, altura=720, sementes=(11, 22, 33, 44)):
    _subir_comfy()
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
        for a in _saidas(_rodar(p, f"chave {s}")):
            shutil.copy(a, Path(saida) / f"chave-{s}.png")


def video(imagem, audio, prompt, saida, largura=1280, altura=720):
    shutil.copy(imagem, "/tmp/in/teddy.png")
    shutil.copy(audio, "/tmp/in/teddy.wav")
    _subir_comfy()
    info = _get("/object_info")
    ui = json.loads(Path(__file__).with_name("longcat_avatar_ui.json").read_text())
    api = ui_para_api(ui, info)

    def por_tipo(t):
        return [k for k, v in api.items() if v["class_type"] == t]

    for k in por_tipo("LoadImage"):
        api[k]["inputs"]["image"] = "teddy.png"
    for k in por_tipo("LoadAudio"):
        api[k]["inputs"]["audio"] = "teddy.wav"
    api["245"]["inputs"]["value"] = largura
    api["246"]["inputs"]["value"] = altura
    api["241"]["inputs"]["positive_prompt"] = prompt
    api["241"]["inputs"]["model_name"] = os.environ.get("UMT5", "umt5-xxl-enc-bf16.safetensors")
    for k in por_tipo("WanVideoModelLoader"):
        api[k]["inputs"]["model"] = os.environ.get("LONGCAT_MODELO", "LongCat/LongCat-Avatar_bf16.safetensors")
        api[k]["inputs"]["attention_mode"] = "sdpa"
        if "fp8" in api[k]["inputs"]["model"]:
            api[k]["inputs"]["quantization"] = "fp8_e4m3fn_scaled"
    for k in por_tipo("WanVideoLoraSelect"):
        api[k]["inputs"]["lora"] = os.environ.get("LONGCAT_LORA", "LongCat_distill_lora_alpha64_bf16.safetensors")
    # voz limpa de TTS: pula o separador de vocal; wav2vec local
    api["194"]["inputs"]["audio_1"] = ["317", 0]
    api["194"]["inputs"]["wav2vec_model"] = ["300", 0]
    for k in ("301", "302", "137"):
        api.pop(k, None)
    for k in por_tipo("VHS_VideoCombine"):
        api[k]["inputs"]["save_output"] = True
        api[k]["inputs"]["filename_prefix"] = f"teddy-{k}"
    for a in _saidas(_rodar(api, "longcat")):
        if a.suffix == ".mp4":
            shutil.copy(a, Path(saida) / a.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["chave", "video"])
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--negativo", default="")
    ap.add_argument("--imagem", default="")
    ap.add_argument("--audio", default="")
    ap.add_argument("--saida", default="saida")
    a = ap.parse_args()
    Path(a.saida).mkdir(parents=True, exist_ok=True)
    texto = Path(a.prompt).read_text(encoding="utf-8").strip()
    if a.modo == "chave":
        neg = Path(a.negativo).read_text(encoding="utf-8").strip() if a.negativo else ""
        chave(texto, neg, a.saida)
    else:
        video(a.imagem, a.audio, texto, a.saida)
    print("[saida]", sorted(os.listdir(a.saida)))
