# Changelog - OBD SuperStar Agent

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-21
### Added
- **Supabase Integration**: Fully migrated to Supabase Database (Postgres), Auth, and Storage.
- **Multi-User Collaboration**: Live presence, campaign-specific comment threads, and team isolation.
- **Admin Dashboard**: New module at `/admin` for user management and system monitoring.
- **Direct Asset Downloads**: Proxying audio and script files with proper attachment headers.
- **Multi-Voice Analytics**: Enhanced results panel showing technical details for up to 3 selected voices per variant.
- **Design System**: 6 premium UI themes (Midnight, Ocean, Ember, Forest, Lavender, Light) with glassmorphism.

### Changed
- **Backend Architecture**: Decoupled persistence and auth into a dedicated `SupabaseClient` with local fallback.
- **Dashboard UI**: Redesigned variant cards with individual download controls and improved readability.
- **Voice Selection**: Refactored logic to pick primary and alternative voices based on cultural market research.

### Fixed
- **Hydration Errors**: Resolved React 19 / Next.js 15 button nesting issues.
- **Serialization**: Fixed username extraction bug in WebSocket presence logs.
- **File Naming**: Standardized audio file naming convention for consistency across TTS engines.

---
## [1.0.0] - 2026-01-15
### Initial Release
- Multi-agent AI pipeline (Product, Market, Script, Eval, Voice, Audio).
- Murf AI and edge-tts integration.
- Standard OBD script generation.
- Local SQLite persistence.
