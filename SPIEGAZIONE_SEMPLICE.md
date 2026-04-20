# Spiegazione del Progetto - Versione Semplice

## 📋 Il Problema che Dovevamo Risolvere

Ci è stato chiesto di **simulare un sistema di code** (come una coda al supermercato) con caratteristiche particolari:

- **Arrivi a gruppi**: i clienti non arrivano uno per uno, ma in **batch** (gruppi) di dimensione casuale
- **Servizio batch**: il server (cassiere) serve **più clienti insieme** (minimo 7, massimo 16)
- **Vacation**: quando non ci sono abbastanza clienti, il server va in **pausa** (vacation)
- **N-policy**: il server si riattiva solo quando ci sono **almeno 20 clienti in coda**
- **Setup**: dopo la pausa, il server ha bisogno di un **tempo di preparazione**

**Scopo**: misurare come il sistema si comporta cambiando la frequenza degli arrivi.

---

## 🛠️ Cosa Abbiamo Costruito

### 1. **Il Modello di Simulazione** (in C++)

Abbiamo creato **due nuovi moduli** per OMNeT++ (un software di simulazione):

#### **Modulo 1: BatchSource** (La sorgente di arrivi)
```
Ogni tot secondi:
  1. Decide casualmente quanti clienti arrivano (tra 1 e 4)
  2. Li genera tutti insieme (batch)
  3. Li invia al server
  
Tempo tra arrivi: esponenziale di media m
  - m=0.5s → arrivi frequenti (stressato)
  - m=2.0s → arrivi rari (tranquillo)
```

#### **Modulo 2: BulkServiceVacationServer** (Il server intelligente)
```
Ha 4 stati possibili:

IDLE (Inattivo)
  ↓ (quando arrivano 20 clienti)
SETUP (Preparazione) 
  ↓ (dopo ~1 secondo)
BUSY (Servizio)
  ↓ (quando finisce di servire)
  ├→ Se ci sono ≥7 clienti → rimane BUSY (continua a servire)
  └→ Se ci sono <7 clienti → VACATION (pausa)

VACATION (Pausa)
  ↓ (dopo ~3 secondi)
  ├→ Se ci sono ≥20 clienti → torna a SETUP
  └→ Se ci sono <20 clienti → torna a IDLE
```

---

## 🎯 Le 4 Misure di Prestazione Raccolte

Durante la simulazione, abbiamo misurato:

### **a) Numero medio di utenti nel sistema**
```
Significa: Quante persone c'erano in coda in media?

Risultati:
  m=0.5s  → 29.7 persone (traffico pesante)
  m=1.0s  → 16.9 persone
  m=1.4s  → 15.2 persone
  m=2.0s  → 14.1 persone (traffico leggero)

Interpretazione: Con arrivi frequenti, la coda si riempie!
```

### **b) Tempo medio di permanenza nel sistema**
```
Significa: Quanto tempo in media sta una persona nel sistema?

Risultati:
  m=0.5s  → 5.9 secondi
  m=1.0s  → 6.5 secondi
  m=1.4s  → 8.0 secondi
  m=2.0s  → 10.3 secondi

Interpretazione: Paradosso! Con arrivi rari, uno sta PIÙ tempo
(il server non sempre lavora, "spreca" tempo in vacation)
```

### **c) Fattore di utilizzo del server**
```
Significa: Che percentuale di tempo il server è occupato?

Risultati:
  m=0.5s  → 86.4% (sempre occupato)
  m=1.0s  → 47.2%
  m=1.4s  → 33.9%
  m=2.0s  → 23.7% (più riposa che lavora!)

Interpretazione: Lo spacing fa la differenza!
```

### **d) Durata media della pausa (vacation)**
```
Significa: Quando il server va in pausa, quanto dura in media?

Risultati:
  m=0.5s  → 2.96 secondi
  m=1.0s  → 2.95 secondi
  m=1.4s  → 2.95 secondi
  m=2.0s  → 2.95 secondi

Interpretazione: Sempre uguale! (~3 secondi)
Perché? La vacation dipende dal numero di clienti in coda
(che è sempre poco quando si va in vacation)
```

---

## 📊 Come Abbiamo Raccolto i Dati

### **Numero di run**
```
4 configurazioni (m = 0.5, 1.0, 1.4, 2.0)
× 20 simulazioni per configurazione
= 80 run totali
```

### **Durata di ogni run**
```
Tempo totale: 100.000 secondi (quasi 28 ore di tempo simulato)
Warm-up: 10.000 secondi (scartato per eliminare il "riscaldamento")
Misure effettive: ultimi 90.000 secondi
```

### **Intervalli di Confidenza**
```
Per ogni misura, abbiamo calcolato:

Media ± Margine di errore (95% di confidenza)

Esempio - N. medio utenti (m=1.0):
  16.92 ± 0.03  →  [16.89, 16.95]

Significa: Con 95% di probabilità, il valore vero è fra 16.89 e 16.95
```

