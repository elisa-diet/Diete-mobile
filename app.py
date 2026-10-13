# -*- coding: utf-8 -*-
"""
Generatore di web app mobile per piani alimentari (Streamlit).

Carichi uno o più PDF (piano completo, "modifiche dieta", ecc.), controlli i dati
estratti e scarichi (o pubblichi) una pagina HTML in stile app, con tab scorrevoli
orizzontalmente, pronta da inviare al paziente su WhatsApp.

Avvio:  streamlit run app.py
"""
import base64
import hashlib
import html as _html
import io
import re
import secrets
import unicodedata
from urllib.parse import quote

import pdfplumber

# ----------------------------------------------------------------------------
# CONFIGURAZIONE
# ----------------------------------------------------------------------------
PARSER_VERSION = "2026-10-13b"
DEFAULT_PROFESSIONISTA = "Dott.ssa Elisa Vasa • Biologa Nutrizionista"

MEAL_KEYS = ("COLAZIONE", "SPUNTINO", "SPUNTINI", "MERENDA", "PRANZO", "CENA", "COCCOLA", "CONDIMENTI")

DAY_NAMES = {
    "lunedi": "Lunedì", "martedi": "Martedì", "mercoledi": "Mercoledì",
    "giovedi": "Giovedì", "venerdi": "Venerdì", "sabato": "Sabato", "domenica": "Domenica",
}
DAY_ABBR = {
    "Lunedì": "Lun", "Martedì": "Mar", "Mercoledì": "Mer", "Giovedì": "Gio",
    "Venerdì": "Ven", "Sabato": "Sab", "Domenica": "Dom",
}
DAY_RE = re.compile(
    r"(luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)", re.I
)

QTY_RE = re.compile(
    r"(?:^|\s)((?:q\.?\s?b\.?)|(?:\d+(?:[.,]\d+)?\s?(?:g|gr|kg|ml|l|cl)))"
    r"(?:\s*(\(.*\)))?\s*$",
    re.I,
)
LISTA_RE = re.compile(r"\bLISTA\s*(\d+)\b", re.I)
LABEL_RE = re.compile(r"^([A-ZÀÈÉÌÒÙ0-9][A-ZÀÈÉÌÒÙ0-9°’'\s,\.\-]{1,70}?)\s*:\s*(.*)$")

NEG_PREFIX = ("EVITARE", "LIMITARE", "NON VANNO", "NON E'", "NON È")
POS_PREFIX = ("E' POSSIBILE", "È POSSIBILE", "E' CONSIGLIATO", "È CONSIGLIATO",
              "PER IL CONTENUTO DI FERRO", "PREDILIGERE")

EMOJI_RULES = [
    (r"\b(t[èe]|the|caff[èe]|tisan|camomill)", "☕"),
    (r"yogurt|yoghurt|skyr", "🥣"),
    (r"\buov|albumi", "🥚"),
    (r"pesce|salmone|tonno|sgombro|spigola|orata|merluzzo|nasello|branzino|cernia|dentice|trota|spada|alici|sogliola|platessa|baccal|pagello|rombo|ricciola|scorfano|corvina|rana pescatrice", "🐟"),
    (r"pollo|tacchino", "🍗"),
    (r"vitell|manzo|bovino|coniglio|agnello|maiale|hamburger", "🥩"),
    (r"prosciutto|bresaola|affettat|speck", "🍖"),
    (r"ricotta|formagg|mozzarella|primo sale|crescenza|robiola|stracchino|certosa|fiocchi di latte", "🧀"),
    (r"\blatte\b", "🥛"),
    (r"biscott|fette|pane|gallett|frisella|cracker|wasa", "🍞"),
    (r"biscotti", "🍪"),
    (r"\briso\b|riso soffiato", "🍚"),
    (r"pasta|couscous|orzo|farro|quinoa|sorgo|bulgur|grano saraceno", "🍝"),
    (r"fiocchi|cereal|avena", "🥣"),
    (r"farina", "🌾"),
    (r"legum|fagioli|ceci|lenticchie|piselli|lupini", "🫘"),
    (r"patat", "🥔"),
    (r"mandorle|noci|nocciole|anacardi|pistacchi|frutta secca|semi|arachidi", "🌰"),
    (r"cioccolat", "🍫"),
    (r"avocado", "🥑"),
    (r"olive|olio", "🫒"),
    (r"verdur|zucchin|insalat|cetriol|bietol|songino|ortagg", "🥦"),
    (r"spremuta|centrifug", "🧃"),
    (r"frutta|banana|mela|agrumi|melone|arancia|frutti", "🍓"),
]

TEXT_FIXES = {
    "preferibilmenteiposodica": "preferibilmente iposodica",
    "pastolibero": "pasto libero",
    "almeno2": "almeno 2",
}

