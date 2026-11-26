"""Monta a linha do tempo do vídeo do Walt a partir do roteiro e das falas (um wav por linha).

Saídas (na pasta de saída):
  narracao.wav      trilha de voz inteira, 48 kHz, com as pausas
  linha.json        {duracao, acoes:[{t,a,p}], walt:[{ini,fim,off}]}  (off = início da fala no áudio do Walt)
  walt-falas.wav    só as falas do Walt emendadas (entrada do LongCat)

Uso: python linha_do_tempo.py roteiro.txt pasta_wavs saida/ [alvo_s=600]
"""
import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf

rot, pasta, saida = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
ALVO = float(sys.argv[4]) if len(sys.argv) > 4 else 600.0
saida.mkdir(parents=True, exist_ok=True)
linhas = [l.strip() for l in Path(rot).read_text(encoding="utf-8").splitlines() if l.strip()]
SR = 48000

def tags(l):
    t = {}
    while True:
        m = re.match(r"^\[([^\]]*)\]\s*", l)
        if not m: break
        k = m.group(1)
        if k == "w": t["w"] = True
        elif ":" in k: a, b = k.split(":", 1); t[a.strip()] = b.strip()
        l = l[m.end():]
    return t, l

itens = []
for i, l in enumerate(linhas, 1):
    t, txt = tags(l)
    w, sr = sf.read(pasta / f"fala-{i:03d}.wav", dtype="float32")
    if w.ndim > 1: w = w.mean(1)
    if sr != SR:
        import librosa; w = librosa.resample(w, orig_sr=sr, target_sr=SR)
    itens.append(dict(i=i, tags=t, txt=txt, audio=w, dur=len(w) / SR))

# pausas: base + extra depois de toques na tela, cartões e do "I'll wait"
def pausa(it, prox):
    p = 0.30
    a = it["tags"].get("a", "")
    if a and not a.startswith(("card", "home")): p += 0.55
    if "I'll wait" in it["txt"]: p += 3.0
    if it["tags"].get("w") or (prox and prox["tags"].get("w")): p += 0.15
    if prox and prox["tags"].get("p"): p += 0.35  # respiro antes de um ajuste novo
    return p

pausas = [pausa(it, itens[k + 1] if k + 1 < len(itens) else None) for k, it in enumerate(itens)]
fala = sum(it["dur"] for it in itens)
total = fala + sum(pausas) + 1.5
# ajusta para o alvo: estica (ou encolhe) as pausas de toque na tela, que é onde a pessoa acompanha
if abs(total - ALVO) > 2:
    elast = [k for k, it in enumerate(itens) if it["tags"].get("a")] or list(range(len(itens)))
    delta = (ALVO - total) / len(elast)
    delta = max(delta, -0.35)
    for k in elast: pausas[k] = max(0.15, pausas[k] + min(delta, 2.5))
    total = fala + sum(pausas) + 1.5

trilha = np.zeros(int((total + 1) * SR), np.float32)
acoes, walt, walt_aud = [], [], []
t = 0.6; off = 0.0; resumo = None
for k, it in enumerate(itens):
    n = len(it["audio"]); s = int(t * SR)
    trilha[s:s + n] += it["audio"]
    tg = it["tags"]; d = it["dur"]
    if tg.get("w"):
        walt.append(dict(ini=round(t, 3), fim=round(t + d, 3), off=round(off, 3), linha=it["i"], txt=it["txt"]))
        walt_aud += [it["audio"], np.zeros(int(0.2 * SR), np.float32)]
        off += d + 0.2
    else:
        a = tg.get("a", "")
        if a.startswith("card summary"): resumo = 2
        elif resumo is not None and not a and not tg.get("p"):
            resumo += 2; acoes.append(dict(t=round(t + 0.1, 3), a=f"reveal {resumo}"))
        elif a: resumo = None
        cmd = a.split(" ")[0] if a else ""
        if cmd in ("go", "off", "on", "check", "tap", "back", "back3", "root"):
            ta = t + max(0.35, min(d * 0.55, d - 1.0))
        else:
            ta = t + 0.15
        if a or tg.get("p"):
            acoes.append(dict(t=round(ta, 3), a=a, p=tg.get("p")))
            if tg.get("p") and a and abs(ta - t) > 0.3:  # painel muda já no começo da linha
                acoes[-1]["p"] = None; acoes.insert(len(acoes) - 1, dict(t=round(t + 0.05, 3), a="", p=tg.get("p")))
    t += d + pausas[k]

dur = t + 0.9
trilha = trilha[: int(dur * SR)]
sf.write(saida / "narracao.wav", trilha, SR)
sf.write(saida / "walt-falas.wav", np.concatenate(walt_aud), SR)
acoes.sort(key=lambda x: x["t"])
json.dump(dict(duracao=round(dur, 3), acoes=acoes, walt=walt), open(saida / "linha.json", "w"), indent=1, ensure_ascii=False)
print(f"duração {dur/60:.2f} min | fala {fala:.0f}s | Walt {sum(w['fim']-w['ini'] for w in walt):.1f}s em {len(walt)} aparições | áudio do Walt {off:.1f}s")
