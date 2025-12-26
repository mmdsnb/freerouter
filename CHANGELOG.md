# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-12-26

### Added
- Interactive `freerouter init` command with config location choice
- Daemon-style service management (start/stop/logs commands)
- Makefile for standardized development commands
- Comprehensive test suite with 79% coverage (74 tests)

### Fixed
- CONFIG_FILE_PATH environment variable conflict with LiteLLM
- All providers now disabled by default in generated config
- Test suite performance and reliability issues

### Changed
- All user-facing messages translated to English
- Documentation restructured (FAQ, ROADMAP moved to docs/)
- CLAUDE.md refactored for clarity and maintainability

### Removed
- Obsolete scripts directory (replaced by CLI commands)
- Temporary development documentation files
- Chinese README (internationalization - English only)

## [0.1.0] - 2025-12-25

### Added
- Initial release
- Strategy Pattern based Provider architecture
- Factory Pattern for provider creation
- OpenRouter Provider with API-based model discovery
- Ollama Provider for local models
- ModelScope Provider with static model list
- Static Provider for manual configuration
- YAML-based configuration
- Environment variable support
- Docker and Docker Compose support
- Basic unit tests
- Documentation and examples

### Design
- KISS principle implementation
- Occam's Razor approach
- Clean project structure (freerouter/, tests/)
- Comprehensive documentation in CLAUDE.md
