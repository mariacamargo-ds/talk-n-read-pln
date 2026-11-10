"""Talk 'N Read — Da voz à legenda na palma da sua mão."""
from __future__ import annotations

import os
import tempfile
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv é opcional
    pass

from talknread import llm
from talknread import subtitles as sub
from talknread import transcribe as tr

st.set_page_config(
    page_title="Talk 'N Read",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GITHUB_URL = "https://github.com/mariacamargo-ds"
LINKEDIN_URL = "https://www.linkedin.com/in/maria-camargo-ds/"
PAGES = ["Sobre o Projeto", "Funcionalidades", "Demonstração"]

# ------------------------------------------------------------------ ícones
_ICON_BODY = {
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-5"/><circle cx="12" cy="7.8" r="0.6" fill="C"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "play": '<circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8" fill="C"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>',
    "wave": '<path d="M2 12h3M7 8v8M12 4v16M17 8v8M22 12h-3"/>',
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v4"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
    "screen": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 21h8M12 18v3M7 14h10"/>',
    "caption": '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M7 11h4M13 11h4M7 15h2M12 15h5"/>',
}


def svg(name: str, color: str = "#FFFFFF", size: int = 24) -> str:
    body = _ICON_BODY[name].replace('fill="C"', f'fill="{color}"')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


def svg_data_uri(name: str, size: int = 20) -> str:
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg(name, "#FFFFFF", size))


GITHUB_SVG = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>'
)
LINKEDIN_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
)

# ------------------------------------------------------------------ estilo
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Karla:wght@400;500;700&family=Montserrat:wght@500;600;700&display=swap');

