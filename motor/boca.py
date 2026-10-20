"""Cola a boca gerada pelo Wav2Lip no rosto original sem o "quadrado" por cima.

O Wav2Lip gera o rosto inteiro em 96x96 e, por padrão, cola esse quadrado ampliado sobre o
quadro: fica borrado, com borda visível e cor diferente. Aqui só a região da boca e do queixo
entra, com máscara oval de borda suave, cor igualada à pele original e um pouco de nitidez.

Copiado para dentro do Wav2Lip pelo patch_wav2lip.py e usado no lugar de `f[y1:y2, x1:x2] = p`.
"""
import atexit
import json
import os

import cv2
import numpy as np

# Quanto a boca gerada está aberta em cada quadro (0 a 1), medido dentro da caixa do rosto.
# O alinhar.py usa essa curva para medir o atraso boca/voz em qualquer enquadramento.
ABERTURA: list[float] = []


@atexit.register
def _salvar_abertura():
    destino = os.environ.get("BOCA_ABERTURA_JSON")
    if destino and ABERTURA:
        with open(destino, "w") as f:
            json.dump(ABERTURA, f)


def _abertura(gerado: np.ndarray) -> float:
    """Boca aberta = interior da boca mais escuro que a pele em volta (dentes/língua/sombra)."""
    h, w = gerado.shape[:2]
    cinza = cv2.cvtColor(gerado, cv2.COLOR_BGR2GRAY)
    interno = np.zeros((h, w), np.uint8)
    cv2.ellipse(interno, (int(w * CENTRO_X), int(h * CENTRO_Y)), (int(w * 0.16), int(h * 0.09)),
                0, 0, 360, 1, -1)
    pele = _anel(h, w)
    if not interno.any() or not pele.any():
        return 0.0
    return float(max(0.0, cinza[pele].mean() - cinza[interno == 1].mean()) / 255.0)


# Região da boca dentro da caixa do rosto (frações da largura/altura da caixa).
CENTRO_X, CENTRO_Y = 0.50, 0.74
RAIO_X, RAIO_Y = 0.34, 0.24
SUAVE = 0.18  # borda da máscara, em fração da largura da caixa

_mascaras = {}


def _mascara(h: int, w: int) -> np.ndarray:
    chave = (h, w)
    if chave not in _mascaras:
        m = np.zeros((h, w), np.float32)
        cv2.ellipse(m, (int(w * CENTRO_X), int(h * CENTRO_Y)), (int(w * RAIO_X), int(h * RAIO_Y)),
                    0, 0, 360, 1.0, -1)
        k = max(3, int(w * SUAVE) | 1)
        _mascaras[chave] = cv2.GaussianBlur(m, (k, k), 0)[..., None]
    return _mascaras[chave]


_aneis = {}


def _anel(h: int, w: int) -> np.ndarray:
    """Pele em volta da boca (dentro da máscara, fora da boca): onde a cor é comparada.
    A boca em si fica de fora, senão a boca aberta (escura) clareia tudo em volta."""
    chave = (h, w)
    if chave not in _aneis:
        dentro = np.zeros((h, w), np.uint8)
        cv2.ellipse(dentro, (int(w * CENTRO_X), int(h * CENTRO_Y)), (int(w * RAIO_X), int(h * RAIO_Y)),
                    0, 0, 360, 1, -1)
        boca = np.zeros((h, w), np.uint8)
        cv2.ellipse(boca, (int(w * CENTRO_X), int(h * CENTRO_Y)), (int(w * 0.20), int(h * 0.12)),
                    0, 0, 360, 1, -1)
        _aneis[chave] = (dentro == 1) & (boca == 0)
    return _aneis[chave]


def _igualar_cor(gerado: np.ndarray, original: np.ndarray) -> np.ndarray:
    """Desloca a cor (LAB) da boca gerada para a pele original bater no anel em volta da boca."""
    h, w = original.shape[:2]
    anel = _anel(h, w)
    if anel.sum() < 20:
        return gerado
    g = cv2.cvtColor(gerado, cv2.COLOR_BGR2LAB).astype(np.float32)
    o = cv2.cvtColor(original, cv2.COLOR_BGR2LAB).astype(np.float32)
    g += (o[anel].mean(axis=0) - g[anel].mean(axis=0))  # só desloca: preserva o contraste da boca
    return cv2.cvtColor(np.clip(g, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def _nitidez(img: np.ndarray, forca: float = 0.6) -> np.ndarray:
    borrado = cv2.GaussianBlur(img, (0, 0), 1.2)
    return cv2.addWeighted(img, 1 + forca, borrado, -forca, 0)


# Suavização no tempo: o Wav2Lip decide a boca quadro a quadro e tremula (a boca "bate" rápido
# demais). Misturar um pouco do quadro anterior calma o movimento sem atrasar a fala.
PESO_ANTERIOR = 0.35
_anterior = {"g": None}


def colar_boca(original: np.ndarray, gerado: np.ndarray) -> np.ndarray:
    """original e gerado: recortes BGR uint8 do mesmo tamanho (caixa do rosto)."""
    h, w = original.shape[:2]
    m = _mascara(h, w)
    ABERTURA.append(_abertura(gerado))  # antes da suavização: é o tempo real da boca
    ant = _anterior["g"]
    suave = gerado
    if ant is not None and ant.shape == gerado.shape:
        suave = cv2.addWeighted(gerado, 1 - PESO_ANTERIOR, ant, PESO_ANTERIOR, 0)
    _anterior["g"] = gerado
    g = _nitidez(_igualar_cor(suave, original))
    out = original.astype(np.float32) * (1 - m) + g.astype(np.float32) * m
    return np.clip(out, 0, 255).astype(np.uint8)
