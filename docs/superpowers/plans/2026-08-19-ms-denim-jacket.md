# Classic Denim Jacket (M&S Design 4041) — piano di implementazione

> Piano del 2026-08-19. Fonte unica: **"Metric Pattern Techniques – Jeans-Basics"
> (M. Müller & Sohn)**, `docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf`:
> Basic Denim Jacket Block (pp. 11–13) + Design 4041 "Classic Denim Jacket"
> (pp. 14–15). Le pagine sono in scala 1:6 (taglia 50) e sono state sondate
> vettorialmente: ogni quota di questo piano è verificata sui vettori.
> Il Design 4042 (Trucker Jacket, pp. 16–18) è fuori scope.

## Obiettivo e vincoli

- Aggiungere la generazione del cartamodello della giacca, selezionabile da una
  **tendina modello** nel form: item esatti `"Basic Jeans"` (default) /
  `"Classic Denim Jacket"`.
- **La logica jeans non cambia**: `build_full_pattern`, `draft_ms.py`,
  `draft_ms_extras.py`, `measurements.py`, export e preview restano intatti.
  L'unica modifica a codice condiviso è l'estensione name-based di
  `SeamAllowances.for_edges` (bordi `fold*` → margine 0), provabilmente inerte
  per i jeans (nessun bordo jeans si chiama `fold*`) e coperta da test dedicato.
- **La suite attuale (128 test) resta verde a ogni fase.**
- Form: riuso dei campi esistenti `waistband` (= Wg giro vita) e `hip_girth`
  (= Hg) e dei margini; nuovi campi `body_height` (Bh), `chest_girth` (Cg),
  `sleeve_length` (Sl). I campi solo-jeans si nascondono col modello giacca e
  viceversa.
- Ogni pezzo: linea netta M&S + contorno di taglio con i margini configurati
  (come i jeans); i bordi in piega ricevono margine 0.

## Misure e formule (unità interne: mm; input form in cm/inch)

Input (default = taglia 50): `Bh` 179 · `Cg` 100 · `Wg` 90 (campo waistband) ·
`Hg` 102 (campo hip_girth) · `Sl` 64.

Derivate del chart p. 12 (formula → valore scelto nell'intervallo → verifica):

| Sigla | Nome                | Formula libro                                   | Scelta         | Taglia 50 | Chart | Verifica |
|-------|---------------------|--------------------------------------------------|----------------|-----------|-------|----------|
| Nw    | Neck width          | 1/10 di ½Cg + 3                                 | +3.0           | **8.0**   | 8.5   | disegno usa 8.0 ovunque → chart refuso (D1) |
| Sd    | Scye depth          | ⅛Cg + 12.5                                      | —              | 25.0      | 25.0  | ✓ |
| Bwl   | Back waist length   | ¼Bh                                              | —              | 44.75     | 44.8  | ✓ |
| Lg    | Length              | ½Bh − ⅛Bh − (2…4)                                | **−3.125**     | 64.0      | 64.0  | esatto (D4) |
| Ad    | Armhole depth       | Sd + 2.5                                         | —              | 27.5      | 27.5  | ✓ |
| Bw    | Back width          | 2/10 Cg + (1…1.5) se Cg≤100; 1/10 Cg + (11…11.5) | **+1.2 / +11.2** | 21.2    | 21.2  | ✓ (continuità a Cg=100) |
| Sw    | Scye width          | ⅛Cg + (2.5…3.5)                                  | **+3.0**       | 15.5      | 15.5  | ✓ |
| Cw    | Chest width         | 2/10 Cg + (0.5…1)                                | **+0.8**       | 20.8      | 20.8  | ✓ |
| Aw    | Abdomen width       | ¼Wg − (1…2); se Aw<Cw → Aw=Cw                    | **−1.3**       | 21.2      | 21.2  | ✓ (21.2>20.8) |
| —     | Total chest         | Bw+Sw+Cw = ½Cg + agio                            | —              | 57.5      | 57.5  | agio 7.5 ✓ |

Derivate manica (chart p. 13; **misurate sul blocco tracciato**, non formule
chiuse — vivono in `draft_jacket_sleeve`, non nelle misure):

| Sigla | Definizione                                                                | Taglia 50 (disegno) | Chart |
|-------|----------------------------------------------------------------------------|---------------------|-------|
| Ah    | back ah (verticale SP_b→linea torace) + front ah (obliqua SP_f→pitch∩torace) | 23.37 + 20.79 = 44.16 | 44.2 |
| ½Ah   | Ah/2 + **0.2 di calibrazione** (D12)                                        | 22.28               | 22.3  |
| Ac    | lunghezza arco giromanica dietro + davanti                                 | 28.48 + 24.82 = 53.30 | 53.4 |
| Sch   | ½Ah − (1/10 di ½Ah + 4.0)                                                  | 16.05               | 16.1  |
| Scw   | ½Ac − 2.5                                                                  | 24.15               | 24.2  |
| Sh    | sleeve hem: scelta di modello, **costante 31.0** (D13)                     | 31.0                | 31.0  |

`JacketMeasurements` (nuova dataclass frozen, mm): campi `body_height_mm`,
`chest_girth_mm`, `waist_girth_mm`, `hip_girth_mm`, `sleeve_length_mm`;
property per tutte le derivate corpo della tabella. Validazione in
`__post_init__`: tutti > 0, `sleeve_length < body_height`,
`jacket_length > armhole_depth` (ricalcolate inline, messaggi espliciti);
nessun range "plausibile" bloccante (coerente con `Measurements` jeans) (D25).

## Sistemi di coordinate

- **Corpo** (dietro+davanti in un unico frame, come il libro): mm, origine =
  punto collo dietro **N**; `y` cresce verso il basso (torace y=Sd, vita y=Bwl,
  orlo y=Lg); `x` cresce dal c.b. **verso il davanti** (specchiato rispetto
  alla pagina: ogni "measure … to the left" del libro diventa `+x`). Gap
  costruttivo dietro/davanti `BODY_GAP_MM = 60.0` (solo piazzamento, identico
  al disegno → overlay 1:1). Nessuno specchio al rendering: i pezzi si
  tagliano indifferentemente ribaltati, il frame è scelto per leggibilità
  delle formule (D11).
- **Manica**: frame proprio, origine = punto **A** (inizio costruzione),
  y giù, x verso il dietro-manica (come il disegno p. 12, nessun mirror).
- **Pezzi liberi** (colletto, cinturino, polsino, linguetta, patta, sacchetti):
  origine locale (0,0), come `build_waistband`/`build_fly_facing` jeans.
- Estrazione PDF p. 11: scala 4.7250 pt/cm, c.b. verticale a x_pdf=527.9,
  N a y_pdf=467.9, orlo y_pdf=770.3 (span = Lg 64):
  `x_cm=(527.9−X_pdf)/4.7250`, `y_cm=(Y_pdf−467.9)/4.7250`. P. 12: scala
  4.72656, A=(415.06,464.23). P. 14: scala 4.7242, **ogni elemento duplicato
  con shift verticale 548.70 pt** (tenere la copia visibile). P. 15: scala
  4.7267, nessun duplicato. P. 11/12: nessun duplicato.

## Costruzione — blocco corpo (pp. 11–12, valori taglia 50 in cm)

**Dietro** (passo 1):
1. Verticale c.b. x=0 da N(0,0) a (0,Lg); orizzontali a y=0, Sd, Bwl, Lg.
2. Cucitura c.b. = **una retta** N→K(2.5, Lg) (rientro 2.5 all'orlo; a vita
   x=1.75, a torace x=0.98). Grainline sulla verticale x=0.
3. Scollo: A1=(Nw,0), su 2 → A2=(8,−2); curva da N (tangente orizzontale)
   ad A2, **prolungata di 1** lungo la tangente finale → E=(8.60,−2.80).
4. Larghezza dietro sul torace **dalla cucitura c.b.**: x_bw = 0.98+Bw = 22.18;
   verticale da y=0 a y=Sd.
5. Pendenza spalla: scendi **2.2** su x_bw → S1=(22.18,2.20) (libro 2–2.5, D2);
   guida = retta A2→S1 prolungata di **1.5 lungo la guida** → SP0=(23.61,2.62).
6. Guide giro: dal x_bw sali ¼Sd e sporgi 1 → G1=(23.18,18.74); fianco dietro
   x_sB = x_bw + ½Sw + 1.5 = 31.43; ascella U_b=(31.43,25).
7. Giromanica: curva SP0→G1→U_b; incavo max ~0.5 oltre x_bw (min x=22.68 a
   y≈12.3); arrivo orizzontale in U_b.
8. Orlo: da K **perpendicolare alla cucitura c.b.** fino a x_sB →
   H_b=(31.43,62.86). Fianco: da H_b **perpendicolare all'orlo** fino alla
   vita → W_b=(30.73,44.79) — il rientro t=0.70 è **conseguenza geometrica**,
   non costante (D8); poi retta W_b→U_b.
9. **Seam relocation +1 verso il davanti**: spalla E→SP0 traslata di 1 ⊥ verso
   lo scollo → SP_b=(23.88,1.62); HSP_b = intersezione del prolungamento
   tangente dello scollo con la retta spalla relocata → (9.12,−3.67) (D5).
   Il giromanica passa per SP0 e termina in SP_b. Spalla finita 15.68.

**Davanti** (passo 2):
10. Fianco davanti a **6.00** dal dietro → x_sF=37.43; U_f=(37.43,25).
    Front pitch line x_fpl = x_sF + ½Sw − 1.5 = 43.68, da y=Sd−Ad=−2.5 alla
    hip line. Sul pitch: tacca **FAN a y = Sd − ¼Sw** = 21.125.
11. Cw sul torace dal pitch → C1=(64.49,25); Aw in vita → C2=(64.88,44.79).
    Retta dei punti metà M2(54.28,44.79)→M1(54.08,25) prolungata; angolo
    scollo **Cn = intersezione con l'orizzontale y = Sd−Ad = −2.5** →
    (53.80,−2.50) (il −2.61 disegnato è slop di stampa, D9).
12. Pendenza spalla davanti: 4.5 giù lungo il pitch da P_top → S2=(43.68,2.0);
    ausiliaria = retta Cn→S2 prolungata. **Spalla davanti finita = spalla
    dietro finita − 0.5** (D3): SP0_f sull'ausiliaria a distanza
    (L_dietro_finita − 0.5) da Cn — la relocation trasla rigidamente, quindi
    la lunghezza si conserva. Disegnato: SP0_f=(39.84,3.57).
13. Giromanica davanti: da SP_f scende, resta a x≤x_fpl, **tangente al pitch
    nel punto ¼Sd** (43.68,18.74), porta la tacca FAN, raccordo orizzontale
    in U_f.
14. **Seam relocation −1**: HSP_f=Cn+n=(54.12,−1.66), SP_f=SP0_f+n=(40.24,4.49).
15. Scollo davanti: da Cn misura Nw **lungo la retta dei punti metà** →
    (53.88,5.39); da lì ⊥ alla retta, Nw+2 → punto collo c.f. C0=(63.89,5.28).
    Curva HSP_f→C0 perpendicolare al c.f. in C0 (arco 13.09).
16. C.f.: spezzata C0→C1→C2 (kink minimo al torace); sotto la vita verticale
    x=64.88.
17. Fianco davanti: **stesso rientro t trasferito dal dietro** → W_f=(38.14,
    44.79); sotto la vita speculare al dietro, lunghezza vita→orlo trasferita
    (18.08) → H_f=(37.43,62.86). Orlo: c.f. sotto vita = fianco + 0.5 = 18.58
    → C3=(64.88,63.38); orlo raccordato C3→H_f (⊥ agli estremi).

**Verifiche del libro** (nel report): torace 30.46+27.06 = 57.52 ≈ Total chest
57.5; orlo 28.96+27.46 = 56.42 ≥ ½Hg+5…6 (warning "Check Hg" se sotto);
fianchi uguali davanti/dietro (18.08 sotto vita, 19.81 sopra).

**Trasferimenti per la manica**: back ah = verticale SP_b→torace (23.37);
front ah = obliqua SP_f→(x_fpl,Sd) (20.79); Ah = 44.16; Ac = 28.48+24.82 =
53.30. La tacca FAN va riportata sulla manica.

## Costruzione — blocco manica (pp. 12–13, disegno "2")

1. Verticale da A(0,0): bicipite y=Sch (16.1); Sl y=64; **front sleeve length**
   y=Sl−1.5=62.5; **back sleeve length** y=Sl+1.5=65.5. Gomito = metà del
   tratto bicipite→front-sleeve-length − 1.5 → y=37.80.
2. **FAN** sulla verticale a ¼Sw−1 sopra il bicipite → (0,13.2). Diagonale
   **Scw** da FAN alla linea originale → E=(√(Scw²−y_FAN²),0)=(20.28,0);
   squadra giù da E. **Sp** = metà A→E + 1 → (11.14,0). M1 = metà A→Sp
   (5.57,0); terzi di Sp→E (14.19,0)/(17.23,0). **Q** = ¼Sw sotto E →
   (20.28,3.90).
3. Guide testa: G1 = M1→FAN, **M2 = punto medio di G1** = (2.78,6.60);
   G2 = M2→Sp; G3 = terzo1→Q; guida bassa = Q→T con T = (x_Sp−2.5, y_bicipite)
   = (8.64,16.10).
4. Attacchi cucitura dietro: **U2** = 2 lungo Q→T → (18.87,5.39), squadra a
   destra; **U22** = 2.2 da Q sull'orizzontale di U2 → (21.91,5.39) (il testo
   dice "¼-scye-depth" ma i vettori ancorano a Q = ¼-scye-width: refuso).
