# CLAUDE.md - Documentazione del progetto DiscoverLastfm

## 🎵 DiscoverLastfm v1.7.6

### 📋 Panoramica del Progetto
DiscoverLastfm è uno strumento di integrazione tra Last.fm, MusicBrainz e Headphones che automatizza la scoperta e l'accodamento di album musicali. Analizza gli ascolti recenti su Last.fm, trova artisti simili, e aggiunge automaticamente i loro album più popolari alla libreria Headphones per il download.

### 🎯 Obiettivi del Progetto
- Automatizzare la scoperta di nuova musica basata sui propri ascolti
- Integrare dati da Last.fm e metadati da MusicBrainz
- Filtrare per trovare album studio di qualità
- Accodare automaticamente gli album in Headphones per il download
- Evitare duplicati con controllo persistente

### 📂 Struttura del Progetto
```
/home/pi/DiscoverLastfm/
├── DiscoverLastfm.py           # Script principale 
├── lastfm_similar_cache.json   # Cache degli artisti simili e album aggiunti
├── log/
│   └── discover.log            # Log delle operazioni 
├── CLAUDE.md                   # Questa documentazione
```

### 🔄 Piano di Migrazione
1. **Creazione directory**:
   ```bash
   mkdir -p /home/pi/DiscoverLastfm/log
   ```

2. **Spostamento files**:
   ```bash
   cp /home/pi/DiscoverLastfm.py /home/pi/DiscoverLastfm/
   cp /home/pi/lastfm_similar_cache.json /home/pi/DiscoverLastfm/ (se esiste)
   ```

3. **Aggiornamento cronjob**:
   ```bash
   crontab -e
   # Sostituire il percorso esistente con:
   # 0 3 * * * python3 /home/pi/DiscoverLastfm/DiscoverLastfm.py >> /home/pi/DiscoverLastfm/log/discover.log 2>&1
   ```

4. **Aggiornamento percorsi nello script**:
   Modificare SCRIPT_DIR e CACHE_FILE nello script per utilizzare i nuovi percorsi.

### 🛠️ Funzionalità Principali
- **Integrazione Last.fm**: Analisi ascolti recenti e scoperta artisti simili
- **Filtro Qualità**: Selezione di soli album studio (escludendo compilation, live, EP, ecc.)
- **Sistema di Cache**: Memorizzazione artisti simili e album aggiunti per evitare richieste duplicate
- **Gestione Rate-Limiting**: Rispetto dei limiti di richieste API
- **Robustezza**: Gestione errori, timeout e retry automatici

### 📊 Parametri Configurabili
- `RECENT_MONTHS`: Mesi di ascolti da considerare (default: 3)
- `MIN_PLAYS`: Minimo numero di riproduzioni per considerare un artista (default: 10)
- `SIMILAR_MATCH_MIN`: Match minimo per considerare un artista simile (default: 0.45)
- `MAX_SIMILAR_PER_ART`: Massimo artisti simili per artista (default: 20)
- `MAX_POP_ALBUMS`: Massimo album popolari per artista (default: 5)

### 🔄 Flusso di Esecuzione
1. Recupero artisti ascoltati di recente su Last.fm
2. Per ogni artista:
   - Aggiunta dell'artista a Headphones
   - Recupero artisti simili (da cache o Last.fm)
   - Aggiunta artisti simili a Headphones
   - Recupero album popolari per ogni artista simile
   - Filtro per mantenere solo album studio
   - Accodamento degli album in Headphones

### 🔧 Ottimizzazioni Implementate
- **Gestione Timeout**: Timeout estesi per operazioni pesanti (120s per add/queue, 300s per forceSearch)
- **Sistema di Retry**: Riprova automatica per richieste fallite con backoff esponenziale
- **Gestione Rate Limit**: Rispetto dei limiti di rate di MusicBrainz
- **Gestione Errori 500**: Retry specifici per errori 500 in queueAlbum
- **Tracciamento Statistiche**: Conteggio dettagliato delle operazioni e tempo di esecuzione

### 📈 Prestazioni Osservate
- **Robustezza**: Significativamente migliorata con le ottimizzazioni implementate
- **Affidabilità**: Capacità di gestire errori temporanei senza interruzioni
- **Rate**: ~2-3 richieste/min per Last.fm, ~20-25 per MusicBrainz, ~10-15 per Headphones

### 🚀 Utilizzo
Eseguire `python3 /home/pi/DiscoverLastfm/DiscoverLastfm.py` per avviare il processo di scoperta.
Il processo è schedulato con cron per esecuzioni giornaliere alle 3:00.

### 📝 Manutenzione e Sviluppo Futuro
- **Batch Processing**: Raggruppare più operazioni per ridurre chiamate API
- **Cache Estesa**: Implementare cache per release-group di MusicBrainz
- **Throttling Dinamico**: Adattare ritardi tra richieste in base al carico server
- **Modalità Ripresa**: Implementare checkpoint per riprendere da interruzioni

---
*Documentazione generata il 22 giugno 2025*