CARD_EMOJI = [
    ("INDICAZION", "📋"), ("METODI", "🍳"), ("CARNE", "🥩"), ("PESCE", "🐟"), ("UOVA", "🥚"),
    ("LEGUMI", "🫘"), ("MINESTRE", "🍲"), ("VERDUR", "🥬"), ("CONTORNO", "🥬"), ("PATATE", "🥔"),
    ("FRUTTA", "🍎"), ("CONDIMENTI", "🫒"), ("PIATTO", "🍝"), ("FARINACEI", "🍞"),
    ("LATTICINI", "🧀"), ("AFFETTATI", "🍖"), ("BEVANDE", "💧"), ("ALTRO", "⚠️"),
]


# ----------------------------------------------------------------------------
# UTILITÀ
# ----------------------------------------------------------------------------
def esc(s):
    return _html.escape(str(s or ""), quote=True)


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_label(s):
    return s.upper().replace("’", "'").strip()


def food_emoji(name):
    n = name.lower()
    for rx, em in EMOJI_RULES:
        if re.search(rx, n):
            return em
    return "🍽️"


def card_emoji(title):
    t = norm_label(title)
    for key, em in CARD_EMOJI:
        if key in t:
            return em
    return "📌"


def fmt_qty(q):
    if not q:
        return ""
    if re.fullmatch(r"(?i)q\.?\s?b\.?", q.strip()):
        return "q.b."
    return re.sub(r"\s+", "", q.strip()) if re.match(r"^\d", q.strip()) else q.strip()


def upper_first(s):
    s = s.strip()
    return s[:1].upper() + s[1:] if s else s


def clean_alt(alt):
    alt = re.sub(r"\s+", " ", alt).strip()
    alt = re.sub(r"\s+/(\s+|$)", " / ", alt)
    alt = re.sub(r"(?<=[^\s\d/])/\s+", " / ", alt)
    return alt.strip(" /")


def join_days(days, bold=True):
    d = [f"<b>{esc(x)}</b>" if bold else esc(x) for x in days]
    if len(d) <= 1:
        return "".join(d)
    return ", ".join(d[:-1]) + " e " + d[-1]


# ----------------------------------------------------------------------------
# LETTURA PDF
# ----------------------------------------------------------------------------
def cluster_lines(words, tol=5.5):
    """Raggruppa le parole in righe (per coordinata verticale)."""
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(w["top"] - lines[-1]["top"]) < tol:
            lines[-1]["words"].append(w)
        else:
            lines.append({"top": w["top"], "words": [w]})
    for ln in lines:
        ln["words"].sort(key=lambda w: w["x0"])
        ln["text"] = " ".join(w["text"] for w in ln["words"]).strip()
        ln["x0"] = ln["words"][0]["x0"]
    return lines


def is_meal_header(text):
    t = text.strip()
    if not t or len(t) > 40 or re.search(r"\d", t):
        return False
    if t != t.upper() and not t.istitle():
        return False
    return any(t.upper().startswith(k) for k in MEAL_KEYS)


def parse_list_page(lines, page_width):
    """Estrae numero lista, giorni e sezioni (pasti) da una pagina 'LISTA n'."""
    num, days = None, []
    opp_xs = [w["x0"] for ln in lines for w in ln["words"] if w["text"].lower().startswith("oppure")]
    split = (min(opp_xs) - 3) if opp_xs else page_width * 0.38

    sections, cur, item, in_header = [], None, None, True
    for ln in lines:
        text = ln["text"]
        m = LISTA_RE.search(text)
        if m and num is None:
            num = int(m.group(1))
        left = [w for w in ln["words"] if w["x0"] < split]
        right = [w for w in ln["words"] if w["x0"] >= split]
        ltxt = " ".join(w["text"] for w in left).strip()
        rtxt = " ".join(w["text"] for w in right).strip()

        if in_header:
            if is_meal_header(ltxt) and not rtxt:
                in_header = False
            else:
                for d in DAY_RE.findall(text):
                    name = DAY_NAMES[strip_accents(d.lower())]
                    if name not in days:
                        days.append(name)
                continue

        if is_meal_header(ltxt) and not rtxt:
            cur = {"title": ltxt.strip(), "items": []}
            sections.append(cur)
            item = None
            continue
        if cur is None:
            continue
        if re.match(r"(?i)questo regime alimentare", ltxt):
            break

        if ltxt:
            q = QTY_RE.search(ltxt)
            if q:
                name = ltxt[: q.start()].strip()
                if not name and item is not None and not item["qty"]:
                    item["qty"] = q.group(1)
                    if q.group(2):
                        item["right"].append(q.group(2))
                else:
                    item = {"name": name, "qty": q.group(1), "right": [], "x0": left[0]["x0"],
                            "standalone": False}
                    if q.group(2):
                        item["right"].append(q.group(2))
                    cur["items"].append(item)
            else:
                if item is not None and abs(left[0]["x0"] - item["x0"]) < 6 and not item["standalone"]:
                    item["name"] += " " + ltxt
                else:
                    item = {"name": ltxt, "qty": "", "right": [], "x0": left[0]["x0"],
                            "standalone": True}
                    cur["items"].append(item)
        if rtxt and item is not None:
            item["right"].append(rtxt)

    for s in sections:
        for it in s["items"]:
            right = re.sub(r"\s+", " ", " ".join(it.pop("right"))).strip()
            alt, note = "", ""
            if right.lower().startswith("oppure"):
                alt = clean_alt(re.sub(r"(?i)^oppure\s*:?\s*", "", right))
            else:
                note = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", right))
            it["alt"], it["note"] = alt, note
            it["name"] = re.sub(r"\s+", " ", it["name"]).strip()
            it.pop("x0", None)
    return num, days, sections


