"""Voz fixa do Hiroshi com o Qwen3-TTS (Apache-2.0), na CPU.

A voz nasceu no Qwen3-TTS VoiceDesign (descrição em texto); o trecho aprovado está em
vozes/hiroshi.wav (+ vozes/hiroshi.txt). O modelo Base clona essa referência, então todas as falas
de todos os vídeos saem com a mesma voz.

Uso:
  python motor/voz_hiroshi.py roteiro.txt pasta/                 # um wav por linha (clipes)
  python motor/voz_hiroshi.py roteiro.txt parte.wav --parte 0 --partes 8   # vídeo longo: um wav
      só com as linhas desta parte, emendadas com pausas naturais
"""
import argparse
import json
import random
import re
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

AQUI = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("roteiro")
ap.add_argument("saida")
ap.add_argument("--parte", type=int, default=None)
ap.add_argument("--partes", type=int, default=1)
a = ap.parse_args()

torch.manual_seed(1); random.seed(1); np.random.seed(1)
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
VOZ = __import__("os").environ.get("VOZ", "hiroshi").strip() or "hiroshi"  # vozes/<VOZ>.wav + .txt
prompt = m.create_voice_clone_prompt(ref_audio=str(AQUI / "vozes" / f"{VOZ}.wav"),
                                     ref_text=(AQUI / "vozes" / f"{VOZ}.txt").read_text(encoding="utf-8").strip())
# VOZ_MISTURA="walt-b:0.4": mistura o timbre (vetor do falante) da voz base com o de outra voz,
# mantendo o sotaque/ritmo da base (referência ICL). Deixa a voz única. (Tom e ritmo: pós-processo com ffmpeg rubberband no workflow walt-falas.)
_mix = __import__("os").environ.get("VOZ_MISTURA", "").strip()
if _mix:
    _outra, _peso = _mix.split(":")
    _o = m.create_voice_clone_prompt(ref_audio=str(AQUI / "vozes" / f"{_outra}.wav"),
                                     ref_text=(AQUI / "vozes" / f"{_outra}.txt").read_text(encoding="utf-8").strip())
    _a, _b = prompt[0].ref_spk_embedding, _o[0].ref_spk_embedding
    _w = float(_peso)
    _e = (1 - _w) * _a + _w * _b
    prompt[0].ref_spk_embedding = _e * (_a.norm() / _e.norm())
    print(f"[voz] timbre misturado: {VOZ} {1 - _w:.0%} + {_outra} {_w:.0%}", flush=True)
# "[broll: ...]" / "[split: ...]" / "[avatar]" no começo da linha são instruções de edição (motor/montar.py)
falas = [re.sub(r"^\s*(\[[^\]]*\]\s*)+", "", l).strip()
         for l in Path(a.roteiro).read_text(encoding="utf-8").splitlines() if l.strip()]


def dizer(texto):
    wavs, sr = m.generate_voice_clone(text=texto, language="English", voice_clone_prompt=prompt)
    return wavs[0].astype(np.float32), sr


if a.parte is None or __import__("os").environ.get("CLIPES"):
    # CLIPES=1 com --parte: um wav por linha, numerado pela posição no roteiro inteiro (vídeo longo em paralelo)
    pasta = Path(a.saida); pasta.mkdir(parents=True, exist_ok=True)
    idx = list(range(1, len(falas) + 1))
    if a.parte is not None:
        idx = [int(i) for i in np.array_split(np.array(idx), a.partes)[a.parte]]
    TAKES = int(__import__("os").environ.get("TAKES", "1"))
    ALVO_HZ = float(__import__("os").environ.get("ALVO_HZ", "0"))  # tom mediano desejado (antes do pós-processo)
    if TAKES > 1:
        import librosa
        from faster_whisper import WhisperModel
        asr = WhisperModel("base.en", device="cpu", compute_type="int8")
        norm = lambda x: re.sub(r"[^a-z0-9 ]", "", re.sub(r"[-/]", " ", x.lower())).split()

        def nota(w, sr, texto):
            """Quanto menor, melhor: palavras erradas, tom fora do alvo, buracos e ritmo estranho."""
            y = librosa.resample(w, orig_sr=sr, target_sr=16000)
            segs, _ = asr.transcribe(y, beam_size=1, language="en")
            ouvido = norm(" ".join(x.text for x in segs)); certo = norm(texto)
            import difflib
            erro = 1 - difflib.SequenceMatcher(None, certo, ouvido).ratio()
            f0 = librosa.yin(y, fmin=60, fmax=300, sr=16000, frame_length=1024, hop_length=320)
            rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=320)[0]
            voz = rms > np.percentile(rms, 40)
            hz = float(np.median(f0[voz])) if voz.sum() > 10 else ALVO_HZ
            st = 12 * np.log2(hz / ALVO_HZ) if ALVO_HZ else 0.0
            # buraco: maior silêncio interno (falha comum do TTS)
            fala_on = rms > 0.1 * rms.max(); on = np.where(fala_on)[0]
            buraco = 0.0
            if len(on) > 1:
                buraco = float(np.diff(on).max() * 320 / 16000)
            cps = len(texto) / max(len(w) / sr, 0.1)  # letras por segundo (normal ~13-17)
            ritmo = max(0.0, abs(cps - 15) - 3) / 3
            return erro * 20 + abs(st) + max(0.0, buraco - 0.7) * 4 + ritmo, st, erro, buraco, cps
    for i in idx:
        fala = falas[i - 1]
        if TAKES > 1:
            melhor = None
            for k in range(TAKES):
                torch.manual_seed(1000 * i + k)
                w, sr = dizer(fala)
                n, st, erro, buraco, cps = nota(w, sr, fala)
                print(f"  fala {i} take {k}: nota {n:.2f} (tom {st:+.1f} st, erro {erro:.2f}, buraco {buraco:.1f}s, {cps:.0f} l/s)", flush=True)
                if melhor is None or n < melhor[0]:
                    melhor = (n, w, sr, st)
                if n < 0.8:  # take boa: não gasta mais tempo
                    break
            _, w, sr, st = melhor
            # corrige o resto do tom no pós-processo (rubberband), no máximo 2 semitons
            (pasta / f"fala-{i:03d}.st").write_text(f"{-max(-2.0, min(2.0, st)):.2f}")
        else:
            w, sr = dizer(fala)
        p = np.zeros(int(sr * 0.25), dtype=np.float32)
        sf.write(pasta / f"fala-{i:03d}.wav", np.concatenate([p, w, p]), sr)
        print(f"fala-{i:03d}.wav: {(len(w) / sr) + 0.5:.1f}s", flush=True)
else:
    minhas = np.array_split(np.array(falas, dtype=object), a.partes)[a.parte]
    partes, sr, tempos = [], 24000, []
    for fala in minhas:
        w, sr = dizer(str(fala))
        partes += [w, np.zeros(int(sr * 0.45), dtype=np.float32)]
        tempos.append(len(w) + int(sr * 0.45))
        print(f"{len(w) / sr:.1f}s  {str(fala)[:40]}", flush=True)
    if partes:
        sf.write(a.saida, np.concatenate(partes), sr)
    # duração (em amostras de 24 kHz) de cada linha desta parte, para a montagem saber quando cada frase começa
    Path(a.saida).with_suffix(".json").write_text(json.dumps({"sr": sr, "amostras": tempos}))