html, body, .stApp, .stMarkdown, p, li, label, input, textarea, select {
  font-family: 'Karla', sans-serif;
  color: #171619;
}
h1, h2, h3, h4, h5 { font-family: 'Montserrat', sans-serif !important; color: #171619; font-weight: 700 !important; }

.stApp {
  background:
    radial-gradient(circle at 12% 8%, rgba(255,255,255,0.40), transparent 38%),
    radial-gradient(circle at 92% 92%, rgba(125,84,172,0.20), transparent 45%),
    linear-gradient(160deg, #DDD4E8 0%, #C9BED6 42%, #B9ACD1 100%);
  background-attachment: fixed;
}
header[data-testid="stHeader"] { background: transparent; }
.stAppDeployButton, #MainMenu, footer { display: none !important; }
.block-container { max-width: 1180px; padding-top: 1.2rem; padding-bottom: 3rem; }

/* ---------- barra superior ---------- */
.st-key-navbar {
  background: #312A5D; border-radius: 20px; padding: 0.7rem 1.2rem;
  box-shadow: 0 8px 24px rgba(49,42,93,0.35); margin-bottom: 1.6rem;
}
.st-key-navbar, .st-key-navbar p, .st-key-navbar label { color: #FFFFFF; }
.tnr-brand { display: flex; align-items: center; gap: 12px; }
.tnr-logo { width: 44px; height: 44px; border-radius: 12px; background: #7D54AC; display: flex; align-items: center; justify-content: center; }
.tnr-brand-name { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 21px; color: #FFFFFF; }
.tnr-social { display: flex; gap: 12px; justify-content: flex-end; }
.tnr-social a {
  width: 44px; height: 44px; border-radius: 50%; background: #7D54AC;
  display: inline-flex; align-items: center; justify-content: center; transition: filter .15s;
}
.tnr-social a:hover { filter: brightness(1.2); }
.st-key-navbar [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-navbar [data-testid="stColumn"] { display: flex; flex-direction: column; justify-content: center; }
.st-key-navbar [data-testid="stMarkdownContainer"] { line-height: 1; margin: 0 !important; padding: 0 !important; }
.st-key-navbar [data-testid="stMarkdown"], .st-key-navbar [data-testid="stElementContainer"] { margin: 0 !important; }
.st-key-navbar [data-testid="stColumn"] > div { gap: 0; }
.st-key-navbar [data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none; }
.st-key-navbar [data-testid="stRadio"], .st-key-navbar [data-testid="stRadio"] > div { gap: 0; margin: 0; }
.st-key-navbar [role="radiogroup"] { gap: 6px; justify-content: center; flex-wrap: nowrap; }
/* opção da navegação: funciona no DOM novo (stRadioOption) e no antigo (baseweb) */
.st-key-navbar label[data-testid="stRadioOption"], .st-key-navbar label[data-baseweb="radio"] {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; min-height: 44px; box-sizing: border-box;
  border-radius: 12px; cursor: pointer; margin: 0; white-space: nowrap; transition: filter .15s, background .15s;
}
.st-key-navbar label[data-testid="stRadioOption"]:hover, .st-key-navbar label[data-baseweb="radio"]:hover { filter: brightness(1.25); }
.st-key-navbar label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
.st-key-navbar label[data-baseweb="radio"] > div:first-child { display: none; }
.st-key-navbar label[data-testid="stRadioOption"] p, .st-key-navbar label[data-baseweb="radio"] p {
  color: #FFFFFF; font-weight: 500; font-size: 15px; line-height: 1.2; margin: 0;
}
.st-key-navbar label[data-testid="stRadioOption"][data-selected="true"], .st-key-navbar label[data-baseweb="radio"]:has(input:checked) { background: #4C4295; }
.st-key-navbar label[data-testid="stRadioOption"][data-selected="true"] p, .st-key-navbar label[data-baseweb="radio"]:has(input:checked) p { font-weight: 700; }
.st-key-navbar label[data-testid="stRadioOption"]::before, .st-key-navbar label[data-baseweb="radio"]::before {
  content: ""; width: 20px; height: 20px; background-repeat: no-repeat; background-size: contain; flex: none;
}
.st-key-navbar [role="radiogroup"] > div:nth-of-type(1) label::before, .st-key-navbar [role="radiogroup"] > label:nth-of-type(1)::before { background-image: url("__ICON_INFO__"); }
.st-key-navbar [role="radiogroup"] > div:nth-of-type(2) label::before, .st-key-navbar [role="radiogroup"] > label:nth-of-type(2)::before { background-image: url("__ICON_GEAR__"); }
.st-key-navbar [role="radiogroup"] > div:nth-of-type(3) label::before, .st-key-navbar [role="radiogroup"] > label:nth-of-type(3)::before { background-image: url("__ICON_PLAY__"); }

/* ---------- cartões ---------- */
.tnr-hero {
  background: linear-gradient(135deg, #312A5D 0%, #4C4295 100%); color: #FFFFFF;
  border-radius: 24px; padding: 48px; box-shadow: 0 10px 28px rgba(49,42,93,0.16); margin-bottom: 1rem;
}
.tnr-eyebrow { font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 13px; letter-spacing: .12em; text-transform: uppercase; }
.tnr-hero .tnr-eyebrow { color: #C9BED6; }
.tnr-hero h1 { color: #FFFFFF; font-size: 52px; line-height: 1.1; margin: 8px 0 4px; padding: 0; }
.tnr-hero .tnr-tag { font-family: 'Montserrat', sans-serif; font-weight: 500; font-size: 24px; color: #C9BED6; margin: 0 0 16px; }
.tnr-hero p.tnr-lead { color: #FFFFFF; font-size: 18px; line-height: 1.55; max-width: 640px; margin: 0; }
.tnr-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin: 0.5rem 0 1.2rem; }
.tnr-card { background: #A8A3C7; border-radius: 20px; padding: 26px; box-shadow: 0 10px 28px rgba(49,42,93,0.16); }
.tnr-card h3 { font-size: 18px; margin: 12px 0 6px; padding: 0; }
.tnr-card p { font-size: 15px; line-height: 1.5; margin: 0; }
.tnr-ico { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; }
.tnr-num { width: 36px; height: 36px; border-radius: 10px; background: #4C4295; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-family: 'Montserrat', sans-serif; font-weight: 700; }
.tnr-chips { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; background: #A8A3C7; border-radius: 20px; padding: 22px 26px; box-shadow: 0 10px 28px rgba(49,42,93,0.16); }
.tnr-chips b { font-family: 'Montserrat', sans-serif; margin-right: 8px; }
.tnr-chip { color: #FFFFFF; border-radius: 999px; padding: 8px 16px; font-size: 14px; font-weight: 700; }

/* ---------- painéis do Streamlit ---------- */
.st-key-opts, .st-key-results {
  background: #A8A3C7; border-radius: 20px; padding: 1.2rem 1.4rem; box-shadow: 0 10px 28px rgba(49,42,93,0.16);
}
.stButton > button, .stDownloadButton > button {
  background: #4C4295; color: #FFFFFF; border: 0; border-radius: 12px; min-height: 44px; padding: 0.4rem 1.4rem;
  font-family: 'Montserrat', sans-serif; font-weight: 600;
}
.stButton > button p, .stDownloadButton > button p { color: #FFFFFF; font-family: 'Montserrat', sans-serif; font-weight: 600; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #7D54AC; color: #FFFFFF; border: 0; }
.stButton > button[kind="primary"] { background: #7D54AC; }
.stButton > button[kind="primary"]:hover { background: #312A5D; }
.stButton > button:disabled { background: #8F89B3; opacity: .75; }
[data-testid="stFileUploaderDropzone"] { background: #A8A3C7; border: 2px dashed #4C4295; border-radius: 16px; }
div[data-baseweb="select"] > div { background: #C9BED6; border-radius: 12px; border-color: #4C4295; }
button[data-baseweb="tab"] p { font-family: 'Montserrat', sans-serif; font-weight: 600; }
[data-baseweb="tab-highlight"] { background: #4C4295 !important; }
.stProgress > div > div > div > div { background: #7D54AC; }
"""


def inject_css() -> None:
    css = (
        _CSS.replace("__ICON_INFO__", svg_data_uri("info"))
        .replace("__ICON_GEAR__", svg_data_uri("gear"))
        .replace("__ICON_PLAY__", svg_data_uri("play"))
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ------------------------------------------------------------------ navegação
def go_demo() -> None:
    st.session_state["page"] = "Demonstração"


def navbar() -> str:
    if "page" not in st.session_state:
        st.session_state["page"] = PAGES[0]
    with st.container(key="navbar"):
        c1, c2, c3 = st.columns([2.6, 7.6, 1.8], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="tnr-brand"><div class="tnr-logo">{svg("caption")}</div>'
                '<span class="tnr-brand-name">Talk \'N Read</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.radio("Navegação", PAGES, key="page", horizontal=True, label_visibility="collapsed")
        with c3:
            st.markdown(
                '<div class="tnr-social">'
                f'<a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer" aria-label="GitHub de Maria Camargo">{GITHUB_SVG}</a>'
                f'<a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn de Maria Camargo">{LINKEDIN_SVG}</a>'
                "</div>",
                unsafe_allow_html=True,
            )
    return st.session_state["page"]


# ------------------------------------------------------------------ páginas
def card(icon: str, color: str, title: str, text: str) -> str:
    return (
        f'<div class="tnr-card"><div class="tnr-ico" style="background:{color}">{svg(icon, size=26)}</div>'
        f"<h3>{title}</h3><p>{text}</p></div>"
    )


def step(n: int, title: str, text: str) -> str:
    return f'<div class="tnr-card"><div class="tnr-num">{n}</div><h3>{title}</h3><p>{text}</p></div>'


def page_sobre() -> None:
    st.markdown(
        '<div class="tnr-hero"><div class="tnr-eyebrow">Sobre o Projeto</div>'
        "<h1>Talk 'N Read</h1>"
        '<p class="tnr-tag">Da voz à legenda na palma da sua mão.</p>'
        '<p class="tnr-lead">Envie um vídeo ou grave um áudio pelo microfone e a aplicação transcreve a fala '
        "automaticamente, gerando legendas sincronizadas prontas para baixar e usar em qualquer player.</p></div>",
        unsafe_allow_html=True,
    )
    st.button("Ver demonstração", key="cta", type="primary", on_click=go_demo)
    st.markdown("### Como funciona")
    st.markdown(
        '<div class="tnr-grid">'
        + step(1, "Envie o vídeo ou grave", "Faça o upload do arquivo ou fale direto no microfone do seu notebook.")
        + step(2, "Transcrição do áudio", "O áudio é extraído e a fala vira texto com marcação de tempo, localmente.")
        + step(3, "Revise e baixe", "Ajuste o texto, se quiser, e exporte em SRT, VTT ou TXT.")
        + "</div>",
        unsafe_allow_html=True,
    )
    ia = "DeepSeek v4 Pro (opcional)"
    st.markdown(
        '<div class="tnr-chips"><b>Construído com</b>'
        '<span class="tnr-chip" style="background:#312A5D">Python</span>'
        '<span class="tnr-chip" style="background:#4C4295">Streamlit</span>'
        '<span class="tnr-chip" style="background:#7D54AC">Whisper · faster-whisper</span>'
        f'<span class="tnr-chip" style="background:#312A5D">{ia}</span></div>',
        unsafe_allow_html=True,
    )


def page_funcionalidades() -> None:
    st.markdown('<div class="tnr-eyebrow" style="color:#4C4295">Funcionalidades</div>', unsafe_allow_html=True)
    st.markdown("# Tudo que você precisa para legendar")
    st.markdown("Do upload à exportação, o fluxo cabe em uma única página.")
    st.markdown(
        '<div class="tnr-grid">'
        + card("upload", "#312A5D", "Upload de vídeo", "Arraste e solte o arquivo. Formatos comuns como MP4, MOV, MKV, AVI e WEBM.")
        + card("mic", "#4C4295", "Gravação pelo microfone", "Fale uma frase e veja-a virar texto com tempo, sem precisar de vídeo.")
        + card("wave", "#7D54AC", "Transcrição automática", "Whisper rodando localmente, com detecção de idioma e tempos por trecho.")
        + card("edit", "#312A5D", "Revisão das legendas", "Edite o texto na tabela e, opcionalmente, deixe a IA revisar ou traduzir.")
        + card("download", "#4C4295", "Exportação em SRT, VTT e TXT", "Baixe o arquivo pronto para YouTube, players e editores de vídeo.")
        + card("screen", "#7D54AC", "Pré-visualização", "Assista ao vídeo com as legendas ligadas para conferir o sincronismo.")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.button("Ir para a demonstração", key="cta2", type="primary", on_click=go_demo)


# ---------- demonstração
LANGS = {"Português (Brasil)": "pt", "English": "en", "Español": "es", "Detectar automaticamente": None}
LANG_NAMES = {"pt": "português", "en": "inglês", "es": "espanhol"}
MODELS = {
    "base": "base — rápido",
    "small": "small — equilibrado (recomendado)",
    "medium": "medium — mais preciso, mais lento",
}
TARGETS = {"Não traduzir": None, "Inglês": "inglês", "Espanhol": "espanhol", "Português": "português do Brasil"}
VIDEO_TYPES = ["mp4", "mov", "mkv", "avi", "webm"]
MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
}


@st.cache_resource(show_spinner=False)
def get_model(size: str):
    return tr.load_model(size)


def process_media(path: str, source: str, media: bytes, suffix: str, is_video: bool, opts: dict) -> None:
    with st.status("Processando…", expanded=True) as status:
        try:
            st.write("Carregando o modelo Whisper (na primeira vez pode demorar)…")
            model = get_model(opts["model"])

            st.write("Transcrevendo o áudio…")
            bar = st.progress(0.0)
            live = st.empty()

            def on_progress(frac: float, text: str) -> None:
                bar.progress(min(max(frac, 0.0), 1.0))
                if text:
                    live.caption(text)

            segs, info = tr.run(
                model, path, opts["language"], vad=True, fast=opts["fast"], short=opts["short"], on_progress=on_progress
            )
            if not segs:
                status.update(label="Nenhuma fala detectada", state="error")
                st.warning("Não encontrei fala nesse arquivo. Confira o áudio e o idioma escolhido.")
                return

            notes: list[str] = []
            translations: dict[str, list[sub.Seg]] = {}
            if opts["ai"]:
                lang_name = LANG_NAMES.get(info.language, info.language)
                st.write("Revisando o texto com a IA (DeepSeek)…")
                segs, failed = llm.process(segs, "review", language=lang_name)
                if failed:
                    notes.append(f"A revisão por IA não alterou {failed} trecho(s); mantive o texto original.")
                if opts["target"]:
                    st.write(f"Traduzindo para {opts['target']}…")
                    translated, failed = llm.process(segs, "translate", target=opts["target"])
                    translations[opts["target_label"]] = translated
                    if failed:
                        notes.append(f"{failed} trecho(s) ficaram sem tradução.")

            st.session_state["result"] = {
                "id": time.time_ns(),
                "source": source,
                "segs": segs,
                "media": media,
                "suffix": suffix,
                "is_video": is_video,
                "lang": info.language,
                "translations": translations,
                "notes": notes,
            }
            status.update(label=f"Pronto! {len(segs)} legendas geradas.", state="complete", expanded=False)
        except Exception as exc:  # mostra o erro de forma amigável
            status.update(label="Algo deu errado", state="error")
            st.error(f"Não consegui concluir: {exc}")


def run_from_bytes(data: bytes, name: str, is_video: bool, opts: dict) -> None:
    suffix = Path(name).suffix.lower() or (".mp4" if is_video else ".wav")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.close()
        process_media(tmp.name, name, data, suffix, is_video, opts)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def render_result() -> None:
    r = st.session_state.get("result")
    if not r:
        return
    with st.container(key="results"):
        st.markdown("### Resultado")
        for note in r["notes"]:
            st.info(note)
        left, right = st.columns([5, 6], gap="large")

        with right:
            st.caption(
                f"Idioma detectado: {LANG_NAMES.get(r['lang'], r['lang'])}. "
                "Edite a coluna “Legenda” para corrigir o texto."
            )
            df = pd.DataFrame(
                {
                    "Início": [sub.fmt_clock(s.start) for s in r["segs"]],
                    "Fim": [sub.fmt_clock(s.end) for s in r["segs"]],
                    "Legenda": [s.text for s in r["segs"]],
                }
            )
            edited = st.data_editor(
                df,
                key=f"editor_{r['id']}",
                hide_index=True,
                disabled=["Início", "Fim"],
                column_config={"Legenda": st.column_config.TextColumn("Legenda", width="large")},
                height=min(440, 45 + 36 * len(df)),
            )
        final = [
            sub.Seg(s.start, s.end, str(t if t is not None else "").strip())
            for s, t in zip(r["segs"], edited["Legenda"])
        ]

        with left:
            tracks = {"Original": sub.to_vtt(final).encode("utf-8")}
            for label, tsegs in r["translations"].items():
                tracks[label] = sub.to_vtt(tsegs).encode("utf-8")
            if r["is_video"]:
                st.video(r["media"], format=MIME.get(r["suffix"], "video/mp4"), subtitles=tracks)
                st.caption("Ative as legendas no player (ícone CC). Alguns formatos, como MKV, podem não tocar no navegador.")
            else:
                st.audio(r["media"])

        stem = Path(r["source"]).stem or "legendas"
        st.markdown("#### Baixar")
        cols = st.columns(3 + len(r["translations"]))
        cols[0].download_button("Baixar .SRT", sub.to_srt(final), f"{stem}.srt", "application/x-subrip", key=f"srt_{r['id']}")
        cols[1].download_button("Baixar .VTT", sub.to_vtt(final), f"{stem}.vtt", "text/vtt", key=f"vtt_{r['id']}")
        cols[2].download_button("Baixar .TXT", sub.to_txt(final), f"{stem}.txt", "text/plain", key=f"txt_{r['id']}")
        for col, (label, tsegs) in zip(cols[3:], r["translations"].items()):
            col.download_button(
                f"Baixar SRT ({label})", sub.to_srt(tsegs), f"{stem}.{label[:2].lower()}.srt", "application/x-subrip",
                key=f"srt_{label}_{r['id']}",
            )


def page_demo() -> None:
    st.markdown('<div class="tnr-eyebrow" style="color:#4C4295">Demonstração</div>', unsafe_allow_html=True)
    st.markdown("# Gere suas legendas")

    ai_ready = llm.is_configured()
    with st.container(key="opts"):
        c1, c2 = st.columns(2)
        model = c1.selectbox("Modelo Whisper", list(MODELS), index=1, format_func=MODELS.get)
        lang_label = c2.selectbox("Idioma do áudio", list(LANGS))
        c3, c4 = st.columns(2)
        short = c3.checkbox("Legendas curtas (recomendado)", value=True, help="Usa tempos por palavra para quebrar o texto em legendas legíveis.")
        fast = c4.checkbox("Priorizar velocidade", value=True, help="Busca mais rápida na CPU, com pequena perda de precisão.")
        c5, c6 = st.columns(2)
        ai = c5.toggle(
            "Revisar com IA (DeepSeek)",
            value=False,
            disabled=not ai_ready,
            help="Corrige pontuação e termos. Envia o texto a um serviço externo."
            if ai_ready
            else "Defina DEEPSEEK_API_KEY no arquivo .env para ativar.",
        )
        target_label = c6.selectbox("Traduzir legendas para", list(TARGETS), disabled=not (ai_ready and ai))

    opts = {
        "model": model,
        "language": LANGS[lang_label],
        "short": short,
        "fast": fast,
        "ai": bool(ai and ai_ready),
        "target": TARGETS[target_label] if (ai and ai_ready) else None,
        "target_label": target_label,
    }

    tab_video, tab_mic = st.tabs(["Enviar vídeo", "Gravar áudio"])
    with tab_video:
        up = st.file_uploader("Arraste o vídeo aqui", type=VIDEO_TYPES, key="uploader")
        if up is not None:
            st.caption(f"{up.name} · {up.size / 1_048_576:.1f} MB")
        if st.button("Gerar legendas", type="primary", disabled=up is None, key="go_video"):
            run_from_bytes(up.getvalue(), up.name, True, opts)

    with tab_mic:
        if not hasattr(st, "audio_input"):
            st.warning("Atualize o Streamlit (pip install -U streamlit) para usar a gravação pelo microfone.")
        else:
            audio = st.audio_input("Fale ao microfone (frases curtas funcionam melhor)", key="mic")
            if st.button("Transcrever gravação", type="primary", disabled=audio is None, key="go_mic"):
                run_from_bytes(audio.getvalue(), "gravacao.wav", False, opts)

    render_result()


# ------------------------------------------------------------------ main
inject_css()
page = navbar()
if page == "Sobre o Projeto":
    page_sobre()
elif page == "Funcionalidades":
    page_funcionalidades()
else:
    page_demo()
