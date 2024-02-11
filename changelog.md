# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [git] - 2024-02-11
### Added
- WIP new GUI (Status: planning)
- Icons (Widget graphics, packed)

### Removed
- Single-app GUI (moved to deprecated `_init_single_app` method)


## [git] - 2024-02-02
### Added
- `HInstaller` (install, upgrade, and uninstall features)
  - Metadata (`hinstaller.meta`) format is based on nopackage metadata format.
- `HInstaller` metadata for installing Minetest
- `install-lmk.py` HInstaller example script and cli script for installing Minetest.


## [git] - 2024-02-02
### Added
- `sysdirs` dict-like constants collection (and generally-enforceable Constants class)
- functions: app_version_dir, appstates_dir, generate_caption, dt_str, str_dt, dt_path_str, path_str_dt
- PATH_TIME_FMT (moved from nopackage).


## [git] - 2024-02-02
### Added
- Several functions in moreplatform: `get_dir_size`, `zip_dir`, `get_digest`, `get_hexdigest`, `same_hash` and `install_shortcut` (moved from EnlivenMinetest/utilities/install-lmk; FIXME: combine with `make_shortcut`?)


## [git] - 2024-02-02
### Added
- rewrite_conf_str (moved from EnlivenMinetest/utilities/install-lmk)
  - FIXME: combine with rewrite_conf?


## [git] - 2022-11-28
### Changed
- Require key for `get_unique_path` (Change it from a keyword argument
  to a sequential argument to prevent accidentally sending only a key
  and not a luid which would set luid to a key).
### Fixed
- Separate LOCALAPPDATA and CACHES in case the program is installed in
  LOCALAPPDATA (Set CACHES to LOCALAPPDATA\cache on Windows).
- Separate LOCALAPPDATA and APPDATA on non-Windows systems into
  `~/.local/share` (synonymous with SHARE since generally written during
  install and since CACHES is elsewere) and `~/.config`.
- Make casing consistent when using the LOCALAPPDATA global.


## [git] - 2022-11-19
### Added
- move `set_syntax_error_fmt`, `to_syntax_error`, `echo_SyntaxWarning`, and `raise_SyntaxError` from pycodetool to logging.
- move logging tests from pycodetool.


## [git] - 2022-11-19
### Added
- move `view_traceback` and `get_traceback` to logging from blnk.

### Changed
- move `echo?`, `write?`, and `*_verbosity` to logging.


## [git] - 2022-11-18
### Added
- move ggrep.py from pycodetool to hierosoft/ which affects:
  - [x] anewcommit
  - [x] (moved to hierosoft) pycodetool/pycodetool/tests/test_ggrep.py
  - [x] (moved entry point line to hierosoft/setup.py) pycodetool/setup.py
  - [x] (moved to hierosoft) pycodetool/scripts/ggrep
  - [x] linux-preinstall/utilities/ggrep
  - [x] nopackage/nopackage/__init__.py has "region same as pycodetool.ggrep" but should require hierosoft instead.
- move path constants (now all caps) from moreplatform/__init__.py to hierosoft/__init__.py which affects:
  - [x] mtanalyze/mtanalyze/__init__.py has redundant code, but should require hierosoft instead
- move moremeta.py from moreplatform to hierosoft
- move checkpath.py from moreplatform to hierosoft


## [git] - 2022-06-10
(all changes are vs the code moved from blendernightly)

### Added
- The first working version is a modified version of blendernightly, so the code was moved from there and now blendernightly requires hierosoft.

### Changed
- Move code into separate submodules.
  - Move the GUI from a file in the repo directory into a submodule (gui_tk.py).
- Move *Arch variables into "meta" (formerly an empty dict attribute of LinkManager)
