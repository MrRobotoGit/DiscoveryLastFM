# Changelog - DiscoveryLastFM

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.7] - 2025-06-22

### Changed
- **BREAKING**: Project renamed from `DiscoverLastfm` to `DiscoveryLastFM`
- Main script renamed from `DiscoverLastfm.py` to `DiscoveryLastFM.py`
- Directory structure updated to use consistent `DiscoveryLastFM` naming
- Updated all documentation to reflect new naming convention
- Cronjob updated to point to new script path and name
- Repository URL updated to `https://github.com/MrRobotoGit/DiscoveryLastFM`

### Fixed
- All internal references updated to use consistent naming
- Documentation and examples updated with correct naming

## [1.7.6] - 2025-06-22

### Added
- Created dedicated directory structure for the project
- Added file logging system in `log/discover.log`
- Created this CHANGELOG.md file
- Created README.md with complete project documentation

### Changed
- Migration from single script to organized project structure
- Updated cache and log paths to use the new structure
- Improved logging system with output to both console and file
- Updated cronjob to use the new script path

### Fixed
- Resolved file organization issues
- Improved project maintainability

## [1.7.5] - 2025-06-22

### Fixed
- Removed duplication of `album_exists` function
- Kept the more robust version that checks both album and tracks data

## [1.7.4] - 2025-06-22

### Added
- Automatic retry system for failed API calls
- Exponential backoff to handle server overloads
- Specific handling for 500 errors in `queueAlbum`
- MusicBrainz rate limiting handling (429 status code)
- Extended timeouts for critical operations (120s for add/queue, 300s for forceSearch)

### Changed
- Improved overall robustness of API calls
- Updated statistics system with skipped albums count
- Added execution time tracking

### Fixed
- Resolved frequent timeout issues with Headphones
- Improved handling of temporary network errors
- Reduced non-recoverable failures

## [1.7.3] - 2025-06-22

### Changed
- Maintained existing functionality with minor corrections

### Notes
- Base version with complete Last.fm, MusicBrainz and Headphones integration
- Cache system for similar artists and already added albums
- Filter for studio albums excluding compilations, live albums, EPs, etc.
