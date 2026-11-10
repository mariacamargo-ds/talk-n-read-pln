<div align="center">

# Talk 'N Read

**Da voz à legenda na palma da sua mão.**

![Python](https://img.shields.io/badge/Python-3.10%2B-7D54AC?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-app-4C4295?style=for-the-badge&logo=streamlit&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-B5338A?style=for-the-badge)
![DeepSeek-v4-Pro](https://img.shields.io/badge/DeepSeek-opcional-312A5D?style=for-the-badge)

</div>

Aplicação em Streamlit que transcreve a fala de um vídeo (ou de uma gravação pelo microfone) e gera
legendas sincronizadas em **SRT**, **VTT** e **TXT**. A transcrição roda localmente, na CPU, com
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), sem enviar seu áudio para a nuvem.

## Funcionalidades

- Upload de vídeo (MP4, MOV, MKV, AVI, WEBM) ou gravação pelo microfone
- Transcrição automática com detecção de idioma e tempos por trecho
- Legendas curtas e legíveis (quebra por pausas, pontuação e tamanho)
- Edição do texto na própria tabela e pré-visualização do vídeo com legenda
- Revisão e tradução opcionais com a API da DeepSeek (os tempos nunca são alterados)

## Como rodar

```bash
# 1. Ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Dependências
pip install -r requirements.txt

# 3. (Recomendado) baixe os modelos uma vez, com internet
python prepare_models.py

# 4. Abra o app
streamlit run app.py
```

### Revisão com IA (opcional)

Copie `.env.example` para `.env` e preencha `DEEPSEEK_API_KEY`. O arquivo `.env` já está no
`.gitignore`: nunca o envie ao GitHub.

## Estrutura

```
app.py                  interface (Streamlit)
talknread/
  transcribe.py         Whisper local (faster-whisper)
  subtitles.py          SRT, VTT, TXT e segmentação das legendas
  llm.py                revisão/tradução opcionais (DeepSeek)
prepare_models.py       baixa os modelos antecipadamente
.streamlit/config.toml  tema (paleta lilás)
```

## Dicas de desempenho (CPU)

- `small` equilibra qualidade e velocidade; use `base` se precisar de mais rapidez.
- Vídeos curtos (1 a 2 minutos) são ideais para demonstrações.
- Em ambientes com eco ou ruído, prefira o upload de vídeo à gravação ao vivo.

---

Feito por [Maria Eduarda Camargo](https://www.linkedin.com/in/maria-camargo-ds/) ·
[Streamlit](https://github.com/mariacamargo-ds)
