#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DiscoveryLastFM.py · v1.7.7
– Integra Last.fm, MusicBrainz e Headphones per scoprire e accodare album
– Usa Release Group ID (RGID) quando possibile, fallback su Release-ID
– Evita duplicati con controllo getAlbum e registro persistente added_albums
– Ripristina queueAlbum su studio albums correggendo il fetch di secondary-types
"""

# ─────────────────── CONFIG ───────────────────
# Try to import configuration from config.py, fallback to defaults
try:
    from config import *
except ImportError:
    print("Warning: config.py not found. Using example values.")
    print("Please copy config.example.py to config.py and update with your credentials.")
    # Default/example values - these should be overridden in config.py
    LASTFM_USERNAME = "your_lastfm_username"
    LASTFM_API_KEY = "your_lastfm_api_key"
    HP_API_KEY = "your_headphones_api_key"
    HP_ENDPOINT = "http://your-headphones-server:port"

# Default configuration values (can be overridden in config.py)
if 'RECENT_MONTHS' not in globals():
    RECENT_MONTHS = 3
if 'MIN_PLAYS' not in globals():
    MIN_PLAYS = 20
if 'REQUEST_LIMIT' not in globals():
    REQUEST_LIMIT = 1/5
if 'MBZ_DELAY' not in globals():
    MBZ_DELAY = 1.1
if 'SIMILAR_MATCH_MIN' not in globals():
    SIMILAR_MATCH_MIN = 0.46
if 'MAX_SIMILAR_PER_ART' not in globals():
    MAX_SIMILAR_PER_ART = 20
if 'MAX_POP_ALBUMS' not in globals():
    MAX_POP_ALBUMS = 5
if 'CACHE_TTL_HOURS' not in globals():
    CACHE_TTL_HOURS = 24
if 'DEBUG_PRINT' not in globals():
    DEBUG_PRINT = True


BAD_SEC = {
    "Compilation", "Live", "Remix", "Soundtrack", "DJ-Mix",
    "Mixtape/Street", "EP", "Single", "Interview", "Audiobook"
}

# ─────────────────── LIBRARIE ───────────────────
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import json, logging, sys, time, urllib.parse, requests

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR / "lastfm_similar_cache.json"
LOG_DIR = SCRIPT_DIR / "log"
LOG_FILE = LOG_DIR / "discover.log"

# ─────────────────── LOGGER ───────────────────
# Assicura che la directory di log esista
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ],
)
log = logging.getLogger("lfm2hp")

def dprint(msg):
    if DEBUG_PRINT:
        print(f"[DEBUG] {msg}")

# ──────────── RATE LIMIT WRAPPERS ────────────
def rate_limited(delay):
    def decorator(fn):
        last = 0
        def wrapped(*args, **kwargs):
            nonlocal last
            wait = delay - (time.time() - last)
            if wait > 0:
                dprint(f"sleep {wait:.2f}s ({fn.__name__})")
                time.sleep(wait)
            result = fn(*args, **kwargs)
            last = time.time()
            return result
        return wrapped
    return decorator

@rate_limited(REQUEST_LIMIT)
def lf_request(method, **params):
    # Last.fm API call
    for alt, real in (("from_", "from"), ("to_", "to")):
        if alt in params:
            params[real] = params.pop(alt)
    url = "https://ws.audioscrobbler.com/2.0/"
    params |= {"method": method, "api_key": LASTFM_API_KEY, "format": "json"}
    dprint(f"LFM → {url}?{urllib.parse.urlencode(params)}")
    try:
        r = requests.get(url, params=params, timeout=30)
        dprint(f"LFM ← {r.status_code}")
        r.raise_for_status()
        j = r.json()
        return None if "error" in j else j
    except Exception as e:
        dprint(f"LFM ERR {e}")
        return None

@rate_limited(MBZ_DELAY)

def mbz_request(path, **params):
    # MusicBrainz API call con gestione retry
    base = "https://musicbrainz.org/ws/2/"
    params.setdefault("fmt", "json")
    url = f"{base}{path}"
    
    # Configurazione retry per MusicBrainz
    max_retries = 2
    retry_delay = 2  # secondi
    
    for attempt in range(max_retries):
        try:
            dprint(f"MBZ → {url}?{urllib.parse.urlencode(params)} (tentativo {attempt+1}/{max_retries})")
            r = requests.get(
                url, params=params, timeout=30,
                headers={"User-Agent": "lfm2hp/1.7.6 (mr.roboto@example.com)"}
            )
            dprint(f"MBZ ← {r.status_code}")
            
            # Gestione del rate limiting di MusicBrainz (codice 429)
            if r.status_code == 429 and attempt < max_retries - 1:
                wait_time = int(r.headers.get('Retry-After', retry_delay * 2))
                log.warning(f"Rate limit MusicBrainz, attendo {wait_time}s")
                time.sleep(wait_time)
                continue
                
            r.raise_for_status()
            return r.json()
        except Exception as e:
            dprint(f"MBZ ERR {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return None

# Aggiungi dopo le importazioni esistenti
from time import sleep

# Modifica la funzione hp_api con retry e timeout aumentato
def hp_api(cmd, **params):
    """Chiamata alle API di Headphones con gestione retry e timeout esteso"""
    base = HP_ENDPOINT.rstrip("/") + "/api"
    params |= {"cmd": cmd, "apikey": HP_API_KEY}
    
    # Configurazione retry
    max_retries = 3
    retry_delay = 5  # secondi
    
    # Timeout più lungo per operazioni critiche
    if cmd in ["forceSearch"]:
        timeout = 300
    elif cmd in ["addAlbum", "queueAlbum", "addArtist"]:
        timeout = 120  # aumentato per operazioni che creano timeout frequentemente
    else:
        timeout = 60
        
    for attempt in range(max_retries):
        try:
            dprint(f"HP  → {base}?{urllib.parse.urlencode(params)} (tentativo {attempt+1}/{max_retries})")
            r = requests.get(base, params=params, timeout=timeout)
            dprint(f"HP  ← {r.status_code}")
            
            # Gestione errori 500 specifici con retry
            if r.status_code == 500 and cmd == "queueAlbum":
                log.warning(f"Errore 500 per queueAlbum, tentativo {attempt+1}/{max_retries}")
                time.sleep(retry_delay * (attempt + 1))  # Backoff esponenziale
                continue
                
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "")
            return r.json() if ct.startswith("application/json") else r.text
        
        except requests.exceptions.Timeout:
            log.warning(f"Timeout per {cmd}, tentativo {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
        
        except Exception as e:
            log.warning(f"Headphones {cmd} fallito: {e}, tentativo {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                log.error(f"Tutti i tentativi falliti per {cmd}: {e}")
                return None
    
    return None



def album_exists(mbid, added):
    """Verifica se un album esiste già in Headphones"""
    if mbid in added:
        return True
        
    response = hp_api("getAlbum", id=mbid)
    if not response or not isinstance(response, dict):
        return False
        
    # Un album non esistente restituisce array vuoti
    album = response.get("album", [])
    tracks = response.get("tracks", [])
    
    # Se entrambi gli array sono vuoti, l'album non esiste
    if not album and not tracks:
        dprint(f"Album {mbid} non trovato in Headphones")
        return False
        
    # Se abbiamo dati in uno dei due array, l'album esiste
    return True

# Aggiorniamo anche la funzione verify_album_status
def verify_album_status(album_id):
    """Verifica lo stato di un album in Headphones"""
    response = hp_api("getAlbum", id=album_id)
    if not response or not isinstance(response, dict):
        return None
        
    album_data = response.get("album", {})
    
    # Se l'album è vuoto ma abbiamo tracks, consideriamo l'album come esistente
    if not album_data and response.get("tracks"):
        album_data = {"status": "Unknown"}
        
    if not album_data:
        return None
        
    valid_states = ["Downloaded", "Completed", "Processed"]
    
    return {
        "status": album_data.get("status"),
        "downloaded": album_data.get("status") in valid_states,
        "exists": True
    }

def wait_for_album_completion(album_id, timeout=300):
    """
    Attende il completamento del download di un album
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = verify_album_status(album_id)
        if not status:
            return False
        if status["downloaded"]:
            return True
        time.sleep(30)
    return False

