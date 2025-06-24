# Changelog - DiscoveryLastFM

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-06-24

### 🚀 Major Features

**🎯 Dual Service Support**
- **NEW**: Complete Lidarr integration alongside existing Headphones support
- **NEW**: Service selection via single `MUSIC_SERVICE` configuration parameter
- **NEW**: Service factory pattern for easy extensibility
- **NEW**: Full API parity between Headphones and Lidarr services

**🏗️ Modular Architecture**
- **NEW**: Clean service layer architecture with abstract base classes
- **NEW**: Structured data handling with `ArtistInfo` and `AlbumInfo` dataclasses
- **NEW**: Custom exception hierarchy (`ServiceError`, `ConfigurationError`)
- **NEW**: Service factory with comprehensive validation

### 🔧 Technical Improvements

**Service Layer**
- **NEW**: `MusicServiceBase` abstract class defining common interface
- **NEW**: `HeadphonesService` - extracted and enhanced from original `hp_api()`
- **NEW**: `LidarrService` - complete Lidarr API v1.0+ implementation
- **NEW**: `MusicServiceFactory` with service creation and validation

**Enhanced Configuration**
- **NEW**: Extended configuration system with service-specific options
- **NEW**: Lidarr quality and metadata profile management
- **NEW**: Advanced Lidarr options (monitor modes, search triggers, folder structure)
- **NEW**: Configuration validation at startup with detailed error messages

**Error Handling & Reliability**
- **NEW**: Service-aware error handling and retry logic
- **NEW**: Enhanced timeout management per service type
- **NEW**: Graceful service switching with connection testing
- **NEW**: Improved logging with service context

### 📁 Project Structure

**New Directory Structure:**
- `services/` - Service layer implementation
  - `base.py` - Abstract classes and dataclasses
  - `factory.py` - Service factory and validation
  - `headphones.py` - Headphones service wrapper
  - `lidarr.py` - Complete Lidarr implementation
  - `exceptions.py` - Custom exception classes
- `tests/` - Comprehensive test suite (framework ready)

### 🔄 Compatibility & Migration

**Zero Breaking Changes**
- ✅ **100% Backward Compatibility**: Existing Headphones users continue without modifications
- ✅ **Cache Compatibility**: Maintains existing cache format and data
- ✅ **Configuration Compatibility**: Existing `config.py` files work unchanged
- ✅ **Workflow Preservation**: Identical discovery and queueing behavior

**Easy Migration Path**
- 🔄 Switch services by changing single `MUSIC_SERVICE` parameter
- 🔄 Gradual migration support with service validation
- 🔄 Configuration examples for both services
- 🔄 Comprehensive migration documentation

### 🎵 Lidarr Integration Features

**Core Operations**
- Artist management with MBID lookup and validation
- Album addition with release group mapping
- Quality and metadata profile integration
- Advanced search and monitoring capabilities
- Command-based operations (search, refresh, rescan)

**Advanced Configuration**
- Quality profile assignment (Any, Lossless, Standard)
- Metadata profile selection (Standard, None)
- Monitor mode configuration (all, future, missing, etc.)
- Root folder management and validation
- Auto-search on add functionality

### 📊 Performance & Reliability

**Enhanced Robustness**
- Service-specific retry logic with exponential backoff
- Connection testing and validation at startup
- Improved rate limiting and timeout management
- Service-aware error recovery mechanisms

**Monitoring & Diagnostics**
- Service information logging for troubleshooting
- Enhanced statistics with service context
- Configuration validation with detailed feedback
- Improved error messages with actionable guidance

### 📚 Documentation

**Comprehensive Updates**
- Updated README with dual service documentation
- Service-specific setup and configuration guides
- Troubleshooting section for both services
- Migration guide from v1.x to v2.0
- Complete API integration documentation

### 🔧 Developer Experience

**Code Quality**
- Clean, modular architecture following SOLID principles
- Comprehensive type hints and documentation
- Service abstraction for easy testing and mocking
- Extensible design for future service additions

**Testing Framework**
- Test structure ready for comprehensive test suite
- Service isolation for unit testing
- Mock-friendly service interfaces
- Integration test framework prepared

### 🚨 Breaking Changes

**None** - This release maintains 100% backward compatibility with v1.7.x

### 🔄 Migration Instructions

**For Existing Users (Headphones)**
- No action required - your setup continues to work identically
- Optionally add `MUSIC_SERVICE = "headphones"` to config.py for explicitness

**For New Users Choosing Lidarr**
- Set `MUSIC_SERVICE = "lidarr"` in config.py
- Add Lidarr-specific configuration parameters
- Follow Lidarr setup guide in README

**For Users Migrating to Lidarr**
- Update `MUSIC_SERVICE` from "headphones" to "lidarr"
- Add required Lidarr configuration parameters
- Test connection and validate setup
- Existing cache and discovered artists are preserved

### 🎯 Future Roadmap Enabled

This release creates the foundation for:
- Additional music service integrations (Plex, Jellyfin, etc.)
- Web dashboard and API endpoints
- Multi-instance support
- Plugin architecture
- Enhanced caching and performance optimizations

---

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
