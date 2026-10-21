"""Gera o vídeo: recorta o treino, fala o roteiro com a voz clonada e sincroniza a boca.

Uso: python motor/gerar.py --treino video.mov --roteiro roteiros/x.txt --saida saida/ \
        --wav2lip /caminho/Wav2Lip --pesos /caminho/wav2lip_gan.pth

Roda em CPU (GitHub Actions). --simular troca voz e boca por versões falsas, só para testar o fluxo.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Menores que o 720p de sempre: na CPU, a detecção de rosto custa por pixel.
FORMATOS = {"vertical": (720, 1280), "feed": (576, 720), "quadrado": (720, 720),
            "horizontal": (1280, 720)}
VOZ_REF_S = 12   # o Chatterbox usa ~10 s de referência
BASE_S = 8       # trecho do rosto; vai e volta (ping-pong) para repetir sem pulo
# Gravação baixa vira clone baixo e sem energia: a referência é limpa do ruído grave e
# normalizada antes de clonar (o volume final é nivelado depois, em falar()).
FILTRO_REFERENCIA = "highpass=f=70,loudnorm=I=-18:TP=-2:LRA=11"
CHARS_TRECHO = 600
# Sem medida confiável, não mexe: a janela de áudio já está centrada no quadro (patch do Wav2Lip).
ATRASO_IMAGEM_PADRAO_S = 0.0


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


def pecas_voz(trecho: str, limite: int = 250, junta: int = 180) -> list[str]:
    """Pedaços para a voz: o Chatterbox gera no máximo ~40 s por chamada.

    Frases curtas vizinhas vão juntas (até `junta` caracteres): gerar frase por frase faz a
    entonação recomeçar do zero a cada uma, e é isso que soa robótico.
    """
    pecas = []
    for f in frases(trecho):
        pecas += [f] if len(f) <= limite else agrupar(re.split(r"(?<=[,;:])\s+", f), limite)
    return agrupar(pecas, junta)


# ---------- Etapas ----------

def preparar(treino: Path, trab: Path, formato: str, inicio_voz: float, inicio_video: float,
             voz_ref: Path | None = None):
    d = duracao(treino)
    ii = min(max(inicio_video, 0), max(d - BASE_S, 0))
    # A voz vem de uma gravação separada (clone feito no estúdio) ou de um trecho do próprio treino.
    origem = voz_ref or treino
    dv = duracao(origem) if voz_ref else d
    iv = min(max(0.5 if voz_ref else inicio_voz, 0), max(dv - VOZ_REF_S, 0))
    ffmpeg("-ss", str(iv), "-t", str(VOZ_REF_S), "-i", str(origem), "-vn", "-af", FILTRO_REFERENCIA, "-ac", "1",
           "-ar", "24000", str(trab / "voz_referencia.wav"))
    w, h = FORMATOS[formato]
    ida = trab / "base_ida.mp4"
    ffmpeg("-ss", str(ii), "-t", str(BASE_S), "-i", str(treino), "-an", "-vf",
           f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=25,setsar=1",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(ida))
    ffmpeg("-i", str(ida), "-filter_complex",
           "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]", "-map", "[v]",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(trab / "base.mp4"))
    fonte = "gravação separada" if voz_ref else "treino"
    print(f"preparar: treino de {d:.0f} s, voz ({fonte}) a partir de {iv:.0f} s, "
          f"rosto a partir de {ii:.0f} s", flush=True)


def preparar_voz(voz_ref: Path, trab: Path):
    """Só a referência de voz, para gerar áudio sem vídeo de treino (texto para fala)."""
    iv = min(0.5, max(duracao(voz_ref) - VOZ_REF_S, 0))
    ffmpeg("-ss", str(iv), "-t", str(VOZ_REF_S), "-i", str(voz_ref), "-vn", "-af", FILTRO_REFERENCIA, "-ac", "1",
           "-ar", "24000", str(trab / "voz_referencia.wav"))
    print("preparar: só a voz (gravação separada)", flush=True)


def falar(trab: Path, texto: str, idioma: str, simular: bool, exagero: float = 0.6,
          cfg: float = 0.55) -> Path:
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
                        str(trab / "trechos.json"), str(audios), idioma, str(exagero), str(cfg)],
                       check=True)
    lista = trab / "audios.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in sorted(audios.glob("trecho_*.wav"))))
    fala = trab / "fala.wav"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-af",
           "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "24000", "-ac", "1", str(fala))  # volume de post
    print(f"voz: {len(trechos)} trecho(s), {duracao(fala):.1f} s de fala", flush=True)
    return fala


def sincronizar(trab: Path, fala: Path, wav2lip: Path, pesos: Path, simular: bool,
                atraso_boca_ms: float = 0) -> Path:
    bruto = trab / "boca.mp4"
    if simular:
        ffmpeg("-stream_loop", "-1", "-i", str(trab / "base.mp4"), "-i", str(fala), "-map", "0:v",
               "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
               str(bruto))
        return bruto
    # O Wav2Lip usa caminhos relativos (temp/) e quebra em caminhos com ponto: roda de dentro dele.
    r = subprocess.run(
        [sys.executable, "inference.py", "--checkpoint_path", str(pesos.resolve()),
         "--face", str((trab / "base.mp4").resolve()), "--audio", str(fala.resolve()),
         "--outfile", str(bruto.resolve()),
         "--face_det_batch_size", "4", "--wav2lip_batch_size", "32", "--pads", "0", "10", "0", "0"],
        cwd=wav2lip, stderr=subprocess.PIPE, text=True,
        # Lidos pelo patch_wav2lip.py e pelo boca.py (curva de abertura da boca para o alinhar.py).
        env={**os.environ, "ATRASO_BOCA_MS": str(atraso_boca_ms),
             "BOCA_ABERTURA_JSON": str((trab / "abertura.json").resolve())})
    sys.stderr.write(r.stderr)
    if r.returncode:
        # Só as últimas linhas do erro da biblioteca (não contêm o seu texto nem arquivos).
        fim = " | ".join(r.stderr.strip().splitlines()[-4:])[:400]
        print(f"::error::Wav2Lip falhou: {fim}", flush=True)
        raise SystemExit(r.returncode)
    return bruto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--treino", type=Path, help="vídeo de treino (dispensável em --so-voz com --voz-ref)")
    ap.add_argument("--roteiro", type=Path, required=True)
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--formato", default="vertical", choices=FORMATOS)
    ap.add_argument("--inicio-voz", type=float, default=5)
    ap.add_argument("--inicio-video", type=float, default=5)
    ap.add_argument("--wav2lip", type=Path)
    ap.add_argument("--pesos", type=Path)
    ap.add_argument("--voz-ref", type=Path, help="gravação só da voz (senão usa o áudio do treino)")
    # Padrões mais expressivos que os do Chatterbox (0.5/0.5), que soavam robóticos.
    ap.add_argument("--exagero", type=float, default=0.6, help="expressividade da voz, de 0 a 1")
    ap.add_argument("--cfg", type=float, default=0.55, help="maior = mais fiel ao jeito e ao sotaque da sua gravação (0 a 1)")
    ap.add_argument("--realce", type=Path, help="pesos do GFPGAN: restaura o rosto depois do Wav2Lip")
    ap.add_argument("--atraso-boca-ms", type=float, default=0,
                    help="ajuste fino da sincronia: positivo = boca mais tarde que a voz")
    ap.add_argument("--so-voz", action="store_true", help="para depois da voz, para você ouvir antes")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    texto = a.roteiro.read_text(encoding="utf-8").strip()
    if not texto:
        sys.exit("O roteiro está vazio.")
    if not a.treino and not (a.so_voz and a.voz_ref):
        sys.exit("Falta --treino (só dá para dispensar em --so-voz com --voz-ref).")
    if not a.so_voz and not a.simular and not (a.wav2lip and a.pesos):
        sys.exit("Faltam --wav2lip e --pesos.")
    trab = a.saida / "trabalho"
    trab.mkdir(parents=True, exist_ok=True)

    if a.treino:
        preparar(a.treino, trab, a.formato, a.inicio_voz, a.inicio_video, a.voz_ref)
    else:
        preparar_voz(a.voz_ref, trab)
    fala = falar(trab, texto, a.idioma, a.simular, min(max(a.exagero, 0), 1), min(max(a.cfg, 0), 1))
    if a.so_voz:
        ffmpeg("-i", str(fala), str(a.saida / "voz.mp3"))
        print(f"pronto: {a.saida / 'voz.mp3'}", flush=True)
        return
    bruto = sincronizar(trab, fala, a.wav2lip.resolve() if a.wav2lip else None,
                        a.pesos.resolve() if a.pesos else None, a.simular, a.atraso_boca_ms)

    if a.realce and not a.simular:
        mudo = trab / "boca_realce.mp4"
        r = subprocess.run([sys.executable, str(AQUI / "realce.py"), str(bruto), str(mudo),
                            str(a.realce.resolve()), "0.3"], stderr=subprocess.PIPE, text=True)
        if r.returncode or not mudo.exists():
            fim = " | ".join(r.stderr.strip().splitlines()[-3:])[:300]
            print(f"::warning::Realce do rosto falhou, sigo sem ele: {fim}", flush=True)
        else:
            com_audio = trab / "boca_realce_audio.mp4"
            ffmpeg("-i", str(mudo), "-i", str(fala), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                   "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(com_audio))
            bruto = com_audio

    final = a.saida / "video_final.mp4"
    atraso, corr = ATRASO_IMAGEM_PADRAO_S, 0.0
    if not a.simular:
        try:
            from alinhar import medir_atraso
            arq = trab / "abertura.json"
            atraso, corr = medir_atraso(str(bruto), json.loads(arq.read_text()) if arq.exists() else None)
            print(f"alinhamento: boca {'adiantada' if atraso > 0 else 'atrasada' if atraso < 0 else 'ok'}"
                  f" {abs(atraso) * 1000:.0f} ms (correlação {corr:.2f})", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Medida de sincronia falhou ({type(e).__name__}); uso o padrão.", flush=True)
            atraso = ATRASO_IMAGEM_PADRAO_S
    # atraso > 0: atrasa a imagem; < 0: atrasa o som.
    off_v, off_a = (atraso, 0.0) if atraso >= 0 else (0.0, -atraso)
    ffmpeg("-itsoffset", f"{off_v:.3f}", "-i", str(bruto), "-itsoffset", f"{off_a:.3f}", "-i", str(bruto),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(final))
    print(f"pronto: {final} ({duracao(final):.1f} s)", flush=True)


if __name__ == "__main__":
    main()