# ──────────── UTIL MBID ────────────

def release_to_rg(release_id):
    data = mbz_request(f"release/{release_id}", inc="release-groups")
    if data and "release-group" in data:
        return data["release-group"]["id"]
    fallback = mbz_request(f"release-group/{release_id}")
    return release_id if fallback else None

def is_studio_rg(rg_id):
    """
    Verifica se una release-group è un album studio su MusicBrainz.
    Logga sempre i campi primary-type e secondary-types per debug.
    """
    data = mbz_request(f"release-group/{rg_id}")
    if not data:
        log.debug(f"Release-group {rg_id}: dati non trovati")
        return None
    primary = data.get("primary-type")
    secondary = data.get("secondary-types", [])
    log.debug(f"Release-group {rg_id}: primary-type={primary}, secondary-types={secondary}")
    if primary != "Album":
        return False
    return set(secondary).isdisjoint(BAD_SEC)

def top_albums(artist_id):
    js = lf_request("artist.getTopAlbums", mbid=artist_id, limit=MAX_POP_ALBUMS*2)
    if not js:
        return []
    arr = js.get("topalbums", {}).get("album", [])
    albs = [(a["mbid"], int(a.get("playcount", 0))) for a in arr if a.get("mbid")]
    albs.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in albs[:MAX_POP_ALBUMS]]