def parse_blocks(lines, start_title=None):
    """lines: lista di (testo, spazio_verticale_prima). Restituisce le card della guida."""
    cards = []
    state = {"card": None, "block": None}

    def new_card(title):
        c = {"title": title, "blocks": []}
        cards.append(c)
        state["card"], state["block"] = c, None
        return c

    def new_block(label, kind):
        if state["card"] is None:
            new_card(start_title or "Note")
        b = {"label": label, "kind": kind, "items": []}
        state["card"]["blocks"].append(b)
        state["block"] = b
        return b

    def add_text(b, text, gap):
        text = text.strip()
        for bad, good in TEXT_FIXES.items():
            text = text.replace(bad, good)
        if not text:
            return
        bullet = text.startswith(("-", "•"))
        if bullet:
            b["items"].append([True, text.lstrip("-• ").strip()])
        elif b["items"] and gap <= 18:
            b["items"][-1][1] += " " + text
        else:
            b["items"].append([False, text])

    for text, gap in lines:
        t = text.strip()
        if not t or re.match(r"(?i)^raccomandazioni", t):
            continue
        m = LABEL_RE.match(t)
        if m:
            label, rest = m.group(1).strip(), m.group(2).strip()
            n = norm_label(label)
            if n.startswith(NEG_PREFIX):
                kind = "neg"
            elif n.startswith(POS_PREFIX):
                kind = "pos"
            else:
                kind = "cat"
            if kind == "cat":
                new_card(label)
                b = new_block("", "plain")
            else:
                b = new_block(label, kind)
            add_text(b, rest, 999)
            continue
        b = state["block"] or new_block("", "plain")
        add_text(b, t, gap)
    return cards


def merge_cards(cards):
    out, idx = [], {}
    for c in cards:
        if not any(b["items"] for b in c["blocks"]):
            continue
        key = norm_label(c["title"])
        if key in idx:
            out[idx[key]]["blocks"].extend(c["blocks"])
        else:
            idx[key] = len(out)
            out.append(c)
    return out


def extract_meta(first_lines, first_words, width):
    full = "\n".join(l["text"] for l in first_lines)
    flat = re.sub(r"\s+", " ", full)
    meta = {}

    m = re.search(r"NOME\s+(.+?)\s+COGNOME\s+(.+?)(?:\s+ET[àA]|\n|$)", flat)
    if m:
        meta["paziente"] = f"{m.group(1).strip().title()} {m.group(2).strip().title()}"
    m = re.search(r"PESO\s*Kg\s*(\d+(?:[.,]\d+)?)", flat, re.I)
    if m:
        meta["peso"] = m.group(1) + " Kg"
    m = re.search(r"BMI\s*Kg/m\s*2?\s*(\d+[.,]\d+)", flat, re.I)
    if m:
        meta["bmi"] = m.group(1)
    m = re.search(r"OBIETTIVO\s*:?.*?\(\s*(\d+(?:[.,]\d+)?)\s*kg\s*\)", flat, re.I)
    if m:
        meta["obiettivo"] = m.group(1) + " Kg"
    m = re.search(r"DA\s+(\d{3,4})\s*Kcal", flat, re.I)
    if m:
        meta["kcal"] = m.group(1)
    m = re.search(r"almeno\s*(\d+(?:[.,]\d+)?)\s*litri", flat, re.I)
    if m:
        meta["acqua"] = f"Min {m.group(1)} Litri/giorno"
    m = re.search(r"Prossimo controllo\s+(.+?)(?:\s+Portare|$)", flat)
    if m:
        c = m.group(1).strip().lower().title().replace(" Ore ", " ore ")
        meta["controllo"] = c
    m = re.search(r"(Dott\.?\s?ssa|Dott\.|Dr\.?\s?ssa|Dr\.)\s+([A-ZÀ-Ù][a-zà-ù']+(?:\s+[A-ZÀ-Ù][a-zà-ù']+)*)", flat)
    if m:
        qual = re.search(r"-\s*(Biolog[oa] Nutrizionista|Dietist[ai]|Nutrizionista|Medico [A-Za-zà-ù ]+)", flat)
        meta["professionista"] = f"{m.group(1)} {m.group(2)}" + (f" • {qual.group(1)}" if qual else "")

    # intestazione a destra (data, nome paziente, sottotitolo) nei PDF di "modifiche"
    right = [w for w in first_words if w["x0"] > width * 0.7 and w["top"] < 140]
    for ln in cluster_lines(right, tol=3):
        t = ln["text"]
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", t):
            meta["data"] = t
        elif re.search(r"(?i)modifich", t):
            meta["sottotitolo"] = upper_first(t)
        elif not re.search(r"\d", t) and "paziente" not in meta and len(t.split()) <= 4:
            meta["paziente"] = t.title()
    return meta


