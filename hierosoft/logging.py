# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import traceback

verbosity_levels = [False, True, 0, 1, 2, 3]

verbosity = 0
for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if arg.startswith("--"):
        if arg == "--verbose":
            verbosity = 1
        elif arg == "--debug":
            verbosity = 2


def write0(arg):
    sys.stderr.write(arg)
    sys.stderr.flush()
    return True


def write1(arg):
    if verbosity < 1:
        return False
    sys.stderr.write(arg)
    sys.stderr.flush()
    return True


def write2(arg):
    if verbosity < 2:
        return False
    sys.stderr.write(arg)
    sys.stderr.flush()
    return True


def write3(arg):
    if verbosity < 3:
        return False
    sys.stderr.write(arg)
    sys.stderr.flush()
    return True


def echo0(*args, **kwargs):  # formerly prerr
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo1(*args, **kwargs):  # formerly debug
    if verbosity < 1:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo2(*args, **kwargs):  # formerly extra
    if verbosity < 2:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo3(*args, **kwargs):
    if verbosity < 3:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def get_verbosity():
    return verbosity


def set_verbosity(verbosity_level):
    global verbosity
    if verbosity_level not in verbosity_levels:
        vMsg = verbosity_levels
        if isinstance(vMsg, str):
            vMsg = '"{}"'.format(vMsg)
        raise ValueError(
            "verbosity_levels must be one of {} not {}."
            "".format(verbosity_levels, vMsg)
        )
    verbosity = verbosity_level


def get_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    msg = "{}{} {}:\n".format(indent, ex_type, ex)
    msg += traceback.format_exc()
    del tb
    return msg

def view_traceback(indent="", min_indent=None):
    '''
    Write the traceback to stderr.

    Keyword arguments:
    indent each line of output this much.

    Globals used:
    import traceback

    Deprecations:
    min_indent keyword argument
    '''
    if min_indent is not None:
        raise ValueError("min_indent is deprecated. Use indent.")
    # # echo0(min_indent+str(ex_type))
    # # echo0(min_indent+str(ex))
    # echo0("{}{} {}: ".format(indent, ex_type, ex))
    # traceback.print_tb(tb)
    echo0(get_traceback(indent=indent))
    # del tb
    echo0("")



# syntax_error_fmt = "{path}:{row}:{column}: {message}"
syntax_error_fmt = 'File "{path}", line {row}, {column} {message}'
# ^ such as (Python-style, so readable by Geany):
'''
  File "/redacted/git/pycodetool/pycodetool/spec.py", line 336, in read_spec
'''


def set_syntax_error_fmt(fmt):
    global syntax_error_fmt
    syntax_error_fmt = fmt


def to_syntax_error(path, lineN, msg, col=None):
    '''
    Convert the error to a syntax error that specifies the file and line
    number that has the bad syntax.

    Keyword arguments:
    col -- is the character index relative to the start of the line,
        starting at 1 for compatibility with outputinspector (which will
        subtract 1 if using editors that start at 0).
    '''
    this_fmt = syntax_error_fmt

    if col is None:
        part = "{column}"
        removeI = this_fmt.find(part)
        if removeI > -1:
            suffixI = removeI + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:removeI] + this_fmt[suffixI:]
    if lineN is None:
        part = "{row}"
        removeI = this_fmt.find(part)
        if removeI > -1:
            suffixI = removeI + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:removeI] + this_fmt[suffixI:]
    return this_fmt.format(path=path, row=lineN, column=col, message=msg)
    # ^ Settings values not in this_fmt is ok.


def echo_SyntaxWarning(path, lineN, msg, col=None):
    msg = to_syntax_error(path, lineN, msg, col=col)
    echo0(msg)
    # ^ So the IDE can try to parse what path&line has an error.


def raise_SyntaxError(path, lineN, msg, col=None):
    echo_SyntaxWarning(path, lineN, msg, col=col)
    raise SyntaxError(msg)
