# Simulazione Coda con Vacation, N-Policy e Set-up

![C++17](https://img.shields.io/badge/C%2B%2B-17-blue) ![OMNeT++ 6.3](https://img.shields.io/badge/OMNeT%2B%2B-6.3-green) ![Python 3.11](https://img.shields.io/badge/Python-3.11-yellow) ![MIT License](https://img.shields.io/badge/License-MIT-lightgrey)

Modello a eventi discreti di una coda con arrivi batch Poisson, servizio bulk, vacation dipendente dalla coda, N-policy con stato dormant e tempo di setup.

| Campo | Valore |
|---|---|
| Autore | Mohamed Samir Haffoudhi |
| Email | mohamed.haffoudhi@studio.unibo.it |
| Corso | Simulazione di Sistemi |
| Anno | Master 1 Informatica - A.A. 2025/2026 |

## Tabella dei Contenuti

- [1. Intestazione](#1-intestazione)
- [2. Panoramica del Modello](#2-panoramica-del-modello)
- [3. Prerequisiti e Installazione](#3-prerequisiti-e-installazione)
- [4. Esecuzione Rapida (Quick Start)](#4-esecuzione-rapida-quick-start)
- [5. Guida Completa all'Esecuzione](#5-guida-completa-allesecuzione)
- [6. Modifica dei Parametri](#6-modifica-dei-parametri)
- [7. Struttura del Progetto](#7-struttura-del-progetto)
- [8. Componenti OMNeT++ e C++ Custom](#8-componenti-omnet-e-c-custom)
- [9. Output e Interpretazione Risultati](#9-output-e-interpretazione-risultati)
- [10. Troubleshooting](#10-troubleshooting)
- [11. Riferimento Bibliografico](#11-riferimento-bibliografico)

---

## 1. Intestazione

Titolo progetto: **Simulazione Coda con Vacation, N-Policy e Set-up**.

Stack usato nel repository:

- C++17 per i moduli custom OMNeT++
- OMNeT++ 6.3.0 come motore di simulazione
- Python (>=3.9, validato su 3.11) per post-analisi statistica
- License badge: MIT (aggiungere file LICENSE nel repository se non ancora presente)

Il sistema simulato rappresenta una coda con logica server non banale: servizio a blocchi, sospensioni (vacation), riattivazione solo oltre soglia N, e tempo di setup prima della ripresa del servizio.

| Metadato | Valore |
|---|---|
| Corso | Simulazione di Sistemi |
| Anno | Master 1 Informatica - A.A. 2025/2026 |
| Autore | Mohamed Samir Haffoudhi |

---

## 2. Panoramica del Modello

Il modello implementa un processo di arrivo **compound Poisson**: gli inter-arrivi sono esponenziali con media `m`, mentre la dimensione del batch in ingresso e uniforme discreta tra `x1=1` e `x2=4`.
Il server usa una regola di **bulk service** con soglie `(a,b)=(7,16)`: non parte sotto `a`, e serve al massimo `b` job per batch.
Il tempo di servizio dipende dalla dimensione reale del batch servito `r` con formula `t = (r/b)*sp + U(l,u)`.
Quando non ci sono abbastanza job (`qLen < a`), il server entra in **Single Vacation Rule (SVR)**: una vacation con durata dipendente da `k` (job in coda): `t = ((k+1)/b)*sv + U(z,w)`.
Alla fine della vacation, il server non riparte subito: se la coda non raggiunge `N`, resta in stato **IDLE (dormant)**.
Quando `qLen >= N`, il server passa in **SETUP**, attende un tempo esponenziale di media `q`, poi torna **BUSY**.
Questa logica implementa in modo esplicito la catena di stati richiesta e consente analisi su stabilita, congestione e tempo medio nel sistema.

Stati server (ASCII art):

```bash
BUSY
  |
  | (se qLen < a a fine servizio)
  v
VACATION
  |
  | (fine vacation)
  +--> [qLen >= N] --> SETUP --(fine setup)--> BUSY
  |
  +--> [qLen <  N] --> IDLE (dormant)
                           |
                           | (nuovi arrivi fino a qLen >= N)
                           v
                         SETUP
```

Misure di prestazione principali:

- `L`: numero medio di utenti nel sistema (`numInSystem:timeavg`)
- `W`: tempo medio di permanenza (`sink.lifeTime:mean`)
- `rho`: utilizzo medio del server (`busy:timeavg`)
- `E[vacation]`: durata media vacation (`vacationDuration:mean`)
- Richiamo a Little: `L = lambda * W` e quindi `W = L / lambda`

Tabella parametri modello (valori default usati nel progetto):

| Gruppo | Parametro | Valore |
|---|---|---|
| Arrivi batch | `m` | `0.5, 1.0, 1.4, 2.0` (per configurazione) |
| Arrivi batch | `x1, x2` | `1, 4` |
| Bulk service | `a, b` | `7, 16` |
| Service time | `sp, l, u` | `0.1, 1.0, 3.92` |
| Vacation | `sv, z, w` | `0.2, 2.0, 3.8` |
| N-policy | `N` | `20` |
| Setup | `q` | `1.0` |
| Simulazione | `sim-time-limit` | `100000s` |
| Simulazione | `warmup-period` | `10000s` |
| Simulazione | `repeat` | `20` |

---

## 3. Prerequisiti e Installazione

#### OMNeT++ 6.3.0

Link ufficiale: https://omnetpp.org/download/

Da root del repository (`progetto`):

```bash
cd opp_workspace/omnetpp-6.3.0
./configure
make -j4
source setenv -q
cd ../modello1
make -j4
```

Note pratiche:

- Il launcher nel progetto usa `../omnetpp-6.3.0` come root OMNeT++.
- Lo script di run esporta anche `OPP_ENV_VERSION=6` e `OMNETPP_ROOT`.

#### Python >= 3.9

Nel repository non e presente un `requirements.txt` dedicato al progetto in root; le dipendenze sono ricavate dagli import di `analisi_risultati.py`:

- `numpy`
- `pandas`
- `scipy`
- `matplotlib`

Setup consigliato da root del repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy pandas scipy matplotlib
```

#### Verifica installazione

Verifica rapida in `opp_workspace/modello1`:

```bash
./modello1 --version
python -c "import pandas"
```

---

## 4. Esecuzione Rapida (Quick Start)

```bash
cd opp_workspace/modello1
# 1. Compila
make -j4
# 2. Lancia simulazioni
./run_all.sh
# 3. Analizza risultati
python3 analisi_risultati.py
```

---

## 5. Guida Completa all'Esecuzione

### Singolo run di test (config `m10`, run `0`)

Comando completo con flag reali (`-n`, `-l`) usati nel progetto:

```bash
cd opp_workspace/modello1
OPPDIR="../omnetpp-6.3.0"
source "$OPPDIR/setenv" -q
export OPP_ENV_VERSION=6
export OMNETPP_ROOT="$(cd $OPPDIR && pwd)"
./modello1 -u Cmdenv -c m10 -r 0 \
  -n ".:$OPPDIR/samples/queueinglib" \
  -l "$OPPDIR/samples/queueinglib/queueinglib" \
  --result-dir=results
```

### 20 run completi per tutte le 4 configurazioni

Script pronto (4 configurazioni x 20 run = 80 run):

```bash
cd opp_workspace/modello1
./run_all.sh
```

Nota tempo stimato:

- dipende dalla macchina; il totale puo richiedere da alcuni minuti a oltre 1 ora.
- lo script usa `Cmdenv` (piu veloce di `Qtenv` per batch run).

### Solo configurazioni transiente (`warmup-period = 0s`)

Nel file `omnetpp.ini` sono presenti le config `transient_m05`, `transient_m10`, `transient_m14`, `transient_m20` con `repeat=1`.

```bash
cd opp_workspace/modello1
OPPDIR="../omnetpp-6.3.0"; source "$OPPDIR/setenv" -q; export OPP_ENV_VERSION=6; export OMNETPP_ROOT="$(cd $OPPDIR && pwd)"
./modello1 -u Cmdenv -c transient_m05 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
./modello1 -u Cmdenv -c transient_m10 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
./modello1 -u Cmdenv -c transient_m14 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
./modello1 -u Cmdenv -c transient_m20 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
```

### Analisi post-simulazione

```bash
cd opp_workspace/modello1
python3 analisi_risultati.py
```

File output generati da script Python:

- `analisi/misure_prestazione.png`
- `analisi/boxplot_prestazioni.png`
- `analisi/risultati_prestazioni.csv`
- `analisi/risultati_dettaglio.csv`
- `analisi/little_check.csv`
- `analisi/report_finale.csv`
- `analisi/transiente_transient_m05.png`
- `analisi/transiente_transient_m10.png`
- `analisi/transiente_transient_m14.png`
- `analisi/transiente_transient_m20.png`

---

## 6. Modifica dei Parametri

Tabella completa parametri `omnetpp.ini`.

| Parametro | Valore default | File | Sezione ini | Descrizione | Vincoli |
|---|---|---|---|---|---|
| `m` | `0.5 / 1.0 / 1.4 / 2.0` | `omnetpp.ini` | `[Config m05/m10/m14/m20]` | media inter-arrivo esponenziale della `BatchSource` | `m > 0` |
| `x1` | `1` | `omnetpp.ini` | `[General]` | minimo batch in ingresso | intero, `x1 >= 1` |
| `x2` | `4` | `omnetpp.ini` | `[General]` | massimo batch in ingresso | intero, `x2 >= x1` |
| `a` | `7` | `omnetpp.ini` | `[General]` | soglia minima per avvio servizio bulk | intero, `a > 0` |
| `b` | `16` | `omnetpp.ini` | `[General]` | capacita massima batch servito | intero, `b >= a` |
| `sp` | `0.1` | `omnetpp.ini` | `[General]` | parte deterministica del service time | reale |
| `l` | `1.0` | `omnetpp.ini` | `[General]` | limite inferiore `U(l,u)` servizio | `l >= 0` |
| `u` | `3.92` | `omnetpp.ini` | `[General]` | limite superiore `U(l,u)` servizio | `u > l` |
| `sv` | `0.2` | `omnetpp.ini` | `[General]` | parte deterministica vacation | reale |
| `z` | `2.0` | `omnetpp.ini` | `[General]` | limite inferiore `U(z,w)` vacation | `z >= 0` |
| `w` | `3.8` | `omnetpp.ini` | `[General]` | limite superiore `U(z,w)` vacation | `w > z` |
| `N` | `20` | `omnetpp.ini` | `[General]` | soglia N-policy per riattivazione | intero, `N >= a` |
| `q` | `1.0` | `omnetpp.ini` | `[General]` | media setup time esponenziale | `q > 0` |
| `warmup-period` | `10000s` | `omnetpp.ini` | `[General]` | transiente scartato nelle run principali | nelle transient e `0s` |
| `repeat` | `20` | `omnetpp.ini` | `[General]` | numero run per configurazione principale | intero `>=1` |
| `sim-time-limit` | `100000s` | `omnetpp.ini` | `[General]` | orizzonte temporale di ogni run | tempo positivo |

### Esempio: aggiungere configurazione `m = 3.0`

Passo 1: aprire `opp_workspace/modello1/omnetpp.ini`.

Passo 2: aggiungere in fondo queste righe esatte:

```ini
[Config m30]
description = "Interarrival mean m=3.0"
Modello_progetto.source.m = 3.0
```

Passo 3: eseguire un test rapido:

```bash
cd opp_workspace/modello1
OPPDIR="../omnetpp-6.3.0"; source "$OPPDIR/setenv" -q; export OPP_ENV_VERSION=6; export OMNETPP_ROOT="$(cd $OPPDIR && pwd)"
./modello1 -u Cmdenv -c m30 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
```

---

## 7. Struttura del Progetto

Albero principale in `opp_workspace/modello1` con descrizione inline:

```bash
modello1/
|-- BatchSource.h                      # interfaccia modulo sorgente arrivi batch
|-- BatchSource.cc                     # implementazione arrivi batch compound Poisson
|-- BulkServiceVacationServer.h        # interfaccia server con stati IDLE/VACATION/SETUP/BUSY
|-- BulkServiceVacationServer.cc       # logica completa di servizio, vacation, N-policy, setup
|-- modello_progetto.ned               # definizione rete OMNeT++ e statistiche
|-- omnetpp.ini                        # configurazioni run (m05,m10,m14,m20 + transient_*)
|-- analisi_risultati.py               # parsing .sca/.vec, IC 95%, grafici, report CSV
|-- run_all.sh                         # lancio automatico 80 run
|-- Makefile                           # build del binario modello1
|-- m05.anf                            # artefatto analisi OMNeT++
|-- m10.anf                            # artefatto analisi OMNeT++
|-- analisi/                           # output post-processing python
|   |-- report_finale.csv              # tabella finale per metriche e check Little
|   |-- little_check.csv               # verifica legge di Little
|   |-- risultati_prestazioni.csv      # medie + IC 95%
|   |-- risultati_dettaglio.csv        # dati run-level
|   `-- *.png                          # grafici prestazioni e transiente
`-- results/                           # generato a runtime dai run OMNeT++
    |-- *.sca                          # scalari per run/configurazione
    `-- *.vec                          # vettori temporali per analisi transiente
```

---

## 8. Componenti OMNeT++ e C++ Custom

### Usato da queueinglib (non modificato)

Moduli/componenti esterni usati dal modello:

- `org.omnetpp.queueing.Sink`
  - ruolo: raccoglie i job completati e fornisce metriche di lifetime (`lifeTime:mean`).
- `queueing::Job` (incluso via `Job.h`)
  - ruolo: messaggio/job con timestamp e campi statistici aggiornati da moduli custom.
- Libreria runtime `queueinglib`
  - caricata a run-time con flag `-l ../omnetpp-6.3.0/samples/queueinglib/queueinglib`.

### Creato da zero (C++ custom)

#### `BatchSource.h` + `BatchSource.cc`

Scopo del modulo:

- genera batch di job con inter-arrivo esponenziale (media `m`)
- genera dimensione batch discreta uniforme in `[x1, x2]`
- invia i job uno a uno al server, mantenendo semantica batch lato sorgente

Segnali/statistiche emesse:

- `created` (somma job creati)
- `batchSize` (media/istogramma/vettore della dimensione batch)

Dettagli tecnici:

- scheduling con self-message `batchTimer`
- stop opzionale tramite `stopTime`
- timestamp iniziale di ogni job impostato all'arrivo nel sistema

#### `BulkServiceVacationServer.h` + `BulkServiceVacationServer.cc`

Scopo del modulo:

- implementare server bulk con soglie `(a,b)`
- applicare Single Vacation Rule con durata dipendente dalla coda
- applicare N-policy con stato dormant e setup esponenziale

Macchina a stati implementata:

- `IDLE`
- `VACATION`
- `SETUP`
- `BUSY`

Segnali/statistiche emesse:

- `queueLength`
- `numInSystem`
- `busy`
- `serverState`
- `batchServiceSize`
- `serviceTime`
- `vacationDuration`
- `setupDuration`

Formule implementate nel codice C++:

```cpp
// service time
t = (r / b) * sp + U(l, u)

// vacation time
t = ((k + 1) / b) * sv + U(z, w)

// setup time
t = Exp(mean=q)
```

Correzione critica applicata nel server (coerenza `numInSystem` a fine batch):

```cpp
batchBeingServed = 0;
emit(numInSystemSignal, getSystemPopulation());
```

Questa emissione avviene subito dopo il reset del batch in servizio, evitando stime temporali incoerenti della popolazione nel sistema.

---

## 9. Output e Interpretazione Risultati

Dove trovare i risultati:

- scalari OMNeT++: `opp_workspace/modello1/results/*.sca`
- vettori OMNeT++: `opp_workspace/modello1/results/*.vec`
- report Python: `opp_workspace/modello1/analisi/`

File principali generati da `analisi_risultati.py`:

- `analisi/report_finale.csv`: riepilogo finale (`L`, `W`, `rho`, `E[vacation]`, `W_little`, errore Little)
- `analisi/little_check.csv`: verifica della legge di Little usando throughput osservato
- `analisi/risultati_prestazioni.csv`: medie, margini e IC 95% per metrica/config
- `analisi/risultati_dettaglio.csv`: valori run-level (20 run per config)
- `analisi/misure_prestazione.png`: grafico errorbar delle quattro metriche
- `analisi/boxplot_prestazioni.png`: distribuzioni run-level
- `analisi/transiente_transient_m05.png`: transiente per `m=0.5`
- `analisi/transiente_transient_m10.png`: transiente per `m=1.0`
- `analisi/transiente_transient_m14.png`: transiente per `m=1.4`
- `analisi/transiente_transient_m20.png`: transiente per `m=2.0`

Tabella riassuntiva risultati (da `report_finale.csv`):

| m | L | W | rho | E[vacation] | Little error% |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 29.7458 | 5.9159 | 0.8645 | 2.9625 | 0.5960 |
| 1.0 | 16.9191 | 6.4631 | 0.4722 | 2.9518 | 4.7222 |
| 1.4 | 15.1996 | 7.9567 | 0.3387 | 2.9525 | 6.9417 |
| 2.0 | 14.0960 | 10.3269 | 0.2372 | 2.9496 | 9.0210 |

Nota di coerenza:

- `rho < 1` in tutte le configurazioni
- andamento `L` coerente con aumento di `m` (arrivi mediamente piu radi)
- errore Little sotto 10% per tutte le config
- `E[vacation] > 0` e stabile intorno a 2.95s
- check complessivi di coerenza: superati

---

## 10. Troubleshooting

### 1) queueinglib not found al lancio

**Problema**: errore di caricamento libreria `queueinglib` o moduli NED non risolti.

**Causa**: `-n`/`-l` mancanti oppure ambiente OMNeT++ non inizializzato.

**Soluzione**:

```bash
cd opp_workspace/modello1
OPPDIR="../omnetpp-6.3.0"; source "$OPPDIR/setenv" -q
./modello1 -u Cmdenv -c m10 -r 0 -n ".:$OPPDIR/samples/queueinglib" -l "$OPPDIR/samples/queueinglib/queueinglib" --result-dir=results
```

### 2) `make: command not found`

**Problema**: impossibile compilare (`make` non presente).

**Causa**: toolchain build non installata sul sistema.

**Soluzione**:

```bash
sudo apt update && sudo apt install -y build-essential
```

### 3) cartella `results/` vuota dopo simulazione

**Problema**: nessun `.sca/.vec` generato.

**Causa**: run fallita o eseguibile non compilato/cmd errato.

**Soluzione**:

```bash
cd opp_workspace/modello1
make -j4 && ./run_all.sh
```

### 4) Python `ModuleNotFoundError`

**Problema**: librerie Python mancanti durante analisi.

**Causa**: virtualenv non attivo o dipendenze non installate.

**Soluzione**:

```bash
source .venv/bin/activate
python -m pip install numpy pandas scipy matplotlib
```

### 5) grafici non generati (`matplotlib` backend)

**Problema**: assenza output PNG o errori backend grafico.

**Causa**: ambiente headless o backend non compatibile.

**Soluzione**:

```bash
cd opp_workspace/modello1
python -c "import matplotlib; print(matplotlib.get_backend())"
python3 analisi_risultati.py
```

Nota: lo script imposta gia `matplotlib.use('Agg')`, quindi e adatto a server/headless.

### 6) simulazione molto lenta

**Problema**: tempi lunghi di esecuzione.

**Causa**: uso interfaccia grafica o parametri run estesi.

**Soluzione**:

```bash
cd opp_workspace/modello1
./modello1 -u Cmdenv -c m10 -r 0 -n ".:../omnetpp-6.3.0/samples/queueinglib" -l "../omnetpp-6.3.0/samples/queueinglib/queueinglib" --result-dir=results
```

Suggerimento: mantenere `Cmdenv` per tutte le batch run, evitare `Qtenv` nelle 80 run.

---

## 11. Riferimento Bibliografico

P. Karan, S. Pradhan, *Analysis of a queue-length-dependent vacation queue with bulk service, N-policy, set-up time and cost optimization*, Performance Evaluation 167 (2025) 102459. https://doi.org/10.1016/j.peva.2024.102459

Riferimenti tecnici:

- Documentazione OMNeT++: https://doc.omnetpp.org/omnetpp/manual/
- Download OMNeT++: https://omnetpp.org/download/
- Queueinglib (sample library in OMNeT++ tree): `samples/queueinglib` sotto installazione OMNeT++

---

### Appendice: comandi sintetici utili

Build e test rapido:

```bash
cd opp_workspace/modello1
make -j4
./modello1 --version
```

Run completo e analisi:

```bash
cd opp_workspace/modello1
./run_all.sh
python3 analisi_risultati.py
```

Pulizia output run (opzionale):

```bash
cd opp_workspace/modello1
rm -f results/*.sca results/*.vec results/*.vci
```

Verifica ultimo report:

```python
import pandas as pd
df = pd.read_csv("opp_workspace/modello1/analisi/report_finale.csv", sep=';')
print(df)
```
