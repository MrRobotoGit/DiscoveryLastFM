#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DiscoveryLastFM.py · v2.0.0
– Integrazione Lidarr/Headphones tramite service layer modulare
– Supporto per entrambi i servizi con switch via configurazione
– Mantiene identico workflow e compatibilità cache v1.7.x
– Zero breaking changes per configurazioni esistenti
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
    MUSIC_SERVICE = "headphones"

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
if 'MUSIC_SERVICE' not in globals():
    MUSIC_SERVICE = "headphones"

BAD_SEC = {
    "Compilation", "Live", "Remix", "Soundtrack", "DJ-Mix",
    "Mixtape/Street", "EP", "Single", "Interview", "Audiobook"
}

# ─────────────────── LIBRARIE ───────────────────
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import json, logging, sys, time, urllib.parse, requests

# Import nuovo service layer
from services import MusicServiceFactory, ArtistInfo, AlbumInfo, ServiceError, ConfigurationError

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
    # Last.fm API call - IDENTICA alla v1.7.x
    for alt, real in (("from_", "from"), ("to_", "to")):
        if alt in params:
            params[real] = params.pop(alt)
    
    base = "https://ws.audioscrobbler.com/2.0/"
    params |= {"method": method, "api_key": LASTFM_API_KEY, "format": "json"}
    
    dprint(f"LF  → {base}?{urllib.parse.urlencode(params)}")
    r = requests.get(base, params=params, timeout=15)
    dprint(f"LF  ← {r.status_code}")
    
    if r.status_code != 200:
        log.warning(f"Last.fm HTTP {r.status_code}: {r.text[:200]}")
        return None
    
    try:
        return r.json()
    except:
        log.warning(f"Last.fm invalid JSON: {r.text[:200]}")
        return None

@rate_limited(MBZ_DELAY)
def mbz_request(path, **params):
    # MusicBrainz API call - IDENTICA alla v1.7.x
    base = "https://musicbrainz.org/ws/2/"
    params |= {"fmt": "json"}
    
    headers = {"User-Agent": "DiscoveryLastFM/2.0.0 ( mrroboto@example.com )"}
    
    dprint(f"MBZ → {base}{path}?{urllib.parse.urlencode(params)}")
    r = requests.get(base + path, params=params, headers=headers, timeout=30)
    dprint(f"MBZ ← {r.status_code}")
    
    if r.status_code != 200:
        log.warning(f"MusicBrainz HTTP {r.status_code}: {r.text[:200]}")
        return None
    
    try:
        return r.json()
    except:
        log.warning(f"MusicBrainz invalid JSON: {r.text[:200]}")
        return None

# ────────────── CORE FUNCTIONS (IDENTICHE) ──────────────
def load_cache():
    """Carica cache da file JSON"""
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            
        # Assicura che added_albums sia un set
        if "added_albums" in cache and isinstance(cache["added_albums"], list):
            cache["added_albums"] = set(cache["added_albums"])
        elif "added_albums" not in cache:
            cache["added_albums"] = set()
            
        return cache
    except:
        return {"similar_cache": {}, "added_albums": set()}

def save_cache(cache):
    """Salva cache su file JSON"""
    try:
        # Converte set in list per JSON
        cache_copy = cache.copy()
        if "added_albums" in cache_copy:
            cache_copy["added_albums"] = list(cache_copy["added_albums"])
            
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_copy, f, indent=2)
    except Exception as e:
        log.error(f"Errore salvataggio cache: {e}")

def recent_artists():
    """Ottiene artisti ascoltati di recente - IDENTICA"""
    end = int(time.time())
    start = end - (RECENT_MONTHS * 30 * 24 * 3600)
    
    js = lf_request("user.getRecentTracks", user=LASTFM_USERNAME, from_=start, to_=end, limit=1000)
    if not js:
        return []
    
    tracks = js.get("recenttracks", {}).get("track", [])
    artist_plays = defaultdict(int)
    
    for t in tracks:
        if isinstance(t, dict):
            artist = t.get("artist", {})
            name = artist.get("#text", "") if isinstance(artist, dict) else str(artist)
            if name:
                artist_plays[name] += 1
    
    # Ottieni MBID per ogni artista
    result = []
    for name, plays in artist_plays.items():
        if plays >= MIN_PLAYS:
            js = lf_request("artist.getInfo", artist=name)
            if js:
                mbid = js.get("artist", {}).get("mbid")
                if mbid:
                    result.append((name, mbid))
    
    log.info(f"Trovati {len(result)} artisti recenti con ≥{MIN_PLAYS} riproduzioni")
    return result

def cached_similars(cache, aid):
    """Controlla cache artisti simili con TTL - IDENTICA"""
    if aid not in cache["similar_cache"]:
        return None
    
    entry = cache["similar_cache"][aid]
    age_hours = (time.time() - entry["ts"]) / 3600
    
    if age_hours > CACHE_TTL_HOURS:
        dprint(f"Cache scaduta per {aid} ({age_hours:.1f}h)")
        return None
    
    return entry["data"]

def top_albums(artist_mbid):
    """Ottiene album popolari filtrati - IDENTICA"""
    js = lf_request("artist.getTopAlbums", mbid=artist_mbid, limit=MAX_POP_ALBUMS*2)
    if not js:
        return []
    
    albums = js.get("topalbums", {}).get("album", [])
    return [a.get("mbid") for a in albums if a.get("mbid")][:MAX_POP_ALBUMS]

def release_to_rg(rel_id):
    """Converte Release ID in Release Group ID - IDENTICA"""
    if not rel_id:
        return None
    
    js = mbz_request(f"release/{rel_id}", inc="release-groups")
    if js and "release-group" in js:
        return js["release-group"]["id"]
    return None

