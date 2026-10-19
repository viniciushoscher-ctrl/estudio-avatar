"""Gera o vídeo: recorta o treino, fala o roteiro com a voz clonada e sincroniza a boca.

Uso: python motor/gerar.py --treino video.mov --roteiro roteiros/x.txt --saida saida/ \
        --wav2lip /caminho/Wav2Lip --pesos /caminho/wav2lip_gan.pth

Roda em CPU (GitHub Actions). --simular troca voz e boca por versões falsas, só para testar o fluxo.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Menores que o 720p de sempre: na CPU, a detecção de rosto custa por pixel.
FORMATOS = {"vertical": (540, 960), "quadrado": (720, 720), "horizontal": (960, 540)}
VOZ_REF_S = 12   # o Chatterbox usa ~10 s de referência
BASE_S = 8       # trecho do rosto; vai e volta (ping-pong) para repetir sem pulo
CHARS_TRECHO = 600


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def duracao(p: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


# ---------- Roteiro ----------

def frases(texto: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?…])\s+", " ".join(texto.split())) if s]


def agrupar(pecas: list[str], limite: int) -> list[str]:
    grupos, atual = [], ""
    for p in pecas:
        if atual and len(atual) + len(p) + 1 > limite:
            grupos.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    return grupos + ([atual] if atual else [])


def pecas_voz(trecho: str, limite: int = 250) -> list[str]:
    """Frases curtas para a voz: o Chatterbox gera no máximo ~40 s por chamada."""
    out = []
    for f in frases(trecho):
        out += [f] if len(f) <= limite else agrupar(re.split(r"(?<=[,;:])\s+", f), limite)
    return out


# ---------- Etapas ----------

def preparar(treino: Path, trab: Path, formato: str, inicio_voz: float, inicio_video: float):
    d = duracao(treino)
    iv = min(max(inicio_voz, 0), max(d - VOZ_REF_S, 0))
    ii = min(max(inicio_video, 0), max(d - BASE_S, 0))
    ffmpeg("-ss", str(iv), "-t", str(VOZ_REF_S), "-i", str(treino), "-vn", "-ac", "1",
           "-ar", "24000", str(trab / "voz_referencia.wav"))
    w, h = FORMATOS[formato]
    ida = trab / "base_ida.mp4"
    ffmpeg("-ss", str(ii), "-t", str(BASE_S), "-i", str(treino), "-an", "-vf",
           f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=25,setsar=1",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(ida))
    ffmpeg("-i", str(ida), "-filter_complex",
           "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]", "-map", "[v]",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(trab / "base.mp4"))
    print(f"preparar: treino de {d:.0f} s, voz a partir de {iv:.0f} s, rosto a partir de {ii:.0f} s",
          flush=True)


def falar(trab: Path, texto: str, idioma: str, simular: bool) -> Path:
    trechos = [pecas_voz(t) for t in agrupar(frases(texto), CHARS_TRECHO)]
    (trab / "trechos.json").write_text(json.dumps(trechos, ensure_ascii=False))
    audios = trab / "audios"
    audios.mkdir(exist_ok=True)
    if simular:
        for i, t in enumerate(trechos):
            seg = max(1.0, sum(len(p.split()) for p in t) / 2.5)
            ffmpeg("-f", "lavfi", "-i", f"sine=frequency=220:duration={seg}",
                   str(audios / f"trecho_{i:03d}.wav"))
    else:
        subprocess.run([sys.executable, str(AQUI / "voz.py"), str(trab / "voz_referencia.wav"),
                        str(trab / "trechos.json"), str(audios), idioma], check=True)
    lista = trab / "audios.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in sorted(audios.glob("trecho_*.wav"))))
    fala = trab / "fala.wav"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-ar", "24000", "-ac", "1", str(fala))
    print(f"voz: {len(trechos)} trecho(s), {duracao(fala):.1f} s de fala", flush=True)
    return fala


def sincronizar(trab: Path, fala: Path, wav2lip: Path, pesos: Path, simular: bool) -> Path:
    bruto = trab / "boca.mp4"
    if simular:
        ffmpeg("-stream_loop", "-1", "-i", str(trab / "base.mp4"), "-i", str(fala), "-map", "0:v",
               "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
               str(bruto))
        return bruto
    # O Wav2Lip usa caminhos relativos (temp/) e quebra em caminhos com ponto: roda de dentro dele.
    subprocess.run(
        [sys.executable, "inference.py", "--checkpoint_path", str(pesos),
         "--face", str(trab / "base.mp4"), "--audio", str(fala), "--outfile", str(bruto),
         "--face_det_batch_size", "4", "--wav2lip_batch_size", "32", "--pads", "0", "10", "0", "0"],
        cwd=wav2lip, check=True)
    return bruto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--treino", type=Path, required=True)
    ap.add_argument("--roteiro", type=Path, required=True)
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--formato", default="vertical", choices=FORMATOS)
    ap.add_argument("--inicio-voz", type=float, default=5)
    ap.add_argument("--inicio-video", type=float, default=5)
    ap.add_argument("--wav2lip", type=Path)
    ap.add_argument("--pesos", type=Path)
    ap.add_argument("--so-voz", action="store_true", help="para depois da voz, para você ouvir antes")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    texto = a.roteiro.read_text().strip()
    if not texto:
        sys.exit("O roteiro está vazio.")
    if not a.simular and not (a.wav2lip and a.pesos):
        sys.exit("Faltam --wav2lip e --pesos.")
    trab = a.saida / "trabalho"
    trab.mkdir(parents=True, exist_ok=True)

    preparar(a.treino, trab, a.formato, a.inicio_voz, a.inicio_video)
    fala = falar(trab, texto, a.idioma, a.simular)
    if a.so_voz:
        ffmpeg("-i", str(fala), str(a.saida / "voz.mp3"))
        print(f"pronto: {a.saida / 'voz.mp3'}", flush=True)
        return
    bruto = sincronizar(trab, fala, a.wav2lip.resolve() if a.wav2lip else None,
                        a.pesos.resolve() if a.pesos else None, a.simular)

    final = a.saida / "video_final.mp4"
    ffmpeg("-i", str(bruto), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-b:a", "160k", "-movflags", "+faststart", str(final))
    print(f"pronto: {final} ({duracao(final):.1f} s)", flush=True)


if __name__ == "__main__":
    main()
