"""Legendas SRT em inglês e capítulos do YouTube a partir de linha.json do vídeo 2.
Uso: python textos.py linha.json saida.srt capitulos.txt [desloc_s=0 para a versão com quadros de thumbnail: ver --insercoes]
--insercoes t1,t2,t3:dur  desloca tudo que vem depois de cada inserção (versão com thumbnails)
"""
import json, re, sys
L = json.load(open(sys.argv[1]))
ins, dins = [], 0.0
for a in sys.argv[4:]:
    if a.startswith("--insercoes="):
        v, dins = a.split("=", 1)[1].split(":"); dins = float(dins); ins = [float(x) for x in v.split(",")]
desl = lambda t: t + dins * sum(1 for x in ins if x <= t)

def hms(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def quebra(txt, n=42):
    ws, linhas, cur = txt.split(), [], ""
    for w in ws:
        if len(cur) + len(w) + 1 > n and cur: linhas.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    linhas.append(cur); return linhas

cues = []
for lg in L["legendas"]:
    ini, fim, txt = lg["ini"], lg["fim"], lg["txt"]
    # divide em frases e depois em blocos de até 2 linhas de 42 caracteres, tempo proporcional ao número de letras
    partes = []
    for fr in re.split(r"(?<=[.?!])\s+", txt):
        ls = quebra(fr)
        for i in range(0, len(ls), 2): partes.append("\n".join(ls[i:i + 2]))
    tot = sum(len(p) for p in partes); t = ini
    for p in partes:
        d = (fim - ini) * len(p) / tot
        cues.append((t, t + d, p)); t += d
with open(sys.argv[2], "w") as f:
    for i, (a, b, p) in enumerate(cues, 1):
        f.write(f"{i}\n{hms(desl(a))} --> {hms(desl(b) - 0.02)}\n{p}\n\n")

# capítulos: começo do vídeo, cada painel novo de ajuste e os cartões principais
NOMES = {"Gmail on your iPhone?": "The Gmail switch most people never see", "1 switch + 4 more settings": "What we will change today", "The three lines = Menu": "Where Gmail hides its settings",
         "Printable guide": "Point your camera here (printable guide)", "The Phone Security Guide": "The Phone Security Guide",
         "Today's Gmail checkup": "Today's Gmail checkup"}
caps, vistos = [], set()
for a in L["acoes"]:
    p = a.get("p")
    if not p or p in vistos: continue
    vistos.add(p)
    nome = NOMES.get(p) or p.replace("  ", " ").replace("→", "—").replace("#", "#")
    if p.startswith("+ 2-Step"): nome = "Turn on 2-Step Verification"
    if p.startswith("Bonus"): nome = "Bonus: 3 checks for a fake email"
    t = 0 if not caps else desl(a["t"])
    caps.append((t, nome))
with open(sys.argv[3], "w") as f:
    for t, n in caps: f.write(f"{int(t // 60)}:{int(t % 60):02d} {n}\n")
print(open(sys.argv[3]).read())
print(len(cues), "legendas")