def is_studio_rg(rg_id):
    """Verifica se è album studio - IDENTICA"""
    if not rg_id:
        return None
    
    js = mbz_request(f"release-group/{rg_id}")
    if not js:
        return None
    
    # Controlla primary type
    primary = js.get("primary-type")
    if primary != "Album":
        return False
    
    # Controlla secondary types
    secondary = js.get("secondary-types", [])
    if any(s in BAD_SEC for s in secondary):
        return False
    
    return True

# ────────────── MUSIC SERVICE INTEGRATION ──────────────
def validate_configuration():
    """Validazione estesa per tutti i servizi"""
    config_dict = {k: v for k, v in globals().items() if k.isupper()}
    service_type = config_dict.get("MUSIC_SERVICE", "headphones")
    
    # Validazione servizio specifico
    if not MusicServiceFactory.validate_service_config(service_type, config_dict):
        available = ", ".join(MusicServiceFactory.get_available_services())
        raise ConfigurationError(
            f"Invalid configuration for {service_type}. "
            f"Available services: {available}"
        )
    
    log.info(f"Configuration validated for {service_type}")

def sync():
    """Sync function modificata per service abstraction"""
    start_time = time.time()
    
    try:
        # Inizializzazione servizio
        config_dict = {k: v for k, v in globals().items() if k.isupper()}
        service_type = config_dict.get("MUSIC_SERVICE", "headphones")
        
        music_service = MusicServiceFactory.create_service(service_type, config_dict)
        log.info(f"Using {service_type} service: {music_service.get_service_info()}")
        
        # Resto del workflow IDENTICO alla v1.7.x
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
            
            # Conversione a structured data
            artist_info = ArtistInfo(mbid=aid, name=name)
            
            # Aggiunta artista (STESSA LOGICA, diversa implementazione)
            if not music_service.add_artist(artist_info):
                log.error(f"Impossibile aggiungere l'artista {name} ({aid})")
                error_count += 1
                continue
            
            # Refresh artista
            music_service.refresh_artist(aid)
            
            # Gestione artisti simili - WORKFLOW IDENTICO
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

                # Aggiunta artista simile con service layer
                similar_artist_info = ArtistInfo(mbid=sid, name=sim_name)
                if not music_service.add_artist(similar_artist_info):
                    log.error(f"Impossibile aggiungere l'artista simile {sim_name} ({sid})")
                    error_count += 1
                    continue
                
                music_service.refresh_artist(sid)

                # Processa album dell'artista simile - LOGICA IDENTICA
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
                        # Per ora skip fallback in service layer - implementazione futura
                        continue

                    # Controlla esistenza album usando service layer
                    if hasattr(music_service, 'album_exists'):
                        # Usa metodo specifico del servizio se disponibile
                        if music_service.album_exists(rg_id, added_albums) or music_service.album_exists(rel_id, added_albums):
                            log.debug(f"Album {rel_id} già esistente")
                            skipped_count += 1
                            continue
                    else:
                        # Fallback per check esistenza
                        if rg_id in added_albums or rel_id in added_albums:
                            log.debug(f"Album {rel_id} già esistente (cache)")
                            skipped_count += 1
                            continue

                    studio = is_studio_rg(rg_id)
                    if studio is False:
                        log.debug(f"Album {rel_id} non è studio")
                        continue

                    try:
                        # Conversione a AlbumInfo per service layer
                        album_info = AlbumInfo(
                            mbid=rg_id if studio else rel_id,
                            title=title,
                            artist_mbid=sid,
                            artist_name=sim_name
                        )
                        
                        # Se non sappiamo se è studio, usa il release ID
                        if studio is None:
                            log.info(f"Aggiungo album (fallback) {rel_id}")
                            album_info.mbid = rel_id
                            fallback_ids.append(rel_id)
                        else:
                            log.info(f"Aggiungo album {rg_id}")
                        
                        # Aggiunta album con service layer
                        if music_service.add_album(album_info):
                            # Queue album
                            music_service.queue_album(album_info, force_new=True)
                            added_albums.add(album_info.mbid)
                            success_count += 1
                            
                            # Salva cache dopo ogni album aggiunto
                            cache["added_albums"] = list(added_albums)
                            save_cache(cache)
                        else:
                            error_count += 1
                            log.error(f"Errore durante l'aggiunta dell'album {album_info.mbid}")

                    except Exception as e:
                        error_count += 1
                        log.error(f"Errore durante l'aggiunta dell'album {rel_id or rg_id}: {e}")

        # Force search finale
        if fallback_ids:
            log.info(f"Aggiornamento finale per {len(fallback_ids)} album...")
            music_service.force_search()
        
        # Statistiche IDENTICHE
        elapsed_time = time.time() - start_time
        log.info("Sync completata in %.1f minuti.", elapsed_time / 60)
        log.info("- Album aggiunti: %d", success_count)
        log.info("- Errori: %d", error_count)
        log.info("- Skippati: %d", skipped_count)
        log.info("- Fallback: %d", len(fallback_ids))
        
    except (ServiceError, ConfigurationError) as e:
        log.error(f"Service error: {e}")
        raise
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise
    finally:
        # Salvataggio cache IDENTICO
        cache["added_albums"] = list(added_albums)
        save_cache(cache)

# Entry point con validation
if __name__ == "__main__":
    try:
        validate_configuration()
        sync()
    except KeyboardInterrupt:
        log.warning("Interrotto.")
    except ConfigurationError as e:
        log.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)