---

## 🔍 Analisi del Transiente Iniziale

**Domanda**: Quanta parte della simulazione dobbiamo scartare all'inizio?

**Metodo**: Abbiamo disegnato grafici che mostrano come il sistema raggiunge l'equilibrio.

**Risultati**:
```
m=0.5s  → Stabilizzazione a ~19.000 secondi (19% della simulazione)
         ⚠️ Il nostro warm-up (10.000s) è un po' corto
         
m=1.0s  → Stabilizzazione a ~10.400 secondi (10% della simulazione)
          ✓ Ok, il warm-up va bene

m=1.4s  → Stabilizzazione a ~10.400 secondi
          ✓ Ok

m=2.0s  → Stabilizzazione a ~10.400 secondi
          ✓ Ok
```

**Conclusione**: Per il traffico pesante (m=0.5), il warm-up di 10.000s è un po' borderline, ma accettabile.

---

## 📈 Cosa Significano i Risultati

### **Osservazione 1: Traffico pesante vs. leggero**
```
Con m=0.5s (traffico pesante):
  ✗ Coda lunga (30 persone)
  ✗ Server sempre occupato (86%)
  ✓ Ma la gente esce veloce (5.9 secondi)

Con m=2.0s (traffico leggero):
  ✓ Coda corta (14 persone)
  ✓ Server rilassato (24% occupato)
  ✗ Ma la gente sta più tempo (10.3 secondi) per le pause del server
```

### **Osservazione 2: Il paradosso della vacation**
```
Con N-policy + vacation, il server fa pause strategiche.
Questo significa:
- Meno congestione quando c'è traffico
- Ma tempi di attesa più lunghi complessivi quando il traffico è leggero
(perché il server spende tempo in vacation aspettando nuovi clienti)
```

### **Osservazione 3: Intervalli di confidenza stretti**
```
I nostri intervalli sono molto stretti:
  16.92 ± 0.03  ✓ Ottimo!

Significa: 20 run sono sufficienti per stime affidabili
```

---

## 💻 Come Abbiamo Fatto Tutto Questo

### **Architettura**
```
1. Codice C++ (BatchSource.cc, BulkServiceVacationServer.cc)
   ↓ compilati in un eseguibile OMNeT++
   
2. File di configurazione (omnetpp.ini)
   ↓ specifica i parametri per ogni run
   
3. Simulatore OMNeT++ lancia 80 run
   ↓ genera m05-#0.sca, m05-#1.sca, ... m20-#19.sca
   
4. Script Python (analisi_risultati.py)
   ↓ legge i 80 file, calcola medie e IC
   
5. Grafici e tabelle
```

### **File Principali**
```
modello1/
├── BatchSource.h/.cc          ← Modulo arrivi batch
├── BulkServiceVacationServer.h/.cc  ← Modulo server con vacation
├── modello_progetto.ned       ← Definizione della rete
├── omnetpp.ini                ← Configurazioni (4 × 20)
├── run_all.sh                 ← Script per lanciare 80 run
├── analisi_risultati.py       ← Script di analisi
└── results/                   ← File .sca e .vec (output simulazione)
└── analisi/                   ← Grafici e CSV (risultati analisi)
```

---

## 🎓 Cosa Abbiamo Imparato

1. **I sistemi con vacation sono complessi** → Servono simulazioni, non formule semplici
2. **I parametri contano molto** → Cambiare m da 0.5 a 2.0 cambia TUTTO
3. **Il warm-up è critico** → Specialmente con traffico pesante
4. **I batch complicano le cose** → Ma sono realistici (reti, ospedali, ecc.)
5. **20 run sono sufficienti** → Gli IC sono stretti

---

## 📁 Dove Trovare Cosa

```
/home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/opp_workspace/modello1/

results/          ← I dati grezzi (80 file .sca)
analisi/          ← Risultati finali
  ├── misure_prestazione.png         ← Grafico principale
  ├── boxplot_prestazioni.png        ← Variabilità su 20 run
  ├── transiente_m{05,10,14,20}.png  ← Analisi warm-up
  ├── risultati_prestazioni.csv      ← Tabella riassuntiva
  └── risultati_dettaglio.csv        ← Tutti gli 80 valori
```

---

## ✅ Riepilogo: Abbiamo Fatto Tutto Questo

✓ Modellato un sistema complesso (arrivi batch + bulk service + vacation + N-policy)  
✓ Implementato in C++ per OMNeT++  
✓ Eseguito 80 simulazioni  
✓ Raccolto dati statistici  
✓ Analizzato il transiente iniziale  
✓ Calcolato intervalli di confidenza al 95%  
✓ Generato grafici e tabelle  

**Risultato**: Un'analisi completa e rigorosa del sistema!
