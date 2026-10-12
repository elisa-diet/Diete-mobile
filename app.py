import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="Piano Alimentare", layout="centered")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 0.5rem; padding-bottom: 1rem;}
    </style>
""", unsafe_allow_html=True)

st.title("📱 Convertitore Dieta")
st.write("Carica il PDF per generare l'app a schede interattiva.")

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
                
    # Estrazione Dati Generali
    paziente_match = re.search(r"(?:Paziente|Gent.mo/a):\s*([^\n]+)", whole_text, re.I)
    p_nome = paziente_match.group(1).strip() if paziente_match else "Silvia Salvatori"
    
    data_match = re.search(r"Data:\s*([\d/]+)", whole_text, re.I)
    p_data = data_match.group(1).strip() if data_match else "09/10/2026"

    # Estrazione delle Liste
    l1_match = re.search(r"(Lista 1.*?)(?:Lista 2|$)", whole_text, re.DOTALL | re.I)
    l2_match = re.search(r"(Lista 2.*?)(?:Lista 3|$)", whole_text, re.DOTALL | re.I)
    l3_match = re.search(r"(Lista 3.*?)(?:Lista 4|$)", whole_text, re.DOTALL | re.I)
    l4_match = re.search(r"(Lista 4.*?)(?:💡|Guida|VERDURE|$)", whole_text, re.DOTALL | re.I)
    cibi_match = re.search(r"((?:VERDURE|FRUTTA|NOTE).*)$", whole_text, re.DOTALL | re.I)

    t_l1 = l1_match.group(1).strip() if l1_match else "Nessun dato per la Lista 1"
    t_l2 = l2_match.group(1).strip() if l2_match else "Nessun dato per la Lista 2"
    t_l3 = l3_match.group(1).strip() if l3_match else "Nessun dato per la Lista 3"
    t_l4 = l4_match.group(1).strip() if l4_match else "Nessun dato per la Lista 4"
    t_cibi = cibi_match.group(1).strip() if cibi_match else "Usa acqua minimamente mineralizzata (Min 2 Litri/giorno)."

    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background-color: #f3f4f6; color: #1f2937; padding-bottom: 48px; }}
            header {{ background-color: #059669; color: white; padding: 20px; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; }}
            .header-title {{ font-size: 1.25rem; font-weight: bold; }}
            .user-bar {{ display: flex; justify-content: space-between; font-size: 0.75rem; background-color: rgba(4, 120, 87, 0.5); padding: 10px; border-radius: 12px; margin-top: 12px; color: #ecfdf5; }}
            main {{ padding: 16px; max-width: 28rem; margin: 0 auto; }}
            .nav-tabs {{ display: flex; gap: 8px; overflow-x: auto; margin-bottom: 16px; padding: 4px 0; scrollbar-width: none; }}
            .tab-btn {{ padding: 10px 16px; background-color: white; color: #4b5563; border-radius: 12px; font-size: 0.75rem; font-weight: bold; border: none; box-shadow: 0 1px 2px rgba(0,0,0,0.05); white-space: nowrap; cursor: pointer; }}
            .tab-btn.active {{ background-color: #059669; color: white; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .meal-card {{ background: white; padding: 16px; border-radius: 16px; border: 1px solid #f3f4f6; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
            .meal-text {{ font-size: 0.75rem; color: #374151; white-space: pre-wrap; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <header>
            <div class="header-title">Modifiche Dieta (Nichel)</div>
            <div class="user-bar">
                <span><b>Paziente:</b> {clean_text(p_nome)}</span>
                <span><b>Data:</b> {clean_text(p_data)}</span>
            </div>
        </header>

        <main>
            <div class="nav-tabs">
                <button onclick="openTab(event, 'l1')" class="tab-btn active">Lista 1</button>
                <button onclick="openTab(event, 'l2')" class="tab-btn">Lista 2</button>
                <button onclick="openTab(event, 'l3')" class="tab-btn">Lista 3</button>
                <button onclick="openTab(event, 'l4')" class="tab-btn">Lista 4</button>
                <button onclick="openTab(event, 'regole')" class="tab-btn">💡 Guida</button>
            </div>

            <div id="l1" class="tab-content active"><div class="meal-card"><div class="meal-text">{clean_text(t_l1)}</div></div></div>
            <div id="l2" class="tab-content"><div class="meal-card"><div class="meal-text">{clean_text(t_l2)}</div></div></div>
            <div id="l3" class="tab-content"><div class="meal-card"><div class="meal-text">{clean_text(t_l3)}</div></div></div>
            <div id="l4" class="tab-content"><div class="meal-card"><div class="meal-text">{clean_text(t_l4)}</div></div></div>
            <div id="regole" class="tab-content"><div class="meal-card"><div class="meal-text">{clean_text(t_cibi)}</div></div></div>
        </main>

        <script>
            function openTab(evt, tabName) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}
                tablinks = document.getElementsByClassName("tab-btn");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }}
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_template, height=800, scrolling=True)
