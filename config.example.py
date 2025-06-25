# =================================================================
# DiscoveryLastFM v2.0 Configuration Template
# Copy to config.py and customize with your values
# =================================================================

# === MUSIC SERVICE SELECTION ===
# Choose your music management service
# Options: "headphones", "lidarr"
MUSIC_SERVICE = "headphones"

# === LAST.FM CONFIGURATION ===
LASTFM_USERNAME = "your_lastfm_username"
LASTFM_API_KEY = "your_lastfm_api_key"

# === HEADPHONES CONFIGURATION ===
# Required if MUSIC_SERVICE = "headphones"
HP_API_KEY = "your_headphones_api_key"
HP_ENDPOINT = "http://your-headphones-server:port"

# Headphones Advanced Options
HP_MAX_RETRIES = 3
HP_RETRY_DELAY = 5
HP_TIMEOUT = 60

# === LIDARR CONFIGURATION ===
# Used if MUSIC_SERVICE = "lidarr"
LIDARR_API_KEY = "your_lidarr_api_key"
LIDARR_ENDPOINT = "http://your-lidarr-server:port"
LIDARR_ROOT_FOLDER = "/music"

# Lidarr Profile Configuration
LIDARR_QUALITY_PROFILE_ID = 2  # ID of quality profile (1=Any, 2=Lossless, 3=Standard)
LIDARR_METADATA_PROFILE_ID = 1  # ID of metadata profile (1=Standard, 2=None)

# Lidarr Behavior Configuration
LIDARR_MONITOR_MODE = "all"  # "all", "future", "missing", "existing", "first", "latest", "none"
LIDARR_SEARCH_ON_ADD = True  # Auto-search when adding artists/albums

# Lidarr Advanced Options (UPDATED for better timeout handling)
LIDARR_MAX_RETRIES = 3
LIDARR_RETRY_DELAY = 5
LIDARR_TIMEOUT = 60  # Base timeout - specific operations use longer timeouts automatically

# Performance Notes:
# - artist/lookup and album/lookup operations automatically use 300s timeout
# - Slow operations (>30s) are logged as warnings  
# - Retry delays are increased for lookup timeouts to give server more time

# === DISCOVERY PARAMETERS ===
RECENT_MONTHS = 3              # Months of recent plays to analyze
MIN_PLAYS = 20                 # Minimum plays to consider an artist
SIMILAR_MATCH_MIN = 0.43       # Minimum similarity match threshold
MAX_SIMILAR_PER_ART = 20       # Max similar artists per artist
MAX_POP_ALBUMS = 5             # Max popular albums to fetch per artist
CACHE_TTL_HOURS = 48           # Cache time-to-live in hours

# === API RATE LIMITING ===
REQUEST_LIMIT = 1/5            # Last.fm requests per second (5 requests/5 seconds)
MBZ_DELAY = 1.1                # MusicBrainz delay between requests (seconds)

# === DEBUGGING ===
# DEBUG_PRINT = True             # Enable debug print statements

# === SYSTEM CONFIGURATION ===
VALIDATE_CONFIG_ON_STARTUP = True    # Validate configuration on startup
ENABLE_CACHE_MIGRATION = True        # Auto-migrate cache format if needed

# === AUTO-UPDATE CONFIGURATION ===
# GitHub Auto-Update System (NEW in v2.1.0)
AUTO_UPDATE_ENABLED = False          # Enable automatic update checking
UPDATE_CHECK_INTERVAL_HOURS = 24     # How often to check for updates (hours)
BACKUP_RETENTION_DAYS = 7            # How long to keep backup files (days)
ALLOW_PRERELEASE_UPDATES = False     # Allow installation of pre-release versions

# GitHub Repository Configuration (optional - defaults to official repo)
GITHUB_REPO_OWNER = "MrRobotoGit"    # GitHub username/organization
GITHUB_REPO_NAME = "DiscoveryLastFM"  # Repository name
# GITHUB_TOKEN = "your_github_token"   # Optional: GitHub token for higher rate limits
