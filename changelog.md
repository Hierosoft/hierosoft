# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [git] - 2022-06-10
(all changes are vs the code moved from blendernightly)

### Added
- The first working version is a modified version of blendernightly, so the code was moved from there and now blendernightly requires hierosoft.

### Changed
- Move code into separate submodules.
  - Move the GUI from a file in the repo directory into a submodule (gui_tk.py).
- Move *Arch variables into "meta" (formerly an empty dict attribute of LinkManager)
