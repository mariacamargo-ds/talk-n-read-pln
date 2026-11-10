"""Estruturas e formatação de legendas (SRT, VTT, TXT)."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass
class Seg:
    """Um trecho de legenda, com tempos em segundos."""

    start: float
    end: float
    text: str


# ---------------------------------------------------------------- tempos
def _stamp(seconds: float, sep: str) -> str:
    ms_total = int(round(max(seconds, 0.0) * 1000))
    h, rest = divmod(ms_total, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def fmt_clock(seconds: float) -> str:
    """Formato curto para exibir na tabela: MM:SS.cc"""
    seconds = max(seconds, 0.0)
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}"


# ---------------------------------------------------------------- texto
def wrap_lines(text: str, width: int = 42, max_lines: int = 2) -> str:
    """Quebra o texto em até `max_lines` linhas de ~`width` caracteres."""
    lines = textwrap.wrap(" ".join(text.split()), width=width) or [""]
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [" ".join(lines[max_lines - 1 :])]
    return "\n".join(lines)


# ---------------------------------------------------------------- exportação
def to_srt(segs: Iterable[Seg]) -> str:
    blocks = []
    n = 0
    for s in segs:
        if not s.text.strip():
            continue
        n += 1
        blocks.append(
            f"{n}\n{_stamp(s.start, ',')} --> {_stamp(s.end, ',')}\n{wrap_lines(s.text)}\n"
        )
    return "\n".join(blocks)


def to_vtt(segs: Iterable[Seg]) -> str:
    blocks = ["WEBVTT\n"]
    for s in segs:
        if not s.text.strip():
            continue
        blocks.append(
            f"{_stamp(s.start, '.')} --> {_stamp(s.end, '.')}\n{wrap_lines(s.text)}\n"
        )
    return "\n".join(blocks)


def to_txt(segs: Iterable[Seg]) -> str:
    return "\n".join(s.text.strip() for s in segs if s.text.strip()) + "\n"


# ---------------------------------------------------------------- segmentação
def chunk_words(
    words: Sequence,
    max_chars: int = 70,
    max_dur: float = 6.0,
    gap: float = 0.8,
    min_sentence: int = 25,
) -> list[Seg]:
    """Agrupa palavras (com tempos) em legendas curtas e legíveis.

    Fecha o trecho ao atingir `max_chars`/`max_dur`, ao fim de uma frase
    (depois de `min_sentence` caracteres) ou depois de uma pausa > `gap`.
    """
    out: list[Seg] = []
    cur: list = []

    def flush() -> None:
        if cur:
            text = "".join(w.word for w in cur).strip()
            if text:
                out.append(Seg(cur[0].start, cur[-1].end, text))
            cur.clear()

    for w in words:
        if w.start is None or w.end is None:
            continue
        if cur and (w.start - cur[-1].end) > gap:
            flush()
        cur.append(w)
        text = "".join(x.word for x in cur).strip()
        if (
            len(text) >= max_chars
            or (w.end - cur[0].start) >= max_dur
            or (text[-1:] in ".?!…" and len(text) >= min_sentence)
        ):
            flush()
    flush()
    return out


def tidy(segs: Sequence[Seg], min_dur: float = 0.4) -> list[Seg]:
    """Garante duração mínima e evita sobreposição entre legendas."""
    out: list[Seg] = []
    for i, s in enumerate(segs):
        end = max(s.end, s.start + min_dur)
        if i + 1 < len(segs):
            end = min(end, max(segs[i + 1].start, s.start + 0.05))
        out.append(Seg(round(s.start, 3), round(end, 3), s.text.strip()))
    return out
