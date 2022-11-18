# Hierosoft Update

Solve Python distribution with a one-click install solution!

## Core features
Hierosoft Update is the Python manager and virtualenv manager module
to download or run a Python program such as an updated copy of:
- itself
- the Hierosoft Launcher (See Project Status).
- any program (when used by the launcher or blendernightly)

## Checkpath
To learn more, see the comment (docstring) at the top of [checkpath.py](hierosoft/checkpath.py).

## Project Status
- [ ] The gui_tk main function should be launched by the icon.
- [ ] In Windows, Hierosoft Icon should be compiled as an exe such as
  using
  [PyOxidizer](https://www.techrepublic.com/article/python-programming-language-pyoxidizer-tackles-existential-threat-posed-by-app-distribution-problem/)
  so that it runs without having to install anything first.
- [ ] Download and run itself (updated Python copy) as the
  main program which should run the launcher.
  - [ ] The process of installing apps should move to the launcher which
    should use the downloaded python version of this module.
- [ ] Complete the launcher a separate project and run that instead of
  running a single program.
  - Potentially,
    [nopackage](https://github.com/poikilos/nopackage) could become the
    launcher or a component in the same virtualenv). It has the
    advantage of having download locations of icons for certain
    programs.
  - [ ] Make a special virtualenv named hierosoft-launcher that only
    contains what Hierosoft Launcher needs to operate, and a copy of
    Hierosoft Update.
- [ ] Add <https://pypi.org/project/eric-ide> as a test case except use
  `~/.virtualenvs`. Keep the `eric7_venv` directory if it exists in case
  manual steps were used prior.
  - [ ] Remember to include `eric7_post_install`.
- [ ] Check for an existing venv directory such as if ~/venv/kivy were
  used according to manual instructions.


## Development

### Purpose
The purpose of Hierosoft Update is to ensure that the launcher can start,
and serve as a platform for installing other Python programs as well.
The way the Hierosoft Update works is by setting up a virtualenv for a
program or set of programs after trying to detect the correct version
of Python regardless of how the program is packaged.

The Python distribution dilemma is that programs are scripts users must
open unless the author puts some custom system in place to install an
icon and to do one of the following:
- Ensure a correct Python version is installed, and where it is.
- Compile the Python code into an exe such as using
  [PyOxidizer](https://www.techrepublic.com/article/python-programming-language-pyoxidizer-tackles-existential-threat-posed-by-app-distribution-problem/).

The dilemma is that though solutions exist, there isn't a de facto
standard other than solutions which already assume you have Python and
require Command-Line Interface (CLI) commands.