def parse_pdf(data: bytes):
    plan = {"meta": {}, "lists": {}, "cards": []}
    guide_lines = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        last_list = None
        for pi, page in enumerate(pdf.pages):
            words = page.extract_words()
            lines = cluster_lines(words)
            if not lines:
                continue
            has_lista = any(LISTA_RE.search(l["text"]) for l in lines)
            has_meals = any(is_meal_header(l["text"]) for l in lines)

            if pi == 0:
                plan["meta"] = extract_meta(lines, words, page.width)

            if has_lista or (has_meals and last_list is not None):
                num, days, sections = parse_list_page(lines, page.width)
                if has_lista and num is not None:
                    last_list = num
                    plan["lists"][num] = {"days": days, "sections": sections}
                elif last_list is not None:
                    plan["lists"][last_list]["sections"].extend(sections)
                continue

            # pagina non-lista: cover (indicazioni) o raccomandazioni
            started = pi != 0
            prev_top = None
            for ln in lines:
                t = ln["text"]
                if pi == 0:
                    if re.fullmatch(r"INDICAZIONI", t.strip()):
                        started = True
                        prev_top = ln["top"]
                        continue
                    if re.search(r"Prossimo controllo", t):
                        started = False
                if not started:
                    prev_top = ln["top"]
                    continue
                if re.match(r"(?i)^questo regime alimentare", t):
                    break
                if re.match(r"(?i)^(Dott|Studio via|Tel studio|Email:|Facebook:)", t):
                    continue
                gap = 999 if prev_top is None else ln["top"] - prev_top
                prev_top = ln["top"]
                guide_lines.append((t, gap))
            guide_lines.append(("", 999))

    # La cover genera la card "Indicazioni", le altre pagine le card per categoria
    plan["cards"] = merge_cards(parse_blocks(guide_lines, start_title="Indicazioni"))
    return plan


def merge_plans(plans):
    out = {"meta": {}, "lists": {}, "cards": []}
    for p in plans:
        for k, v in p["meta"].items():
            if v:
                out["meta"][k] = v
        out["lists"].update(p["lists"])
        if p["cards"]:
            out["cards"] = p["cards"]
    return out


# ----------------------------------------------------------------------------
# GENERAZIONE HTML
# ----------------------------------------------------------------------------
CARD = "bg-white p-4 rounded-2xl shadow-sm border border-gray-100"
HEAD_B = "flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100"
HEAD_C = "flex items-center gap-2 text-emerald-600 font-bold mb-1"
ALT_BOX = "text-[11px] text-gray-500 bg-gray-50 p-2 rounded-lg mt-1 border border-gray-100"


def render_item_li(it):
    name = upper_first(it["name"])
    if it["standalone"] and not it["qty"]:
        return f"<li>{food_emoji(name)} <b>{esc(name)}</b></li>"
    s = f"<li>{food_emoji(name)} <b>{esc(name)}:</b> {esc(fmt_qty(it['qty']))}"
    if it["note"]:
        s += f' <span class="text-gray-500 text-[11px]">{esc(it["note"])}</span>'
    if it["alt"]:
        if len(it["alt"]) > 80:
            s += f'\n<div class="{ALT_BOX}"><b>Oppure:</b> {esc(it["alt"])}</div>'
        else:
            s += f'\n<span class="block text-[11px] text-gray-500"><b>Oppure:</b> {esc(it["alt"])}</span>'
    return s + "</li>"


