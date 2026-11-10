"""Baixa os modelos Whisper com antecedência (rode UMA vez, com internet).

Uso:
    python prepare_models.py            # baixa base e small
    python prepare_models.py small      # baixa só o small
"""
import sys

from talknread.transcribe import load_model

sizes = sys.argv[1:] or ["base", "small"]
for size in sizes:
    print(f"Baixando/carregando o modelo '{size}'…")
    load_model(size)
    print(f"  ok: '{size}' pronto.")
print("Tudo certo! Agora o app funciona mesmo sem internet.")
