"""Edição final no estilo dos canais de avatar: avatar sozinho, tela dividida e b-roll em tela cheia.

Cada linha do roteiro vira um trecho do vídeo, com a duração exata da fala dessa linha:
  linha sem marca                  -> Hiroshi falando em tela cheia
  [split: descrição da imagem] ... -> Hiroshi à esquerda, imagem à direita (com zoom lento)
  [broll: descrição da imagem] ... -> imagem em tela cheia (zoom lento), a voz continua
  [avatar] ...                     -> força o Hiroshi em tela cheia
As imagens vêm de gpu/broll_imagens.py (broll/linha-NNN.jpg). Só usa ffmpeg (sem dependências).

Uso:
  python motor/montar.py --roteiro r.txt --tempos tempos.json --avatar avatar.mp4 --audio fala.wav \
      --broll broll --saida final.mp4
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

FPS = 25
W, H = 1920, 1080


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def trechos(roteiro, tempos):
    linhas = [l for l in Path(roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]
    sr, amostras = tempos["sr"], tempos["amostras"]
    assert len(amostras) == len(linhas), f"{len(amostras)} tempos para {len(linhas)} linhas"
    out, q0, acum = [], 0, 0
    for i, (l, n) in enumerate(zip(linhas, amostras)):
        acum += n
        q1 = round(acum / sr * FPS)
        m = re.match(r"^\s*\[(broll|split|avatar)\b", l, re.I)
        tipo = m.group(1).lower() if m else "avatar"
        if out and tipo == "avatar" and out[-1]["tipo"] == "avatar":
            out[-1]["q1"] = q1  # junta falas seguidas do avatar num trecho só
        else:
            out.append({"tipo": tipo, "linha": i, "q0": q0, "q1": q1})
        q0 = q1
    return out


def zoom(img, quadros, w, h, sentido):
    """Filtro de zoom lento (Ken Burns) para uma imagem parada."""
    z = f"min(1+0.10*on/{quadros},1.10)" if sentido else f"max(1.10-0.10*on/{quadros},1.0)"
    return (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={quadros}:s={w}x{h}:fps={FPS},"
            f"setsar=1")


def montar(roteiro, tempos, avatar, audio, broll, saida):
    tempos = json.loads(Path(tempos).read_text())
    tmp = Path(tempfile.mkdtemp())
    lista = []
    for k, t in enumerate(trechos(roteiro, tempos)):
        n = t["q1"] - t["q0"]
        if n <= 0:
            continue
        ini, dur = t["q0"] / FPS, n / FPS
        seg = tmp / f"s{k:04d}.mp4"
        img = Path(broll, f"linha-{t['linha']:03d}.jpg")
        tipo = t["tipo"] if img.exists() or t["tipo"] == "avatar" else "avatar"
        enc = ["-frames:v", str(n), "-r", str(FPS), "-an", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
               "-pix_fmt", "yuv420p", str(seg)]
        if tipo == "avatar":
            ff("-ss", f"{ini:.3f}", "-i", avatar, "-vf", f"scale={W}:{H}:flags=lanczos,setsar=1", *enc)
        elif tipo == "broll":
            ff("-loop", "1", "-i", str(img), "-vf", zoom(img, n, W, H, k % 2 == 0), *enc)
        else:  # split: Hiroshi à esquerda (recorte central), imagem à direita
            ff("-ss", f"{ini:.3f}", "-i", avatar, "-loop", "1", "-i", str(img), "-filter_complex",
               f"[0:v]crop=ih*{W // 2}/{H}:ih,scale={W // 2}:{H}:flags=lanczos,setsar=1[a];"
               f"[1:v]{zoom(img, n, W // 2, H, k % 2 == 0)}[b];[a][b]hstack=inputs=2[v]",
               "-map", "[v]", *enc)
        lista.append(seg)
        print(f"[montar] {tipo:6s} {ini:7.2f}s +{dur:5.2f}s", flush=True)
    (tmp / "lista.txt").write_text("".join(f"file '{p}'\n" for p in lista))
    ff("-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"), "-i", audio, "-map", "0:v", "-map", "1:a",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida)
    print(f"[montar] {saida} pronto", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for a in ["roteiro", "tempos", "avatar", "audio", "broll", "saida"]:
        ap.add_argument(f"--{a}", required=True)
    a = ap.parse_args()
    montar(a.roteiro, a.tempos, a.avatar, a.audio, a.broll, a.saida)
