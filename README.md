# secureblue Control Center

### Features:
- Provides a UI-agnostic and thread-safe API for feature scripts (simply called features) to provide functionality to users.<br>
  Write once, works in both CLI and GUI.
- Supports toggles (enable/disable functions) and utilities (idempotent functions)
  - Complex variants of those are available for the CLI frontend, allowing registration of custom subcommands, arguments and states, directly through the Click Command API.
- Categories
- Limiting features to specific frontends (CLI/GUI) or environments (server/desktop).
- gettext integration for translation
- Native tab-completion support (courtesy of Click)
- GUI support is fully optional. The `sbcc_gui` module can be removed; the application will remain functional and does not attempt to load related libraries.
- Supports graceful user-cancellation of features in the GUI

## Folder structure:
### `sbcc_framework`
Provides the framework and API for the secureblue Control Center.
### `sbcc_cli`
CLI frontend and implementation of the framework.
### `sbcc_gui`
GUI frontend and implementation of the framework.
### `sbcc`
Application core and main entry point.
### `sbbc/features`
Feature scripts