def render_list(lst, num):
    days = lst["days"]
    sections = lst["sections"]
    out = [f'<div id="lista{num}" class="tab-content{"" if num == FIRST_LIST[0] else " hidden"} space-y-3">']

    if days:
        label = "Giornata" if len(days) == 1 else "Giornate"
        out.append(
            '<div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-2.5 rounded-xl '
            'font-medium flex justify-between items-center">'
            f"<span>🗓️ {label}: {join_days(days)}</span>"
            f'<span class="bg-amber-200 text-amber-900 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Lista {num}</span></div>'
        )

    idx_pranzo = next((i for i, s in enumerate(sections) if s["title"].startswith("PRANZO")), None)
    idx_cena = next((i for i, s in enumerate(sections) if s["title"].upper().startswith("CENA")), None)
    n_spunt = sum(
        1 for i, s in enumerate(sections)
        if s["title"].upper().startswith(("SPUNTINO", "SPUNTINI", "MERENDA"))
        and (idx_cena is None or i < idx_cena)
    )
    day_badge = days[0].upper() if len(days) == 1 else " / ".join(DAY_ABBR.get(d, d).upper() for d in days)

    for i, s in enumerate(sections):
        title = s["title"].upper()
        items = s["items"]
        if not items:
            continue

        # Pasto libero
        free = next((it for it in items if it["standalone"] and "LIBERO" in it["name"].upper()), None)
        if free:
            badge = f"{day_badge} {title}".strip()
            out.append(
                '<div class="bg-purple-50 p-4 rounded-2xl border border-purple-200 shadow-sm">'
                '<div class="flex items-center justify-between text-purple-900 font-bold mb-1">'
                f'<span class="flex items-center gap-2"><i class="fa-solid fa-star text-purple-600"></i> {esc(title)}: PASTO LIBERO</span>'
                f'<span class="bg-purple-200 text-purple-800 text-[10px] px-2 py-0.5 rounded-full font-bold">{esc(badge)}</span></div>'
                + "</div>"
            )
            continue

        # Condimenti
        if title.startswith("CONDIMENTI"):
            head = "CONDIMENTI GIORNALIERI" if len(days) != 1 else f"CONDIMENTI {days[0].upper()}"
            body = []
            for it in items:
                name = upper_first(it["name"])
                q = fmt_qty(it["qty"])
                if q == "q.b.":
                    body.append(f'<p class="text-gray-600 text-[11px] mt-0.5">{esc(name)}: {esc(q)}</p>')
                else:
                    note = f" {esc(it['note'])}" if it["note"] else ""
                    body.append(f'<p class="mt-1"><b>{esc(name)}:</b> {esc(q)}{note}</p>')
            out.append(
                '<div class="bg-emerald-50 p-3.5 rounded-2xl border border-emerald-100 text-xs text-emerald-900">'
                '<p class="font-bold flex items-center gap-1.5"><i class="fa-solid fa-bottle-droplet text-emerald-600"></i> '
                f"{esc(head)}</p>" + "".join(body) + "</div>"
            )
            continue

        # Icona e titolo del pasto
        if title.startswith("COCCOLA") or (
            idx_cena is not None and i > idx_cena and title.startswith(("SPUNTINO", "SPUNTINI", "MERENDA"))
        ):
            # spuntino dopo cena: compare solo se previsto dalla lista
            title = "COCCOLA DOPO CENA"
            icon = "fa-cookie-bite"
        elif title.startswith(("SPUNTINO", "SPUNTINI", "MERENDA")):
            before = idx_pranzo is None or i < idx_pranzo
            if n_spunt >= 2 and "MATTINA" not in title and "POMERIGGIO" not in title:
                title = title + (" MATTINA" if before else " POMERIGGIO")
            icon = "fa-apple-whole" if before else "fa-cookie-bite"
        elif title.startswith("COLAZIONE"):
            icon = "fa-mug-hot"
        elif title.startswith("PRANZO"):
            icon = "fa-utensils"
        elif title.startswith("CENA"):
            icon = "fa-moon"
        else:
            icon = "fa-utensils"

        compact = (
            title.startswith(("SPUNTINO", "SPUNTINI", "MERENDA"))
            and len(items) == 1
            and len(items[0]["alt"]) <= 90
            and not items[0]["standalone"]
        )
        if compact:
            it = items[0]
            name = upper_first(it["name"])
            alt = f' <span class="text-gray-500 text-[11px]">(Oppure {esc(it["alt"])})</span>' if it["alt"] else ""
            out.append(
                f'<div class="{CARD}"><div class="{HEAD_C}"><i class="fa-solid {icon}"></i> {esc(title)}</div>'
                f'<p class="text-xs text-gray-700">{food_emoji(name)} <b>{esc(name)}:</b> {esc(fmt_qty(it["qty"]))}{alt}</p></div>'
            )
        else:
            lis = "\n".join(render_item_li(it) for it in items)
            out.append(
                f'<div class="{CARD}"><div class="{HEAD_B}"><i class="fa-solid {icon}"></i> {esc(title)}</div>'
                f'<ul class="text-xs space-y-2 text-gray-700">\n{lis}\n</ul></div>'
            )
    out.append("</div>")
    return "\n".join(out)


FIRST_LIST = [1]
TITOLO_FISSO = "Piano Alimentare Mobile"

