# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Tasks
- Move moreplatform/__init__.py code to hierosoft/__init__.py which affects:
  - /home/owner/git/blnk/blnk/__init__.py

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
