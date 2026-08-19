# M&S Jeans Pattern App

Applicazione desktop (Windows + macOS) che genera cartamodelli su misura e li
esporta in PDF/SVG in scala 1:1 (per proiettore da cartamodelli o plotter).
La **tendina "Modello"** in cima al form sceglie fra:

- **Basic Jeans** (default) — jeans classico da uomo a 5 tasche, Design 3069;
- **Classic Denim Jacket** — giacca di jeans, Design 4041.

I campi del form si adattano al modello scelto: `Waistband W` e `Hip girth Hg`
sono comuni, gli altri si mostrano/nascondono.

## Metodo di tracciamento

Il tracciato segue **"Metric Pattern Techniques – Jeans-Basics" di
M. Müller & Sohn**: Basic Jeans Block (pp. 2–3) + Design 3069 (pp. 4–5) e
Basic Denim Jacket Block (pp. 11–13) + Design 4041 (pp. 14–15),
`docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf`.

Le pagine del fascicolo sono disegnate in scala (taglia 50):
`scripts/extract_ms_reference.py` ne estrae la geometria vettoriale in
`tests/data/ms_reference_size50.json` e la suite di test verifica che ogni
landmark del tracciato generato coincida col disegno del libro entro ~1.5 mm
(curve entro ~2.5 mm). Le regole di costruzione e le costanti di forma delle
curve sono documentate in `src/jeans_pattern/draft_ms.py` e nel piano
`docs/superpowers/plans/2026-07-15-ms-jeans-draft.md`.

Per la giacca valgono gli stessi criteri: `scripts/extract_jacket_reference.py`
→ `tests/data/ms_jacket_reference_size50.json`, tracciato in
`src/jeans_pattern/draft_jacket.py` (blocco) e
`src/jeans_pattern/draft_jacket_design.py` (Design 4041), piano
`docs/superpowers/plans/2026-08-19-ms-denim-jacket.md`.

## Basic Jeans — misure richieste (chart M&S, default = taglia 50)

| Sigla | Misura | Default |
|---|---|---|
| W  | giro vita (waistband) | 90 cm |
| Hg | giro fianchi | 102 cm |
| Kg | giro ginocchio | 43 cm |
| Hw | giro fondo gamba | 38 cm |
| Os | lunghezza esterna (outseam) | 102 cm |
| Is | lunghezza interna (inseam) | 82 cm |

Derivate automaticamente: cavallo `Br = Os − Is`, altezza ginocchio
`Kl = Is/2 + Is/10 − 2`, larghezze Ftw/Fcw/Btw/Bcw da Hg.

## Basic Jeans — pezzi generati (Design 3069)

davanti ×2 · dietro ×2 · carré ×2 (pinces chiuse) · cinturino (con tacche
c.f./tasca/fianco/c.b. e segni passanti) · tasca posteriore · sacchetto e
paramontura tasca davanti · paramontura e scudo patta zip* · taschino
porta-monete* · striscia passanti — (*pezzi derivati, non tracciati nel
fascicolo).

Ogni pezzo riporta la **linea netta** (tratteggiata) e la **linea di taglio**
(continua) con margini configurabili nel form: default 1.5 cm sulle cuciture
e 3 cm all'orlo; 0 = solo linee nette. Sotto il form compaiono i valori
derivati e le verifiche del libro (agio fianchi, resto vita) con eventuali
avvisi.

## Classic Denim Jacket — misure richieste (chart M&S, default = taglia 50)

| Sigla | Misura | Default |
|---|---|---|
| Bh | statura (body height) | 179 cm |
| Cg | giro petto (chest girth) | 100 cm |
| Wg | giro vita — campo `Waistband W` | 90 cm |
| Hg | giro fianchi | 102 cm |
| Sl | lunghezza manica (sleeve length) | 64 cm |

Derivate automaticamente dal chart di p. 12 (valori alla taglia 50):

| Sigla | Nome | Formula | Taglia 50 |
|---|---|---|---|
| Nw  | neck width | 1/10 di ½Cg + 3 | 8.0 cm |
| Sd  | scye depth | ⅛Cg + 12.5 | 25.0 cm |
| Ad  | armhole depth | Sd + 2.5 | 27.5 cm |
| Bwl | back waist length | ¼Bh | 44.75 cm |
| Lg  | lunghezza | ½Bh − ⅛Bh − 3.125 | 64.0 cm |
| Bw  | back width | 2/10 Cg + 1.2 (Cg ≤ 100); 1/10 Cg + 11.2 sopra | 21.2 cm |
| Sw  | scye width | ⅛Cg + 3 | 15.5 cm |
| Cw  | chest width | 2/10 Cg + 0.8 | 20.8 cm |
| Aw  | abdomen width | ¼Wg − 1.3, mai meno di Cw | 21.2 cm |

Manica: altezza testa `Sch` e larghezza testa `Scw` sono misurate sul blocco
generato (giro Ah e Ac), non su formule chiuse; `Sh` (fondo manica) è una
costante di modello di 31 cm.

## Classic Denim Jacket — pezzi generati (Design 4041)