5. Piega davanti: FAN(0,13.2) → (2,37.8) al gomito → (0,62.5) all'orlo.
   Orlo: ½Sh in diagonale dal punto (0,62.5) alla back sleeve length →
   B_hem=(√((½Sh)²−3²),65.5)=(15.21,65.5) con Sh=31 (D13).
6. Piega dietro: al gomito, dal fold davanti misura **½Sh + 3.5** → F_b=(21.0,
   37.8) (D14: il disegno vince sul testo "+4.5"); piega F_b→B_hem quasi retta.
7. Cuciture davanti: offset **±3 ⊥ alla piega** (giunti mitre al gomito);
   estremi alti sulla ⊥ alla piega nel punto piega∩bicipite: FST=(−2.75,16.36),
   UST=(3.23,15.88); all'orlo squadrature orizzontali ±3 dal punto (0,62.5).
8. Testa sopramanica: da FST la **copia specchiata** (rispetto alla piega)
   dell'incavo del sottomanica fino a FAN; da FAN **rettilinea lungo G1 fino a
   M2**; da M2 curva esterna a G2 (freccia ~1.7) fino a Sp con tangente
   orizzontale; da Sp scende per Q e termina in U22. Testa sottomanica: da UST
   incavo tangente al bicipite (~x 4–7), segue la guida Q→T, termina in U2.
9. Cucitura dietro sopra: U22 → pancia (max x=22.43 a y≈19) → F_b → lungo la
   piega fino a B_hem. Cucitura dietro sotto: U2 → pancia interna (max
   x=20.85 a y≈30) → **blend tangente sulla piega dietro a 9.0 sotto il
   gomito** (D16) → coincide con la piega fino a B_hem.
10. Orlo sopramanica = retta (−3,62.5)→B_hem come disegnato (D15); orlo
    sottomanica = retta (3,62.5)→B_hem.
11. Report blocco: `cap_len_mm` (disegnato 54.90), `cap_ease_mm` vs Ac
    (disegnato +1.50 = +2.8%; il libro dichiara 4–6%: **solo report**, nessuna
    regolazione nel blocco, D17).

## Design 4041 — corpo (p. 14, passo 1)

1. **Orlo −4.5** (altezza cinturino) parallelo all'orlo blocco, davanti+dietro.
   C.b. nuovo collo→orlo = 59.06.
2. **Scollo abbassato**: −0.5 al c.b. (⊥ al c.b.), −1 alla spalla (lungo la
   cucitura spalla), −1.5 al c.f.; scollo davanti orizzontale al c.f.,
   prolungato attraverso il sormonto. Archi risultanti: dietro 11.40, davanti
   14.61, **½ scollo = 26.01** (base del colletto).
3. **Carré dietro**: 13 dal collo nuovo **lungo il c.b.**, linea ⊥ al c.b.
   fino al giro (lunghezza 22.18, incontra il giro a y≈12.6).
4. **Cucitura pannello dietro**: retta dal punto a **3.5 dal giro lungo il
   carré** al punto orlo a **½−2 dal fianco** (12.48; al c.b. ½+2=16.48).
5. **C.f. raddrizzato** = retta dal collo nuovo al punto c.f. dell'orlo
   (scostamento tollerato ~0.2–0.3); **sormonto 2** parallelo (bordo in
   piega); **impuntura cannoncino 4.5 dal bordo** (=2.5 dal c.f.), collo→orlo.
6. **Occhielli** (5): n.1 a 2 sotto il collo sul c.f.; n.5 centrato sul
   cinturino unito (orlo+2.25); n.2–4 distribuiti uniformemente (passo
   (bh1→bh5)/4 ≈ 13.1). Orizzontali, lunghezza **2.5** (D22), estremità tonda
   **1 prima del c.f.** verso il bordo; **bottoni marcati sul c.f.** (D21).
7. **Carré davanti**: orizzontale a **4 sopra l'occhiello n.2** (risulta 7.12
   sopra il torace), dal bordo-piega al giro (~sulla pitch line; 22.48).
8. **Pintuck**: 2 linee parallele al c.f. a 1 e 2 dalla linea di impuntura del
   cannoncino (3.5 e 4.5 dal c.f.), dal carré all'orlo, 3 trattini; il pezzo
   `davanti` riceve **slash&spread +2 cm** tra le due linee (D18).
9. **Taschino petto**: patta appoggiata sul carré a 1 dalla pintuck, larga
   **13**, lati **4**, punta a **6** dal carré, bottone ⊕ sull'asse (~4.2 dal
   carré). Apertura **12×1** a 1 sotto il carré, centrata (0.5 per lato).
   Asse verticale dal punto medio fino all'orlo. Sacchetto (impuntura):
   pentagono largo 12, fianchi **12** sotto l'apertura, punta **14**.
