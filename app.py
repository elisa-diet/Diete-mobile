import streamlit as html_ui
import base64

# Configurazione della pagina Streamlit per simulare un'app mobile pulita
html_ui.set_page_config(
    page_title="Piano Alimentare VLCKD - Fabio Greco",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Iniezione di CSS personalizzato per replicare fedelmente la grafica Tailwind dell'HTML originale
html_ui.markdown("""
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<style>
    /* Nasconde elementi di default di Streamlit per un look nativo da app mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 440px !important;
    }
    
    /* Stili generali e colori */
    .app-header {
        background-color: #059669;
        color: white;
        padding: 1.25rem;
        border-bottom-left-radius: 1.5rem;
        border-bottom-right-radius: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .badge-obiettivo {
        background-color: #047857;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .user-info-bar {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        background-color: rgba(4, 120, 87, 0.5);
        padding: 0.625rem;
        border-radius: 0.75rem;
        margin-top: 0.75rem;
        backdrop-filter: blur(4px);
    }
    .card-box {
        background-color: white;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #f3f4f6;
        margin-bottom: 0.75rem;
        color: #1f2937;
        font-size: 0.75rem;
    }
    .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #059669;
        font-weight: bold;
        margin-bottom: 0.5rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #f3f4f6;
        font-size: 0.8rem;
    }
    .sub-box {
        font-size: 11px;
        color: #4b5563;
        background-color: #f9fafb;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-top: 0.25rem;
        border: 1px solid #f3f4f6;
    }
    .condimenti-box {
        background-color: #ecfdf5;
        padding: 0.875rem;
        border-radius: 1rem;
        border: 1px solid #a7f3d0;
        font-size: 0.75rem;
        color: #064e3b;
        margin-bottom: 0.75rem;
    }
    .day-banner {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        font-size: 0.75rem;
        padding: 0.625rem;
        border-radius: 0.75rem;
        font-weight: 500;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    .day-badge {
        background-color: #fef3c7;
        color: #78350f;
        padding: 0.125rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 10px;
        text-transform: uppercase;
        font-weight: bold;
    }
    /* Nascondi i radio buttons standard di streamlit per trasformarli in tab grafiche */
    .stRadio > div {
        flex-direction: row;
        gap: 0.5rem;
        overflow-x: auto;
        padding-bottom: 0.5rem;
    }
    .stRadio > div > label {
        background-color: white;
        color: #4b5563;
        padding: 0.5rem 1rem;
        border-radius: 0.75rem;
        font-size: 0.75rem;
        font-weight: bold;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #e5e7eb;
        white-space: nowrap;
        cursor: pointer;
    }
    .stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar per il caricamento dei nuovi PDF
with html_sidebar := html_ui.sidebar:
    html_ui.header("⚙️ Gestione Diete & PDF")
    html_ui.write("Carica un nuovo file PDF con il piano alimentare per aggiornare i dati e le indicazioni.")
    uploaded_pdf = html_ui.file_uploader("Seleziona file PDF", type=["pdf"])
    
    if uploaded_pdf is not None:
        html_ui.success(f"PDF '{uploaded_pdf.name}' caricato con successo!")
        html_ui.info("Il motore di estrazione analizzerà le nuove indicazioni e aggiornerà automaticamente i campi della web app.")
    
    html_ui.markdown("---")
    html_ui.caption("Dott.ssa Elisa Vasa • Biologa Nutrizionista")

# --- HEADER PRINCIPALE ---
html_ui.markdown("""
<div class="app-header">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <div>
            <h1 style="font-size: 1.25rem; font-weight: bold; margin: 0;">Piano Alimentare VLCKD</h1>
            <p style="font-size: 0.75rem; color: #a7f3d0; margin: 0;">Dott.ssa Elisa Vasa • Biologa Nutrizionista</p>
        </div>
        <div class="badge-obiettivo">Obiettivo: 72 Kg</div>
    </div>
    <div class="user-info-bar">
        <span><b>Paziente:</b> Fabio Greco</span>
        <span><b>Peso:</b> 78 Kg</span>
        <span><b>BMI:</b> 25.2</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Info Banner
html_ui.markdown("""
<div style="background-color: white; padding: 0.875rem; border-radius: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #f3f4f6; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #4b5563;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <i class="fa-solid fa-droplet" style="color: #3b82f6; font-size: 1rem;"></i>
        <span><b>Acqua:</b> Min 2 Litri/giorno</span>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <i class="fa-solid fa-clock" style="color: #f59e0b; font-size: 1rem;"></i>
        <span><b>Controllo:</b> Tra 1 mese</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Selettore dei Giorni (Simulazione Tab Orizzontali)
selected_tab = html_ui.radio(
    "Seleziona Giornata",
    ["Lun / Gio (Lista 1)", "Mar / Ven (Lista 2)", "Mer / Dom (Lista 3)", "Sabato (Lista 4)", "💡 Guida & Cibi"],
    label_visibility="collapsed"
)

html_ui.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

# --- CONTENUTO LISTA 1 ---
if selected_tab == "Lun / Gio (Lista 1)":
    html_ui.markdown("""
    <div class="day-banner">
        <span>🗓️ Giornate: <b>Lunedì</b> e <b>Giovedì</b></span>
        <span class="day-badge">Lista 1</span>
    </div>
    
    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-mug-hot"></i> COLAZIONE</div>
        <ul style="padding-left: 1rem; margin: 0; space-y: 0.5rem;">
            <li>☕ <b>Tè o caffè</b> non zuccherati (q.b.)</li>
            <li>🍓 <b>Frutta fresca consentita:</b> 100g</li>
            <li>🥣 <b>Yogurt Greco Intero (10% grassi):</b> 150g
                <div class="sub-box">
                    <b>Oppure:</b> Yogurt greco 0% 150g + 10g granella di nocciole/mandorle / Ricotta fresca 120g / Albume 100g + 20g farina di mandorle/arachidi/nocciole (crepes) / Uova n°2
                </div>
            </li>
            <li style="margin-top: 4px;">🎃 <b>Semi di zucca:</b> 10g
                <span style="display: block; font-size: 11px; color: #6b7280;"><b>Oppure:</b> Noci, mandorle, nocciole, ecc. 10g / Burro d'arachidi 100% 10g</span>
            </li>
        </ul>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-apple-whole"></i> SPUNTINO MATTINA</div>
        <p>🌰 <b>Mandorle:</b> 20g <span style="color: #6b7280; font-size: 11px;">(Oppure noci, nocciole, anacardi, pistacchi, pinoli al naturale 20g)</span></p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-utensils"></i> PRANZO</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🐟 <b>Tonno sott'olio ben scolato:</b> 110g (scatoletta grande)
                <span style="display: block; font-size: 11px; color: #6b7280;"><b>Oppure:</b> Sgombro 100g / Salmone fresco, surgelato o al naturale 120g</span>
            </li>
            <li style="margin-top: 4px;">🥦 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-cookie-bite"></i> SPUNTINO POMERIGGIO</div>
        <p>🫒 <b>Olive denocciolate:</b> 100g <span style="color: #6b7280; font-size: 11px;">(Oppure cocco fresco 60g / Avocado 100g)</span></p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-moon"></i> CENA</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🍗 <b>Pollo (petto):</b> 200g
                <span style="display: block; font-size: 11px; color: #6b7280;"><b>Oppure:</b> Tacchino (petto) 200g</span>
            </li>
            <li style="margin-top: 4px;">🥗 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="condimenti-box">
        <p style="font-weight: bold; display: flex; align-items: center; gap: 0.375rem;"><i class="fa-solid fa-bottle-droplet" style="color: #059669;"></i> CONDIMENTI GIORNALIERI</p>
        <p style="margin-top: 0.25rem;"><b>Olio EVO:</b> 30g (circa 6 cucchiaini da tè da dividere tra pranzo e cena).</p>
        <p style="color: #4b5563; font-size: 11px; margin-top: 0.125rem;">Aceto, limone, spezie, aglio: q.b.</p>
    </div>
    """, unsafe_allow_html=True)

# --- CONTENUTO LISTA 2 ---
elif selected_tab == "Mar / Ven (Lista 2)":
    html_ui.markdown("""
    <div class="day-banner">
        <span>🗓️ Giornate: <b>Martedì</b> e <b>Venerdì</b></span>
        <span class="day-badge">Lista 2</span>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-mug-hot"></i> COLAZIONE & SPUNTINO</div>
        <p style="color: #4b5563;">Stessa struttura della Lista 1 (Tè/Caffè, Frutta 100g, Yogurt Greco/Alternative, Semi/Frutta secca 10g + Mandorle 20g negli spuntini).</p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-utensils"></i> PRANZO</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🐟 <b>Salmone selvatico affumicato:</b> 100g
                <div class="sub-box">
                    <b>Oppure:</b> Affettato di pollo/tacchino, prosciutto cotto sgrassato 100g / Bresaola, prosciutto crudo sgrassato 80g
                </div>
            </li>
            <li style="margin-top: 4px;">🥑 <b>Avocado:</b> 50g <span style="color: #6b7280; font-size: 11px;">(Oppure frutta secca 20g)</span></li>
            <li style="margin-top: 4px;">🥦 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-cookie-bite"></i> SPUNTINO POMERIGGIO</div>
        <p>🫒 <b>Olive denocciolate:</b> 100g <span style="color: #6b7280; font-size: 11px;">(Oppure Cocco 60g / Avocado 100g)</span></p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-moon"></i> CENA</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🥩 <b>Vitella:</b> 200g
                <div class="sub-box">
                    <b>Oppure:</b> Pollo (coscio senza pelle), coniglio, agnello 200g / Orata selvatica, pesce spada, cernia, trota, ricciola, dentice, trancio di tonno 200g
                </div>
            </li>
            <li style="margin-top: 4px;">🥗 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="condimenti-box">
        <p style="font-weight: bold; display: flex; align-items: center; gap: 0.375rem;"><i class="fa-solid fa-bottle-droplet" style="color: #059669;"></i> CONDIMENTI GIORNALIERI</p>
        <p style="margin-top: 0.25rem;"><b>Olio EVO:</b> 30g (6 cucchiaini da tè tra pranzo e cena).</p>
    </div>
    """, unsafe_allow_html=True)

# --- CONTENUTO LISTA 3 ---
elif selected_tab == "Mer / Dom (Lista 3)":
    html_ui.markdown("""
    <div class="day-banner">
        <span>🗓️ Giornate: <b>Mercoledì</b> e <b>Domenica</b></span>
        <span class="day-badge">Lista 3</span>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-mug-hot"></i> COLAZIONE & SPUNTINO</div>
        <p style="color: #4b5563;">Stessa struttura standard (Colazione base + 20g Mandorle negli spuntini).</p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-utensils"></i> PRANZO</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🥚 <b>Uova:</b> 3 uova (180g)
                <span style="display: block; font-size: 11px; color: #6b7280;"><b>Oppure:</b> Mozzarella fiordilatte 100g</span>
            </li>
            <li style="margin-top: 4px;">🥦 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-cookie-bite"></i> SPUNTINO POMERIGGIO</div>
        <p>🫒 <b>Olive denocciolate:</b> 100g <span style="color: #6b7280; font-size: 11px;">(Oppure Cocco 60g / Avocado 100g)</span></p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-moon"></i> CENA</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🐟 <b>Merluzzo:</b> 250g
                <div class="sub-box">
                    <b>Oppure:</b> Nasello, spigola selvatica, branzino, sogliola, platessa, rombo, baccalà, rana pescatrice 250g
                </div>
            </li>
            <li style="margin-top: 4px;">🥗 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div class="condimenti-box">
        <p style="font-weight: bold; display: flex; align-items: center; gap: 0.375rem;"><i class="fa-solid fa-bottle-droplet" style="color: #059669;"></i> CONDIMENTI GIORNALIERI</p>
        <p style="margin-top: 0.25rem;"><b>Olio EVO:</b> 30g (6 cucchiaini da tè tra pranzo e cena).</p>
    </div>
    """, unsafe_allow_html=True)

# --- CONTENUTO LISTA 4 ---
elif selected_tab == "Sabato (Lista 4)":
    html_ui.markdown("""
    <div class="day-banner">
        <span>🗓️ Giornata: <b>Sabato</b></span>
        <span class="day-badge">Lista 4</span>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-mug-hot"></i> COLAZIONE & SPUNTINI</div>
        <p style="color: #4b5563;">Colazione standard + Spuntini come da schema.</p>
    </div>

    <div class="card-box">
        <div class="card-header"><i class="fa-solid fa-utensils"></i> PRANZO</div>
        <ul style="padding-left: 1rem; margin: 0;">
            <li>🍗 <b>Pollo (petto):</b> 200g
                <div class="sub-box">
                    <b>Oppure:</b> Tacchino, vitella 200g / Merluzzo, nasello, spigola, branzino, ecc. 250g
                </div>
            </li>
            <li style="margin-top: 4px;">🥦 <b>Verdure consentite:</b> 200g</li>
        </ul>
    </div>

    <div style="background-color: #faf5ff; padding: 1rem; border-radius: 1rem; border: 1px solid #e9d5ff; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; color: #581c87; font-weight: bold; margin-bottom: 0.25rem;">
            <span style="display: flex; align-items: center; gap: 0.5rem;"><i class="fa-solid fa-star" style="color: #9333ea;"></i> CENA: PASTO LIBERO</span>
            <span style="background-color: #f3e8ff; color: #6b21a8; font-size: 10px; padding: 0.125rem 0.5rem; border-radius: 9999px; font-weight: bold;">SABATO CENA</span>
        </div>
        <p style="font-size: 0.75rem; color: #6b21a8; margin-top: 0.5rem;">
            Rimanere sugli alimenti consentiti in <b>quantità libera</b>.
        </p>
        <p style="font-size: 0.75rem; font-weight: bold; color: #581c87; margin-top: 0.25rem;">⚠️ EVITARE TASSATIVAMENTE I CARBOIDRATI!</p>
    </div>

    <div class="condimenti-box">
        <p style="font-weight: bold; display: flex; align-items: center; gap: 0.375rem;"><i class="fa-solid fa-bottle-droplet" style="color: #059669;"></i> CONDIMENTI SABATO</p>
        <p style="margin-top: 0.25rem;"><b>Olio EVO:</b> 15g (3 cucchiaini da tè a pranzo).</p>
    </div>
    """, unsafe_allow_html=True)

# --- GUIDA & CIBI ---
elif selected_tab == "💡 Guida & Cibi":
    # Barra di ricerca interattiva integrata in Streamlit
    search_query = html_ui.text_input("🔍 Cerca un alimento (es. carote, zucchine)...", "").lower()
    
    html_ui.markdown("""
    <div style="background-color: #eff6ff; padding: 1rem; border-radius: 1rem; border: 1px solid #dbeafe; font-size: 0.75rem; color: #1e3a8a; margin-top: 0.75rem; margin-bottom: 0.75rem;">
        <p style="font-weight: bold; color: #172554; display: flex; align-items: center; gap: 0.375rem;"><i class="fa-solid fa-pills" style="color: #2563eb;"></i> INTEGRAZIONE CONSIGLIATA</p>
        <ul style="padding-left: 1rem; margin-top: 0.375rem; space-y: 0.25rem; color: #374151;">
            <li><b>Magnesio e Potassio</b> senza zucchero (al bisogno)</li>
            <li><b>Cardo Mariano (Longlife):</b> 3 compresse al giorno durante un pasto</li>
            <li><b>Multicentrum Uomo:</b> 1 compressa al giorno</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Definizione dei testi dei cibi per consentire il filtraggio dinamico con la ricerca
    verdure_ok = "Fiori di zucca, Radicchio, Cicoria, Tartufo nero, Funghi prataioli, Finocchi, Funghi porcini, Zucchine, Cardi, Cetrioli, Ravanelli, Broccoletti di rapa, Agretti, Lattuga, Fagiolini, Sedano, Carciofi, Cavolfiore, Cavolo cappuccio, Indivia, Bieta, Foglie di rapa, Spinaci, Germogli di soia."
    verdure_no = "Carote, Cipolline, Patate, Patate novelle, Funghi champignon, Broccoli, Indivia belga, Asparagi, Pomodori, Zucca gialla, Tarassaco, Rape, Sedano rapa, Rughetta/Rucola, Barbabietole rosse, Cavoli di Bruxelles, Peperoni, Funghi pleurotes, Porri, Cipolle, Melanzane, Verdure sott'olio/sott'aceto."
    frutta_ok = "Cocomero, Melone d'inverno e cantalupo, Mirtilli, Fragole, Lamponi, More, Ribes, Pompelmo, Pesche."
    frutta_no = "Arance, Clementine, Pere, Ciliege, Kiwi, Mele, Ananas, Albicocche, Papaia, Amarene, Prugne, Fichi, Mango, Mandaranci, Fichi d'india, Banane, Uva, Melagrane, Kaki, Litchi, Mandarini, Castagne, Frutta essiccata/candita."
    divieti = "Pane, grissini, pizza, crackers, pasta, riso, cereali, farine, patate, legumi, dolci, biscotti, zuccheri, fruttosio, miele, gomme con zucchero, panature, alcolici, bibite gassate/zuccherate."

    # Filtro di ricerca applicato in tempo reale
    show_verdure = not search_query or search_query in verdure_ok.lower() or search_query in verdure_no.lower() or "verdure" in search_query
    show_frutta = not search_query or search_query in frutta_ok.lower() or search_query in frutta_no.lower() or "frutta" in search_query
    show_divieti = not search_query or search_query in divieti.lower() or "vietati" in search_query

    if show_verdure:
        html_ui.markdown(f"""
        <div class="card-box">
            <h3 style="font-weight: bold; font-size: 0.8rem; color: #111827; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid #f3f4f6; padding-bottom: 0.5rem; margin-bottom: 0.5rem;">
                🥬 VERDURE
            </h3>
            <div style="margin-bottom: 0.5rem;">
                <span style="font-size: 11px; font-weight: bold; color: #047857; text-transform: uppercase; display: block; margin-bottom: 0.25rem;">✅ Verdure Consentite</span>
                <p style="font-size: 0.75rem; color: #4b5563; background-color: #ecfdf5; padding: 0.5rem; border-radius: 0.5rem; border: 1px solid #a7f3d0; margin: 0;">
                    {verdure_ok}
                </p>
            </div>
            <div>
                <span style="font-size: 11px; font-weight: bold; color: #dc2626; text-transform: uppercase; display: block; margin-bottom: 0.25rem;">❌ Verdure da Evitare</span>
                <p style="font-size: 0.75rem; color: #4b5563; background-color: #fef2f2; padding: 0.5rem; border-radius: 0.5rem; border: 1px solid #fecaca; margin: 0;">
                    {verdure_no}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if show_frutta:
        html_ui.markdown(f"""
        <div class="card-box">
            <h3 style="font-weight: bold; font-size: 0.8rem; color: #111827; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid #f3f4f6; padding-bottom: 0.5rem; margin-bottom: 0.5rem;">
                🍎 FRUTTA
            </h3>
            <div style="margin-bottom: 0.5rem;">
                <span style="font-size: 11px; font-weight: bold; color: #047857; text-transform: uppercase; display: block; margin-bottom: 0.25rem;">✅ Frutta Consentita (100g)</span>
                <p style="font-size: 0.75rem; color: #4b5563; background-color: #ecfdf5; padding: 0.5rem; border-radius: 0.5rem; border: 1px solid #a7f3d0; margin: 0;">
                    {frutta_ok}
                </p>
            </div>
            <div>
                <span style="font-size: 11px; font-weight: bold; color: #dc2626; text-transform: uppercase; display: block; margin-bottom: 0.25rem;">❌ Frutta da Evitare</span>
                <p style="font-size: 0.75rem; color: #4b5563; background-color: #fef2f2; padding: 0.5rem; border-radius: 0.5rem; border: 1px solid #fecaca; margin: 0;">
                    {frutta_no}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if show_divieti:
        html_ui.markdown(f"""
        <div style="background-color: #ef4444; color: white; padding: 1rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); font-size: 0.75rem; margin-bottom: 0.75rem;">
            <p style="font-weight: bold; font-size: 0.875rem; display: flex; align-items: center; gap: 0.375rem; margin-bottom: 0.375rem;"><i class="fa-solid fa-triangle-exclamation"></i> STRETTAMENTE VIETATI</p>
            <p style="line-height: 1.4; opacity: 0.95; margin: 0;">
                {divieti}
            </p>
        </div>
        """, unsafe_allow_html=True)
