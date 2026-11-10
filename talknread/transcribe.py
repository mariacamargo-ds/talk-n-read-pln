"""Transcrição de fala com Whisper (faster-whisper), 100% local na CPU."""
from __future__ import annotations

import os
from typing import Callable, Optional

from .subtitles import Seg, chunk_words, tidy

ProgressFn = Callable[[float, str], None]


def load_model(size: str = "small"):
    """Carrega o modelo Whisper na CPU com quantização int8 (rápido e leve).

    Na primeira execução os pesos são baixados; depois ficam em cache local.
    """
    from faster_whisper import WhisperModel

    return WhisperModel(
        size,
        device="cpu",
        compute_type="int8",
        cpu_threads=min(8, os.cpu_count() or 4),
    )


def run(
    model,
    path: str,
    language: Optional[str] = None,
    vad: bool = True,
    fast: bool = True,
    short: bool = True,
    on_progress: Optional[ProgressFn] = None,
):
    """Transcreve `path` (vídeo ou áudio) e devolve (legendas, info).

    - language: código ISO ("pt", "en"...) ou None para detectar sozinho.
    - vad: ignora silêncios (menos alucinação e mais velocidade).
    - fast: beam_size=1 (mais rápido na CPU).
    - short: usa tempos por palavra para montar legendas curtas.
    """
    segments, info = model.transcribe(
        path,
        language=language,
        vad_filter=vad,
        beam_size=1 if fast else 5,
        word_timestamps=short,
        condition_on_previous_text=False,
    )
    duration = float(getattr(info, "duration", 0) or 0)
    out: list[Seg] = []
    for seg in segments:  # `segments` é um gerador: a transcrição acontece aqui
        if short and getattr(seg, "words", None):
            out.extend(chunk_words(seg.words))
        else:
            text = seg.text.strip()
            if text:
                out.append(Seg(seg.start, seg.end, text))
        if on_progress:
            frac = min(seg.end / duration, 1.0) if duration else 0.0
            on_progress(frac, out[-1].text if out else "")
    return tidy(out), info
