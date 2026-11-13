"""B-roll em VÍDEO (filmagens reais) para cada linha [broll: ...] do roteiro, sem custo e sem chave.

Fontes (todas com licença de uso comercial grátis, inclusive YouTube, sem atribuição obrigatória):
- Coverr (coverr.co): até 1080p, sem chave
- Mixkit (mixkit.co): 720p grátis, sem chave
- Pexels (até 4K), só se houver PEXELS_API_KEY
Sem resultado bom, a linha fica com a imagem de IA.

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


UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) estudio-avatar"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"[broll] {url}: {e}", flush=True)
            time.sleep(3 * (tentativa + 1))
    return ""


def coverr(q):
    html = _get("https://coverr.co/s?" + urllib.parse.urlencode({"q": q}))
    slugs = dict.fromkeys(re.findall(r"cdn\.coverr\.co/videos/([a-z0-9-]+)/", html))
    return [{"id": "c:" + s, "url": f"https://cdn.coverr.co/videos/{s}/1080p.mp4", "palavras": set(s.split("-")),
             "largura": 1920} for s in slugs]


def mixkit(q):
    """Mixkit só busca por etiqueta (uma ou duas palavras): tenta a busca inteira e cada palavra."""
    termos = re.findall(r"[a-z]+", q.lower())
    etiquetas = ["-".join(termos)] + ([f"{termos[i]}-{termos[i + 1]}" for i in range(len(termos) - 1)]) + termos
    out = []
    for e in dict.fromkeys(etiquetas):
        html = _get(f"https://mixkit.co/free-stock-video/{e}/")
        for s_, i in dict.fromkeys(re.findall(r'"/free-stock-video/([a-z0-9-]+)-(\d+)/"', html)):
            out.append({"id": "m:" + i, "url": f"https://assets.mixkit.co/videos/{i}/{i}-720.mp4",
                        "palavras": set(s_.split("-")), "largura": 1280})
        if len(out) >= 20:
            break
    return out


def pexels_cands(q, chave):
    out = []
    for v in pexels(q, chave):
        arq = melhor_arquivo(v)
        if arq:
            out.append({"id": f"p:{v['id']}", "url": arq["link"], "largura": arq["width"],
                        "palavras": set(re.findall(r"[a-z]+", (v.get("url") or "").lower()))})
    return out


def acertos(c, termos):
    p = c["palavras"]
    return sum(1 for t in termos if t in p or t.rstrip("s") in p)


def nota(c, termos):
    """Quantas palavras da busca aparecem no nome do vídeo (+1 se for do Japão/Ásia)."""
    p = c["palavras"]
    acerto = sum(1 for t in termos if t in p or t.rstrip("s") in p)
    return acerto + (1 if p & {"japan", "japanese", "tokyo", "kyoto", "asian", "okinawa"} else 0) \
        + c["largura"] / 10000


JAPAO = {"japan", "japanese", "tokyo", "kyoto", "osaka", "okinawa", "okinawan", "asian", "asia", "kimono", "geisha"}
PESSOAS = {"man", "men", "woman", "women", "people", "person", "family", "couple", "grandmother", "grandfather",
           "grandma", "grandpa", "seniors", "senior", "elderly", "friends", "child", "children", "hands", "hand",
           "fisherman", "gardener", "mother", "father", "group", "girl", "boy", "chef", "cook"}


def precisa_japao(marca):
    """Cena com gente descrita como japonesa: o clipe tem que ser de pessoa asiática (nada de jantar americano)."""
    p = set(re.findall(r"[a-z]+", marca.lower()))
    return bool(p & JAPAO) and bool(p & PESSOAS)


def candidatos(q, chave, marca=""):
    termos = [t for t in re.findall(r"[a-z]+", q.lower()) if t not in ("japan", "japanese")]
    cands = []
    buscas = [q] + ([" ".join(termos)] if termos else []) + ([termos[-1]] if len(termos) > 1 else [])
    for b in dict.fromkeys(buscas):
        if chave:
            cands += pexels_cands(b, chave)
        cands += coverr(b) + mixkit(b)
        if sum(1 for c in cands if nota(c, termos) >= 1) >= 3:
            break
    vistos, unicos = set(), []
    for c in cands:
        if c["id"] not in vistos:
            vistos.add(c["id"])
            unicos.append(c)
    # busca curta (até 3 palavras): todas têm que estar no nome do clipe ("green tea field" não aceita
    # "green cabbage field"); busca maior: falta no máximo 1, e o 1º termo é obrigatório
    minimo = len(termos) if len(termos) <= 3 else len(termos) - 1
    primeiro = termos[0] if termos else ""
    unicos = [c for c in unicos if not termos or (acertos(c, termos) >= minimo and acertos(c, [primeiro]))]
    if precisa_japao(marca + " " + q):
        unicos = [c for c in unicos if c["palavras"] & JAPAO]
    return sorted(unicos, key=lambda c: -nota(c, termos))


def duracao_arquivo(p):
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout)
    except ValueError:
        return 0.0


def main(roteiro, tempos, saida):
    chave = os.environ.get("PEXELS_API_KEY", "").strip()
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
        precisa = (t["q1"] - t["q0"]) / 25 + 0.5
        q = busca(m.group(1))
        tem, k = 0.0, 0
        for c in candidatos(q, chave, m.group(1)):
            if c["id"] in usados:
                continue
            destino = Path(saida, f"linha-{t['linha']:03d}-{k + 1}.mp4")
            try:
                baixar(c["url"], destino)
            except Exception as e:
                print(f"[broll] falhou {c['id']}: {e}", flush=True)
                continue
            d = duracao_arquivo(destino)
            if d < 1:
                destino.unlink(missing_ok=True)
                continue
            k += 1
            usados.add(c["id"])
            tem += min(d - 0.4, 8.0)
            print(f"[broll] linha {t['linha']:3d} '{q}' -> {c['id']} ({c['largura']}p, {d:.1f}s)", flush=True)
            if tem >= precisa or k >= 4:
                break
        if k == 0:
            print(f"[broll] linha {t['linha']:3d} '{q}': nada bom, fica a imagem de IA", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
