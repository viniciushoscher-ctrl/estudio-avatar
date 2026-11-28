"""Montagem do vídeo 2 do Walt em 4K, por pedaços (pouca memória), com o logo do canal no canto inferior direito.

Entradas (pasta de trabalho): linha.json, narracao.wav, palco.mp4 (telas 3840x2160, 30 fps) e o clipe HeyGen (720p).
Cada fala do Walt é o trecho [src, src+dur] do clipe colocado em [ini, fim]. Falas com "qr": cartão do QR em tela
cheia e o Walt num quadro à direita (ele fala do código que está na tela). Entre as falas entra o palco.
Fala "GANCHO": vem do clipe do gancho (HeyGen, renderizado com o gancho.wav), alinhado pelo áudio.
Sem esse clipe a montagem para: o gancho nunca vira foto parada.
Uso: python montar.py pasta clipe.mp4 saida.mp4 [gancho.mp4]
"""
import json, subprocess, sys
from pathlib import Path

d = Path(sys.argv[1]); clipe = sys.argv[2]; out = sys.argv[3]
AQUI = Path(__file__).parent
L = json.load(open(d / "linha.json"))
FPS = 30
q = lambda t: round(t * FPS) / FPS
tmp = d / "pedacos"; tmp.mkdir(exist_ok=True)
LOGO = str(AQUI / "logo-canal.png")
QR = str(AQUI.parent / "telas" / "qr-card-4k.png")
ENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-profile:v", "high", "-video_track_timescale", "15360"]
UP = "scale=3840:2160:flags=lanczos,unsharp=5:5:0.6:5:5:0.0,setsar=1"
# logo: 75% do tamanho do PNG, 70 px da borda direita e 56 px de baixo
LOGO_F = "[1:v]scale=iw*0.75:-1:flags=lanczos[lg];[v][lg]overlay=W-w-70:H-h-56:format=auto,format=yuv420p"

GANCHO = next((a for a in sys.argv[4:] if not a.startswith("--")), None)

def atraso_gancho(mp4, wav):
    """Onde o áudio do gancho.wav começa dentro do clipe do HeyGen (correlação cruzada)."""
    import numpy as np, soundfile as sf, tempfile
    tmpw = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-ac", "1", "-ar", "8000", tmpw], check=True)
    a, _ = sf.read(tmpw, dtype="float32")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ac", "1", "-ar", "8000", tmpw], check=True)
    b, _ = sf.read(tmpw, dtype="float32")
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    k = int(np.argmax(c[: len(a)])); return k / 8000

pecas, t = [], 0.0
total = q(L["duracao"])
for w in L["walt"]:
    ini, fim = q(w["ini"]), q(w["fim"])
    if ini > t:
        if pecas and pecas[-1][0] in ("walt", "gancho") and ini - t < 1.2:
            # pausa curta entre duas falas do Walt: o Walt continua na tela (sem piscar o iPhone)
            tp, i0, d0, s0, q0 = pecas[-1]; pecas[-1] = (tp, i0, d0 + ini - t, s0, q0)
        else:
            pecas.append(("palco", t, ini - t, None, False))
    if w["id"] == "GANCHO":
        SEM = "--sem-gancho" in sys.argv  # prepara todos os outros pedaços enquanto o clipe do HeyGen não chega
        assert GANCHO or SEM, "falta o clipe do gancho do HeyGen (não usar foto parada)"
        off = atraso_gancho(GANCHO, str(d / "gancho.wav")) if GANCHO else 0.0
        if GANCHO: print(f"gancho: áudio começa em {off:.3f}s do clipe")
        pecas.append(("gancho", ini, fim - ini, off, False))
    else:
        pecas.append(("walt", ini, fim - ini, w["src"], w.get("qr", False)))
    t = fim
if t < total: pecas.append(("palco", t, total - t, None, False))

lista = []
for k, (tipo, ini, dur, src, qr) in enumerate(pecas):
    f = tmp / f"{k:03d}.mp4"; lista.append(f)
    if f.exists() and f.stat().st_size > 1000 and "--refazer" not in sys.argv:
        continue
    n = round(dur * FPS)
    if tipo == "gancho" and not GANCHO:
        print("gancho: pedaço pulado (sem o clipe do HeyGen)"); continue
    if tipo == "palco":
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{ini:.4f}", "-i", str(d / "palco.mp4"), "-i", LOGO,
               "-filter_complex", f"[0:v]fps={FPS},setsar=1[v];{LOGO_F}", "-frames:v", str(n)] + ENC + [str(f)]
    elif tipo == "gancho":
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{src:.4f}", "-i", GANCHO, "-i", LOGO, "-filter_complex",
               f"[0:v]scale=3840:2160:force_original_aspect_ratio=increase:flags=lanczos,crop=3840:2160,"
               f"unsharp=5:5:0.6:5:5:0.0,setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=1[v];{LOGO_F}",
               "-frames:v", str(n)] + ENC + [str(f)]
    elif not qr:
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{src:.4f}", "-i", clipe, "-i", LOGO,
               "-filter_complex", f"[0:v]{UP},fps={FPS},tpad=stop_mode=clone:stop_duration=1[v];{LOGO_F}",
               "-frames:v", str(n)] + ENC + [str(f)]
    else:
        # QR à esquerda (como no cartão), Walt num quadro com borda creme sobre a parte de baixo do texto
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", QR, "-i", LOGO,
               "-ss", f"{src:.4f}", "-i", clipe, "-filter_complex",
               f"[2:v]scale=1600:900:flags=lanczos,unsharp=5:5:0.5:5:5:0.0,pad=1624:924:12:12:color=0xF6F0E4,fps={FPS},"
               f"tpad=stop_mode=clone:stop_duration=1[w];[0:v]scale=3840:2160,setsar=1[bg];[bg][w]overlay=2140:1150[v];{LOGO_F}",
               "-frames:v", str(n)] + ENC + [str(f)]
    subprocess.run(cmd, check=True)
    print(f"{k:02d} {tipo}{' +QR' if qr else ''} {ini:7.2f} +{dur:5.2f}", flush=True)
if not GANCHO and "--sem-gancho" in sys.argv:
    sys.exit("pedaços prontos; falta só o gancho. Rode de novo com o clipe do HeyGen.")
(tmp / "lista.txt").write_text("".join(f"file '{p.name}'\n" for p in lista))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
                "-i", str(d / "narracao.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", out], check=True)
print("ok", out)
