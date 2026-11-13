"""Legenda palavra por palavra (estilo canais de avatar): 3 palavras por vez, a palavra falada em amarelo.

Tempos das palavras com faster-whisper (MIT) na CPU; desenho com o libass do ffmpeg.
Uso: python motor/legendas.py video.mp4 saida.mp4 [--modelo base.en]
"""
import argparse
import subprocess
from pathlib import Path

AMARELO = r"{\c&H00D7FF&}"  # BGR do ASS
BRANCO = r"{\c&HFFFFFF&}"


def tempo(s):
    h, s = divmod(max(s, 0), 3600)
    m, s = divmod(s, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def palavras(audio, modelo):
    from faster_whisper import WhisperModel
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="en", word_timestamps=True, vad_filter=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words if w.word.strip()]


def ass(ps, largura, altura, por_vez=3):
    tam = int(altura * 0.075)
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L,DejaVu Sans,{tam},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{max(3, tam // 12)},2,2,60,60,{int(altura * 0.09)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    for g in range(0, len(ps), por_vez):
        grupo = ps[g:g + por_vez]
        fim_grupo = ps[g + por_vez][1] if g + por_vez < len(ps) else grupo[-1][2] + 0.4
        fim_grupo = min(fim_grupo, grupo[-1][2] + 0.6)
        for i, (_, ini, _) in enumerate(grupo):
            fim = grupo[i + 1][1] if i + 1 < len(grupo) else fim_grupo
            txt = " ".join((AMARELO if j == i else BRANCO) + p.upper() for j, (p, _, _) in enumerate(grupo))
            linhas.append(f"Dialogue: 0,{tempo(ini)},{tempo(fim)},L,,0,0,0,,{txt}")
    return cab + "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("saida")
    ap.add_argument("--modelo", default="base.en")
    a = ap.parse_args()
    w, h = 1920, 1080  # sai sempre em 1080p
    wav = Path(a.saida).with_suffix(".wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-ar", "16000", "-ac", "1", str(wav)], check=True)
    ps = palavras(str(wav), a.modelo)
    arq = Path(a.saida).with_suffix(".ass")
    arq.write_text(ass(ps, w, h), encoding="utf-8")
    print(len(ps), "palavras")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},ass={arq}", "-c:v", "libx264",
                    "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", a.saida], check=True)


if __name__ == "__main__":
    main()
