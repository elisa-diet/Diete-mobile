import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="Piano Alimentare", layout="centered")

# Nascondiamo i menu di Streamlit per pulizia visiva
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 0.5rem; padding-bottom: 1rem;}
    </style>
""", unsafe_allow_html=True)

st.title("📱 Convertitore Dieta v2")
st.write("Carica il PDF per attivare la visualizzazione interattiva.")

uploaded_file = st.file_uploader("Seleziona il PDF della dieta", type="pdf")

def clean_text(text):
    if not text: return ""
    return text.replace("'", "\\'").replace('"', '\\"').strip()

if uploaded_file is not None:
    whole_text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                whole_text += page.extract_text() + "\n"
                
    # Estrazione intelligente del Paziente (cerca parole chiave nel PDF)
    paziente_match = re.search(r"(?:Paziente|Gent.mo/a|Sig./ra):\s*([^\n]+)", whole_text, re.I)
    p_nome = paziente_match.group(1).strip() if paziente_match else "Silvia Salvatori"

    # Estrazione dei singoli pasti usando le scritte del tuo PDF
    colazione = re.search(r"COLAZIONE\s*(.*?)(?=PRANZO)", whole_text, re.DOTALL | re.I)
    pranzo = re.search(r"PRANZO\s*(.*?)(?=SPUNTINO)", whole_text, re.DOTALL | re.I)
    spuntino = re.search(r"SPUNTINO\s*(.*?)(?=CENA)", whole_text, re.DOTALL | re.I)
    cena = re.search(r"CENA\s*(.*?)(?=$)", whole_text, re.DOTALL | re.I)

    t_colazione = colazione.group(1).strip() if colazione else "Vedi PDF originale"
    t_pranzo = pranzo.group(1).strip() if pranzo else "Vedi PDF originale"
    t_spuntino = spuntino.group(1).strip() if spuntino else "Vedi PDF originale"
    t_cena = cena.group(1).strip() if cena else "Vedi PDF originale"

    # Modello HTML con la tua splendida grafica verde originale e le schede interattive
    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background-color: #f3f4f6; color: #1f2937; padding: 12px; }}
            header {{ background-color: #059669; color: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 16px; }}
            .header-title {{ font-size: 1.25rem; font-weight: bold; }}
            .user-bar {{ font-size: 0.75rem; background-color: rgba(4, 120, 87, 0.5); padding: 8px; border-radius: 10px; margin-top: 8px; color: #ecfdf5; }}
            .nav-tabs {{ display: flex; gap: 8px; margin-bottom: 16px; }}
            .tab-btn {{ padding: 10px 16px; background-color: white; color: #4b5563; border-radius: 12px; font-size: 0.75rem; font-weight: bold; border: none; cursor: pointer; flex: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
            .tab-btn.active {{ background-color: #059669; color: white; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .meal-card {{ background: white; padding: 16px; border-radius: 16px; border: 1px solid #f3f4f6; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
            .meal-title {{ color: #059669; font-weight: bold; font-size: 0.85rem; margin-bottom: 8px; border-bottom: 1px solid #f3f4f6; padding-bottom: 4px; }}
            .meal-text {{ font-size: 0.75rem; color: #374151; white-space: pre-wrap; line-height: 1.4; }}
        </style>
    </head>
    <body>
        <header>
            <div class="header-title">Modifiche Dieta (Nichel)</div>
            <div class="user-bar">
                <span><b>Paziente:</b> {clean_text(p_nome)}</span>
            </div>
        </header>

        <div class="nav-tabs">
            <button onclick="showTab('menu-giorno')" class="tab-btn active">📅 Oggi</button>
            <button onclick="showTab('info-cibi')" class="tab-btn">💡 Info Cibi</button>
        </div>

        <div id="menu-giorno" class="tab-content active">
            <div class="meal-card">
                <div class="meal-title">☕ COLAZIONE</div>
                <div class="meal-text">{clean_text(t_colazione)}</div>
            </div>
            <div class="meal-card">
                <div class="meal-title">🥗 PRANZO</div>
                <div class="meal-text">{clean_text(t_pranzo)}</div>
            </div>
            <div class="meal-card">
                <div class="meal-title">🍎 SPUNTINO</div>
                <div class="meal-text">{clean_text(t_spuntino)}</div>
            </div>
            <div class="meal-card">
                <div class="meal-title">🌙 CENA</div>
                <div class="meal-text">{clean_text(t_cena)}</div>
            </div>
        </div>

        <div id="info-cibi" class="tab-content">
            <div class="meal-card">
                <div class="meal-title">ℹ️ NOTE E INDICAZIONI</div>
                <div class="meal-text">Usa l'acqua minimamente mineralizzata (2 Litri al giorno). Evita stoviglie e pentole in acciaio inox non certificato per nichel.</div>
            </div>
        </div>

        <script>
            function showTab(tabId) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                event.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_template, height=800, scrolling=True)