# Funzione album_exists già definita sopra

# ──────────── CACHE ────────────

def load_cache():
    """
    Carica o crea il file cache JSON se non esiste
    """
    try:
        # Verifica se il file esiste
        if not CACHE_FILE.exists():
            # Crea la directory padre se non esiste
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Crea un nuovo file cache con struttura di default
            default_cache = {
                "similar_cache": {},
                "added_albums": []
            }
            # Salva il file cache di default
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(default_cache, f, indent=2)
            return default_cache
            
        # Se il file esiste, caricalo
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
            
    except Exception as e:
        log.warning(f"Errore nel caricamento della cache: {str(e)}")
        c = {}
        
    # Assicurati che tutte le chiavi necessarie esistano
    c.setdefault("similar_cache", {})
    c.setdefault("added_albums", [])
    
    return c

def save_cache(c):
    try:
        tmp = CACHE_FILE.with_suffix(".tmp")
        json.dump(c, open(tmp, "w"))
        tmp.replace(CACHE_FILE)
    except Exception as e:
        log.error(f"Errore durante il salvataggio della cache: {str(e)}")

def cached_similars(cache, mbid):
    e = cache["similar_cache"].get(mbid)
    if e and (time.time() - e["ts"]) / 3600 <= CACHE_TTL_HOURS:
        return e["data"]

# ──────────── RECENT TRACKS ────────────
def recent_artists(minp=MIN_PLAYS, months=RECENT_MONTHS):
    since = int((datetime.utcnow() - timedelta(days=30 * months)).timestamp())
    counts = defaultdict(int)
    page = 1
    while True:
        js = lf_request(
            "user.getRecentTracks", user=LASTFM_USERNAME,
            limit=200, page=page, from_=since
        )
        if not js:
            break
        for t in js["recenttracks"]["track"]:
            a = t["artist"]
            counts[(a["#text"], a.get("mbid", ""))] += 1
        total = int(js["recenttracks"]["@attr"]["totalPages"])
        if page >= total:
            break
        page += 1
    return [(n, m) for (n, m), c in counts.items() if c >= minp]

