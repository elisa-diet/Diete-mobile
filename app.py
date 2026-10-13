import streamlit as st, PyPDF2, re
st.set_page_config(page_title="Dieta Digitale", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.stApp{background:#f8f9fa;color:#212529;font-family:sans-serif;}.header-card{background:linear-gradient(135deg,#2e7d32,#4caf50);color:white;padding:25px;border-radius:15px;text-align:center;margin-bottom:20px;}.patient-info{background:white;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:20px;border-left:5px solid #2e7d32;}.horizontal-scroll-container{display:flex;flex-wrap:nowrap;overflow-x:auto;padding:10px 0;gap:15px;-webkit-overflow-scrolling:touch;}.day-card{flex:0 0 320px;background:white;border-radius:12px;padding:20px;box-shadow:0 4px 10px rgba(0,0,0,0.08);border-top:5px solid #4caf50;}.meal-title{font-weight:bold;color:#2e7d32;margin-top:12px;margin-bottom:4px;font-size:0.95rem;border-bottom:1px dashed #ddd;padding-bottom:2px;}.food-box{background:white;padding:15px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);}</style>", unsafe_allow_html=True)

def parse_diet_pdf(file):
    pdf, full_text, pages_text = PyPDF2.PdfReader(file), "", []
    for p in pdf.pages:
        t = p.extract_text()
        if t: pages_text.append(t); full_text += t + "\n"
    d, np = {}, "Paziente Rilevato"
    sm = re.search(r"NOME\s+([a-zA-Z\s]+)\s+COGNOME\s+([a-zA-Z\s\n]+)", full_text, re.I)
    if sm: np = f"{sm.group(1).strip()} {sm.group(2).strip().split('\n')[0].strip()}"
    else:
        for pt in pages_text:
            for l in [ln.strip() for ln in pt.split('\n') if ln.strip()][:8]:
                if not any(k in l.upper() for k in ["STUDIO","TEL","EMAIL","WEB","DOTTSA","DIETA","PIANO","BIOLOGA","MODIFICHE","PAGE"]) and len(l.split())>=2 and re.match(r"^[a-zA-Z\s]+$",l):
                    np = l; break
            if np != "Paziente Rilevato": break
    d['paziente'] = np
    td = re.search(r"((?:PIANO\s+ALIMENTARE\s+VLCKD|PIANO\s+ALIMENTARE\s+DA\s+\d+\s*Kcal|MODIFICHE\s+DIETA))", full_text, re.I)
    d['tipo_dieta'] = td.group(1).strip() if td else "Piano Alimentare Personalizzato"
    pm, am, bm, om, cm = re.search(r"PESO\s*(?:Kg)?\s*([\d,\.]+)",full_text,re.I), re.search(r"ALTEZZA\s*(?:cm)?\s*(\d+)",full_text,re.I), re.search(r"BMI\s*(?:Kg/m\s*\d*)?\s*([\d,\.]+)",full_text,re.I), re.search(r"OBIETTIVO:?\s*([^\n\)]+)",full_text,re.I), re.search(r"Prossimo controllo\s*([^\n]+)",full_text,re.I)
    d['peso'], d['altezza'], d['bmi'], d['obiettivo'], d['controllo'] = f"{pm.group(1)} Kg" if pm else "N/D", f"{am.group(1)} cm" if am else "N/D", bm.group(1) if bm else "N/D", om.group(1).strip() if om else "Raggiungimento peso desiderabile", cm.group(1).strip() if cm else "Vedere PDF"
    d['giorni'] = []
    for pt in pages_text:
        if "LISTA" in pt.upper():
            nl = re.search(r"LISTA\s*(\d+)", pt, re.I)
            if not nl: continue
            tl = f"Lista {nl.group(1)}"
            gm = re.search(r"([A-ZÈÒÀÙÌa-zèòàùì\s]+(?:\s*[-–]\s*[A-ZÈÒÀÙÌa-zèòàùì\s]+)+)", pt)
            if gm and any(day in gm.group(1).upper() for day in ["LUNED","MARTED","MERCOLED","GIOVED","VENERD","SABATO","DOMENICA"]): tl += f" ({gm.group(1).strip().replace('\n',' ')})"
            elif "SABATO" in pt.upper() and nl.group(1)=="4": tl += " (SABATO)"
            pasti, pc, cp = {}, None, []
            for l in pt.split('\n'):
                lc = l.strip()
                if not lc: continue
                if any(p in lc.upper() for p in ["COLAZIONE","SPUNTINO","PRANZO","CENA","CONDIMENTI"]):
                    if pc: pasti[pc] = "\n".join(cp)
                    pc = "SPUNTINO POMERIGGIO" if lc.upper()=="SPUNTINO" and "SPUNTINO MATTINA" in pasti else "SPUNTINO MATTINA" if lc.upper()=="SPUNTINO" else lc
                    cp = []
                elif pc and not any(k in lc.upper() for k in ["STUDIO VIA CASSIA","TEL STUDIO","EMAIL:","DOTT.SSA","LISTA","QUESTO REGIME"]): cp.append(lc)
            if pc: pasti[pc] = "\n".join(cp)
            if pasti: d['giorni'].append({"titolo":tl, "pasti":pasti})
    vo = re.search(r"VERDURE CONSENTITE:\s*([^\n\r]+(?:(?!\n[A-Z\s]+:)\n[^\n\r]+)*)", full_text, re.I)
    vn = re.search(r"VERDURE DA EVITARE:\s*([^\n\r]+(?:(?!\n[A-Z\s]+:)\n[^\n\r]+)*)", full_text, re.I)
    fo = re.search(r"FRUTTA CONSENTITA:\s*([^\n\r]+(?:(?!\n[A-Z\s]+:)\n[^\n\r]+)*)", full_text, re.I)
    fn = re.search(r"FRUTTA DA EVITARE:\s*([^\n\r]+(?:(?!\n[A-Z\s]+:)\n[^\n\r]+)*)", full_text, re.I)
    d['v_ok'], d['v_no'], d['f_ok'], d['f_no'] = vo.group(1).strip() if vo else "", vn.group(1).strip() if vn else "", fo.group(1).strip() if fo else "", fn.group(1).strip() if fn else ""
    it = re.search(r"INTEGRAZIONE CONSIGLIATA:\s*(.*?)(?=\n[A-Z\s]{4,}:|$)", full_text, re.S|re.I)
    d['integrazione'] = it.group(1).strip() if it else ""
    return d

st.markdown('<div class="header-card"><h1>Piano Alimentare Digitale</h1><p>Trascina il PDF per generare la dieta del paziente</p></div>', unsafe_allow_html=True)
file = st.file_uploader("📂 Carica il file PDF della dieta", type=["pdf"])
if file is not None:
    try:
        p = parse_diet_pdf(file)
        st.markdown(f"<p style='text-align:center;color:#2e7d32;font-size:1.1rem;font-weight:bold;'>Dott.ssa Elisa Vasa — Biologa Nutrizionista</p>", unsafe_allow_html=True)
        st.markdown(f'<div class="patient-info"><div style="display:flex;flex-wrap:wrap;justify-content:space-between;row-gap:10px;"><div>👤 <b>Paziente:</b> <span style="color:#2e7d32;">{p["paziente"]}</span></div><div>📋 <b>Tipo:</b> {p["tipo_dieta"]}</div><div>⚖️ <b>Peso:</b> {p["peso"]}</div><div>📊 <b>BMI:</b> {p["bmi"]}</div></div><hr style="margin:10px 0;border:0;border-top:1px solid #eee;"><div style="display:flex;flex-wrap:wrap;justify-content:space-between;font-size:0.95rem;color:#555;"><div>🎯 <b>Obiettivo:</b> {p["obiettivo"]}</div><div>📅 <b>Controllo:</b> {p["controllo"]}</div></div></div>', unsafe_allow_html=True)
        if p['giorni']:
            st.subheader("🗓️ Menu Giornalieri")
            scroll_html = '<div class="horizontal-scroll-container">'
            for g in p['giorni']:
                cc = f'<div class="day-card"><h3>{g["titolo"]}</h3>'
                for pasto, desc in g['pasti'].items():
                    dh = desc.replace('\n', '<br>').replace('Oppure:', '<br><strong style="color:#e65100;">Oppure:</strong>')
                    cc += f'<div class="meal-title">{pasto}</div><div style="font-size:0.88rem;color:#333;line-height:1.4;">{dh}</div>'
                cc += '</div>'; scroll_html += cc
            st.markdown(scroll_html+'</div>', unsafe_allow_html=True)
        if p['integrazione']: st.markdown("---"); st.subheader("💊 Integrazione"); st.info(p['integrazione'])
        if p['v_ok'] or p['f_ok']:
            st.markdown("---"); st.subheader("💡 Tabelle Guida Alimenti")
            t1, t2 = st.tabs(["🥬 Verdure", "🍎 Frutta"])
            with t1:
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="food-box"><h4 style="color:#1b5e20;">Consentite</h4><p style="font-size:0.9rem;">{p["v_ok"]}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="food-box"><h4 style="color:#b71c1c;">Da Evitare</h4><p style="font-size:0.9rem;">{p["v_no"]}</p></div>', unsafe_allow_html=True)
            with t2:
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="food-box"><h4 style="color:#1b5e20;">Consentite</h4><p style="font-size:0.9rem;">{p["f_ok"]}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="food-box"><h4 style="color:#b71c1c;">Da Evitare</h4><p style="font-size:0.9rem;">{p["f_no"]}</p></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Errore: {e}")
else: st.info("👋 Trascina qui il PDF della dieta per vederla all'istante.")
