# DiscoverLastFM    

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.7.6-orange.svg)](CHANGELOG.md)

An automated music discovery tool that integrates Last.fm, MusicBrainz, and Headphones to discover and queue new albums based on your listening history.

## 🎵 Features

- **Smart Discovery**: Analyzes your Last.fm listening history to find similar artists
- **Quality Filtering**: Only queues studio albums, excluding compilations, live albums, EPs, etc.
- **Duplicate Prevention**: Maintains persistent cache to avoid adding albums multiple times
- **Robust API Handling**: Built-in retry mechanisms with exponential backoff
- **Rate Limiting**: Respects API rate limits for all services
- **Comprehensive Logging**: Detailed logging both to console and file

## 🛠️ How It Works

1. **Fetch Recent Artists**: Retrieves artists you've listened to recently on Last.fm
2. **Find Similar Artists**: Discovers similar artists using Last.fm's recommendation engine
3. **Add to Headphones**: Automatically adds both original and similar artists to your Headphones library
4. **Queue Top Albums**: Fetches and queues the most popular studio albums from each artist
5. **Smart Filtering**: Uses MusicBrainz metadata to filter out non-studio releases
6. **Cache Management**: Maintains cache to optimize performance and avoid duplicates

## 📋 Prerequisites

- Python 3.8 or higher
- Last.fm account and API key
- Headphones installation with API access
- MusicBrainz access (public API)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MrRobotoGit/DiscoveryLastFM.git
   cd DiscoverLastfm
   ```

2. **Install dependencies**:
   ```bash
   pip install requests
   ```

3. **Configure the script**:
   Copy the example configuration and edit with your credentials:
   ```bash
   cp config.example.py config.py
   ```
   
   Edit `config.py` with your actual values:
   ```python
   LASTFM_USERNAME = "your_lastfm_username"
   LASTFM_API_KEY = "your_lastfm_api_key"
   HP_API_KEY = "your_headphones_api_key"
   HP_ENDPOINT = "http://your-headphones-server:port"
   ```

   **⚠️ Important**: Never commit `config.py` to version control as it contains sensitive API keys!

## ⚙️ Configuration

The script offers several configurable parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RECENT_MONTHS` | 3 | Months of listening history to analyze |
| `MIN_PLAYS` | 20 | Minimum plays required to consider an artist |
| `SIMILAR_MATCH_MIN` | 0.46 | Minimum similarity score for artist matching |
| `MAX_SIMILAR_PER_ART` | 20 | Maximum similar artists to process per artist |
| `MAX_POP_ALBUMS` | 5 | Maximum popular albums to queue per artist |
| `CACHE_TTL_HOURS` | 24 | Cache time-to-live in hours |

## 🏃 Usage

### Manual Execution
```bash
python3 DiscoverLastfm.py
```

### Automated Execution (Cron)
Set up a daily cron job for automated discovery:
```bash
# Run daily at 3:00 AM
0 3 * * * python3 /path/to/DiscoverLastfm/DiscoverLastfm.py >> /path/to/DiscoverLastfm/log/discover.log 2>&1
```

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
DiscoverLastfm/
├── DiscoverLastfm.py           # Main script
├── config.example.py           # Example configuration file
├── config.py                   # Your configuration (not in git)
├── lastfm_similar_cache.json   # Cache file for artists and albums (not in git)
├── log/                        # Log directory (not in git)
│   └── discover.log            # Application logs
├── .gitignore                  # Git ignore file
├── README.md                   # This file
├── CHANGELOG.md                # Version history
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

### Headphones API
- Adds artists to library
- Queues albums for download
- Checks for existing albums

## 🛡️ Error Handling

The script includes robust error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Rate Limit Management**: Respects API rate limits and retry-after headers
- **Timeout Handling**: Extended timeouts for heavy operations
- **Graceful Degradation**: Continues processing even if some operations fail

## 📈 Performance Optimizations

- **Intelligent Caching**: Reduces API calls by caching similar artists and processed albums
- **Rate Limiting**: Built-in delays to respect API limitations
- **Efficient Filtering**: Early filtering to avoid processing unwanted content
- **Batch Operations**: Groups related operations where possible

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all API keys are valid and have proper permissions
2. **Network Timeouts**: Check network connectivity and increase timeout values if needed
3. **Rate Limiting**: The script handles this automatically, but manual delays might be needed for very large libraries
4. **Cache Issues**: Delete the cache file to reset if you encounter persistent issues

### Debug Mode
Enable debug output by setting `DEBUG_PRINT = True` in the configuration.

## 😊 User Reviews

> *"I for one am happy to wake up on my Sunday to this new music discovery tool."*  
> **— Shark7809**

> *"Wow! That sounds amazing! For a newbie like me, who is just starting out in the Plexamp world."*  
> **— Hisxela**

> *"This is something I've been looking for actually."*  
> **— AlteRedditor**

> *"I'm excited to try this. I've already pulled in a few recommendations and can't wait to let the script keep running to see what else it uncovers."*  
> **— mush0uth2**

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

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the logs in `log/discover.log`
3. Open an issue on GitHub with relevant log excerpts

---

**Note**: This tool is designed for personal use. Please respect the terms of service of all integrated APIs and services.
