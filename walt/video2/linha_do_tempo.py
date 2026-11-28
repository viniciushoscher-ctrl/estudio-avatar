"""Linha do tempo do vídeo 2 do Walt: narração (voz 3, um wav por linha de narracao.txt) + falas do clipe HeyGen.

roteiro.txt: linhas "[w: ID]" são falas do Walt na tela, tiradas do clipe (clipe.json); as outras são narração.
Tags: [a: ação do palco] [p: painel] [pausa: s] (pausa extra antes da linha) [qr] (Walt + QR na tela) [end].
Saídas: narracao.wav (trilha inteira 48 kHz), linha.json {duracao, acoes, walt:[{ini,fim,src,id,qr}], legendas}.
Uso: python linha_do_tempo.py roteiro.txt pasta_wavs clipe.wav saida/ [gancho.wav]
"[w: GANCHO]" = gancho do Walt para a câmera: o áudio é o próprio gancho.wav (o mesmo enviado ao HeyGen),
o vídeo vem do clipe do gancho renderizado no HeyGen (montar.py alinha pelo áudio).
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, soundfile as sf

rot, pasta, clipe_wav, saida = sys.argv[1], Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
saida.mkdir(parents=True, exist_ok=True)
SR = 48000
CL = json.load(open(Path(__file__).with_name("clipe.json")))["falas"]
cw, csr = sf.read(clipe_wav, dtype="float32")
if cw.ndim > 1: cw = cw.mean(1)
assert csr == SR
GANHO_CLIPE = 10 ** (3.2 / 20)  # clipe com EQ (clip-eq) medido no mesmo LUFS da narração

def tags(l):
    t = {}
    while True:
        m = re.match(r"^\[([^\]]*)\]\s*", l)
        if not m: break
        k = m.group(1)
        if ":" in k: a, b = k.split(":", 1); t[a.strip()] = b.strip()
        else: t[k.strip()] = True
        l = l[m.end():]
    return t, l

TMP = Path(tempfile.mkdtemp()); MAX_PPM = 172
# numeração dos wavs = posição da linha em narracao.txt (o que foi narrado); o roteiro pode omitir linhas
NARR = [tags(l.strip())[1] for l in Path(rot).with_name("narracao.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
itens = []
for l in [l.strip() for l in Path(rot).read_text(encoding="utf-8").splitlines() if l.strip()]:
    t, txt = tags(l)
    if t.get("w") == "GANCHO":
        g, gsr = sf.read(sys.argv[5], dtype="float32")
        if g.ndim > 1: g = g.mean(1)
        if gsr != SR:
            import librosa; g = librosa.resample(g, orig_sr=gsr, target_sr=SR)
        txt = " ".join(l.strip() for l in Path(rot).with_name("gancho.txt").read_text(encoding="utf-8").splitlines() if l.strip())
        itens.append(dict(tags=t, txt=txt, audio=g, dur=len(g) / SR, walt=dict(id="GANCHO", src=0.0)))
        continue
    if "w" in t:
        a, b = CL[t["w"]]; a -= 0.12; b += 0.25
        w = cw[int(a * SR): int(b * SR)] * GANHO_CLIPE
        itens.append(dict(tags=t, txt=txt, audio=w, dur=len(w) / SR, walt=dict(id=t["w"], src=round(a, 3))))
        continue
    k = NARR.index(txt) + 1; arq = pasta / f"fala-{k:03d}.wav"
    d0 = sf.info(arq).duration - 0.57
    ppm = len(txt.split()) / max(d0, 0.5) * 60
    if ppm > MAX_PPM:
        novo = TMP / arq.name
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(arq), "-af",
                        f"rubberband=tempo={max(0.82, MAX_PPM / ppm):.4f}:formant=preserved:pitchq=quality:window=standard", str(novo)], check=True)
        arq = novo
    w, sr = sf.read(arq, dtype="float32")
    if w.ndim > 1: w = w.mean(1)
    if sr != SR:
        import librosa; w = librosa.resample(w, orig_sr=sr, target_sr=SR)
    itens.append(dict(tags=t, txt=txt, audio=w, dur=len(w) / SR))

def pausa(it, prox):
    p = 0.30
    a = it["tags"].get("a", "")
    if a and not a.startswith(("card", "home", "reveal")): p += 0.55
    if "w" in it["tags"] or (prox and "w" in prox["tags"]): p += 0.25
    if prox and prox["tags"].get("p"): p += 0.35
    if prox and prox["tags"].get("pausa"): p += float(prox["tags"]["pausa"])
    return p

trilha = np.zeros(int(1200 * SR), np.float32)
acoes, walt, legendas = [], [], []
t = 0.0 if itens[0]["tags"].get("w") == "GANCHO" else 0.6
for n, it in enumerate(itens):
    prox = itens[n + 1] if n + 1 < len(itens) else None
    s = int(t * SR); trilha[s:s + len(it["audio"])] += it["audio"]
    tg, d = it["tags"], it["dur"]
    # legenda: só a parte com fala (wav da narração tem 0,25 s de silêncio em cada ponta)
    m = 0.12 if "w" in tg else 0.25
    legendas.append(dict(ini=round(t + m, 3), fim=round(t + d - m, 3), txt=it["txt"]))
    if "w" in tg:
        walt.append(dict(ini=round(t, 3), fim=round(t + d, 3), src=it["walt"]["src"], id=it["walt"]["id"], qr=bool(tg.get("qr"))))
    a = tg.get("a", "")
    cmd = a.split(" ")[0] if a else ""
    if cmd in ("go", "off", "on", "check", "tap", "back", "back2", "root", "menu", "close"):
        ta = t + max(0.35, min(d * 0.55, d - 1.0))
    else:
        ta = t + 0.15
    if a or tg.get("p"):
        acoes.append(dict(t=round(ta, 3), a=a, p=tg.get("p"), d=round(d, 2)))
        if tg.get("p") and a and abs(ta - t) > 0.3:
            acoes[-1]["p"] = None; acoes.insert(len(acoes) - 1, dict(t=round(t + 0.05, 3), a="", p=tg.get("p")))
    t += d + pausa(it, prox)
    if tg.get("end"):
        acoes.append(dict(t=round(t - 0.2, 3), a="card end", p=None)); t += 7.0

dur = t + 0.5
trilha = trilha[: int(dur * SR)]
pico = np.abs(trilha).max()
if pico > 0.98: trilha *= 0.98 / pico
sf.write(saida / "narracao.wav", trilha, SR)
acoes.sort(key=lambda x: x["t"])
json.dump(dict(duracao=round(dur, 3), acoes=acoes, walt=walt, legendas=legendas), open(saida / "linha.json", "w"), indent=1, ensure_ascii=False)
print(f"duração {dur // 60:.0f}:{dur % 60:04.1f} | Walt {sum(w['fim'] - w['ini'] for w in walt):.1f}s em {len(walt)} falas")
for w in walt: print(f"  {w['id']} {w['ini'] // 60:.0f}:{w['ini'] % 60:05.2f}{' + QR' if w['qr'] else ''}")
