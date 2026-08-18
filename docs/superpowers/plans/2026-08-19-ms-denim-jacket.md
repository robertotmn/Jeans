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
