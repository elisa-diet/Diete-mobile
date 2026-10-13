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
DEFAULT_PROFESSIONISTA = "Dott.ssa Elisa Vasa • Biologa Nutrizionista"
DEFAULT_PASTO_LIBERO = "Pasto a libera scelta."

MEAL_KEYS = ("COLAZIONE", "SPUNTINO", "SPUNTINI", "MERENDA", "PRANZO", "CENA", "CONDIMENTI")

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
    if t != t.upper():
        return False
    return any(t.startswith(k) for k in MEAL_KEYS)


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


def render_list(lst, num, free_text, free_warn):
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
    n_spunt = sum(1 for s in sections if s["title"].startswith(("SPUNTINO", "SPUNTINI", "MERENDA")))
    day_badge = " / ".join(DAY_ABBR.get(d, d).upper() for d in days)

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
                + (f'<p class="text-xs text-purple-800 mt-2">{esc(free_text)}</p>' if free_text else "")
                + (f'<p class="text-xs font-bold text-purple-900 mt-1">⚠️ {esc(free_warn)}</p>' if free_warn else "")
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
        if title.startswith(("SPUNTINO", "SPUNTINI", "MERENDA")):
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


def render_guide(cards, integrazione, red_title, red_text):
    out = ['<div id="regole" class="tab-content hidden space-y-4">']
    out.append(
        '<div class="relative"><i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-gray-400 text-xs"></i>'
        '<input type="text" id="foodSearch" onkeyup="searchFoods()" placeholder="Cerca un alimento (es. carote, zucchine)..." '
        'class="w-full bg-white pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none '
        'focus:ring-2 focus:ring-emerald-500 shadow-sm"></div>'
    )
    if integrazione:
        lis = "".join(f"<li>{esc(l)}</li>" for l in integrazione)
        out.append(
            '<div class="bg-blue-50 p-4 rounded-2xl border border-blue-100 text-xs text-blue-900 space-y-1.5">'
            '<p class="font-bold text-blue-950 flex items-center gap-1.5"><i class="fa-solid fa-pills text-blue-600"></i> INTEGRAZIONE CONSIGLIATA</p>'
            f'<ul class="list-disc pl-4 space-y-1 text-gray-700">{lis}</ul></div>'
        )

    box = {
        "plain": ("", "bg-gray-50", "border-gray-100"),
        "pos": ("✅", "bg-emerald-50/50", "border-emerald-100/50"),
        "neg": ("❌", "bg-red-50/50", "border-red-100/50"),
    }
    label_color = {"plain": "text-gray-700", "pos": "text-emerald-700", "neg": "text-red-600"}

    for c in cards:
        blocks = []
        for b in c["blocks"]:
            if red_text and c["title"] == "Indicazioni" and b["kind"] == "neg" and norm_label(b["label"]).startswith("EVITARE"):
                continue
            if not b["items"]:
                continue
            em, bg, bd = box[b["kind"]]
            parts, i = [], 0
            while i < len(b["items"]):
                if b["items"][i][0]:
                    j = i
                    lis = []
                    while j < len(b["items"]) and b["items"][j][0]:
                        lis.append(f"<li>{esc(b['items'][j][1])}</li>")
                        j += 1
                    parts.append(f'<ul class="list-disc pl-4 space-y-1">{"".join(lis)}</ul>')
                    i = j
                else:
                    parts.append(f"<p>{esc(b['items'][i][1])}</p>")
                    i += 1
            label = ""
            if b["label"]:
                label = (f'<span class="text-[11px] font-bold {label_color[b["kind"]]} uppercase tracking-wider block mb-1">'
                         f"{em} {esc(b['label'])}</span>")
            blocks.append(
                f"<div>{label}"
                f'<div class="text-xs text-gray-600 leading-relaxed {bg} p-2.5 rounded-xl border {bd} food-item space-y-1.5">'
                f'{"".join(parts)}</div></div>'
            )
        if not blocks:
            continue
        title = re.sub(r"°(?=\S)", "° ", c["title"]).upper()
        out.append(
            f'<div class="{CARD} space-y-3 guide-card">'
            '<h3 class="font-bold text-xs text-gray-900 flex items-center gap-2 border-b border-gray-100 pb-2">'
            f"{card_emoji(c['title'])} {esc(title)}</h3>" + "".join(blocks) + "</div>"
        )

    if red_text:
        out.append(
            '<div class="bg-red-500 text-white p-4 rounded-2xl shadow-md text-xs space-y-2">'
            '<p class="font-bold text-sm flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation"></i> '
            f"{esc(red_title)}</p>"
            f'<p class="leading-relaxed opacity-95">{esc(red_text)}</p></div>'
        )
    out.append("</div>")
    return "\n".join(out)