# CSS equivalente alle classi Tailwind usate dal modello: la pagina non dipende da CDN per lo stile.
CSS = """
*,::before,::after{box-sizing:border-box;border:0 solid #e5e7eb}
html{line-height:1.5;-webkit-text-size-adjust:100%;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
body{margin:0;line-height:inherit;background:#f3f4f6;color:#1f2937;padding-bottom:3rem;-webkit-tap-highlight-color:transparent}
h1,p,ul{margin:0}ul{list-style:none;padding:0}b{font-weight:700}
button{font-family:inherit;font-size:100%;line-height:inherit;color:inherit;background:transparent;border:0;padding:0;cursor:pointer}
i{font-style:normal}
.no-scrollbar::-webkit-scrollbar{display:none}.no-scrollbar{-ms-overflow-style:none;scrollbar-width:none}
.hidden{display:none}.block{display:block}.flex{display:flex}
.sticky{position:sticky}.top-0{top:0}.z-50{z-index:50}
.items-center{align-items:center}.justify-between{justify-content:space-between}
.gap-1\\.5{gap:.375rem}.gap-2{gap:.5rem}
.mx-auto{margin-left:auto;margin-right:auto}.max-w-md{max-width:28rem}
.overflow-x-auto{overflow-x:auto}.whitespace-nowrap{white-space:nowrap}
.mb-1{margin-bottom:.25rem}.mb-2{margin-bottom:.5rem}.mb-4{margin-bottom:1rem}
.mt-0\\.5{margin-top:.125rem}.mt-1{margin-top:.25rem}.mt-2{margin-top:.5rem}.mt-3{margin-top:.75rem}
.p-2{padding:.5rem}.p-2\\.5{padding:.625rem}.p-3\\.5{padding:.875rem}.p-4{padding:1rem}.p-5{padding:1.25rem}
.px-2{padding-left:.5rem;padding-right:.5rem}.px-3{padding-left:.75rem;padding-right:.75rem}.px-4{padding-left:1rem;padding-right:1rem}
.py-0\\.5{padding-top:.125rem;padding-bottom:.125rem}.py-1{padding-top:.25rem;padding-bottom:.25rem}.py-2\\.5{padding-top:.625rem;padding-bottom:.625rem}
.pb-1{padding-bottom:.25rem}.pb-2{padding-bottom:.5rem}
.space-y-2>:not([hidden])~:not([hidden]){margin-top:.5rem}
.space-y-3>:not([hidden])~:not([hidden]){margin-top:.75rem}
.rounded{border-radius:.25rem}.rounded-lg{border-radius:.5rem}.rounded-xl{border-radius:.75rem}
.rounded-2xl{border-radius:1rem}.rounded-full{border-radius:9999px}
.rounded-b-3xl{border-bottom-left-radius:1.5rem;border-bottom-right-radius:1.5rem}
.border{border-width:1px}.border-b{border-bottom-width:1px}
.shadow-sm{box-shadow:0 1px 2px 0 rgba(0,0,0,.05)}
.shadow-lg{box-shadow:0 10px 15px -3px rgba(0,0,0,.1),0 4px 6px -4px rgba(0,0,0,.1)}
.text-xs{font-size:.75rem;line-height:1rem}.text-xl{font-size:1.25rem;line-height:1.75rem}
.text-\\[10px\\]{font-size:10px}.text-\\[11px\\]{font-size:11px}
.font-medium{font-weight:500}.font-semibold{font-weight:600}.font-bold{font-weight:700}
.uppercase{text-transform:uppercase}
.transition-all{transition:all .15s cubic-bezier(.4,0,.2,1)}
.backdrop-blur-sm{-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.text-white{color:#fff}.text-gray-500{color:#6b7280}.text-gray-600{color:#4b5563}.text-gray-700{color:#374151}
.bg-white{background:#fff}.bg-gray-50{background:#f9fafb}.border-gray-100{border-color:#f3f4f6}
.bg-emerald-50{background:#ecfdf5}.bg-emerald-600{background:#059669}.bg-emerald-700{background:#047857}
.bg-emerald-700\\/50{background:rgba(4,120,87,.5)}
.text-emerald-50{color:#ecfdf5}.text-emerald-100{color:#d1fae5}.text-emerald-600{color:#059669}.text-emerald-900{color:#064e3b}
.border-emerald-100{border-color:#d1fae5}
.bg-amber-50{background:#fffbeb}.bg-amber-200{background:#fde68a}.border-amber-200{border-color:#fde68a}
.text-amber-800{color:#92400e}.text-amber-900{color:#78350f}
.bg-purple-50{background:#faf5ff}.bg-purple-200{background:#e9d5ff}.border-purple-200{border-color:#e9d5ff}
.text-purple-600{color:#9333ea}.text-purple-800{color:#6b21a8}.text-purple-900{color:#581c87}
"""

HTML_HEAD = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <meta name="theme-color" content="#059669">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Piano Alimentare">
    <title>__TITLE__</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>__CSS__</style>
</head>
<body>
"""

HTML_SCRIPT = """
    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-emerald-600', 'text-white');
                btn.classList.add('bg-white', 'text-gray-600');
            });
            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById('tab-' + tabId);
            activeBtn.classList.remove('bg-white', 'text-gray-600');
            activeBtn.classList.add('bg-emerald-600', 'text-white');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""


def tab_label(num, days):
    if not days:
        return f"Lista {num}"
    if len(days) == 1:
        return f"{days[0]} (Lista {num})"
    return " / ".join(DAY_ABBR.get(d, d) for d in days) + f" (Lista {num})"