10. **Cuciture pannello davanti**: attacco **±4.5 dal punto medio SULLA linea
    apertura**; all'orlo **±2.5 dall'asse**; due rette ~40.0, **prolungate
    collinearmente di 1 fino al carré** per separare i pezzi (D19). Apertura
    (12) e patta (13) scavalcano le cuciture: i marks si **clippano per
    pannello** (intersezione shapely col contorno) (D20).
11. **Tasca laterale**: taglio obliquo **16** con listino **1.5** verso il
    c.f.; estremo basso su pitch line a **3.5 dall'orlo**, estremo alto a
    **1.5 prima della pitch line**; tasca a filetto obliqua: listino 16×1.5 +
    sacchetto derivato (D23).
12. **Cinturino**: 4.5 × (orlo davanti dal bordo-piega 29.29 + orlo dietro
    28.96) = **58.25**, in piega sul c.b.; c.f. a 2 dall'estremità; occhiello
    a 1 prima del c.f., bottone sul c.f.; tacche: fianco a 27.29 dal c.f.,
    pannello dietro a +12.48.
13. **Linguetta**: 8×3.5 centrata sul cinturino dalla tacca fianco verso il
    c.b.; 2 bottoni ⊕ sul cinturino a 6.5 e 9.5 dalla tacca (interasse 3);
    sulla linguetta **asola verticale 2.5 a 1.5 dall'estremità libera** (D24).
14. Grainline: davanti lungo il bordo-piega, dietro lungo il c.b.

## Colletto convertibile (p. 14, passo 2)

Frame locale: x=0 al c.f., +x verso c.b. (in piega), y=0 baseline, +y in alto.
1. Baseline L = ½ scollo abbassato **misurato sul corpo generato** (26.01 alla 50).
2. Al c.b.: cucitura collo +1.5, linea di rollo +4.5, bordo esterno +9.5.
   Al c.f.: cucitura collo +1.
3. Cucitura collo: da (0,1) tocca la baseline (tangente orizzontale) a
   **x=L/3**, risale a (L,1.5) orizzontale al c.b.
4. Linea di rollo (interna): da (0,1) a (L,4.5), orizzontale al c.b.
5. Punta: **7.5 dalla baseline** al c.f., prolungata 2.5 oltre → (−2.5,7.5);
   bordo esterno convesso punta→(L,9.5); bordo davanti retta punta→(0,1).
6. Verifica: cucitura collo = scollo abbassato ±2.5 mm (warning + correzione
   parallela al c.b. nel report). Pezzo unico con rollo marcato, ×2 in piega
   (sopra+sotto), nessuna riduzione del sottocolletto (D10).

## Design 4041 — manica (p. 15, passo 3)

1. **Orlo −4.5** (polsino) parallelo all'orlo, misurato lungo le cuciture, su
   entrambi i pezzi.
2. **Spacco 9** sulla cucitura dietro dal nuovo orlo, marcato su entrambi.
3. Cucitura davanti **"blend"**: curva liscia al posto della spezzata col
   gomito (estremi invariati, scostamento max ~±0.4).
4. **Agio testa → 0**: misurare cap seam vs Ac del corpo 4041 generato e
   annullare la differenza con slash&pivot (sopramanica: taglio Sp→angolo
   orlo-dietro; sottomanica: dal pivot all'angolo davanti della testa; perno
   all'orlo), loop iterativo con clamp ±25 mm, max 10 iterazioni, warning se
   residuo > 1 mm (D17).
5. **Polsino**: 4.5 × lunghezza orlo manica **misurata sui pezzi accorciati**
   (≈31.0 alla 50; il 31.4 disegnato è slop); asola orizzontale 2 all'estremità
   lato spacco (dietro), bottone all'estremità davanti, entrambi a 1.5 dagli
   estremi, centrati in altezza (D24). Tagliato doppio in piega sul lato lungo.
6. Drittofilo ⊥ alla linea gomito su entrambi i pezzi.

## Decisioni

Tutte le open questions degli analisti, risolte:

- **D1 — Nw = 8.0** (`NW_ADD_MM=30`): la formula (1/10 di ½Cg + 3 = 8.0) e il
  disegno (scollo a x=7.99, quote "Nw 8"/"Nw+2 10") concordano; il chart
  stampa 8.5 → refuso. Precedente: negli emendamenti jeans il disegno vince
  sul testo quando c'è doppia conferma grafica.
- **D2 — Pendenza spalla dietro 2.2** fissa (`SHOULDER_SLOPE_BACK_MM=22`):
  valore disegnato dentro il range 2–2.5; nessun parametro esposto.
- **D3 — Spalla davanti finita = dietro finita − 0.5** (`FRONT_SHOULDER_SUB_MM=5`):
  regola equivalente al "./. 0.5–1" del libro ma robusta (la relocation è una
  traslazione rigida ⇒ conserva le lunghezze); verificata esatta sul disegno
  (15.68 vs 15.18).
- **D4 — Lg: deviazione −3.125 cm** (`LG_SHORTEN_MM=31.25`): unico valore nel
  range 2–4 che dà 64.0 esatto per Bh 179 (89.5 − 22.375 − 3.125); Lg resta
  derivata, non editabile.
- **D5 — HSP_b** = intersezione del prolungamento tangente dello scollo con la
  retta spalla relocata (formalizza il "+1" del libro + l'effetto relocation;
  riproduce il punto disegnato (9.12,−3.67)).
- **D6 — Curve**: nell'app costruzioni **parametriche** (`curve_through`/
  `cubic_with_tangents`/`smooth_polyline`) vincolate dalle tangenze note +
  costanti di forma calibrate col fit contro le polilinee estratte (stesso
  approccio di `draft_ms.py`); le polilinee del PDF vivono SOLO nel JSON di
  riferimento come oracolo, mai nel codice dell'app (le forme devono scalare
  con le misure).
- **D7 — Frame corpo condiviso** con x verso il davanti e gap 60 mm (sez.
  "Sistemi di coordinate"); manica in frame proprio su A; nessuno specchio al
  rendering.
- **D8 — Rientro vita t** = conseguenza geometrica del fianco ⊥ all'orlo
  inclinato (t = (y_H − Bwl)·tan(atan(2.5/Lg)) ≈ 0.70), non costante.
- **D9 — Cn** = intersezione retta-metà-punti con y = Sd − Ad (il −2.61
  disegnato vs −2.50 teorico è imprecisione di stampa).