# ──────────── MAIN SYNC ────────────
def sync():
    """
    Funzione principale di sincronizzazione con debug e gestione errori.
    """
    start_time = time.time()
    try:
        cache = load_cache()
        added_albums = set(cache.get("added_albums", []))

        recent = recent_artists()
        log.info("Analizzo %d artisti...", len(recent))

        seen = set()
        fallback_ids = []
        success_count = 0
        error_count = 0
        skipped_count = 0

        for name, aid in recent:
            if not aid:
                continue

            log.info(f"Processo artista: {name} ({aid})")

            # Aggiungi artista principale (solo parametri previsti)
            result = hp_api("addArtist", id=aid)
            # Puoi lasciare il debug, ma togli parametri extra
            hp_api("refreshArtist", id=aid)

            if not result:
                log.error(f"Impossibile aggiungere l'artista {name} ({aid})")
                error_count += 1
                continue

            # Gestione artisti simili
            sims = cached_similars(cache, aid)
            if not sims:
                log.info(f"Cerco artisti simili per {name}...")
                js = lf_request("artist.getSimilar", mbid=aid, limit=50)
                sims = js.get("similarartists", {}).get("artist", []) if js else []
                cache["similar_cache"][aid] = {"ts": time.time(), "data": sims}

            proc = 0
            for s in sims:
                sim_name = s.get("name", "Sconosciuto")
                sid = s.get("mbid")
                sim_match = float(s.get("match", 0))

                if proc >= MAX_SIMILAR_PER_ART:
                    log.debug(f"Scarto {sim_name} ({sid}): superato MAX_SIMILAR_PER_ART")
                    break
                if not sid:
                    log.debug(f"Scarto {sim_name}: MBID mancante")
                    continue
                if sid in seen:
                    log.debug(f"Scarto {sim_name} ({sid}): già processato")
                    continue
                if sim_match < SIMILAR_MATCH_MIN:
                    log.debug(f"Scarto {sim_name} ({sid}): match troppo basso ({sim_match})")
                    continue

                seen.add(sid)
                proc += 1
                log.info(f"Processo artista simile: {sim_name} ({sid})")

                # Aggiungi artista simile (solo parametri previsti)
                result = hp_api("addArtist", id=sid)
                hp_api("refreshArtist", id=sid)

                if not result:
                    log.error(f"Impossibile aggiungere l'artista simile {sim_name} ({sid})")
                    error_count += 1
                    continue

                # Processa album dell'artista simile
                albums = top_albums(sid)
                log.info(f"Trovati {len(albums)} album per {sim_name}")

                # Recupera anche la lista originale con titoli
                js_albums = lf_request("artist.getTopAlbums", mbid=sid, limit=MAX_POP_ALBUMS*2)
                albums_raw = js_albums.get("topalbums", {}).get("album", []) if js_albums else []
                mbid_to_title = {a.get("mbid"): a.get("name") for a in albums_raw if a.get("mbid")}

                for rel_id in albums:
                    rg_id = release_to_rg(rel_id)
                    title = mbid_to_title.get(rel_id, rel_id)
                    if not rg_id:
                        # Fallback: MBID mancante, usa nome artista e titolo album
                        log.info(f"Fallback: aggiungo album senza MBID (artista: {sim_name}, titolo: {title})")
                        hp_api("addAlbum", artistName=sim_name, albumTitle=title)
                        hp_api("queueAlbum", artistName=sim_name, albumTitle=title, new=True)
                        continue

                    if album_exists(rg_id, added_albums) or album_exists(rel_id, added_albums):
                        log.debug(f"Album {rel_id} già esistente")
                        skipped_count += 1
                        continue

                    studio = is_studio_rg(rg_id)
                    if studio is False:
                        log.debug(f"Album {rel_id} non è studio")
                        continue

                    try:
                        # Se non sappiamo se è studio, usa il release ID
                        if studio is None:
                            log.info(f"Aggiungo album (fallback) {rel_id}")
                            hp_api("addAlbum", id=rel_id)
                            hp_api("queueAlbum", id=rel_id, new=True)
                            added_albums.add(rel_id)
                            fallback_ids.append(rel_id)
                        else:
                            log.info(f"Aggiungo album {rg_id}")
                            hp_api("addAlbum", id=rg_id)
                            hp_api("queueAlbum", id=rg_id, new=True)
                            added_albums.add(rg_id)

                        success_count += 1

                        # Salva cache dopo ogni album aggiunto
                        cache["added_albums"] = list(added_albums)
                        save_cache(cache)

                    except Exception as e:
                        error_count += 1
                        log.error(f"Errore durante l'aggiunta dell'album {rel_id or rg_id}: {str(e)}")

        # Aggiornamento finale del database
        if fallback_ids:
            log.info(f"Aggiornamento finale per {len(fallback_ids)} album...")
            hp_api("forceSearch")

        # Statistiche finali
        elapsed_time = time.time() - start_time
        log.info("Sync completata in %.1f minuti. Statistiche:", elapsed_time / 60)
        log.info("- Album aggiunti con successo: %d", success_count)
        log.info("- Errori riscontrati: %d", error_count)
        log.info("- Album skippati: %d", skipped_count)
        log.info("- Album in fallback: %d", len(fallback_ids))
        log.info("- Artisti processati: %d", len(seen))

    except Exception as e:
        log.error(f"Errore durante la sincronizzazione: {str(e)}")
        raise
    finally:
        # Salvataggio finale della cache
        try:
            cache["added_albums"] = list(added_albums)
            save_cache(cache)
        except Exception as e:
            log.error(f"Errore nel salvataggio finale della cache: {str(e)}")


# ──────────── ENTRYPOINT ────────────
if __name__ == "__main__":
    try:
        sync()
    except KeyboardInterrupt:
        log.warning("Interrotto.")