def build_html(plan, opts):
    lists = dict(sorted(plan["lists"].items()))
    if not lists:
        raise ValueError("Nessuna lista trovata nei PDF.")
    FIRST_LIST[0] = next(iter(lists))
    paziente = opts.get("paziente", "")
    head = HTML_HEAD.replace("__TITLE__", esc(TITOLO_FISSO)).replace("__CSS__", CSS)
    out = [head]

    info = []
    if paziente:
        info.append(("Paziente", paziente))
    if opts.get("peso"):
        info.append(("Peso", opts["peso"]))
    if opts.get("bmi"):
        info.append(("BMI", opts["bmi"]))
    if not opts.get("peso") and not opts.get("bmi") and opts.get("data"):
        info.append(("Data", opts["data"]))

    out.append(
        '    <header class="bg-emerald-600 text-white p-5 rounded-b-3xl shadow-lg sticky top-0 z-50">\n'
        '        <div class="flex justify-between items-center mb-2">\n            <div>\n'
        f'                <h1 class="text-xl font-bold">{esc(TITOLO_FISSO)}</h1>\n'
        f'                <p class="text-xs text-emerald-100">{esc(opts.get("professionista", ""))}</p>\n'
        "            </div>\n"
        + (f'            <div class="bg-emerald-700 px-3 py-1 rounded-full text-xs font-semibold">Obiettivo: {esc(opts["obiettivo"])}</div>\n'
           if opts.get("obiettivo") else "")
        + "        </div>\n"
        + (
            '        <div class="flex justify-between text-xs bg-emerald-700/50 p-2.5 rounded-xl mt-3 text-emerald-50 backdrop-blur-sm">'
            + "".join(f"<span><b>{esc(k)}:</b> {esc(v)}</span>" for k, v in info)
            + "</div>\n"
            if info else ""
        )
        + "    </header>\n"
    )
    out.append('    <main style="padding:1rem;max-width:28rem;margin:0 auto">\n')

    tabs = []
    for n, lst in lists.items():
        active = "bg-emerald-600 text-white" if n == FIRST_LIST[0] else "bg-white text-gray-600"
        tabs.append(
            f'<button onclick="showTab(\'lista{n}\')" id="tab-lista{n}" class="tab-btn px-4 py-2.5 {active} '
            f'rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all" style="flex:none">{esc(tab_label(n, lst["days"]))}</button>'
        )
    out.append('<div class="flex gap-2 overflow-x-auto no-scrollbar mb-4 py-1">\n' + "\n".join(tabs) + "\n</div>\n")

    for n, lst in lists.items():
        out.append(render_list(lst, n))
    out.append("    </main>\n")
    out.append(HTML_SCRIPT)
    return "\n".join(out)


# ----------------------------------------------------------------------------
# PUBBLICAZIONE SU GITHUB PAGES (opzionale)
# ----------------------------------------------------------------------------
def publish_to_github(html, slug, cfg):
    import requests

    token = secrets.token_urlsafe(12).replace("-", "x").replace("_", "y")
    filename = f"{slug}-{token}.html"
    folder = cfg.get("GITHUB_FOLDER", "piani").strip("/")
    path = f"{folder}/{filename}" if folder else filename
    r = requests.put(
        f"https://api.github.com/repos/{cfg['GITHUB_REPO']}/contents/{path}",
        headers={"Authorization": f"Bearer {cfg['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"},
        json={
            "message": f"Aggiunto piano {slug}",
            "content": base64.b64encode(html.encode("utf-8")).decode(),
            "branch": cfg.get("GITHUB_BRANCH", "main"),
        },
        timeout=30,
    )
    r.raise_for_status()
    return f"{cfg['GITHUB_PAGES_BASE'].rstrip('/')}/{path}"


# ----------------------------------------------------------------------------
# INTERFACCIA STREAMLIT
# ----------------------------------------------------------------------------
def share_button(html, filename, text):
    """Pulsante che apre il menu di condivisione del telefono (WhatsApp) con il file allegato."""
    import json
    import streamlit.components.v1 as components

    b64 = base64.b64encode(html.encode("utf-8")).decode()
    components.html(
        f"""
<button id="s" style="width:100%;padding:14px;border:0;border-radius:12px;background:#059669;color:#fff;
font:600 16px system-ui,sans-serif;cursor:pointer">📲 Invia al paziente (WhatsApp)</button>
<p id="m" style="font:13px system-ui,sans-serif;color:#555;margin:8px 2px"></p>
<script>
const b64 = "{b64}";
const name = {json.dumps(filename)};
const msg = {json.dumps(text)};
function mk() {{
  const bin = atob(b64), u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return new File([u8], name, {{type: "text/html"}});
}}
document.getElementById("s").onclick = async () => {{
  const f = mk(), m = document.getElementById("m");
  try {{
    if (navigator.canShare && navigator.canShare({{files: [f]}})) {{
      await navigator.share({{files: [f], text: msg}});
      return;
    }}
  }} catch (e) {{ if (e.name === "AbortError") return; }}
  const a = document.createElement("a");
  a.href = URL.createObjectURL(f); a.download = name; document.body.appendChild(a); a.click();
  m.textContent = "La condivisione diretta non è disponibile su questo dispositivo: ho scaricato il file. Invialo da WhatsApp (graffetta → Documento).";
}};
</script>""",
        height=120,
    )