- **D10 — Colletto**: pezzo unico convertibile con linea di rollo marcata,
  ×2 in piega sul c.b., senza riduzione sottocolletto (il bullet "with collar
  stand" appartiene al 4042, non al 4041).
- **D11 — Convivenza col frame jeans**: nessun conflitto — ogni draft ha il
  suo frame, l'export è frame-agnostico (`bbox` + layout side-by-side).
- **D12 — Ah/Sch**: l'app misura Ah sul blocco generato e usa
  `½Ah_eff = Ah/2 + AH_HALF_CAL_MM (2.0)`; compensa l'incoerenza interna del
  chart (44.2 totale vs 22.3 metà) e riproduce Sch 16.05≈16.1 = testa
  disegnata. Documentato come emendamento.
- **D13 — Sh = 31.0** dal chart (`SLEEVE_HEM_MM=310`), costante di stile in
  `draft_jacket.py`, NON campo del form (il task chiede solo 3 campi nuovi) e
  NON scalata con la taglia; l'etichetta "½ sleeve hem 15" del disegno è
  incoerente col chart → il chart vince (misura dichiarata, non slop grafico).
  Overlay: eccezione documentata ~4.6 mm su B_hem.
- **D14 — Piega dietro al gomito = fold davanti + ½Sh + 3.5**
  (`BACK_FOLD_ADD_MM=35`, non 45 del testo): riproduce esattamente il
  disegnato x=21.0 con Sh=31; il "+4.5" stampato non torna con nessuna
  combinazione pulita. Precedente jeans (emendamento 3: disegno > quota
  stampata). Emendamento documentato.
- **D15 — Orlo blocco sopramanica** = retta (−3,62.5)→B_hem come disegnato
  (la squadratura ±3 + raccordo del testo è irrilevante: l'orlo viene tagliato
  a −4.5 per il polsino e il blocco non è un pezzo esportato).
- **D16 — Merge cucitura dietro sottomanica**: blend tangente che raggiunge la
  piega dietro a **9.0 cm sotto il gomito** (`BACK_MERGE_BELOW_ELBOW_MM=90`,
  calibrata dal disegno 8.96; nessuna regola stampata).
- **D17 — Agio testa**: il blocco riporta l'agio misurato (disegnato +2.8%,
  target dichiarato 4–6%: solo report, nessun warning bloccante perché il
  disegno stesso è sotto target); il 4041 **normalizza sempre a ~0** con lo
  slash&pivot iterativo (clamp ±25 mm + warning), fedele al libro ("without
  any ease for the denim construction").
- **D18 — Pintuck**: slash&spread **+2 cm** tra le due linee tuck sul pezzo
  `davanti` (piega cucita da 1 cm ⇒ 2 cm di stoffa); il testo non lo dice
  esplicitamente → emendamento.
- **D19 — Cuciture pannello davanti** prolungate collinearmente di 1 cm dalla
  linea apertura fino al carré per chiudere i 3 pannelli.
- **D20 — Marks a cavallo delle cuciture** (apertura 12, patta 13, sacchetto):
  ogni pannello riceve la porzione di mark che ricade nel proprio contorno
  (clipping shapely); il pannello petto porta i marks completi di piazzamento.
- **D21 — Bottoni davanti sul c.f.**: l'estremità tonda dell'occhiello sta 1 cm
  prima del c.f. verso il bordo (misurato 0.79–0.88); il bottone al c.f. è la
  lettura meccanicamente coerente del "relocated accordingly" (il gambo si
  assesta nell'estremità tonda tenendo i c.f. allineati). Solo marks.
- **D22 — Occhielli lunghezza 2.5** (disegnati ~2.4), bottoni ø20 come mark ⊕.
- **D23 — Tasca laterale** = filetto obliquo: listino 16×1.5 (dal disegno) +
  **sacchetto derivato** rettangolo arrotondato ~17×16 appeso all'apertura
  (non nel PDF → emendamento, asterisco nel README come i pezzi derivati jeans).
  Sacchetto taschino petto = pentagono di impuntura esteso 1 cm sopra
  l'apertura (fino al carré) — derivato, stesso trattamento.
- **D24 — Polsino e linguetta**: polsino asola lato spacco / bottone lato
  davanti (il libro non lo lega: emendamento); linguetta rettangolare 8×3.5,
  ×4 (doppiata), asola verticale 2.5 a 1.5 dall'estremità libera.
- **D25 — Validazione misure**: positività + `Sl < Bh` + `Lg > Ad`; niente
  range bloccanti.
- **D26 — UI**: campi non pertinenti **nascosti** (`QFormLayout.setRowVisible`,
  PySide6≥6.7 ok), non disabilitati; etichette dei campi condivisi invariate
  ("Waistband W (giro vita)" vale anche per Wg — zero rischio sui test);
  titolo finestra e nome eseguibile PyInstaller invariati (eventuale rinomina
  = commit separato fuori piano); `reset_to_defaults` estende il dict con i
  default giacca (obbligatorio: il loop itera tutti gli spinbox) e non cambia
  il modello selezionato.
- **D27 — Bordi orlo giacca**: nessun bordo `hem` (orlo corpo cucito al
  cinturino, fondo manica al polsino ⇒ margine `seam_mm`); bordi in piega
  nominati `fold_*` ⇒ margine 0 via l'estensione di `for_edges`.

## Pezzi prodotti (Design 4041) — `EXPECTED_JACKET_PIECES` (17)

| nome                     | qty | taglio                       | linee interne / marks |
|--------------------------|-----|------------------------------|------------------------|
| `carre_davanti`          | 2   | specchiato                   | c.f., piega bordo, impuntura cannoncino, occhiello 1, grainline ∥ bordo |
| `davanti`                | 2   | specchiato (bordo `fold_edge`) | c.f., piega bordo, impuntura cannoncino, occhielli 2–4 + bottoni ⊕, pintuck (2 linee +2 cm spread, 3 trattini), grainline ∥ bordo |
| `pannello_petto`         | 2   | specchiato                   | apertura 12 + listino 12×1, pentagono sacchetto, asse ½, piazzamento patta+bottone, grainline ∥ asse |
| `fianchetto_davanti`     | 2   | specchiato                   | apertura tasca laterale 16×1.5, tacca FAN sul giro, grainline |
| `carre_dietro`           | 1   | in piega sul c.b. (`fold_cb`) | scollo nuovo, grainline sul c.b. |
| `dietro`                 | 1   | in piega sul c.b. (`fold_cb`) | grainline sul c.b. |
| `fianchetto_dietro`      | 2   | specchiato                   | tacca BAN sul giro, grainline ∥ c.b. |
| `sopramanica`            | 2   | specchiato                   | tacche FAN/Sp, spacco 9, drittofilo ⊥ gomito |
| `sottomanica`            | 2   | specchiato                   | spacco 9, drittofilo ⊥ gomito |
| `polsino`                | 2   | doppio in piega (lato lungo `fold_edge`) | bottone ⊕ + asola, quota "seam length from sleeve" |
| `colletto`               | 2   | in piega sul c.b. (`fold_cb`) | linea di rollo, tacca 1/3, grainline ∥ c.b. |
| `cinturino`              | 2   | in piega sul c.b. (`fold_cb`) | c.f., occhiello + bottone ⊕, tacche fianco/pannello, piazzamento linguetta + 2 bottoni ⊕ |
| `patta_taschino`         | 4   | specchiato (2 per tasca)     | bottone ⊕ sull'asse, grainline |
| `sacchetto_taschino` *   | 4   | specchiato (2 per tasca)     | — (derivato) |
| `listino_tasca_laterale` | 2   | specchiato                   | — |
| `sacchetto_tasca_laterale` * | 4 | specchiato (2 per tasca)   | — (derivato) |
| `linguetta`              | 4   | specchiato (2 per lato)      | asola verticale 2.5 |

\* pezzi derivati non tracciati nel libro (come patta zip/porta-monete jeans).

## Mappa landmark taglia 50 (ground truth attesa, cm nei frame giacca)

**Dietro** (frame corpo): N(0,0) · A2(7.99,−2.01) · E(8.60,−2.80) ·
HSP_b(9.12,−3.67) · S1(22.18,2.20) · SP0(23.61,2.62) · SP_b(23.88,1.62) ·
G1(23.18,18.74) · min-giro(22.68,12.25) · U_b(31.43,24.99) ·
W_b(30.73,44.79) · H_b(31.43,62.86) · K(2.49,63.99).

**Davanti**: P_top(43.68,−2.51) · Cn(53.80,−2.50) · S2(43.68,2.0*) ·
SP0_f(39.84,3.57) · HSP_f(54.12,−1.66) · SP_f(40.24,4.49) · FAN(43.68,21.09)
· ¼Sd(43.68,18.74) · U_f(37.43,24.99) · W_f(38.14,44.79) · H_f(37.43,62.86)
· C0(63.89,5.28) · C1(64.49,24.99) · C2(64.88,44.79) · C3(64.88,63.38).
(*teorico; disegnato 1.89 per lo slop di Cn.)

**Manica** (frame su A): E(20.28,0) · Sp(11.14,0) · M1(5.57,0) · M2(2.78,6.60)
· FAN(0,13.20) · Q(20.28,3.90) · T(8.64,16.10) · U2(18.87,5.39) ·
U22(21.91,5.39) · FST(−2.75,16.36) · UST(3.23,15.88) · fold-gomito(2,37.8) ·
F_b(21.0,37.8) · fold-orlo(0,62.5) · B_hem formula (15.21,65.5) [disegnato
(14.75,65.5): eccezione D13] · merge dietro (19.02,46.76) · pance dietro
(22.43,19.1)/(20.85,30.0).

**Design corpo** (frame dietro): collo nuovo c.b.(0.02,0.51) · carré
(0.53,13.51)→(22.69,12.64) · pannello (19.20,12.76)→(18.79,58.89) · orlo c.b.
(2.33,59.52) · BAN(23.20,18.75). (Frame davanti p.14, x=0 pitch/y=0 torace):
collo c.f. nuovo (20.26,−18.22) · bordo (22.25,−18.24)/(23.22,33.85) · carré
y=−7.12 · occhielli x≈21.1–22.1, y −16.23/−3.07/9.94/22.99/36.17 · patta
(1.95…14.97,−7.12) punta (8.46,−1.13) · apertura y=−6.13 x 2.46…14.46 ·
sacchetto fianchi y=5.87 punta (8.46,7.86) · cuciture pannello
(12.95,−6.13)→(10.96,33.87) e (3.96,−6.13)→(5.97,33.79) · tasca laterale
(0,30.11)→(1.50,14.17).

**Colletto**: base 26.01 · punta (−2.50,7.51) · tocco baseline x=8.59 (≈L/3) ·
c.b. 1.5/4.51/9.50 · c.f. 0.99. **Cinturino**: 58.25×4.51 · c.f. x=1.99 ·
tacche 29.28/41.76 · linguetta x 29.28–37.28 · bottoni x 35.79/38.79 (y 2.25).

**Lunghezze derivate** (test/report): spalle 15.68/15.18 (Δ0.50) · scolli
10.50/13.09 · giri 28.48/24.82 (Ac 53.30) · back/front ah 23.37/20.79
(Ah 44.16) · fianco vita→orlo 18.08 (=dietro=davanti), c.f. 18.59 · torace
57.52 · orlo 56.42 · testa manica 35.17+19.73=54.90 (ease +1.50) · cuciture
dietro manica 60.92/60.83 · scollo abbassato 11.40+14.61=26.01 · carré 22.18/
22.48 · pannello dietro 46.13 · orlo dietro 12.48+16.48=28.96 · cinturino
58.25 · spalle 4041 14.66/14.18.

Le polilinee complete delle curve (già estratte, i PDF le disegnano come
polilinee) vanno nel JSON di riferimento.

## Architettura

**File nuovi:**
- `src/jeans_pattern/measurements_jacket.py` — `JacketMeasurements`
  (`from_cm`/`from_inches`, derivate, costanti `NW_ADD_MM=30`,
  `LG_SHORTEN_MM=31.25`, `BW_ADD_MM=12`, `BW_ADD_LARGE_MM=112`, `SW_ADD_MM=30`,
  `CW_ADD_MM=8`, `AW_SUB_MM=13`, `SD_ADD_MM=125`, `AD_ADD_MM=25`).
- `src/jeans_pattern/draft_jacket.py` — blocco pp. 11–13:
  `draft_jacket_back(m) -> JacketBackDraft`,
  `draft_jacket_front(m, back) -> JacketFrontDraft`,
  `draft_jacket_sleeve(m, back, front) -> SleeveDraft`.
  Dataclass frozen con `landmarks`, `edges` (catene nominate chiuse),
  `construction_lines`, `report`, `outline()`/`edge(name)` come `FrontDraft`.
  Costanti di forma in testa (v. Decisioni + `BODY_GAP_MM=60`,
  `SLEEVE_HEM_MM=310`, `AH_HALF_CAL_MM=2`, `BACK_FOLD_ADD_MM=35`,
  `BACK_MERGE_BELOW_ELBOW_MM=90`, `FRONT_TAPER_ELBOW_MM=20`,
  `FRONT_SEAM_OFFSET_MM=30`, alpha/beta curve dal fit).
- `src/jeans_pattern/draft_jacket_design.py` — Design 4041:
  `design_body(m, back, front) -> DesignBody` (geometria comune),
  `build_back_yoke/back_centre/back_side_panel(db)`,
  `build_front_yoke/front_centre/front_chest_panel/front_side_panel(db)`,
  `build_collar(db)`, `build_jacket_waistband(db)`,
  `build_chest_pocket_flap/chest_pocket_bag(db)`,
  `build_side_pocket_welt/side_pocket_bag(db)`, `build_tab(db)`,
  `split_sleeve(m, sleeve) -> tuple[PieceDraft, PieceDraft]`,
  `build_cuff(top, under) -> PieceDraft`, `front_jacket_marks(db)`.
  Importa `PieceDraft` da `draft_ms_extras` (model-agnostico, zero modifiche
  al file jeans; coupling accettato, refactor in modulo neutro rimandato).
- `scripts/extract_jacket_reference.py` →
  `tests/data/ms_jacket_reference_size50.json` (committato). Importa gli
  helper puri di `extract_ms_reference.py` via `sys.path` (chains, merge,
  Similarity, …) senza modificarlo; `dedupe_shifted` locale parametrizzato
  (p. 14: shift 548.70 pt; p. 11/12/15 senza duplicati). Default PDF:
  `docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf`.
- `scripts/verify_jacket_overlay.py` → `verification_jacket_size50.pdf`
  (rosso=libro, blu=generato; `LANDMARK_TOL_MM=2.5`, `CURVE_TOL_MM=3.0`,
  eccezioni documentate D13; exit code gate).
- Test: `tests/test_measurements_jacket.py`, `test_draft_jacket.py`,
  `test_draft_jacket_sleeve.py`, `test_draft_jacket_design.py`,
  `test_pattern_jacket.py`.

**File modificati (solo aggiunte):**
- `src/jeans_pattern/pattern.py` — (a) `SeamAllowances.for_edges`:
  `hem→hem_mm`, **`fold*`→0.0**, altrimenti `seam_mm` (inerte per i jeans,
  test dedicato); (b) import moduli giacca; (c) in coda
  `build_jacket_pattern(m: JacketMeasurements, sa: SeamAllowances | None) ->
  Pattern` che assembla i 17 pezzi con `_make_piece` riusato e produce il
  report con chiave `"model": "jacket"`, `chest_ease_mm`, `hip_ease_mm` +
  warning "Check Hg" (< ½Hg+5), `armhole_circ_mm`, `sleeve_cap_height_mm`,
  `sleeve_cap_ease_mm` (~0, warning se |·|>10 o clamp), lunghezze accoppiate
  (colletto/scollo, polsino/fondo manica, cinturino/orlo, fianchi, pannelli,
  carré) con warning oltre 2.5 mm, `scye_depth_mm`, `length_mm`, `warnings`.
  `build_full_pattern` INVARIATA.
- `src/jeans_app/measurement_form.py` — tendina modello in cima
  (`MODEL_JEANS`/`MODEL_JACKET`, default jeans), segnale
  `model_changed = Signal(str)` (emette anche `measurements_changed`),
  `JACKET_FIELDS` (`body_height` "Body height Bh (statura)", `chest_girth`
  "Chest girth Cg (giro petto)", `sleeve_length` "Sleeve length Sl (lunghezza
  manica)"), `JACKET_DEFAULTS_CM = {179.0, 100.0, 64.0}`, `JEANS_ONLY_KEYS`/
  `JACKET_ONLY_KEYS`, righe registrate e mostrate/nascoste con
  `setRowVisible`; API `model()`, `set_model(name)`,
  `to_jacket_measurements() -> JacketMeasurements`; `reset_to_defaults` con
  dict esteso `{**DEFAULTS_CM, **JACKET_DEFAULTS_CM, **SA_DEFAULTS_CM}`.
  `FIELDS`/`DEFAULTS_CM`/`to_measurements` jeans INTOCCATI.
- `src/jeans_app/main_window.py` — `_build_pattern` dispatcha sul modello;
  `_show_report` branch su `r.get("model") == "jacket"` con testo tipo
  `"Prof. giro Sd: … · Lunghezza Lg: …\nAgio petto: … · Check fianchi Hg: …\n
  Giro manica Ac: … · Agio testa: …"` + warnings; ramo jeans byte-identico.
  Nome file export `jacket_pattern.pdf/.svg` col modello giacca.
- `tests/conftest.py` — fixture `jacket_reference` (session) e `size50_jacket`.
- `tests/test_measurement_form.py`, `tests/test_main_window.py` — estensioni
  in place, nessun test esistente modificato.
- `README.md` — sezione Classic Denim Jacket (chart, tendina, pezzi,
  emendamenti/derivati con asterisco).

**File non toccati (confermato dalla lettura):** `measurements.py`,
`constants.py`, `geometry.py` (primitive sufficienti), `draft_ms.py`,
`draft_ms_extras.py`, `export_svg.py`/`export_pdf.py` (già generici:
iterano `Pattern` via `bbox` con layout side-by-side), `preview_widget.py`,
`main.py`, `extract_ms_reference.py`, `verify_ms_overlay.py`,
`pyproject.toml`, `packaging/*.spec` (PyInstaller segue gli import).

## Fasi (commit per fase, su master; suite jeans verde a ogni fase)

0. **Riferimento vettoriale giacca**: `extract_jacket_reference.py` + JSON
   committato (pp. 11, 12, 14, 15; frame giacca; dedupe p. 14). ∥ con Fase 1.
1. **Misure**: `measurements_jacket.py` + `test_measurements_jacket.py`
   (derivate vs chart, switch Bw a Cg>100, regola Aw=Cw, from_inches,
   validazioni). ∥ con Fase 0.
2. **Blocco corpo**: `draft_jacket_back`/`draft_jacket_front` + test landmark
   (tol 1.5 mm, per-landmark 2.5 dove il disegno è impreciso), curve
   (tol 2.0–2.5), invarianti su dict `SIZES` multi-taglia. Dipende da 0+1.
   È la fase di calibrazione più lunga.
3. **Blocco manica**: `draft_jacket_sleeve` + test (landmark/curve testa;
   Ah/Ac/Sch/Scw vs chart p. 13 tol ~2 mm; agio testa nel report). Dipende da 2.
4. **Design 4041**: `draft_jacket_design.py` + test (pezzi chiusi e semplici;
   colletto=scollo ±2.5; polsino=fondo manica; cinturino=orlo+sormonto;
   carré 13/3.5; agio testa ~0 dopo split; quote taschino/patta/tasca
   laterale/linguetta vs p. 14–15). Dipende da 2+3.
5. **Assemblaggio**: `pattern.py` (`for_edges` fold + `build_jacket_pattern` +
   report) + `test_pattern_jacket.py` (17 pezzi, cut⊇net, `fold*` a offset 0,
   allowances disabled, report, altre taglie) + test di regressione esplicito
   "nessun edge jeans inizia per fold / mapping jeans invariato". Dipende da 4.
6. **UI**: 6a form (tendina, campi, visibilità, reset, `to_jacket_measurements`;
   dipende solo da Fase 1, ∥ con 2–5) · 6b main_window (dispatch, report label,
   filename; dipende da 5) + estensioni test UI (default "Basic Jeans",
   `isHidden()` sulle righe, 17 pezzi col modello giacca, label giacca, ramo
   jeans intatto).
7. **Verifica end-to-end**: `verify_jacket_overlay.py` (corpo+manica possibile
   già dopo la Fase 3; design dopo la 4), README, export manuale PDF
   singolo/tiled + SVG, quadrato calibrazione, GUI.

## Calibrazione curve e tolleranze

- Le curve "as shown" (scolli, giromanica, testa manica, raccordo orlo
  davanti, cucitura collo/bordo colletto) si costruiscono con i vincoli duri
  del libro (tangenti orizzontali in N/C0/ascelle/Sp; giro davanti tangente
  al pitch in ¼Sd; tratto rettilineo FAN→M2; incavo dietro ~0.5 oltre Bw;
  specchio del sottomanica oltre la cucitura davanti; tangenza bicipite) +
  poche costanti di forma (frecce/pesi bezier) **fittate** contro le polilinee
  del JSON di riferimento, come in `draft_ms.py`.
- Tolleranze test: **landmark 1.5 mm** (default), **2.5 mm** per-landmark dove
  il disegno ha slop noto (Cn, S2, punta scollo dietro, pance manica);
  **curve 2.0–3.0 mm** (max deviazione punto-curva). Eccezioni documentate
  (confronto vs regola, non vs disegno): B_hem manica (~4.6 mm, D13),
  larghezza polsino (31.0 vs 31.4 disegnato), F_b se Sh cambia.
- Anti-overfitting: invarianti parametriche su più taglie (fianchi
  davanti=dietro, orlo ⊥ c.b., agio petto = costante di formula, spalle
  Δ=0.5, Aw=Cw sotto soglia, poligoni semplici, catene chiuse, colletto =
  scollo, cinturino = orlo, cap ease ~0 nel 4041), come `test_front_invariants`.

## Strategia test + regressione jeans

Nuovi test per fase (v. sopra). Punti fragili jeans presidiati:
1. `test_main_window_default_pattern_builds` (11 pezzi) → default tendina
   resta "Basic Jeans", `build_full_pattern` intoccata.
2. `test_main_window_report_label` → ramo jeans di `_show_report` identico
   carattere per carattere ("Cavallo Br: 20.0 cm").
3. `test_form_reset_*` → dict defaults esteso obbligatoriamente (il loop di
   reset itera TUTTI gli spinbox: senza estensione va in KeyError).
4. `test_form_defaults_are_size_50` / `test_form_collects_measurements_in_cm`
   → `to_measurements` continua a leggere solo `FIELDS` jeans.
5. `test_form_unit_toggle_converts_values` → la conversione tocca anche i
   campi giacca (voluto, trasparente per il test).
6. `test_pattern.py` → protetto da `build_full_pattern` intoccata + test
   esplicito sull'inerzia di `for_edges` per i jeans.
7. `test_preview_widget`/`test_export_*` → moduli non modificati.

Gate: `pytest` completo (128 esistenti + nuovi) verde a fine di ogni fase;
Fase 7 chiude con l'overlay giacca sotto soglia e l'overlay jeans invariato.

## Fuori scope

Design 4042 Trucker Jacket (pp. 16–18); gradazione automatica; riduzione
sottocolletto/sormonti sartoriali; istruzioni di cucito; rinomina di titolo
finestra ed eseguibile; esposizione di Sh nel form.

## Emendamenti dalla calibrazione

**Fase 2 — blocco corpo (2026-08-19).** Il fit contro le polilinee del JSON di
riferimento ha confermato tutte le quote del piano tranne la meccanica della
*seam relocation*, riformulata qui sotto. Accordo raggiunto: landmark dietro
≤ 0.56 mm, davanti ≤ 1.64 mm (Cn/S2/C0/HSP_f/SP0_f/SP_f ereditano l'~1.1 mm con
cui il disegno stampa la linea di profondità giro), curve ≤ 1.62 mm.

- **E2.1 — D5 rivisto: HSP_b sta SULLA curva dello scollo, non su una
  tangente.** L'intersezione del prolungamento tangente con la retta spalla
  relocata cade in (8.67,−2.90), 0.9 cm dal punto disegnato (9.12,−3.67); i
  vettori mostrano invece che lo scollo dietro è **un unico tratto di curva**
  di cui A2 è solo un punto di costruzione: E sta a 1 cm di arco oltre A2
  ("lengthen the neckline 1 cm") e HSP_b a 1 cm ancora oltre. La relocation è
  quindi simmetrica ai due capi: **+1 cm lungo lo scollo** al collo e **+1 cm
  ⊥ alla retta spalla** alla spalla (SP_b = SP0 + 1·n). Implementazione: un
  cubico N→A2 (tangente ⊥ al c.b. in N, −46.5° in A2) campionato **oltre
  t = 1**, che è ciò che fa il curvilineo del libro. Errore residuo su E 0.24 mm,
  su HSP_b 0.29 mm, sulla spalla finita 0.58 mm.
- **E2.2 — D3 rivisto: la regola “−0.5 cm” vale sulle spalle FINITE.** Le due
  traslazioni da 1 cm (davanti: lungo lo scollo al collo, ⊥ alla guida alla
  spalla) non sono parallele, quindi la relocation **non** conserva la
  lunghezza: sul disegno la guida grezza davanti è 15.27 contro 16.29 dietro
  (−1.02) mentre le spalle finite sono 15.18 contro 15.68 (−0.50). SP_f si
  determina perciò come intersezione retta/cerchio: punto della guida
  *relocata* a distanza (spalla dietro finita − 0.5) da HSP_f. Δ spalle esatto
  a 5.0 mm su tutte le taglie.
- **E2.3 — HSP_f = 1 cm di arco lungo lo scollo davanti da Cn** (misurato
  10.01 mm sul disegno), non `Cn + n` con n perpendicolare alla spalla come
  scritto al passo 14; SP_f = SP0_f + 1 cm ⊥ alla guida spalla resta valido.
- **E2.4 — Convenzione degli agi: entrambi i controlli del libro si leggono
  sul mezzo modello.** `chest_ease_mm` = torace totale − ½Cg (= 7.5 cm alla 50,
  l'aritmetica del chart) e `hip_ease_mm` = orlo totale − ½Hg, con warning
  "Check Hg" sotto 5 cm. Da riusare identica in `build_jacket_pattern` (fase 5).
- **E2.5 — Valori generati per la fase 3** (taglia 50, dal blocco parametrico):
  back ah 23.33, front ah 20.65, **Ah 43.99** (chart 44.2, disegnato 44.16);
  giri 28.43 + 24.68 = **Ac 53.12** (chart 53.4, disegnato 53.30). La
  calibrazione di `AH_HALF_CAL_MM` (D12) va rifatta su questi numeri, non su
  quelli del disegno.

Costanti di forma vincenti (in testa a `draft_jacket.py`): scollo dietro
−46.5°/0.35 (0.3 mm), giro dietro ⊥spalla → −11.4° con 0.194/0.260 e
0.534/0.161 (0.4 mm), scollo davanti +6.7° con 0.572/0.331 (0.2 mm), giro
davanti ⊥spalla → verticale con 0.128/0.361 e 0.612/0.264 (0.7 mm), orlo
davanti 0.474 (0.1 mm).

**Fase 3 — blocco manica (2026-08-19).** Tutte le quote dei passi 1–11 del
piano sono state confermate sui vettori tranne il punto 8 (v. E3.2). Accordo:
landmark ≤ 1.07 mm (unica eccezione B_hem, D13), curve ≤ 1.07 mm salvo i bordi
ancorati a B_hem. Lunghezza cucitura testa 549.01 mm — identica al disegno.

- **E3.1 — D12 ricalibrata + nuova costante per Scw.** Ah e Ac misurate sul
  blocco parametrico escono ~0.5 % sotto i numeri del libro (Ah 439.9 contro
  442 del chart e 441.6 disegnati; Ac 531.2 contro 534 e 533.0). Con
  `AH_HALF_CAL_MM = 2.0` Sch sarebbe 159.7 invece di 161.0 e tutta la manica
  scivolerebbe di 1.3 mm. Costanti vincenti: **`AH_HALF_CAL_MM = 3.4`**
  (Sch = 160.999, disegnato 161.0) e la nuova **`SCW_CAL_MM = 1.4`**
  (Scw = 241.98, chart 242.0; senza di essa E cadrebbe 1.9 mm dentro). Le due
  costanti assorbono insieme lo scarto blocco/libro e l'incoerenza interna del
  chart (Ah 44.2 ma ½Ah 22.3).
- **E3.2 — il passo 8 del piano è sbagliato: la testa davanti NON è la copia
  specchiata del sottomanica.** Il riflesso del giro sottomanica rispetto alla
  piega manda UST esattamente in FST (conferma che FST e UST sono i ±3 ⊥ alla
  piega), ma prosegue **a sinistra** di FST, fuori dal pezzo: è il controllo di
  cucitura che il testo chiede ("check the seam transitions"), non la linea
  disegnata. Il tratto FST→FAN del disegno sale invece verso FAN ed è
  implementato come cubico con tangente d'uscita a **−24.0° dalla ⊥ alla
  cucitura davanti** e tangente d'arrivo lungo la guida G1 (fit 0.21 mm).
- **E3.3 — U22** sta a 2.2 cm **in linea d'aria** da Q sull'orizzontale di U2
  (intersezione cerchio/orizzontale), non a 2.2 cm di ascissa: riproduce il
  punto disegnato a 0.63 mm. Il tratto Q→U22 della testa è rettilineo (la
  freccia del disegno vale 0.15 mm) e risulta ⊥ alla guida Q→T.
- **E3.4 — cuciture dietro**: entrambe escono da U22/U2 **squadrate in giù**
  (l'angolo libero fittato vale 0.09° e 0.08°, quindi fissato a 0) e arrivano
  **tangenti alla piega dietro**. `merge_back` = punto della piega a 9.0 cm
  **verticali** sotto il gomito (1.07 mm dal disegnato); alfa/beta 0.100/0.400
  sopra (fit 0.63 mm, pancia 22.48 contro 22.43) e 0.080/0.480 sotto (fit
  1.07 mm, pancia 20.87 contro 20.85).
- **E3.5 — angoli al gomito delle cuciture davanti** = mitre delle due
  parallele a ±3 cm della piega rastremata (residuo 0.03 mm): conferma il
  passo 7 del piano, che quindi non richiede costanti.
- **E3.6 — conseguenza di D13**: B_hem calcolato con Sh 31.0 cade a 4.60 mm dal
  disegnato, e i bordi `back_fold` e `hem` (dritti, ancorati a B_hem) ereditano
  lo scostamento. Tolleranza di test dedicata 5.0 mm, il resto a 2.0 mm.
  Nota: il JSON di riferimento non ha un `back_fold` per il sottomanica (il
  tratto merge_back→B_hem coincide col fold del sopramanica e non è stato
  estratto separatamente) — testato con l'invariante di collinearità.
- **E3.7 — valori generati alla 50** (per le fasi 4–5): Sch 161.00 · Scw 241.98
  · testa 549.01 (disegnata 549.01) · **agio testa +17.85 mm = 3.36 %**
  (disegnato +2.8…3.0 %, il libro dichiara 4–6 %: solo report, D17) · cuciture
  dietro 608.81/608.02 (disegnate 609.19/608.35) · orlo totale 310.23 ≈ Sh.
  Su altre taglie l'agio va da 2.2 % (44) a 5.2 % (62) e il Δ fra le due
  cuciture dietro cresce 0.06/0.79/1.76/2.90 mm (44/50/56/62) perché Sh resta
  fisso per D13: l'invariante multi-taglia usa quindi 3.0 mm, il test sulla
  taglia 50 resta a 2.0 mm.

Costanti di forma manica: testa davanti −24.0°/0.385/0.412 (0.21 mm), testa
M2→Sp 0.229/0.467 con tangente d'uscita esattamente su G1 (0.44 mm), testa
Sp→Q 0.111/0.604 (0.41 mm), giro sottomanica +14.8° dalla ⊥ alla cucitura
davanti con 0.288/0.632 (0.64 mm), cuciture dietro 0.100/0.400 e 0.080/0.480.

**Fase 4 — Design 4041 (2026-08-19).** Tutte le quote dei passi 1–14 del corpo,
dei 6 punti del colletto e dei 6 della manica sono state confermate sui vettori
di p. 14–15 tranne i punti qui sotto. Accordo alla taglia 50: landmark dietro
≤ 0.55 mm, davanti ≤ 1.10 mm (ereditano lo slop del blocco), bordi del corpo
≤ 1.61 mm, colletto ≤ 0.60 mm, marks (patta/apertura/sacchetto/tasca laterale)
≤ 0.91 mm, cinturino 582.31 contro 582.51 disegnato.

- **E4.1 — firme senza `m`.** `design_body(back, front)` e
  `split_sleeve(sleeve)` non usano le misure: tutto quello che serve è già nei
  draft (l'Ac di riferimento sta in `sleeve.report["armhole_circ_mm"]`).
  Le firme del piano (`design_body(m, back, front)`,
  `split_sleeve(m, sleeve)`) avrebbero un parametro morto.
- **E4.2 — occhielli misurati, D21/D22 corretti.** Il PDF disegna ogni asola
  come una fessura **lunga 2.206 cm** (non 2.5) la cui estremità verso il bordo
  sta **0.54–0.61 cm oltre il c.f.** (non 1 cm prima). La stessa regola vale
  sul cinturino (asola 14.22→36.50 dal bordo, c.f. a 20.0: 0.58 cm oltre il
  c.f.). Costanti: `BUTTONHOLE_LEN_MM = 22.0`, `BUTTONHOLE_PAST_CF_MM = 5.5`.
  I bottoni restano marcati sul c.f. (D21 confermato). Le y degli occhielli —
  la parte che il libro prescrive davvero — cadono entro 0.9 mm dal disegno,
  passo 130.6 contro 131.0.
- **E4.3 — l'annullamento dell'agio testa lo porta il SOLO sopramanica.** Lo
  slash del sottomanica va dal perno all'**angolo** della testa (UST): ruotando
  la cucitura davanti attorno al perno, UST si sposta *fuori* dal pezzo (sopra
  il giro) invece di mangiare testa, e il contorno si autointerseca. Il taglio
  Sp→angolo orlo-dietro del sopramanica invece funziona: il punto di taglio
  scorre lungo la curva della testa, che si accorcia della corda. Il
  sottomanica viene quindi solo accorciato e raccordato. Loop proporzionale
  (max 10 giri, tolleranza 1 mm) con clamp a 2.5 cm come da D17.
  Risultati: 44 agio 10.66→0.25 mm (1.18°), 50 17.85→0.50 mm (1.89°),
  **56 25.03→3.36 mm e 62 31.79→9.61 mm con warning** (l'agio del blocco supera
  il clamp: il libro non prevede il caso, il residuo è dichiarato).
- **E4.4 — colletto: la correzione si riporta, non si applica.** Con la
  baseline = ½ scollo abbassato la cucitura collo esce 1.41–1.69 mm più lunga
  su tutte le taglie (0.6 % della corda), dentro il ±2.5 mm del piano; il
  disegno stesso non applica nessuna correzione (baseline 260.22 = scollo
  disegnato 260.11). `correction_mm` sta nel report e il warning scatta solo
  oltre 2.5 mm.
- **E4.5 — polsino 32.1 cm, non 31.0.** Il fondo manica si allarga accorciando
  di 4.5 cm (la manica è rastremata): blocco 310.2 → design 321.5 alla 50,
  contro i 314.0 disegnati. La differenza di 7.5 mm è esattamente il doppio
  dello scarto D13 sull'angolo B_hem (3.7 + 4.0 mm), che la cimatura porta con
  sé. Il "≈31.0 alla 50" del piano era la misura del BLOCCO, non del pezzo
  accorciato; tolleranza di test dedicata 8.0 mm sul confronto col disegno.
- **E4.6 — p. 15 disegna la manica NON slashata.** Le polilinee della testa nel
  riferimento design coincidono con quelle del blocco: il libro mostra il
  pezzo prima dello slash. Solo i bordi non ruotati (testa e cucitura davanti
  del sottomanica, cuciture dietro, angoli d'orlo) si possono confrontare col
  disegno; il sopramanica ruotato scarta fino a ~16 mm per costruzione.
- **E4.7 — cuciture pannello davanti chiuse sul carré.** Il riferimento le
  ferma sulla linea apertura; il prolungamento di 1 cm (D19) è calcolato come
  intersezione con la linea del carré (non come 1 cm lungo la retta) perché le
  catene dei tre pannelli devono chiudersi esattamente. Differenza fra le due
  letture: 0.01 mm.
- **E4.8 — anche `carre_davanti` ha il bordo `fold_edge`.** La piega del bordo
  davanti corre da collo a orlo, quindi attraversa carré e pannello centrale:
  la tabella dei pezzi la annotava solo su `davanti`.
- **E4.9 — marks clippati con shapely su TUTTI i pannelli davanti** (D20 alla
  lettera). L'apertura da 12 cm si spartisce 15.0 / 90.0 / 15.0 mm fra
  `davanti`, `pannello_petto` e `fianchetto_davanti`; la somma torna a 120.0.
  Il pintuck slash&spread (D18) è applicato dopo il clipping, così i marks del
  pannello centrale traslano con la parte di pezzo che si apre.

Costanti di forma Design 4041 (in testa a `draft_jacket_design.py`): scollo
dietro abbassato 0.300/0.400 con tangente d'arrivo = quella dello scollo del
blocco (0.51 mm), scollo davanti abbassato 0.405/0.405 fra la tangente del
blocco e la ⊥ al c.f. (1.19 mm), colletto cucitura collo −14.4° con
0.086/0.500 e 0.213/0.485 (0.49 mm), bordo esterno +6.9° con 0.439/0.461
(0.38 mm), linea di rollo +15.1° con 0.328/0.383 (0.16 mm). La cucitura
davanti manica "blend" usa `smooth_polyline` sui tre punti orlo/gomito/testa
(1.33 mm dal disegno sul sottomanica): nessuna costante.

**Valori generati alla 50** (per la fase 5): scollo abbassato 113.78 + 144.49 =
**258.27** · spalle 4041 147.35/142.35 · carré dietro 222.07 (disegnato 221.87)
e davanti 224.72 (224.75) · pannello dietro 461.03 (461.14) · orlo dietro
289.49 + davanti 292.82 = **cinturino 582.31** (582.51) · passo occhielli
130.61 · polsino **321.47** · testa manica 333.85 + 197.80 = 531.65 contro
Ac 531.15 (**agio 0.50 mm**) · aree: i tre pannelli dietro ricompongono
esattamente il dietro design, i quattro davanti lo ricompongono più la
striscia di 2 cm del pintuck.

**Fase 5 — assemblaggio (2026-08-19).** Nessuna quota del libro rimessa in
discussione: `build_jacket_pattern` monta i 17 pezzi della fase 4 con
`_make_piece` e la regola `fold*` → 0 di `for_edges`. Note:

- **E5.1 — le verifiche di lunghezza accoppiata vanno lette sui BORDI dei pezzi
  montati, non sugli scalari dei report**, altrimenti sono tautologie (il
  polsino *è* la somma dei due fondi manica, il cinturino *è* la somma dei due
  orli). Le otto coppie controllate (cinturino/orlo, polsino/fondo manica,
  carré dietro e davanti, i tre pannelli, i fianchi) tornano a **0.00 mm** su
  tutte e quattro le taglie, quindi la soglia `SEAM_MATCH_TOL_MM = 2.5` non
  scatta mai: resta come rete di sicurezza per le fasi future.
- **E5.2 — il pintuck entra nei conti degli orli e del carré davanti.** Lo
  slash&spread (D18) apre `davanti` di 2 cm: la sua catena guadagna il labbro
  del taglio **due volte**, sul bordo carré e sul bordo orlo. La somma dei
  bordi dei pannelli davanti è quindi `carré + 20 mm` e `cinturino + 20 mm`;
  le due verifiche sottraggono `PINTUCK_SPREAD_MM` (la piega cucita richiude
  quei 2 cm prima del montaggio).
- **E5.3 — nessun warning duplicato sull'agio testa.** Il piano prevedeva in
  `build_jacket_pattern` un warning per `|cap_ease| > 10 mm` o clamp:
  `split_sleeve` ne emette già uno più severo (tolleranza 1 mm, D17), che
  viene propagato tale e quale invece di essere raddoppiato.

**Valori generati dal report (taglie 44/50/56/62):** agio petto 72/75/66/57 mm ·
agio fianchi 37/54.1/61.3/73.7 mm (warning "Check Hg" solo alla 44) ·
Ac 490.3/531.2/571.3/609.6 · Sch 147.7/161.0/173.9/185.6 · agio testa
0.25/0.50/3.36/9.61 mm (warning di clamp su 56 e 62) · scollo
240.8/258.3/275.1/292.1 · correzione colletto −1.69/−1.58/−1.49/−1.41 mm ·
cinturino 515.1/582.3/649.6/722.0 · polsino 321.8/321.5/321.4/321.4.

**Fase 7 — verifica end-to-end (2026-08-19).** Nessuna quota rimessa in
discussione. `scripts/verify_jacket_overlay.py` sovrappone il generato al libro
su quattro pannelli (blocco corpo p. 11, blocco manica p. 12, corpo Design 4041
e colletto p. 14) e chiude con `LANDMARK_TOL_MM = 2.5` / `CURVE_TOL_MM = 3.0`.
Margine minimo residuo **0.86 mm** (SP0_f, dopo E8.1 ed E8.4). Eccezioni
whitelistate, tutte già decise in fase di calibrazione:

- **`panel_cf`/`panel_side`** misurate libro→generato: il prolungamento di 1 cm
  fino al carré (D19/E4.7) è collineare ma esce dalla polilinea estratta.
- **`pocket_opening`**: il PDF estrae solo la linea d'apertura da 12 cm, il
  mark generato ci chiude attorno il listino da 1 cm.
- `under back_fold` non è confrontato: nel riferimento non esiste (coincide col
  fold del sopramanica, E3.6).

Il design manica di p. 15 resta fuori dall'overlay: il libro disegna la manica
**prima** dello slash (E4.6), quindi il sopramanica ruotato scarterebbe fino a
~16 mm per costruzione. Resta coperto dai test della fase 4.

`scripts/verify_ms_overlay.py` invariato e verde (landmark peggiore 1.91 mm).
Smoke test di export reale (PDF singolo + SVG, `SeamAllowances(15, 30)`) su
taglie 44/50/56 e Bh 190: 17 pezzi, nessuna eccezione, foglio singolo
4.20–4.62 m × 0.80–0.87 m.

**Revisione (2026-08-19).** Correzioni dopo la review dei findings.

- **E8.1 — D13 rovesciata: `Sh` = 30.0 cm dal disegno, non 31.0 dal chart**
  (`SLEEVE_HEM_MM = 300`, `BACK_FOLD_ADD_MM = 40` per tenere F_b a 21.0 come
  disegnato). Il disegno lo dichiara tre volte: l'etichetta stampata "sleeve
  hem 15" sulla metà d'orlo, la geometria estratta (½ = hypot(147.47, 30.02) =
  150.5 mm; i due bordi d'orlo sommano 180.02 + 121.06 = 301.1) e il polsino di
  p. 15 (314.0 disegnato contro 313.1 generato, era 321.5). Il chart stampa
  mezzo centimetro in più sulla metà, esattamente come fa per `Nw` (D1, chart
  8.5 contro 8.0 disegnato): stesso refuso, stessa risoluzione — il disegno
  vince quando ha doppia conferma grafica. Cadono così **tutte** le eccezioni
  D13/E3.6/E4.5: B_hem 4.60 → 0.50 mm, `upper back_fold` 4.48 → 0.50,
  `upper hem` 4.60 → 0.05, `under hem` 4.60 → 0.20, cuciture dietro 1.48–1.55
  (erano 0.63–1.07), polsino 7.5 mm fuori → 0.9. Rimosse le tolleranze
  dedicate dei test manica/design e la whitelist `B_HEM_ITEMS` dell'overlay;
  il "+4.5" stampato del passo 6 resta un emendamento (D14), ma lo scarto
  scende da 1.0 a 0.5 cm. Unico effetto collaterale: il Δ fra le due cuciture
  dietro alla taglia 62 passa da 2.90 a 3.01 mm, quindi l'invariante
  multi-taglia sale da 3.0 a 3.5 mm.
- **E8.2 — la patta del taschino non è un pezzo in piega.** Il bordo alto era
  chiamato `fold_edge`, quindi D27 gli toglieva il margine proprio dove il
  pezzo si cuce sul carré, in contraddizione con la tabella dei pezzi (x 4
  specchiato, nessuna piega). Ora è una sola catena `seam` come il sacchetto
  del taschino, che è lo stesso pentagono.
- **E8.3 — degradazione invece di eccezione sui corpi sproporzionati.** Il ramo
  giacca sollevava la `ValueError` grezza di `PatternPiece` (nessun pezzo, solo
  un QMessageBox) per corpi plausibili con vita larga sul petto stretto, mentre
  il ramo jeans degrada sempre con warning di dominio. Due clamp in
  `design_body` (report `warnings`, propagati da `build_jacket_pattern`):
  la linea del carré davanti resta almeno `FRONT_YOKE_MARGIN_MM = 20` dentro
  il giromanica, e le due cuciture del pannello davanti si spostano insieme
  verso il c.f. finché il fianchetto tiene `FRONT_PANEL_MIN_WIDTH_MM = 5` dal
  punto più avanzato del giro sotto il carré (le taglie 44–62 del libro ne
  hanno 20–72, nessun clamp scatta su di esse; su 1000 corpi plausibili
  casuali scatta 9 volte). In `build_jacket_pattern` un contorno di taglio non
  offsettabile non uccide più il pattern: il pezzo esce con la sola linea netta
  e il warning "margine troppo largo per <pezzo>". Su 2000 misure casuali
  (Bh 150–200, Cg 75–135, Wg 60–135, Hg 80–145, Sl 40–78) i 17 pezzi escono
  sempre; restano casi impossibili fuori da qualunque corporatura reale
  (Bh 131 con Wg 132, Sl 27 su Bh 197), dove l'eccezione arriva ancora — come
  già succede al ramo jeans su misure incoerenti.
- **E8.4 — oracoli per asole e bottoni.** Sei costanti di piazzamento
  (`BUTTONHOLE_LEN_MM`, `BUTTONHOLE_PAST_CF_MM`, `TAB_BUTTONHOLE_LEN_MM`,
  `TAB_BUTTONHOLE_FROM_END_MM`, `FLAP_BUTTON_MM`, `CUFF_MARK_INSET_MM`) non
  erano presidiate da nulla: mutarle di ±3 mm lasciava la suite verde. Il JSON
  di riferimento le conteneva già: fessura del cinturino 14.22→36.50 dal bordo
  (c.f. a 20.0), fessura e bottone del polsino 275.52→296.59 e 15.01 dal bordo,
  bottone della patta a 41.1 sotto il carré. Aggiunti quattro test in
  `test_draft_jacket_design.py` (fessure c.f. e cinturino, polsino, linguetta
  per D24, bottone patta): 23 mutanti su 24 (±2/±3 mm) muoiono, sopravvive solo
  `FLAP_BUTTON_MM −2` perché il disegnato è 41.1 contro i 42.0 del codice.
  Scarti misurati: fessure c.f. 0.75–1.12 mm, cinturino 1.2 mm (l'estremità
  tonda generata sporge un po' più della disegnata), polsino 3.9 mm sull'inizio
  della fessura (il libro la mette a 1.7 cm dall'estremità, D24 dice 1.5).
  L'overlay confronta ora il **centro della fessura generata** contro quello
  disegnato invece del bottone sul c.f.: cade la whitelist `BUTTONHOLE_ITEMS`
  (6.0 mm) e il margine minimo del gate diventa reale, 0.86 mm.
- **E8.5 — minori.** `split_sleeve` riportava nel `pivot_deg` del sottomanica
  la rotazione del sopramanica (il sottomanica non ruota: ora 0.0, e ogni pezzo
  ha la sua copia della lista warnings); il test che li confrontava era
  tautologico ed è sostituito dal confronto punto a punto fra il giro del
  sottomanica e quello del blocco. `.gitignore` ignora anche
  `jacket_pattern.pdf/.svg`, i nomi di export proposti col modello giacca.
