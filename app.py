<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Piano Alimentare - Web App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <!-- PDF.js per la lettura dei PDF direttamente nel browser -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    </script>
    <style>
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        body { -webkit-tap-highlight-color: transparent; }
    </style>
</head>
<body class="bg-gray-100 text-gray-800 font-sans pb-12">

    <!-- Header -->
    <header class="bg-emerald-600 text-white p-5 rounded-b-3xl shadow-lg sticky top-0 z-50">
        <div class="flex justify-between items-center mb-2">
            <div>
                <h1 id="app-title" class="text-xl font-bold">Piano Alimentare VLCKD</h1>
                <p id="app-subtitle" class="text-xs text-emerald-100">Dott.ssa Elisa Vasa • Biologa Nutrizionista</p>
            </div>
            <div id="app-goal" class="bg-emerald-700 px-3 py-1 rounded-full text-xs font-semibold">
                Obiettivo: 72 Kg
            </div>
        </div>
        <!-- User Info Bar -->
        <div class="flex justify-between text-xs bg-emerald-700/50 p-2.5 rounded-xl mt-3 text-emerald-50 backdrop-blur-sm">
            <span><b>Paziente:</b> <span id="info-patient">Fabio Greco</span></span>
            <span><b>Peso:</b> <span id="info-weight">78 Kg</span></span>
            <span><b>BMI:</b> <span id="info-bmi">25.2</span></span>
        </div>
        
        <!-- PDF Loader Button -->
        <div class="mt-3 pt-3 border-t border-emerald-500/50 flex items-center justify-between">
            <label for="pdf-upload" class="cursor-pointer bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition-all flex items-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-file-pdf"></i> Carica PDF Piano
            </label>
            <input type="file" id="pdf-upload" accept="application/pdf" class="hidden" onchange="loadPdf(event)">
            <span id="pdf-loading-status" class="text-[11px] text-emerald-100 italic">Usa il default o carica un PDF</span>
        </div>
    </header>

    <!-- Main Container -->
    <main class="p-4 max-w-md mx-auto">

        <!-- Quick Info Banner -->
        <div class="bg-white p-3.5 rounded-2xl shadow-sm border border-gray-100 mb-4 flex items-center justify-between text-xs text-gray-600">
            <div class="flex items-center gap-2">
                <i class="fa-solid fa-droplet text-blue-500 text-base"></i>
                <span><b>Acqua:</b> Min 2 Litri/giorno</span>
            </div>
            <div class="flex items-center gap-2">
                <i class="fa-solid fa-clock text-amber-500 text-base"></i>
                <span><b>Controllo:</b> Tra 1 mese</span>
            </div>
        </div>

        <!-- Day Selector Tabs -->
        <div class="flex gap-2 overflow-x-auto no-scrollbar mb-4 py-1">
            <button onclick="showTab('lista1')" id="tab-lista1" class="tab-btn px-4 py-2.5 bg-emerald-600 text-white rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">
                Lun / Gio (Lista 1)
            </button>
            <button onclick="showTab('lista2')" id="tab-lista2" class="tab-btn px-4 py-2.5 bg-white text-gray-600 rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">
                Mar / Ven (Lista 2)
            </button>
            <button onclick="showTab('lista3')" id="tab-lista3" class="tab-btn px-4 py-2.5 bg-white text-gray-600 rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">
                Mer / Dom (Lista 3)
            </button>
            <button onclick="showTab('lista4')" id="tab-lista4" class="tab-btn px-4 py-2.5 bg-white text-gray-600 rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">
                Sabato (Lista 4)
            </button>
            <button onclick="showTab('regole')" id="tab-regole" class="tab-btn px-4 py-2.5 bg-white text-gray-600 rounded-xl text-xs font-bold shadow-sm whitespace-nowrap transition-all">
                💡 Guida & Cibi
            </button>
        </div>

        <!-- Dynamic Content Container -->
        <div id="dynamic-content">
            <!-- LISTA 1 -->
            <div id="lista1" class="tab-content space-y-3">
                <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-2.5 rounded-xl font-medium flex justify-between items-center">
                    <span>🗓️ Giornate: <b>Lunedì</b> e <b>Giovedì</b></span>
                    <span class="bg-amber-200 text-amber-900 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Lista 1</span>
                </div>

                <!-- Colazione -->
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100">
                        <i class="fa-solid fa-mug-hot"></i> COLAZIONE
                    </div>
                    <ul class="text-xs space-y-2 text-gray-700">
                        <li>☕ <b>Tè o caffè</b> non zuccherati (q.b.)</li>
                        <li>🍓 <b>Frutta fresca consentita:</b> 100g</li>
                        <li>🥣 <b>Yogurt Greco Intero (10% grassi):</b> 150g
                            <div class="text-[11px] text-gray-500 bg-gray-50 p-2 rounded-lg mt-1 border border-gray-100">
                                <b>Oppure:</b> Yogurt greco 0% 150g + 10g granella di nocciole/mandorle / Ricotta fresca 120g / Albume 100g + 20g farina di mandorle/arachidi/nocciole (crepes) / Uova n°2
                            </div>
                        </li>
                        <li>🎃 <b>Semi di zucca:</b> 10g
                            <span class="block text-[11px] text-gray-500"><b>Oppure:</b> Noci, mandorle, nocciole, ecc. 10g / Burro d'arachidi 100% 10g</span>
                        </li>
                    </ul>
                </div>

                <!-- Spuntino Mattina -->
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-1">
                        <i class="fa-solid fa-apple-whole"></i> SPUNTINO MATTINA
                    </div>
                    <p class="text-xs text-gray-700">🌰 <b>Mandorle:</b> 20g <span class="text-gray-500 text-[11px]">(Oppure noci, nocciole, anacardi, pistacchi, pinoli al naturale 20g)</span></p>
                </div>

                <!-- Pranzo -->
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100">
                        <i class="fa-solid fa-utensils"></i> PRANZO
                    </div>
                    <ul class="text-xs space-y-2 text-gray-700">
                        <li>🐟 <b>Tonno sott'olio ben scolato:</b> 110g (scatoletta grande)
                            <span class="block text-[11px] text-gray-500"><b>Oppure:</b> Sgombro 100g / Salmone fresco, surgelato o al naturale 120g</span>
                        </li>
                        <li>🥦 <b>Verdure consentite:</b> 200g</li>
                    </ul>
                </div>

                <!-- Spuntino Pomeriggio -->
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-1">
                        <i class="fa-solid fa-cookie-bite"></i> SPUNTINO POMERIGGIO
                    </div>
                    <p class="text-xs text-gray-700">🫒 <b>Olive denocciolate:</b> 100g <span class="text-gray-500 text-[11px]">(Oppure cocco fresco 60g / Avocado 100g)</span></p>
                </div>

                <!-- Cena -->
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100">
                        <i class="fa-solid fa-moon"></i> CENA
                    </div>
                    <ul class="text-xs space-y-2 text-gray-700">
                        <li>🍗 <b>Pollo (petto):</b> 200g
                            <span class="block text-[11px] text-gray-500"><b>Oppure:</b> Tacchino (petto) 200g</span>
                        </li>
                        <li>🥗 <b>Verdure consentite:</b> 200g</li>
                    </ul>
                </div>

                <!-- Condimenti -->
                <div class="bg-emerald-50 p-3.5 rounded-2xl border border-emerald-100 text-xs text-emerald-900">
                    <p class="font-bold flex items-center gap-1.5"><i class="fa-solid fa-bottle-droplet text-emerald-600"></i> CONDIMENTI GIORNALIERI</p>
                    <p class="mt-1"><b>Olio EVO:</b> 30g (circa 6 cucchiaini da tè da dividere tra pranzo e cena).</p>
                    <p class="text-gray-600 text-[11px] mt-0.5">Aceto, limone, spezie, aglio: q.b.</p>
                </div>
            </div>

            <!-- LISTA 2 -->
            <div id="lista2" class="tab-content hidden space-y-3">
                <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-2.5 rounded-xl font-medium flex justify-between items-center">
                    <span>🗓️ Giornate: <b>Martedì</b> e <b>Venerdì</b></span>
                    <span class="bg-amber-200 text-amber-900 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Lista 2</span>
                </div>
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100">
                        <i class="fa-solid fa-utensils"></i> PRANZO
                    </div>
                    <ul class="text-xs space-y-2 text-gray-700">
                        <li>🐟 <b>Salmone selvatico affumicato:</b> 100g</li>
                        <li>🥑 <b>Avocado:</b> 50g</li>
                        <li>🥦 <b>Verdure consentite:</b> 200g</li>
                    </ul>
                </div>
            </div>

            <!-- LISTA 3 -->
            <div id="lista3" class="tab-content hidden space-y-3">
                <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-2.5 rounded-xl font-medium flex justify-between items-center">
                    <span>🗓️ Giornate: <b>Mercoledì</b> e <b>Domenica</b></span>
                    <span class="bg-amber-200 text-amber-900 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Lista 3</span>
                </div>
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
                    <div class="flex items-center gap-2 text-emerald-600 font-bold mb-2 pb-1 border-b border-gray-100">
                        <i class="fa-solid fa-utensils"></i> PRANZO
                    </div>
                    <ul class="text-xs space-y-2 text-gray-700">
                        <li>🥚 <b>Uova:</b> 3 uova (180g)</li>
                        <li>🥦 <b>Verdure consentite:</b> 200g</li>
                    </ul>
                </div>
            </div>

            <!-- LISTA 4 -->
            <div id="lista4" class="tab-content hidden space-y-3">
                <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-2.5 rounded-xl font-medium flex justify-between items-center">
                    <span>🗓️ Giornata: <b>Sabato</b></span>
                    <span class="bg-amber-200 text-amber-900 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Lista 4</span>
                </div>
                <div class="bg-purple-50 p-4 rounded-2xl border border-purple-200 shadow-sm">
                    <span class="flex items-center gap-2 text-purple-900 font-bold mb-1"><i class="fa-solid fa-star text-purple-600"></i> CENA: PASTO LIBERO</span>
                    <p class="text-xs text-purple-800 mt-2">Rimanere sugli alimenti consentiti in quantità libera. ⚠️ EVITARE TASSATIVAMENTE I CARBOIDRATI!</p>
                </div>
            </div>

            <!-- REGOLE E LISTE CIBI -->
            <div id="regole" class="tab-content hidden space-y-4">
                <div class="relative">
                    <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-gray-400 text-xs"></i>
                    <input type="text" id="foodSearch" onkeyup="searchFoods()" placeholder="Cerca un alimento (es. carote, zucchine)..." class="w-full bg-white pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm">
                </div>

                <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100 text-xs text-blue-900 space-y-1.5">
                    <p class="font-bold text-blue-950 flex items-center gap-1.5"><i class="fa-solid fa-pills text-blue-600"></i> INTEGRAZIONE CONSIGLIATA</p>
                    <ul class="list-disc pl-4 space-y-1 text-gray-700">
                        <li><b>Magnesio e Potassio</b> senza zucchero (al bisogno)</li>
                        <li><b>Cardo Mariano:</b> 3 compresse al giorno</li>
                    </ul>
                </div>

                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 space-y-3">
                    <h3 class="font-bold text-xs text-gray-900 border-b border-gray-100 pb-2">🥬 VERDURE & FRUTTA</h3>
                    <div>
                        <span class="text-[11px] font-bold text-emerald-700 uppercase block mb-1">✅ Verdure Consentite</span>
                        <p class="text-xs text-gray-600 bg-emerald-50/50 p-2.5 rounded-xl food-item">Fiori di zucca, Radicchio, Cicoria, Funghi, Zucchine, Cetrioli, Lattuga, Spinaci.</p>
                    </div>
                    <div>
                        <span class="text-[11px] font-bold text-red-600 uppercase block mb-1">❌ Verdure da Evitare</span>
                        <p class="text-xs text-gray-600 bg-red-50/50 p-2.5 rounded-xl food-item">Carote, Patate, Pomodori, Peperoni, Cipolle, Melanzane.</p>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Interactive Script -->
    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-emerald-600', 'text-white');
                btn.classList.add('bg-white', 'text-gray-600');
            });
            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById('tab-' + tabId);
            if(activeBtn) {
                activeBtn.classList.remove('bg-white', 'text-gray-600');
                activeBtn.classList.add('bg-emerald-600', 'text-white');
            }
        }

        function searchFoods() {
            let input = document.getElementById('foodSearch').value.toLowerCase();
            let items = document.querySelectorAll('.food-item');
            items.forEach(item => {
                let text = item.textContent.toLowerCase();
                item.parentElement.style.display = text.includes(input) ? "block" : "none";
            });
        }

        // Funzione per leggere e convertire dinamicamente un PDF caricato
        async function loadPdf(event) {
            const file = event.target.files[0];
            if (!file) return;

            const statusEl = document.getElementById('pdf-loading-status');
            statusEl.textContent = "Lettura PDF in corso...";

            try {
                const arrayBuffer = await file.arrayBuffer();
                const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                let fullText = "";

                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const pageText = textContent.items.map(item => item.str).join(" ");
                    fullText += pageText + "\n";
                }

                // Estrazione dati di base o generazione vista formattata dal testo estratto
                parseAndDisplayPdfText(fullText, file.name);
                statusEl.textContent = "PDF caricato con successo! ✅";
            } catch (error) {
                console.error(error);
                statusEl.textContent = "Errore nella lettura del PDF ❌";
            }
        }

        function parseAndDisplayPdfText(text, filename) {
            // Aggiorna titolo con il nome del file PDF caricato
            document.getElementById('app-title').textContent = filename.replace(/\.[^/.]+$/, "");
            
            // Crea una vista dinamica basata sul testo estratto dal PDF
            const container = document.getElementById('dynamic-content');
            container.innerHTML = `
                <div class="space-y-3">
                    <div class="bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs p-3 rounded-xl font-medium">
                        📄 <b>Contenuto estratto dal PDF:</b> ${filename}
                    </div>
                    <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 space-y-2">
                        <h3 class="font-bold text-xs text-emerald-600 border-b pb-1"><i class="fa-solid fa-file-lines"></i> Testo del Piano</h3>
                        <p class="text-xs text-gray-700 whitespace-pre-line leading-relaxed max-h-96 overflow-y-auto">${escapeHtml(text)}</p>
                    </div>
                </div>
            `;
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }
    </script>
</body>
</html>
