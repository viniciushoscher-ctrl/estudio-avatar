"""B-roll em VÍDEO (filmagens reais, até 4K) do Pexels para cada linha [broll: ...] do roteiro.

Licença Pexels: uso comercial grátis, sem atribuição obrigatória. Precisa da chave grátis em
PEXELS_API_KEY (pexels.com/api). Sem chave ou sem resultado, a linha fica com a imagem de IA.

Marca no roteiro:  [broll: descrição longa da imagem | busca curta em inglês]
Sem "|", a busca é tirada do começo da descrição.

Saída: broll/linha-NNN-1.mp4, linha-NNN-2.mp4 ... (clipes suficientes para cobrir a fala da linha)
Uso: python motor/broll_videos.py roteiro.txt tempos.json broll/
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from montar import FPS, trechos  # noqa: E402

API = "https://api.pexels.com/videos/search"
TIRAR = {"photorealistic", "documentary", "photo", "close", "up", "soft", "light", "natural", "warm", "morning",
         "evening", "seen", "from", "above", "top", "view", "the", "a", "an", "of", "on", "in", "with", "and",
         "at", "into", "his", "her", "their", "small", "nobody", "frame", "still", "life", "portrait", "behind"}


def busca(marca):
    if "|" in marca:
        return marca.split("|", 1)[1].strip()
    base = marca.split(",")[0].lower()
    palavras = [p for p in re.findall(r"[a-z]+", base) if p not in TIRAR]
    q = " ".join(palavras[:5])
    return q if "japan" in q else f"japan {q}".strip()


def pexels(q, chave, pagina=1):
    url = API + "?" + urllib.parse.urlencode({"query": q, "orientation": "landscape", "size": "large",
                                              "per_page": 20, "page": pagina})
    req = urllib.request.Request(url, headers={"Authorization": chave, "User-Agent": "estudio-avatar"})
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("videos", [])
        except Exception as e:  # limite de requisições ou rede: espera e tenta de novo
            print(f"[pexels] {q}: {e}", flush=True)
            time.sleep(5 * (tentativa + 1))
    return []


def melhor_arquivo(video):
    """Maior resolução até 4K, em mp4."""
    arqs = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")]
    arqs = [f for f in arqs if f["width"] <= 3840] or arqs
    return max(arqs, key=lambda f: f["width"] * f["height"], default=None)


def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "estudio-avatar"})
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)


def main(roteiro, tempos, saida):
    chave = os.environ.get("PEXELS_API_KEY", "").strip()
    if not chave:
        print("[pexels] sem PEXELS_API_KEY: b-roll fica com as imagens de IA")
        return
    linhas = [l for l in Path(roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]
    tempos = json.loads(Path(tempos).read_text())
    Path(saida).mkdir(parents=True, exist_ok=True)
    usados = set()
    for t in trechos(roteiro, tempos):
        if t["tipo"] not in ("broll", "split"):
            continue
        m = re.match(r"^\s*\[(?:broll|split)\s*:\s*([^\]]*)\]", linhas[t["linha"]], re.I)
        if not m:
            continue
        precisa = (t["q1"] - t["q0"]) / FPS + 0.5
        q = busca(m.group(1))
        videos = [v for v in pexels(q, chave) if v["id"] not in usados]
        # prefere clipes longos o bastante; senão junta vários
        videos.sort(key=lambda v: (v.get("duration", 0) < precisa, -(v.get("width", 0))))
        tem, k = 0.0, 0
        for v in videos:
            arq = melhor_arquivo(v)
            if not arq:
                continue
            k += 1
            destino = Path(saida, f"linha-{t['linha']:03d}-{k}.mp4")
            try:
                baixar(arq["link"], destino)
            except Exception as e:
                print(f"[pexels] falhou {v['id']}: {e}", flush=True)
                k -= 1
                continue
            usados.add(v["id"])
            tem += min(v.get("duration", 0), 8.0) if precisa > 8 else v.get("duration", 0)
            print(f"[pexels] linha {t['linha']:3d} '{q}' -> {v['id']} {arq['width']}x{arq['height']} "
                  f"{v.get('duration')}s", flush=True)
            if tem >= precisa:
                break
        if k == 0:
            print(f"[pexels] linha {t['linha']:3d} '{q}': nada encontrado, fica a imagem", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
