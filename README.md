# DiscoveryLastFM   

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0-brightgreen.svg)](CHANGELOG.md)
[![Headphones](https://img.shields.io/badge/service-Headphones-blue.svg)](https://github.com/rembo10/headphones)
[![Lidarr](https://img.shields.io/badge/service-Lidarr-orange.svg)](https://github.com/Lidarr/Lidarr)
[![Star](https://img.shields.io/github/stars/MrRobotoGit/DiscoveryLastFM?style=social)](https://github.com/MrRobotoGit/DiscoveryLastFM)

🎵 **Modern music discovery tool** that integrates Last.fm, MusicBrainz, and **both Headphones & Lidarr** to automatically discover and queue new albums based on your listening history.

## 🚀 What's New in v2.1.0

- **Dual Service Support**: Choose between **Headphones** or **Lidarr** with a single configuration change
- **Modular Architecture**: Clean service layer for easy extensibility
- **Zero Breaking Changes**: Existing Headphones users continue without modifications
- **Advanced Configuration**: Enhanced quality and metadata profile management for Lidarr
- **Robust Error Handling**: Improved retry logic and connection management
- **Service Parity**: Identical functionality across both music management services
- **Auto Update System**: includes a built-in auto-update system

## 🎵 Features

### Core Discovery Engine
- **Smart Discovery**: Analyzes your Last.fm listening history to find similar artists
- **Quality Filtering**: Only queues studio albums, excluding compilations, live albums, EPs, etc.
- **Duplicate Prevention**: Maintains persistent cache to avoid adding albums multiple times
- **Comprehensive Logging**: Detailed logging both to console and file

### Service Integration
- **Dual Service Support**: Seamlessly works with both **Headphones** and **Lidarr**
- **Easy Service Switching**: Change between services with a single configuration parameter
- **Quality Profiles**: Advanced quality and metadata profile management (Lidarr)
- **Folder Management**: Automatic root folder and library organization

### Technical Excellence  
- **Robust API Handling**: Built-in retry mechanisms with exponential backoff
- **Rate Limiting**: Respects API rate limits for all services
- **Modular Architecture**: Clean, extensible service layer design
- **Configuration Validation**: Startup validation ensures proper setup

## 🛠️ How It Works

1. **Fetch Recent Artists**: Retrieves artists you've listened to recently on Last.fm
2. **Find Similar Artists**: Discovers similar artists using Last.fm's recommendation engine  
3. **Add to Music Service**: Automatically adds both original and similar artists to your chosen service (Headphones/Lidarr)
4. **Queue Top Albums**: Fetches and queues the most popular studio albums from each artist
5. **Smart Filtering**: Uses MusicBrainz metadata to filter out non-studio releases
6. **Cache Management**: Maintains cache to optimize performance and avoid duplicates
7. **Service Integration**: Seamlessly works with your chosen music management service

## 😊 User Reviews

> *"I for one am happy to wake up on my Sunday to this new music discovery tool."*  
> **— Shark7809**

> *"Wow! That sounds amazing! For a newbie like me, who is just starting out in the Plexamp world."*  
> **— Hisxela**

> *"This is something I've been looking for actually."*  
> **— AlteRedditor**

> *"I'm excited to try this. I've already pulled in a few recommendations and can't wait to let the script keep running to see what else it uncovers."*  
> **— mush0uth2**

> *"This is incredible! I'm in the middle of setting things up and was wandering if such thing existed, you made my day!!"*  
> **— williewaller**

## 📋 Prerequisites

### Required
- **Python 3.8+**: Modern Python installation
- **Last.fm Account**: Free account with API key ([Get API Key](https://www.last.fm/api/account/create))
- **MusicBrainz Access**: Public API (no registration required)

### Music Service (Choose One)
- **Option A**: [Headphones](https://github.com/rembo10/headphones) installation with API access
- **Option B**: [Lidarr](https://github.com/Lidarr/Lidarr) installation with API access


## 🐳 Quick Start with Docker

**The easiest way to run DiscoveryLastFM is using Docker!**

[![Docker Pulls](https://img.shields.io/docker/pulls/mrrobotogit/discoverylastfm)](https://hub.docker.com/r/mrrobotogit/discoverylastfm)
[![Docker Image Size](https://img.shields.io/docker/image-size/mrrobotogit/discoverylastfm/latest)](https://hub.docker.com/r/mrrobotogit/discoverylastfm)

### Automated Setup Script

```bash
# Clone the repository
git clone https://github.com/MrRobotoGit/DiscoveryLastFM-Docker.git
cd DiscoveryLastFM-Docker

# Run the automated setup
./scripts/setup-docker.sh
```

**🔗 [Complete Docker Guide & Examples](https://github.com/MrRobotoGit/DiscoveryLastFM-Docker)**

---

## 🛠️ Manual Installation

For advanced users who prefer running without Docker:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MrRobotoGit/DiscoveryLastFM.git
   cd DiscoveryLastFM
   ```

2. **Install dependencies**:
   ```bash
   # Recommended for Debian/Ubuntu/Raspberry Pi
   sudo apt update && sudo apt install python3-requests python3-packaging
   
   # Alternative for other systems
   pip install requests packaging
   ```

3. **Configure the script**:
   Copy the example configuration and edit with your credentials:
   ```bash
   cp config.example.py config.py
   ```
   
   Edit `config.py` with your actual values:
   
   **For Headphones users:**
   ```python
   MUSIC_SERVICE = "headphones"
   LASTFM_USERNAME = "your_lastfm_username"
   LASTFM_API_KEY = "your_lastfm_api_key"
   HP_API_KEY = "your_headphones_api_key"
   HP_ENDPOINT = "http://your-headphones-server:port"
   ```
   
   **For Lidarr users:**
   ```python
   MUSIC_SERVICE = "lidarr"
   LASTFM_USERNAME = "your_lastfm_username"
   LASTFM_API_KEY = "your_lastfm_api_key"
   LIDARR_API_KEY = "your_lidarr_api_key"
   LIDARR_ENDPOINT = "http://your-lidarr-server:port"
   LIDARR_ROOT_FOLDER = "/music"
   LIDARR_QUALITY_PROFILE_ID = 2  # 2=Lossless (recommended)
   LIDARR_METADATA_PROFILE_ID = 1  # 1=Standard
   ```



## ⚙️ Configuration

### Service Selection

Choose your music management service with the `MUSIC_SERVICE` parameter:

```python
MUSIC_SERVICE = "headphones"  # or "lidarr"
```

### Discovery Parameters

The script offers several configurable parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MUSIC_SERVICE` | "headphones" | Music service: "headphones" or "lidarr" |
| `RECENT_MONTHS` | 3 | Months of listening history to analyze |
| `MIN_PLAYS` | 20 | Minimum plays required to consider an artist |
| `SIMILAR_MATCH_MIN` | 0.46 | Minimum similarity score for artist matching |
| `MAX_SIMILAR_PER_ART` | 20 | Maximum similar artists to process per artist |
| `MAX_POP_ALBUMS` | 5 | Maximum popular albums to queue per artist |
| `CACHE_TTL_HOURS` | 24 | Cache time-to-live in hours |

### Lidarr-Specific Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LIDARR_QUALITY_PROFILE_ID` | 2 | Quality profile (1=Any, 2=Lossless, 3=Standard) |
| `LIDARR_METADATA_PROFILE_ID` | 1 | Metadata profile (1=Standard, 2=None) |
| `LIDARR_MONITOR_MODE` | "all" | Monitor mode: "all", "future", "missing", etc. |
| `LIDARR_SEARCH_ON_ADD` | True | Auto-search when adding artists/albums |

## 🏃 Usage

### Manual Execution
```bash
python3 DiscoveryLastFM.py
```

### Automated Execution (Cron)
Set up a daily cron job for automated discovery:
```bash
# Run daily at 3:00 AM
0 3 * * * python3 /path/to/DiscoveryLastFM/DiscoveryLastFM.py >> /path/to/DiscoveryLastFM/log/discover.log 2>&1
```

## 🔄 Auto-Update System

DiscoveryLastFM includes a built-in auto-update system to keep your installation current.

### CLI Commands
```bash
# Check for updates and install
python3 DiscoveryLastFM.py --update

# Show current version
python3 DiscoveryLastFM.py --version

# Show update status
python3 DiscoveryLastFM.py --update-status

# List available backups
python3 DiscoveryLastFM.py --list-backups
```

### Configuration
Add to your `config.py` to enable automatic update checking:
```python
AUTO_UPDATE_ENABLED = True           # Enable automatic update checking
UPDATE_CHECK_INTERVAL_HOURS = 24     # Check frequency in hours
BACKUP_RETENTION_DAYS = 7            # Backup retention period
```

The auto-update system includes automatic backup creation, safe installation with verification, and automatic rollback if issues are detected. Your configuration files and cache are always preserved during updates.

## 📊 Sample Output

```
2025-06-22 03:00:01  INFO      Analizzo 15 artisti...
2025-06-22 03:00:05  INFO      Processo artista: Radiohead (a74b1b7f-71a5-4011-9441-d0b5e4122711)
2025-06-22 03:00:10  INFO      Trovati 5 album per Thom Yorke
2025-06-22 03:00:15  INFO      Aggiungo album f47ac10b-58cc-4372-a567-0e02b2c3d479
2025-06-22 03:05:30  INFO      Sync completata in 5.5 minuti. Statistiche:
2025-06-22 03:05:30  INFO      - Album aggiunti con successo: 42
2025-06-22 03:05:30  INFO      - Errori riscontrati: 3
2025-06-22 03:05:30  INFO      - Album skippati: 18
2025-06-22 03:05:30  INFO      - Artisti processati: 85
```

## 📁 Project Structure

```
DiscoveryLastFM/
├── DiscoveryLastFM.py          # Main script
├── config.example.py           # Example configuration file
├── config.py                   # Your configuration (not in git)
├── services/                   # Service layer (v2.0)
│   ├── __init__.py             # Module initialization
│   ├── base.py                 # Abstract base classes
│   ├── exceptions.py           # Custom exceptions
│   ├── factory.py              # Service factory
│   ├── headphones.py           # Headphones service
│   └── lidarr.py               # Lidarr service
├── tests/                      # Test suite (v2.0)
│   ├── __init__.py
│   ├── test_headphones.py
│   ├── test_lidarr.py
│   └── fixtures/
├── lastfm_similar_cache.json   # Cache file (not in git)
├── log/                        # Log directory (not in git)
│   └── discover.log            # Application logs
├── .gitignore                  # Git ignore file
├── README.md                   # This file
└── CHANGELOG.md                # Version history
```

## 🔧 API Integration

### Last.fm API
- Fetches recent listening history
- Discovers similar artists
- Retrieves album popularity data

### MusicBrainz API
- Validates album metadata
- Filters release types (studio vs. live/compilation)
- Resolves release group IDs

### Music Service APIs

**Headphones API:**
- Adds artists to library
- Queues albums for download
- Checks for existing albums
- Force search functionality

**Lidarr API:**
- Artist management with quality profiles
- Album monitoring and search
- Advanced metadata management
- Command-based operations

## 🛡️ Error Handling

The script includes robust error handling:

- **Service Layer**: Abstracted error handling across both Headphones and Lidarr
- **Retry Logic**: Automatic retries with exponential backoff
- **Rate Limit Management**: Respects API rate limits and retry-after headers
- **Timeout Handling**: Extended timeouts for heavy operations
- **Configuration Validation**: Startup validation ensures proper service setup
- **Graceful Degradation**: Continues processing even if some operations fail
- **Service Switching**: Easy migration between services with error recovery

## 📈 Performance Optimizations

- **Intelligent Caching**: Reduces API calls by caching similar artists and processed albums
- **Rate Limiting**: Built-in delays to respect API limitations
- **Efficient Filtering**: Early filtering to avoid processing unwanted content
- **Batch Operations**: Groups related operations where possible

## 🐛 Troubleshooting

### Common Issues

**General Issues:**
1. **API Key Errors**: Ensure all API keys are valid and have proper permissions
2. **Network Timeouts**: Check network connectivity and increase timeout values if needed
3. **Rate Limiting**: The script handles this automatically, but manual delays might be needed for very large libraries
4. **Cache Issues**: Delete the cache file to reset if you encounter persistent issues

**Service-Specific Issues:**

**Headphones:**
- Check `HP_ENDPOINT` format (include http:// and port)
- Verify API key in Headphones settings
- Ensure Headphones is running and accessible

**Lidarr:**
- Check `LIDARR_ENDPOINT` format (no trailing slash)
- Verify API key in Lidarr Settings → General
- Confirm `LIDARR_ROOT_FOLDER` exists and is writable
- Validate quality and metadata profile IDs exist

**Service Switching:**
- Update `MUSIC_SERVICE` parameter in config.py
- Ensure all required configuration parameters are set
- Cache is compatible between services

### Debug Mode
Enable debug output by setting `DEBUG_PRINT = True` in the configuration.

## 🗺️ Roadmap

### Completed ✅
- Headphones support
- Lidarr support  
- Service layer architecture
- Zero breaking changes migration
- Advanced configuration management

### Planned 🔜
- CSV export functionality
- Web dashboard interface
- Multiple instance support
- Enhanced caching system
- Plugin architecture for additional services

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 🙏 Acknowledgments

- [Last.fm](https://www.last.fm/) for the music discovery API
- [MusicBrainz](https://musicbrainz.org/) for comprehensive music metadata
- [Headphones](https://github.com/rembo10/headphones) for automated music management
- [Lidarr](https://github.com/Lidarr/Lidarr) for modern music library management
- The open-source community for continuous improvement and feedback

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the logs in `log/discover.log`
3. Open an issue on GitHub with relevant log excerpts

---
---

*Concept and development by [Matteo Rancilio](https://www.linkedin.com/in/matteorancilio/).*

**Note**: This tool is designed for personal use. Please respect the terms of service of all integrated APIs and services.
