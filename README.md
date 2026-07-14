# M&S Jeans Pattern App

Applicazione desktop (Windows + macOS) che genera il cartamodello su misura del
jeans classico da uomo a 5 tasche e lo esporta in PDF/SVG in scala 1:1 (per
proiettore da cartamodelli o plotter).

## Metodo di tracciamento

Il tracciato segue **"Metric Pattern Techniques – Jeans-Basics" di
M. Müller & Sohn**: Basic Jeans Block (pp. 2–3) + Design 3069 (pp. 4–5),
`docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf`.

Le pagine del fascicolo sono disegnate in scala (taglia 50):
`scripts/extract_ms_reference.py` ne estrae la geometria vettoriale in
`tests/data/ms_reference_size50.json` e la suite di test verifica che ogni
landmark del tracciato generato coincida col disegno del libro entro ~1.5 mm
(curve entro ~2.5 mm). Le regole di costruzione e le costanti di forma delle
curve sono documentate in `src/jeans_pattern/draft_ms.py` e nel piano
`docs/superpowers/plans/2026-07-15-ms-jeans-draft.md`.

## Misure richieste (chart M&S, default = taglia 50)

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

## Pezzi generati (Design 3069)

davanti ×2 · dietro ×2 · carré ×2 (pinces chiuse) · cinturino (con tacche
c.f./tasca/fianco/c.b. e segni passanti) · tasca posteriore · sacchetto e
paramontura tasca davanti · paramontura e scudo patta zip* · taschino
porta-monete* · striscia passanti — (*pezzi derivati, non tracciati nel
fascicolo).

Ogni pezzo riporta la **linea netta** (tratteggiata) e la **linea di taglio**
(continua) con margini configurabili nel form: default 1 cm sulle cuciture e
3 cm all'orlo; 0 = solo linee nette. Sotto il form compaiono i valori derivati
e le verifiche del libro (agio fianchi, resto vita) con eventuali avvisi.

## Sviluppo

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows bash; su macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m jeans_app.main          # GUI
```

Dopo modifiche al tracciato, oltre a `pytest`, genera l'overlay
generato-vs-libro con `python scripts/verify_ms_overlay.py`
(`verification_ms_size50.pdf`: rosso = libro, blu = generato).

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
