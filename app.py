import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="Dieta App", layout="centered")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
""", unsafe_allow_html=True)

st.title("📱 Convertitore Dieta")
st.write("Carica il PDF per generare l'app a schede.")

uploaded_file = st.file_uploader("Seleziona il PDF", type="pdf")

def clean_text(text):
    if not text: return "Nessun dato"
    return text.replace("'", "\\'").replace('"', '\\"').strip()

if uploaded_file is not None:
    whole_text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                whole_text += page.extract_text() + "\n"
                
    paziente = re.search(r"Paziente:\s*([^\n]+)", whole_text, re.I)
    p_nome = paziente.group(1).strip() if paziente else "Paziente Rilevato"
    
    lista1 = re.search(r"(Lista 1.*?)(?:Lista 2|$)", whole_text, re.DOTALL | re.I)
    l1_text = lista1.group(1) if lista1 else "Dati non trovati"

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: sans-serif; background-color: #f3f4f6; padding: 12px; }}
            header {{ background-color: #059669; color: white; padding: 16px; border-radius: 16px; margin-bottom: 12px; }}
            .card {{ background: white; padding: 14px; border-radius: 14px; border: 1px solid #e5e7eb; font-size: 0.8rem; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <header>
            <h2>Piano Alimentare</h2>
            <p><b>Paziente:</b> {clean_text(p_nome)}</p>
        </header>
        <div class="card">{clean_text(l1_text)}</div>
    </body>
    </html>
    """
    st.components.v1.html(html_template, height=600, scrolling=True)
