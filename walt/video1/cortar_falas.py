"""Corta walt-falas.wav (falas do Walt emendadas, ver linha_do_tempo.py) em grupos de no máximo ~10 s.

O LongCat perde o rosto em clipes longos, então cada grupo vira um clipe separado que parte da foto.
Junta falas seguidas enquanto o grupo couber em MAX segundos; fala maior que MAX é partida no silêncio.
Uso: python cortar_falas.py pasta_linha/ pasta_saida/ prefixo
  (pasta_linha tem linha.json e walt-falas.wav; grava prefixo-gNN.wav e cortes.json)
"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf

MAX = 10.0
ent, sai, pref = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sai.mkdir(parents=True, exist_ok=True)
L = json.load(open(ent / "linha.json")); y, sr = sf.read(ent / "walt-falas.wav", dtype="float32")
if y.ndim > 1: y = y.mean(1)
tot = len(y) / sr
falas = [(w["off"], w["fim"] - w["ini"]) for w in L["walt"]]
# trechos [ini, fim] em walt-falas.wav, cada fala com seus 0,2 s de respiro
pedacos = []
for k, (o, d) in enumerate(falas):
    fim = falas[k + 1][0] if k + 1 < len(falas) else tot
    if fim - o <= MAX:
        pedacos.append([o, fim]); continue
    # fala longa: parte nos silêncios mais próximos de cada MAX
    seg = y[int(o * sr):int(fim * sr)]; hop = int(0.02 * sr)
    rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2)) for i in range(0, len(seg) - hop, hop)])
    ini = 0.0
    while (fim - o) - ini > MAX:
        a, b = int((ini + MAX * 0.55) / 0.02), int((ini + MAX) / 0.02)
        corte = (a + int(np.argmin(rms[a:b]))) * 0.02
        pedacos.append([o + ini, o + corte]); ini = corte
    pedacos.append([o + ini, fim])
grupos = []
for p in pedacos:
    if grupos and p[1] - grupos[-1][0] <= MAX: grupos[-1][1] = p[1]
    else: grupos.append(list(p))
for f in sai.glob(f"{pref}-g*.wav"): f.unlink()
for n, (s, e) in enumerate(grupos, 1):
    sf.write(sai / f"{pref}-g{n:02d}.wav", y[int(s * sr):int(e * sr)], sr)
json.dump({"grupos": [[round(s, 3), round(e, 3)] for s, e in grupos]}, open(sai / "cortes.json", "w"))
print(f"{len(grupos)} grupos, {tot:.1f} s de fala:", " ".join(f"{e - s:.1f}" for s, e in grupos))
