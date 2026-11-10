"""Etapa opcional: revisão e tradução das legendas com a API da DeepSeek.

A API é compatível com o SDK da OpenAI. O modelo recebe apenas o TEXTO de cada
trecho e devolve o mesmo número de trechos; os tempos nunca são alterados.
"""
from __future__ import annotations

import json
import os
from typing import Callable, Optional

from .subtitles import Seg

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


def is_configured() -> bool:
    return bool(os.getenv("DEEPSEEK_API_KEY"))


def _client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
        timeout=60,
        max_retries=1,
    )


_JSON_RULES = (
    'Responda SOMENTE com JSON no formato {"items":[{"id":<int>,"text":"<string>"}]}, '
    "com exatamente os mesmos ids recebidos, na mesma ordem."
)


def _system_prompt(task: str, language: Optional[str], target: Optional[str]) -> str:
    if task == "review":
        idioma = language or "o idioma original"
        return (
            f"Você revisa legendas geradas por reconhecimento automático de fala em {idioma}. "
            "Corrija pontuação, acentuação, maiúsculas, nomes próprios e termos técnicos óbvios. "
            "NÃO resuma, NÃO una nem divida itens, NÃO acrescente informação e NÃO mude o idioma. "
            "Mantenha praticamente o mesmo tamanho de cada item. " + _JSON_RULES
        )
    if task == "translate":
        return (
            f"Você traduz legendas de vídeo para {target}. Traduza cada item de forma natural e "
            "concisa, mantendo o sentido e um tamanho parecido com o original (é uma legenda). "
            "NÃO una nem divida itens. " + _JSON_RULES
        )
    raise ValueError(f"Tarefa desconhecida: {task}")


def _parse(content: str) -> dict[int, str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:  # tolera cercas de código ou texto em volta
        data = json.loads(content[content.index("{") : content.rindex("}") + 1])
    return {int(x["id"]): str(x["text"]).strip() for x in data["items"]}


def _call(client, model: str, system: str, items: list[tuple[int, str]]) -> dict[int, str]:
    payload = json.dumps(
        {"items": [{"id": i, "text": t} for i, t in items]}, ensure_ascii=False
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": payload},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return _parse(resp.choices[0].message.content)


def process(
    segs: list[Seg],
    task: str,
    language: Optional[str] = None,
    target: Optional[str] = None,
    on_progress: Optional[Callable[[float], None]] = None,
    batch_size: int = 25,
    client=None,
    model: Optional[str] = None,
) -> tuple[list[Seg], int]:
    """Revisa (`task="review"`) ou traduz (`task="translate"`) as legendas.

    Devolve (novas_legendas, quantidade_de_trechos_que_falharam). Em caso de falha
    de um lote, o texto original é mantido: o app nunca fica sem legenda.
    """
    client = client or _client()
    model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    system = _system_prompt(task, language, target)

    out = list(segs)
    failed = 0
    for start in range(0, len(segs), batch_size):
        chunk = segs[start : start + batch_size]
        items = [(start + i, s.text) for i, s in enumerate(chunk)]
        try:
            result = _call(client, model, system, items)
            if set(result) != {i for i, _ in items}:
                raise ValueError("ids divergentes na resposta")
        except Exception:
            failed += len(chunk)
        else:
            for i, text in result.items():
                if text:
                    out[i] = Seg(segs[i].start, segs[i].end, text)
                else:
                    failed += 1
        if on_progress:
            on_progress(min((start + batch_size) / len(segs), 1.0))
    return out, failed
