# secureblue Control Center

### Features:
- Provides a UI-agnostic and thread-safe API for feature scripts (simply called features) to provide functionality to users.<br>
  Write once, works in both CLI and GUI.
- Supports preferences (enable/disable functions), multi-preferences (non-binary functions, arbitrary states) and utilities (idempotent functions)
  - Complex variants of `Preference` and `Utility` are available for the CLI frontend, allowing registration of custom subcommands and arguments, directly through the Click Command API.
- Categories
- Limiting features to specific frontends (CLI/GUI) or environments (server/desktop).
- gettext integration for translation
- Native tab-completion support (courtesy of Click)
- GUI support is fully optional. The `sbcc_gui` module can be removed; the application will remain functional and does not attempt to load related libraries.
- Supports graceful user-cancellation of features in the GUI

### Usage:
###### (Prerequisite: Install necessary dependencies)
The application is started by invoking `sbcc/app.py#launch()`.
The recommended way of doing this is by placing a wrapper-script `sbcc` in your `~/.local/bin/`:
```python
#!/usr/bin/env python

import sys
sys.path.insert(0, "/PATH/TO/THIS/REPO")

import sbcc.app

sbcc.app.launch()
```
After making that file executable, you can simply run `sbcc` from anywhere to launch the application.

To enable bash-completion for your current session, save the output of
```
_SBCC_COMPLETE=bash_source sbcc
```
somewhere and source that file.
If you are using a different shell than bash, consult the [Click Shell Completion](https://click.palletsprojects.com/en/stable/shell-completion/) documentation.

You can alternatively start the application by running
```
python -m sbcc
```
from inside the project root directory, though shell completion won't work that way.

## Folder structure:
### `sbcc_framework`
Provides the framework and API for the secureblue Control Center.
### `sbcc_cli`
CLI frontend and implementation of the framework.
### `sbcc_gui`
GUI frontend and implementation of the framework.
### `sbcc`
Application core and main entry point.
### `sbcc/features`
Feature scripts
