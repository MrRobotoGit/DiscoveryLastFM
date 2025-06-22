# Changelog

Tutte le modifiche importanti a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.6] - 2025-06-22

### Added
- Creata struttura di directory dedicata per il progetto
- Aggiunto sistema di logging su file in `log/discover.log`
- Aggiunta documentazione completa in `CLAUDE.md`
- Creato questo file CHANGELOG.md

### Changed
- Migrazione da script singolo a struttura di progetto organizzata
- Aggiornati i percorsi di cache e log per utilizzare la nuova struttura
- Migliorato il sistema di logging con output sia su console che su file
- Aggiornato cronjob per utilizzare il nuovo percorso dello script

### Fixed
- Risolti problemi di organizzazione dei file
- Migliorata la manutenibilità del progetto

## [1.7.5] - 2025-06-22

### Fixed
- Rimossa duplicazione della funzione `album_exists`
- Mantenuta la versione più robusta che verifica sia album che tracce

## [1.7.4] - 2025-06-22

### Added
- Sistema di retry automatico per chiamate API fallite
- Backoff esponenziale per gestire sovraccarichi dei server
- Gestione specifica degli errori 500 per `queueAlbum`
- Gestione del rate limiting di MusicBrainz (codice 429)
- Timeout estesi per operazioni critiche (120s per add/queue, 300s per forceSearch)

### Changed
- Migliorata robustezza generale delle chiamate API
- Aggiornato sistema di statistiche con conteggio album skippati
- Aggiunto tracciamento del tempo di esecuzione

### Fixed
- Risolti problemi di timeout frequenti con Headphones
- Migliorata gestione degli errori temporanei di rete
- Ridotti i fallimenti non recuperabili

## [1.7.3] - 2025-06-22

### Changed
- Mantenimento della funzionalità esistente con correzione minori

### Notes
- Versione di base con funzionalità complete di integrazione Last.fm, MusicBrainz e Headphones
- Sistema di cache per artisti simili e album già aggiunti
- Filtro per album studio escludendo compilation, live, EP, etc.
