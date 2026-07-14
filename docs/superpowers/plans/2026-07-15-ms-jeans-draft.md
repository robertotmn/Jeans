# Riscrittura del cartamodello jeans secondo M. Müller & Sohn "Jeans-Basics"

> Piano approvato il 2026-07-14. Vedi gli **emendamenti della fase 0** in fondo:
> la regola del punto cavallo davanti è stata corretta rispetto al piano originale.

## Contesto

L'app (PySide6 + export PDF/SVG 1:1) generava il cartamodello con 5 varianti
(Landis basic/updated, Mueller 1/2/3) giudicate sbagliate: si riparte da zero.
La nuova unica fonte è il PDF **"Metric Pattern Techniques – Jeans-Basics"
(M. Müller & Sohn)**: Basic Jeans Block (pp. 2–3) + Design 3069 "jeans classico
5 tasche" (pp. 4–5). Le pagine del PDF sono in scala (taglia 50): estratte
vettorialmente, danno sia l'algoritmo sia l'oracolo di test
(`tests/data/ms_reference_size50.json`).

**Decisioni utente:**
1. Margini di cucitura **configurabili nel form** (linee nette M&S + contorno di
   taglio; default cuciture 1 cm, orlo 3 cm).
2. Pezzi: **tutti quelli del PDF + patta zip (paramontura+scudo) + taschino
   porta-monete** (derivati, non tracciati nel libro).
3. **Eliminare tutti** i vecchi sistemi di tracciamento e relativi test/template.

## Misure e formule (unità interne: mm; input form in cm/inch)

Input (default = taglia 50): `W` 90 · `Hg` 102 · `Kg` 43 · `Hw` 38 · `Os` 102 · `Is` 82.

Derivate: `Br = Os − Is` (20) · `Kl = Is/2 + Is/10 − 2` (47.2) · `Ftw = Hg/4`
(25.5) · `Fcw = Hg/20` (5.1) · `Bcw = Hg/10 + 2.0` (12.2) · `Btw = Hg/4 + 2.5`
(28.0) · quota fianchi = `Is + Hg/20 + 3` sopra l'orlo.

## Algoritmo di tracciamento (validato sul disegno in scala, ~1 mm)

Coordinate: mm, `x=0` linea base davanti (lato fianco), `y=0` linea vita,
y verso l'orlo. Crease davanti a `x_cr = (Ftw+Fcw)/2 − 2`.

**Davanti** (pp. 2–3):
1. Orizzontali: vita y=0, fianchi y=Os−(Is+Hg/20+3), cavallo y=Os−Is,
   ginocchio y=Os−Kl, orlo y=Os.
2. Sulla linea fianchi: `Ftw` da x=0 (verticale c.f.), poi `Fcw` → punto
   guida `(Ftw+Fcw, y_fianchi)` **sulla linea fianchi** (emendamento, v. sotto).
3. Orlo: `±(Hw/4 − 0.5)` dal crease; ginocchio: `±(Kg/4 − 0.5)` dal crease.
4. Guida interna: dal ginocchio-interno al punto Fcw sulla linea fianchi;
   **punto cavallo = intersezione con la linea cavallo** (drawn: x=292.8 mm).
   Guida fianco: ginocchio → punto su x=0 a metà tra fianchi e cavallo.
5. Vita: c.f. abbassato 1 cm e rientrato 1.5 → `(Ftw−1.5, 1)`; linea c.f. da lì
   per `(Ftw, y_fianchi)`. Vita lato fianco a `(1, 0)`. Vita ⊥ c.f., poco curva.
6. Curva cavallo: `d` = distanza sul cavallo tra la **verticale c.f.** (x=Ftw)
   e il punto cavallo; risalire `d/2` sulla verticale; guida obliqua dal punto
   `d/2` al punto cavallo; curva tangente al c.f. che chiude sul punto cavallo.
7. Interna leggermente scavata; fianco curvo vita→guida.
8. Design: apertura tasca dalla vita (inizio a **130 mm dall'angolo fianco
   lungo la vita** — v. emendamenti) al fianco ~80 mm sotto vita, +6 mm;
   impuntura patta 3.4 cm, apertura 15 cm; grainline sul crease.

**Dietro** (sopra il davanti, stesso frame):
1. Sotto il ginocchio: +1 cm fuori dal davanti (orlo e ginocchio).
2. Fianchi esteso 2 cm → `P_out=(−20, y_fianchi)`; `Btw` **in orizzontale** →
   `P_btw`; `Bcw` **in orizzontale** → `P_bcw`.
3. Punto slant `P_1 = (0, y_cavallo − 10)`; linea ausiliaria `P_1 → P_btw`;
   **c.b. ⊥ alla ausiliaria** per `P_btw`.
4. Guida fianco dietro: ginocchio-fianco → `P_out`; guida interna dietro:
   ginocchio-interno → `P_bcw`.
5. Trasferimenti (validati: 54.98 / −0.7 / +3.5):
   - `W_raw` sulla guida fianco a lunghezza-arco = fianco davanti (vita→ginocchio);
   - punto cavallo dietro sulla guida interna a lunghezza-arco = interna davanti − 0.7;
   - punto c.b.-vita sul c.b. a `dist(crease@ginocchio → W_raw) + 3.5`
     (aggiustato perché vita ⊥ c.b.).
6. Vita dietro: da c.b., lunghezza `W/2 + 2 − vita_davanti`; resto ≤1–1.5
   assorbito nella curva fianco (warning oltre).
7. Carré: da 3.5 sotto vita (fianco) a 7.0 sotto vita lungo il c.b. Pinces ai
   terzi della vita, profondità 0.8 (esterna) e 1.2 (interna), punte sul carré.
