"""Legendas gravadas no vídeo: texto do roteiro, tempo de cada palavra tirado do áudio final (Whisper).
Uso: python legendas_ass.py audio_final.wav linha.json saida.ass [saida.srt]
Ficam à direita, embaixo (o celular ocupa a esquerda), grandes para quem tem mais de 60 anos."""
import json, re, sys, difflib
import librosa
from faster_whisper import WhisperModel
wav, lj, out_ass = sys.argv[1:4]; out_srt = sys.argv[4] if len(sys.argv) > 4 else None
L = json.load(open(lj))
y, _ = librosa.load(wav, sr=16000)
m = WhisperModel("base.en", device="cpu", compute_type="int8")
ww = [w for s in m.transcribe(y, beam_size=5, word_timestamps=True)[0] for w in s.words]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
hw = [norm(w.word) for w in ww]
# palavras do roteiro, cada uma com o trecho (legenda) de onde veio
sw, dono = [], []
for k, lg in enumerate(L["legendas"]):
    for p in lg["txt"].split(): sw.append(p); dono.append(k)
sm = difflib.SequenceMatcher(None, [norm(p) for p in sw], hw, autojunk=False)
ini = [None] * len(sw); fim = [None] * len(sw)
for a, b, n in sm.get_matching_blocks():
    for i in range(n): ini[a + i] = ww[b + i].start; fim[a + i] = ww[b + i].end
# palavras sem par (números escritos por extenso etc.): interpola dentro do trecho
for k, lg in enumerate(L["legendas"]):
    idx = [i for i, d in enumerate(dono) if d == k]
    for i in idx:
        if ini[i] is None or not (lg["ini"] - 0.6 <= ini[i] <= lg["fim"] + 0.6):
            j = idx.index(i); ini[i] = lg["ini"] + (lg["fim"] - lg["ini"]) * j / len(idx); fim[i] = ini[i] + 0.25
MAXC = 34
cues = []
for k, lg in enumerate(L["legendas"]):
    idx = [i for i, d in enumerate(dono) if d == k]
    bloco, linhas, cur = [], [], ""
    def fecha():
        global bloco, linhas, cur
        if cur: linhas.append(cur)
        if bloco: cues.append([ini[bloco[0]], fim[bloco[-1]] + 0.2, "\\N".join(linhas)])
        bloco, linhas, cur = [], [], ""
    for i in idx:
        p = sw[i]
        if cur and len(cur) + 1 + len(p) > MAXC:
            linhas.append(cur); cur = ""
            if len(linhas) == 2: cur_save = p; linhas_tmp = linhas; cur = ""; fecha()
        cur = (cur + " " + p).strip(); bloco.append(i)
        if p[-1] in ".?!" and len(" ".join(linhas) + cur) > 18: fecha()
    fecha()
for a, b in zip(cues, cues[1:]):
    a[1] = min(a[1], b[0] - 0.04)
def t(x):
    x = max(0, x); h = int(x // 3600); mm = int(x % 3600 // 60); s = x % 60
    return f"{h}:{mm:02d}:{s:05.2f}"
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 3840
PlayResY: 2160
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Walt,Inter,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,3,18,0,2,1640,420,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(out_ass, "w") as f:
    f.write(head)
    for a, b, txt in cues: f.write(f"Dialogue: 0,{t(a)},{t(b)},Walt,,0,0,0,,{txt}\n")
if out_srt:
    def ts(x):
        ms = int(round(max(0, x) * 1000)); h, ms = divmod(ms, 3600000); mi, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{mi:02d}:{s:02d},{ms:03d}"
    with open(out_srt, "w") as f:
        for n, (a, b, txt) in enumerate(cues, 1): f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{txt.replace(chr(92)+'N', chr(10))}\n\n")
print(len(cues), "legendas;", sum(1 for x in ini if x is not None), "palavras com tempo")
