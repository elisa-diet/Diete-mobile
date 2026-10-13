import streamlit as st
import PyPDF2
import re
import os

if not os.path.exists("requirements.txt"):
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("streamlit>=1.30.0\nPyPDF2>=3.0.0\n")

st.set_page_config(page_title="Visualizzatore Dieta VLCKD", page_icon="🥗", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; color: #212529; font-family: sans-serif; }
    .header-card { background: linear-gradient(135deg, #2e7d32, #4caf50); color: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px; text-align: center; }
    .patient-info { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 25px; border-left: 5px solid #2e7d32; }
    .horizontal-scroll-container { display: flex; flex-wrap: nowrap; overflow-x: auto; padding: 15px 5px; gap: 20px; -webkit-overflow-scrolling: touch; }
    .day-card { flex: 0 0 320px; background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 5px solid #4caf50; transition: transform 0.2s; }
    .day-card:hover { transform: translateY(-5px); }
    .meal-title { font-weight: bold; color: #2e7d32; margin-top: 15px; margin-bottom: 5px; font-size: 0.95rem; letter-spacing: 0.5px; border-bottom: 1px dashed #ddd; padding-bottom: 3px; }
    .food-box { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .allowed-list { color: #1b5e20; list-style-type: '✅ '; padding-left: 20px;}
    .forbidden-list { color: #b71c1c; list-style-type: '❌ '; padding-left: 20px;}
</style>
""", unsafe_allow_index=True)

def parse_diet_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n"
    data = {}
    paziente_match = re.search(r"Paziente:\s*([^\n*#]+)", full_text, re.IGNORECASE)
    peso_match = re.search(r"Peso:\s*([^\n*#]+)", full_text, re.IGNORECASE)
    bmi_match = re.search(r"BMI:\s*([^\n*#]+)", full_text, re.IGNORECASE)
    obiettivo_match = re.search(r"Obiettivo:\s*([^\n*#]+)", full_text, re.IGNORECASE)
    dott_match = re.search(r"(Dott\..*?)\n", full_text, re.IGNORECASE)
    data['paziente'] = paziente_match.group(1).strip() if paziente_match else "Paziente Anonimo"
    data['peso'] = peso_match.group(1).strip() if peso_match else "N/D"
    data['bmi'] = bmi_match.group(1).strip() if bmi_match else "N/D"
    data['obiettivo'] = obiettivo_match.group(1).strip() if obiettivo_match else "N/D"
    data['medico'] = dott_match.group(1).strip() if dott_match else "Biologa Nutrizionista"
    acqua_match = re.search(r"Acqua:\s*([^\n]+)", full_text, re.IGNORECASE)
    controllo_match = re.search(r"Controllo:\s*([^\n]+)", full_text, re.IGNORECASE)
    data['acqua'] = acqua_match.group(1).strip() if acqua_match else "Min 2 Litri/giorno"
    data['controllo'] = controllo_match.group(1).strip() if controllo_match else "Tra 1 mese"
    data['giorni'] = []
    pattern_liste = r"(🗓\s*Giornat[e|a]:.*?)(?=🗓\s*Giornat[e|a]:|###\s*🥬|###\s*🍎|STRETTAMENTE|$)"
    blocchi = re.findall(pattern_liste, full_text, re.DOTALL | re.IGNORECASE)
    for blocco in blocchi:
        linee = blocco.split('\n')
        titolo = linee[0].replace('🗓', '').strip()
        pasti = {}
        pasto_corrente = None
        contenuto_pasto = []
        for linea in linee[1:]:
            linea_clean = linea.strip()
            if not linea_clean:
                continue
            if any(p in linea_clean.upper() for p in ["COLAZIONE", "SPUNTINO MATTINA", "PRANZO", "SPUNTINO POMERIGGIO", "CENA", "CONDIMENTI"]):
                if pasto_corrente:
                    pasti[pasto_corrente] = "\n".join(contenuto_pasto)
                pasto_corrente = linea_clean
                contenuto_pasto = []
            elif pasto_corrente:
                contenuto_pasto.append(linea_clean)
        if pasto_corrente:
            pasti[pasto_corrente] = "\n".join(contenuto_pasto)
        data['giorni'].append({"titolo": titolo, "pasti": pasti})
    def extract_section(allowed_pattern, avoid_pattern, text):
        allowed = re.search(allowed_pattern, text, re.DOTALL | re.IGNORECASE)
        avoid = re.search(avoid_pattern, text, re.DOTALL | re.IGNORECASE)
        return (allowed.group(1).strip() if allowed else "", avoid.group(1).strip() if avoid else "")
    v_ok, v_no = extract_section(r"✅\s*Verdure Consentite\n(.*?)(?=❌|$)", r"❌\s*Verdure da Evitare\n(.*?)(?=###|🍎|$)", full_text)
    f_ok, f_no = extract_section(r"✅\s*Frutta Consentite.*\n(.*?)(?=❌|$)", r"❌\s*Frutta da Evitare\n(.*?)(?=STRETTAMENTE|$)", full_text)
    data['verdure'] = {"ok": v_ok, "no": v_no}
    data['frutta'] = {"ok": f_ok, "no": f_no}
    integrazione = re.search(r"INTEGRAZIONE CONSIGLIATA\n(.*?)(?=###|$)", full_text, re.DOTALL | re.IGNORECASE)
    vietati = re.search(r"STRETTAMENTE VIETATI\n([^\n]+)", full_text, re.IGNORECASE)
    data['integrazione'] = integrazione.group(1).strip() if integrazione else ""
    data['vietati'] = vietati.group(1).strip() if vietati else ""
    return data

st.markdown('<div class="header-card"><h1>Piano Alimentare VLCKD</h1><p>Carica il PDF per generare la dieta digitale interattiva</p></div>', unsafe_allow_index=True)
uploaded_file = st.file_uploader("📂 Rilascia o seleziona il file PDF della dieta", type=["pdf"])

if uploaded_file is not None:
    try:
        pazio = parse_diet_pdf(uploaded_file)
        st.markdown(f"<p style='text-align:center; color:#666; font-style: italic;'>{pazio.get('medico', 'Biologa Nutrizionista')}</p>", unsafe_allow_index=True)
        st.markdown(f"""
        <div class="patient-info">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; row-gap: 10px;">
                <div>👤 <b>Paziente:</b> {pazio['paziente']}</div>
                <div>⚖️ <b>Peso Attuale:</b> {pazio['peso']}</div>
                <div>📊 <b>BMI:</b> {pazio['bmi']}</div>
                <div>🎯 <b>Obiettivo:</b> <span style="color:#2e7d32; font-weight:bold;">{pazio['obiettivo']}</span></div>
            </div>
            <hr style="margin: 12px 0; border:0; border-top:1px solid #eee;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; font-size: 0.95rem; color: #555;">
                <div>💧 <b>Idratazione:</b> {pazio['acqua']}</div>
                <div>📅 <b>Prossimo Controllo:</b> {pazio['controllo']}</div>
            </div>
        </div>
        """, unsafe_allow_index=True)
        st.subheader("🗓️ Giorni e Liste Alimentari")
        st.caption("Scorri lateralmente ➡️ per visualizzare tutti i giorni del piano")
        scroll_html = '<div class="horizontal-scroll-container">'
        for g in pazio['giorni']:
            card_content = f'<div class="day-card"><h3>{g["titolo"]}</h3>'
            for pasto, desc in g['pasti'].items():
                desc_html = desc.replace('\n', '<br>').replace('- ', '• ')
                card_content += f'<div class="meal-title">{pasto}</div><div style="font-size:0.9rem; color:#424242;">{desc_html}</div>'
            card_content += '</div>'
            scroll_html += card_content
        scroll_html += '</div>'
        st.markdown(scroll_html, unsafe_allow_index=True)
        if pazio.get('integrazione'):
            st.markdown("---")
            st.subheader("💊 Integrazione Consigliata")
            st.info(pazio['integrazione'])
        st.markdown("---")
        st.subheader("💡 Guida Alimenti & Tabelle di Riferimento")
        tab1, tab2, tab3 = st.tabs(["🥬 Verdure", "🍎 Frutta", "⚠️ Alimenti Vietati"])
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="food-box"><h4 style="color:#1b5e20;">Consentite</h4><div class="allowed-list">{pazio["verdure"]["ok"].replace("- ", "").replace("\n", "<br>")}</div></div>', unsafe_allow_index=True)
            with col2:
                st.markdown(f'<div class="food-box"><h4 style="color:#b71c1c;">Da Evitare</h4><div class="forbidden-list">{pazio["verdure"]["no"].replace("- ", "").replace("\n", "<br>")}</div></div>', unsafe_allow_index=True)
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="food-box"><h4 style="color:#1b5e20;">Consentita (100g)</h4><div class="allowed-list">{pazio["frutta"]["ok"].replace("- ", "").replace("\n", "<br>")}</div></div>', unsafe_allow_index=True)
            with col2:
                st.markdown(f'<div class="food-box"><h4 style="color:#b71c1c;">Da Evitare</h4><div class="forbidden-list">{pazio["frutta"]["no"].replace("- ", "").replace("\n", "<br>")}</div></div>', unsafe_allow_index=True)
        with tab3:
            if pazio.get('vietati'):
                st.error(f"🚫 **STRETTAMENTE VIETATI:** {pazio['vietati']}")
            else:
                st.error("🚫 **STRETTAMENTE VIETATI:** Pane, grissini, pizza, crackers, pasta, riso, cereali, farine, patate, legumi, dolci, biscotti, zuccheri, fruttosio, miele, alcolici, bibite gassate.")
    except Exception as e:
        st.error(f"Errore nella lettura del PDF. Verifica la struttura del testo. Dettaglio: {e}")
else:
    st.info("👋 In attesa del file. Trascina qui sopra il PDF della dieta per visualizzarla all'istante.")