def main():
    import streamlit as st
    import streamlit.components.v1 as components

    st.set_page_config(page_title="Generatore piano alimentare", page_icon="🥗", layout="wide")
    st.title("🥗 Generatore piano alimentare mobile")
    st.caption(
        "Carica uno o più PDF (piano completo, modifiche dieta…). Se carichi più file, le liste con lo stesso "
        "numero vengono sostituite da quelle del file caricato per ultimo."
    )

    @st.cache_data(show_spinner="Leggo il PDF…")
    def cached_parse(b: bytes, version: str):
        return parse_pdf(b)

    files = st.file_uploader("PDF del piano alimentare", type=["pdf"], accept_multiple_files=True)
    if not files:
        st.info("Carica un PDF per iniziare.")
        return

    raw = [f.getvalue() for f in files]
    plan = merge_plans([cached_parse(b, PARSER_VERSION) for b in raw])
    sig = hashlib.md5(b"".join(raw)).hexdigest()[:8]
    meta = plan["meta"]

    if not plan["lists"]:
        st.error("Non ho trovato nessuna 'LISTA n' nei PDF caricati.")
        return

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("Intestazione")
        prof = st.text_input("Professionista", meta.get("professionista") or DEFAULT_PROFESSIONISTA, key=f"pr{sig}")
        paziente = st.text_input("Paziente", meta.get("paziente", ""), key=f"pz{sig}")
        c1, c2, c3 = st.columns(3)
        peso = c1.text_input("Peso", meta.get("peso", ""), key=f"pe{sig}")
        bmi = c2.text_input("BMI", meta.get("bmi", ""), key=f"b{sig}")
        obiettivo = c3.text_input("Obiettivo", meta.get("obiettivo", ""), key=f"o{sig}")

        problemi = []
        for n, lst in sorted(plan["lists"].items()):
            for s in lst["sections"]:
                if not s["items"]:
                    problemi.append(f"Lista {n} – {s['title']}: nessuna voce letta")
                for it in s["items"]:
                    if it["standalone"] and "LIBERO" not in it["name"].upper():
                        problemi.append(f"Lista {n} – {s['title']}: voce senza quantità «{it['name']}»")
        if problemi:
            st.warning("Possibile lettura incompleta, controlla l'anteprima:\n\n" + "\n".join(f"- {p}" for p in problemi[:12]))

        with st.expander("Liste estratte (controllo)"):
            for n, lst in sorted(plan["lists"].items()):
                st.markdown(f"**Lista {n}** – {', '.join(lst['days']) or 'giorni non rilevati'}")
                for s in lst["sections"]:
                    st.markdown(f"*{s['title']}* ({len(s['items'])} voci)")
                    for it in s["items"]:
                        st.text(f"  {it['name']} | {it['qty']} | oppure: {it['alt'][:60]}")
            try:
                import pdfplumber as _p
                st.caption(f"pdfplumber {_p.__version__} · parser {PARSER_VERSION}")
            except Exception:  # noqa: BLE001
                pass

    opts = dict(
        professionista=prof, paziente=paziente, peso=peso, bmi=bmi, obiettivo=obiettivo,
        data=meta.get("data", ""),
    )
    try:
        html = build_html(plan, opts)
    except Exception as e:  # noqa: BLE001
        st.error(f"Errore nella generazione: {e}")
        return

    with right:
        st.subheader("Anteprima")
        components.html(html, height=820, scrolling=True)

    st.divider()
    slug = re.sub(r"[^a-z0-9]+", "-", strip_accents(paziente.lower())).strip("-") or "piano"
    filename = f"piano-alimentare-{slug}.html"

    st.subheader("Invio al paziente")
    share_button(html, filename, "Ecco il tuo piano alimentare. Aprilo dal file allegato.")
    st.download_button("⬇️ Scarica il file", html.encode("utf-8"), file_name=filename, mime="text/html")
    st.caption(
        "Il paziente apre il file da WhatsApp e lo vede come un'app. Per tenerlo sul telefono può salvarlo "
        "(tenendo premuto sul file → Salva/Scarica). Per avere l'icona sulla home serve invece un link: "
        "vedi la pubblicazione qui sotto, poi dal browser ⋮ → «Aggiungi a schermata Home»."
    )

    cfg = {}
    try:
        cfg = dict(st.secrets)
    except Exception:  # noqa: BLE001
        pass
    if all(k in cfg for k in ("GITHUB_TOKEN", "GITHUB_REPO", "GITHUB_PAGES_BASE")):
        with st.expander("Pubblica come link (opzionale)"):
            st.warning(
                "⚠️ Dati sanitari: se il repository è pubblico, chiunque abbia il link (o veda il repo) può leggere il piano. "
                "Usa un repository dedicato e cancella i file quando non servono."
            )
            phone = st.text_input("Numero WhatsApp del paziente (formato internazionale, es. 393331234567)", "")
            if st.button("🚀 Pubblica e genera link"):
                try:
                    st.session_state[f"url{sig}"] = publish_to_github(html, slug, cfg)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Pubblicazione non riuscita: {e}")
            if st.session_state.get(f"url{sig}"):
                url = st.session_state[f"url{sig}"]
                st.success(f"Pubblicato (online entro circa 1 minuto): {url}")
                msg = f"Ecco il tuo piano alimentare: {url}"
                digits = re.sub(r"\D", "", phone)
                wa = f"https://wa.me/{digits}?text={quote(msg)}" if digits else f"https://wa.me/?text={quote(msg)}"
                st.markdown(f"[📲 Apri WhatsApp con il messaggio pronto]({wa})")


if __name__ == "__main__":
    main()