FIRST_LIST = [1]

HTML_HEAD = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .no-scrollbar::-webkit-scrollbar {{ display: none; }}
        .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
        body {{ -webkit-tap-highlight-color: transparent; }}
    </style>
</head>
<body class="bg-gray-100 text-gray-800 font-sans pb-12">
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

        function searchFoods() {
            const input = document.getElementById('foodSearch').value.toLowerCase();
            document.querySelectorAll('.food-item').forEach(item => {
                const hit = item.textContent.toLowerCase().includes(input);
                item.parentElement.style.display = hit ? "block" : "none";
            });
            document.querySelectorAll('.guide-card').forEach(card => {
                const visible = Array.from(card.querySelectorAll('.food-item'))
                    .some(i => i.parentElement.style.display !== "none");
                card.style.display = (input === "" || visible) ? "block" : "none";
            });
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
    guide_cards = plan["cards"] if opts.get("mostra_guida", True) else []
    integrazione = [l.strip() for l in (opts.get("integrazione") or "").splitlines() if l.strip()]
    red_text = (opts.get("red_text") or "").strip()
    has_guide = bool(guide_cards or integrazione or red_text)

    titolo = opts.get("titolo") or "Piano Alimentare"
    paziente = opts.get("paziente", "")
    out = [HTML_HEAD.format(title=esc(f"{titolo} - {paziente}" if paziente else titolo))]

    # Header
    badge = ""
    if opts.get("obiettivo"):
        badge = f"Obiettivo: {opts['obiettivo']}"
    elif opts.get("badge"):
        badge = opts["badge"]
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
        f'                <h1 class="text-xl font-bold">{esc(titolo)}</h1>\n'
        f'                <p class="text-xs text-emerald-100">{esc(opts.get("professionista", ""))}</p>\n'
        "            </div>\n"
        + (f'            <div class="bg-emerald-700 px-3 py-1 rounded-full text-xs font-semibold">{esc(badge)}</div>\n' if badge else "")
        + "        </div>\n"
        + (
            '        <div class="flex justify-between text-xs bg-emerald-700/50 p-2.5 rounded-xl mt-3 text-emerald-50 backdrop-blur-sm">'
            + "".join(f"<span><b>{esc(k)}:</b> {esc(v)}</span>" for k, v in info)
            + "</div>\n"
            if info else ""
        )
        + "    </header>\n"
    )

    out.append('    <main class="p-4 max-w-md mx-auto">\n')

    # Banner info rapide
    banner = []
    if opts.get("acqua"):
        banner.append(
            '<div class="flex items-center gap-2"><i class="fa-solid fa-droplet text-blue-500 text-base"></i>'
            f"<span><b>Acqua:</b> {esc(opts['acqua'])}</span></div>"
        )
    if opts.get("controllo"):
        banner.append(
            '<div class="flex items-center gap-2"><i class="fa-solid fa-clock text-amber-500 text-base"></i>'
            f"<span><b>Controllo:</b> {esc(opts['controllo'])}</span></div>"
        )
    if banner:
        out.append(
            '<div class="bg-white p-3.5 rounded-2xl shadow-sm border border-gray-100 mb-4 flex items-center '
            'justify-between text-xs text-gray-600 gap-3">' + "".join(banner) + "</div>\n"
        )

    # Tab (scorrevoli orizzontalmente)
    tabs = []
    for n, lst in lists.items():
        active = "bg-emerald-600 text-white" if n == FIRST_LIST[0] else "bg-white text-gray-600"
        tabs.append(
            f'<button onclick="showTab(\'lista{n}\')" id="tab-lista{n}" class="tab-btn px-4 py-2.5 {active} '
            f'rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">{esc(tab_label(n, lst["days"]))}</button>'
        )
    if has_guide:
        tabs.append(
            '<button onclick="showTab(\'regole\')" id="tab-regole" class="tab-btn px-4 py-2.5 bg-white text-gray-600 '
            'rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">💡 Guida & Cibi</button>'
        )
    out.append('<div class="flex gap-2 overflow-x-auto no-scrollbar mb-4 py-1">\n' + "\n".join(tabs) + "\n</div>\n")

    for n, lst in lists.items():
        out.append(render_list(lst, n, opts.get("free_text", ""), opts.get("free_warn", "")))
    if has_guide:
        out.append(render_guide(guide_cards, integrazione, opts.get("red_title", "DA EVITARE"), red_text))

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
def main():
    import streamlit as st
    import streamlit.components.v1 as components

    st.set_page_config(page_title="Generatore piano alimentare", page_icon="🥗", layout="wide")
    st.title("🥗 Generatore web app piano alimentare")
    st.caption(
        "Carica uno o più PDF (piano completo, modifiche dieta…). Se carichi più file, le liste con lo stesso "
        "numero vengono sostituite da quelle del file caricato per ultimo."
    )

    @st.cache_data(show_spinner="Leggo il PDF…")
    def cached_parse(b: bytes):
        return parse_pdf(b)

    files = st.file_uploader("PDF del piano alimentare", type=["pdf"], accept_multiple_files=True)
    if not files:
        st.info("Carica un PDF per iniziare.")
        return

    raw = [f.getvalue() for f in files]
    plan = merge_plans([cached_parse(b) for b in raw])
    sig = hashlib.md5(b"".join(raw)).hexdigest()[:8]
    meta = plan["meta"]

    if not plan["lists"]:
        st.error("Non ho trovato nessuna 'LISTA n' nei PDF caricati.")
        return

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Dati e intestazione")
        titolo = st.text_input("Titolo", f"Piano Alimentare{' ' + meta['kcal'] + ' Kcal' if meta.get('kcal') else ''}", key=f"t{sig}")
        prof = st.text_input("Professionista", meta.get("professionista") or DEFAULT_PROFESSIONISTA, key=f"pr{sig}")
        paziente = st.text_input("Paziente", meta.get("paziente", ""), key=f"pz{sig}")
        c1, c2, c3 = st.columns(3)
        peso = c1.text_input("Peso", meta.get("peso", ""), key=f"pe{sig}")
        bmi = c2.text_input("BMI", meta.get("bmi", ""), key=f"b{sig}")
        obiettivo = c3.text_input("Obiettivo", meta.get("obiettivo", ""), key=f"o{sig}")
        c4, c5 = st.columns(2)
        acqua = c4.text_input("Acqua", meta.get("acqua", ""), key=f"a{sig}")
        controllo = c5.text_input("Prossimo controllo", meta.get("controllo", ""), key=f"c{sig}")
        badge = st.text_input("Badge in alto (se manca l'obiettivo)", meta.get("sottotitolo", ""), key=f"bd{sig}")

        st.subheader("Guida & note")
        mostra_guida = st.checkbox("Mostra tab 'Guida & Cibi'", True, key=f"mg{sig}")
        evitare_default = ""
        for card in plan["cards"]:
            if card["title"] == "Indicazioni":
                for b in card["blocks"]:
                    if b["kind"] == "neg" and norm_label(b["label"]).startswith("EVITARE"):
                        evitare_default = "; ".join(t for _, t in b["items"])
                        break
        red_title = st.text_input("Titolo box rosso", "DA EVITARE", key=f"rt{sig}")
        red_text = st.text_area("Box rosso (vuoto = nascosto)", evitare_default, key=f"rx{sig}", height=90)
        integrazione = st.text_area("Integrazione consigliata (una voce per riga, opzionale)", "", key=f"i{sig}", height=90)
        free_text = st.text_input("Testo del pasto libero", DEFAULT_PASTO_LIBERO, key=f"ft{sig}")
        free_warn = st.text_input("Avviso nel pasto libero (opzionale)", "", key=f"fw{sig}")

        with st.expander("Liste estratte (controllo)"):
            for n, lst in sorted(plan["lists"].items()):
                st.markdown(f"**Lista {n}** – {', '.join(lst['days']) or 'giorni non rilevati'}")
                for s in lst["sections"]:
                    st.markdown(f"- {s['title']}: {len(s['items'])} voci")

    opts = dict(
        titolo=titolo, professionista=prof, paziente=paziente, peso=peso, bmi=bmi, obiettivo=obiettivo,
        acqua=acqua, controllo=controllo, badge=badge, data=meta.get("data", ""),
        mostra_guida=mostra_guida, red_title=red_title, red_text=red_text, integrazione=integrazione,
        free_text=free_text, free_warn=free_warn,
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
    st.download_button("⬇️ Scarica HTML", html.encode("utf-8"), file_name=f"piano-{slug}.html", mime="text/html")

    st.subheader("Invio al paziente")
    st.caption(
        "Su WhatsApp il file HTML non si apre bene (soprattutto su iPhone): meglio inviare un link. "
        "Pubblica la pagina (es. GitHub Pages) e condividi l'indirizzo."
    )

    cfg = {}
    try:
        cfg = dict(st.secrets)
    except Exception:  # noqa: BLE001
        pass
    can_publish = all(k in cfg for k in ("GITHUB_TOKEN", "GITHUB_REPO", "GITHUB_PAGES_BASE"))

    if can_publish:
        st.warning(
            "⚠️ Dati sanitari: se il repository è pubblico, chiunque abbia il link (o veda il repo) può leggere il piano. "
            "Usa un repository dedicato, valuta di omettere il cognome e cancella i file quando non servono."
        )
        phone = st.text_input("Numero WhatsApp del paziente (formato internazionale, es. 393331234567)", "")
        if st.button("🚀 Pubblica e genera link"):
            try:
                url = publish_to_github(html, slug, cfg)
                st.session_state[f"url{sig}"] = url
            except Exception as e:  # noqa: BLE001
                st.error(f"Pubblicazione non riuscita: {e}")
        if st.session_state.get(f"url{sig}"):
            url = st.session_state[f"url{sig}"]
            st.success(f"Pubblicato (online entro circa 1 minuto): {url}")
            msg = f"Ciao! Ecco il tuo piano alimentare aggiornato: {url}"
            digits = re.sub(r"\D", "", phone)
            wa = f"https://wa.me/{digits}?text={quote(msg)}" if digits else f"https://wa.me/?text={quote(msg)}"
            st.markdown(f"[📲 Apri WhatsApp con il messaggio pronto]({wa})")
    else:
        st.info(
            "Per pubblicare con un clic aggiungi in `.streamlit/secrets.toml` (o nei Secrets di Streamlit Cloud): "
            "GITHUB_TOKEN, GITHUB_REPO (utente/repo), GITHUB_PAGES_BASE (https://utente.github.io/repo) e, "
            "facoltativi, GITHUB_BRANCH e GITHUB_FOLDER. In alternativa scarica l'HTML e caricalo dove preferisci."
        )


if __name__ == "__main__":
    main()