| Pezzo | Qtà | Taglio |
|---|---|---|
| `carre_davanti` | 2 | specchiato (bordo davanti in piega) |
| `davanti` | 2 | specchiato (bordo davanti in piega) |
| `pannello_petto` | 2 | specchiato |
| `fianchetto_davanti` | 2 | specchiato |
| `carre_dietro` | 1 | in piega sul c.b. |
| `dietro` | 1 | in piega sul c.b. |
| `fianchetto_dietro` | 2 | specchiato |
| `sopramanica` | 2 | specchiato |
| `sottomanica` | 2 | specchiato |
| `polsino` | 2 | doppio, in piega sul lato lungo |
| `colletto` | 2 | in piega sul c.b. (sopra + sotto) |
| `cinturino` | 2 | in piega sul c.b. |
| `patta_taschino` | 4 | specchiato (2 per tasca) |
| `sacchetto_taschino` * | 4 | specchiato (2 per tasca) |
| `listino_tasca_laterale` | 2 | specchiato |
| `sacchetto_tasca_laterale` * | 4 | specchiato (2 per tasca) |
| `linguetta` | 4 | specchiato (2 per lato) |

\* pezzi derivati, non tracciati nel fascicolo.

I bordi in piega non ricevono margine di cucitura; nessun bordo è un orlo
libero (l'orlo del corpo va sul cinturino e il fondo manica sul polsino), quindi
tutti gli altri prendono il margine cuciture. Il report sotto il form mostra
profondità giro, lunghezza, agio petto, check fianchi Hg, giro manica Ac e agio
testa manica, con gli avvisi del libro.

Emendamenti rispetto alle quote stampate (dettaglio e motivazione nel piano
`docs/superpowers/plans/2026-08-19-ms-denim-jacket.md`):

- **D12** — `Sch`/`Scw` ricalibrate: Ah e Ac misurate sul blocco parametrico
  escono ~0.5 % sotto i numeri del chart, due costanti di calibrazione
  riportano l'altezza e la larghezza della testa sui valori dichiarati.
- **D13** — fondo manica `Sh` = 31 cm dal chart; l'etichetta "½ sleeve hem 15"
  del disegno è incoerente col chart, per cui l'angolo d'orlo della manica cade
  4.6 mm fuori dal disegnato (eccezione dichiarata nell'overlay di verifica).
- **D14** — piega dietro della manica al gomito = piega davanti + ½Sh + 3.5 cm:
  riproduce esattamente il disegno, mentre il "+4.5" stampato non torna.

## Sviluppo

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows bash; su macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m jeans_app.main          # GUI
```

Dopo modifiche al tracciato, oltre a `pytest`, genera gli overlay
generato-vs-libro (rosso = libro, blu = generato; escono con codice diverso da
zero se una deviazione supera la soglia):

```bash
python scripts/verify_ms_overlay.py       # verification_ms_size50.pdf (jeans)
python scripts/verify_jacket_overlay.py   # verification_jacket_size50.pdf (giacca)
```

L'overlay della giacca confronta blocco corpo (p. 11), blocco manica (p. 12),
corpo Design 4041 e colletto (p. 14) e stampa la deviazione di ogni landmark e
di ogni curva.

## Packaging

```bash
# Windows:
pyinstaller packaging/pyinstaller_win.spec --noconfirm   # dist/SelvedgeJeansPattern.exe
# macOS:
pyinstaller packaging/pyinstaller_mac.spec --noconfirm   # dist/SelvedgeJeansPattern.app
```

## Uso con proiettore da cartamodelli

1. **Esporta PDF (singola pagina)** — un unico PDF (~3.2 m × 1.3 m) in scala
   1:1 con quadrato di calibrazione 10×10 cm in alto a sinistra.
2. Apri il PDF nel software del proiettore (Pattern Projector, ecc.).
3. Calibra col quadrato: proiettato sul tessuto deve misurare esattamente
   10×10 cm.
4. Proietta e ricalca i pezzi (la linea continua è quella di taglio).

**Non stampare il PDF singolo su A4**: i viewer lo scalano silenziosamente.
In alternativa usa **Esporta PDF (tile A4)** e assembla i fogli con i
crocini d'angolo, oppure un plotter che rispetti le dimensioni native.

## Adattamento vita/fianchi

Il fascicolo quadra tutta la vita sul dietro (regola ½W+2−vita davanti), il
che funziona solo nella proporzione del chart (W = Hg − 12 cm). Per misure
personalizzate l'app distribuisce la deviazione da quella proporzione metà sul
davanti (variando la rientranza al c.f., fino a −2/+3.5 cm) e metà sul dietro;
oltre i limiti compaiono avvisi nel report (resto vita, proporzione esaurita).
Alla proporzione del chart il tracciato resta esattamente quello del libro.

## Limiti noti

- Paramontura/scudo patta e taschino porta-monete sono pezzi standard derivati,
  non tracciati nel fascicolo M&S.
- L'inizio dello scasso tasca è a 13 cm dall'angolo fianco lungo la vita, come
  nel disegno di pagina 5 e nella tacca del cinturino del libro (la quota
  stampata "12" non trova riscontro esatto nell'illustrazione).
- Il disegno di pagina 5 prevede di raccordare il fianco davanti con 6 mm in
  più all'ingresso tasca ("add width"): il contorno del davanti resta quello
  del block; l'estensione è indicata dal segno dello scasso.
- Tacche di montaggio limitate a cinturino e segni tasca; nessuna gradazione
  automatica delle taglie.
