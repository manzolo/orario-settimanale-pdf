# Orario Settimanale

Genera un PDF con l'orario settimanale delle attività extrascolastiche a partire da un semplice file CSV.

## Come funziona

```
orario.csv  →  genera_html.py  →  orario.html  →  WeasyPrint  →  orario.pdf
```

Il tutto gira dentro un container Docker: **non serve nessuna dipendenza sul sistema host** tranne `docker` e `make`.

## Utilizzo

1. Copia `orario.example.csv` in `orario.csv` e modificalo con i tuoi dati
2. Esegui:

```bash
make
```

Il PDF viene generato in `orario.pdf`.

## Formato CSV

```
giorno,nome,attivita,inizio,fine,note
```

| Campo      | Valori accettati                                          |
|------------|-----------------------------------------------------------|
| `giorno`   | `Lunedi`, `Martedi`, `Mercoledi`, `Giovedi`, `Venerdi`   |
| `nome`     | Nome del bambino (determina il colore nella tabella)      |
| `attivita` | Nome dell'attività (es. `Calcio`, `Danza`, `Judo` …)     |
| `inizio`   | Orario `HH:MM` oppure `mattina`                           |
| `fine`     | Orario `HH:MM` oppure `mattina`                           |
| `note`     | Testo opzionale mostrato sotto il nome (es. `a scuola`)  |

Gli orari vengono arrotondati automaticamente al quarto d'ora di 30 minuti più vicino per la costruzione della griglia.  
Se due attività si sovrappongono nello stesso giorno, la colonna viene **divisa automaticamente** in due sotto-colonne.

### Colori automatici

I colori delle celle vengono assegnati automaticamente per nome. I nomi riconosciuti di default sono `Linda`, `Mariel`, `Vittoria`; per aggiungerne altri modifica il dizionario `COLORS` in `genera_html.py`.

## Comandi Make

| Comando        | Descrizione                                          |
|----------------|------------------------------------------------------|
| `make`         | Costruisce l'immagine e genera il PDF                |
| `make build`   | Solo build dell'immagine Docker                      |
| `make run`     | Solo generazione PDF (richiede build precedente)     |
| `make rebuild` | Forza rebuild completo dell'immagine e rigenera      |
| `make clean`   | Rimuove il PDF e l'immagine Docker                   |

## Struttura del progetto

```
├── genera_html.py        # Script Python: CSV → HTML
├── generate-pdf.sh       # Script shell: avvia Python + WeasyPrint
├── Dockerfile            # Immagine con Python + WeasyPrint
├── docker-compose.yml    # Monta la directory locale nel container
├── Makefile              # Comandi di build e generazione
├── orario.example.csv    # CSV di esempio (struttura dati)
└── .github/
    └── workflows/
        └── genera-pdf.yml  # CI: genera e verifica il PDF su ogni push
```