8. Sella: retta c.b.-vita → c.b.@fianchi, poi curva a J al punto cavallo
   tangente all'interna. Interna scavata (~1.6 max). Fianco per il punto a 2 cm.
9. Il pezzo "dietro" è tagliato alla linea carré.

Verifiche integrate: somma orli = Hw, ginocchia = Kg, agio `A+B−Hg/2` (~2.5 sul
disegno; warning se < 1 → tessuto stretch), transizioni cavallo tangenti.

**Oracolo taglia 50** (drawn, frame app mm): crease x=133; cavallo davanti
(292.8, 200.0); d=37.8; ginocchio dietro (20.0, 548)/(245.9, 548); cavallo
dietro (350.0, 219.8); vita fianco dietro (−21.2, −1.6); c.b. (212.9, −52.8);
carré (−21.9, 34.4)→(231.4, 14.7); pinces: centri (56.9, −18.7)/(134.9, −35.7),
intake 8/12 mm, punte sul carré. Vita dietro corda 23.94 = ½W+2−23.08 ✓.

## Pezzi prodotti (Design 3069)

davanti ×2 · dietro ×2 · carré ×2 (pinces chiuse per rotazione, raccordi +
verifica lunghezza) · cinturino (½W, h 4, tacca tasca ~100 mm, tacca Ss =
vita davanti, passanti 1.2 a 78.6 / Ss+20 / c.b., + sormonto configurabile) ·
tasca posteriore (top 17, centro 18, fondo 6.5/7.5 proiettati, punta 3;
piazzamento: TL 50 mm/TR 40 mm sotto carré, asse punta a crease −10.5 mm) ·
sacchetto tasca (~24) + paramontura · patta (paramontura+scudo, ~4.2 ×
vent15+3) · taschino porta-monete (~9×10.5) · striscia passanti.

Ogni pezzo: linea netta + contorno di taglio (margini per classe di bordo,
default cuciture 10 mm, orlo 30 mm; 0 = disattivato).

## Architettura

**Riuso**: `geometry.py` (+ arc-length e offset per-bordo), `export_pdf.py`,
`export_svg.py`, `preview_widget.py`, struttura `main_window.py`.

**Nuovi/riscritti**: `measurements.py` (unica dataclass M&S con derivate);
`draft_ms.py` (`draft_front`, `draft_back`: landmark, edge nominati,
construction lines, report); `draft_ms_extras.py` (carré, cinturino, tasche,
patta, taschino, passanti); `pattern.py` (`PatternPiece.cut_outline`,
`Pattern.report`, `build_full_pattern(m, sa)` unico).

**UI**: `measurement_form.py` (6 campi M&S + unità + 2 campi margini);
`main_window.py` (label con Br, Kl, agio, warning).

**Script**: `scripts/extract_ms_reference.py` → `tests/data/ms_reference_size50.json`
(committato: i test non richiedono il PDF).

**Eliminati**: draft_basic/updated/extras, draft_mueller*, warp.py,
raster_warp.py, templates/*, scripts/extract_mueller_template.py,
scripts/preview_mueller3_anchors.py, verification_*.pdf, test relativi.

## Fasi (commit per fase, su master)

0. Riferimento vettoriale + PDF in docs ✅
1. `measurements.py` + test chart taglia 50
2. `geometry.py`: arc-length + offset per-bordo + test
3. `draft_front` + test landmark (tol 1.5 mm) + invarianti
4. `draft_back` + test landmark + invarianti (trasferimenti ±1 mm, vita, ⊥, somme, agio)
5. `draft_ms_extras.py` + test (carré: lunghezza cucitura == linea carré ±2 mm)
6. `pattern.py` + margini + report + PDF di prova
7. UI + export + eliminazioni + README; suite completa verde
8. Verifica end-to-end: overlay generato-vs-libro (max dev < 2 mm su landmark),
   GUI, export PDF singolo/tiled + SVG, quadrato calibrazione

## Fuori scope

Salopette e giacche (pp. 6–18); gradazione automatica; tacche di montaggio
complete; istruzioni di cucito.

## Emendamenti dalla fase 0 (estrazione vettoriale)

1. **Punto cavallo davanti** — il piano originale lo poneva a `(Ftw+Fcw,
   y_cavallo)`. Il disegno dimostra che `Fcw` è misurato **sulla linea
   fianchi**: la guida interna va dal ginocchio-interno a `(Ftw+Fcw,
   y_fianchi)` e il punto cavallo è l'intersezione della guida con la linea
   cavallo (drawn x=292.8 vs 306 della vecchia lettura; conferma incrociata:
   interna davanti 35.34 − 0.7 = 34.63 = interna dietro disegnata ✓).
2. **Costruzione curva cavallo davanti** — `d` è misurato dalla **verticale**
   c.f. (non dalla c.f. obliqua): d=37.8 mm, ½d risalito sulla verticale.
3. **Apertura tasca davanti** — il disegno (pezzo p.5 e tacca sul cinturino,
   concordi) pone l'inizio a ~130 mm dall'angolo fianco lungo la vita; la quota
   stampata "12" non trova riscontro esatto nel disegno (illustrazione con ~2%
   di slop). Si adotta **130 mm** (doppia conferma grafica); profondità fianco
   80 mm (quota stampata "8") + 6 mm di estensione.
4. **Tasca dietro** — quote esatte dal disegno: top 17.00, centro 18.03,
   proiezioni fondo 6.5/7.5, punta 3 sotto; piazzamento TL 50 mm / TR 40 mm
   sotto il carré, asse della punta a crease −10.5 mm.
5. **Cinturino** — disegnato esattamente 45×4 (½W, senza sormonto): tacca Ss a
   230.8 = vita davanti, tacca tasca a 100.6, passanti (1.2) a 78.6 e Ss+20,
   passante c.b. a cavallo della cucitura c.b.
