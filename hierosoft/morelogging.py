# -*- coding: utf-8 -*-
'''
This submodule provides logging features such as for handling verbosity
and representation of data in human-readable form.

This module can't import hierosoft or it would be a circular dependency
(It would cause an incomplete module error and stop the program).
'''
from __future__ import print_function
from __future__ import division
import sys
import traceback
import os

from collections import OrderedDict

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

# import hierosoft.moreweb  # avoid this--circular import

if sys.version_info.major >= 3:
    import logging  # noqa F401
    from logging import (
        Formatter,
        Logger,
        Handler,
        getLogger,
        basicConfig,
        critical,
        debug,
        error,
        exception,
        fatal,
        info,
        warn,
        warning,
    )
else:
    # Polyfills for Python 2
    import hierosoft.logging2 as logging
    from hierosoft.logging2 import (
        Formatter,
        Logger,
        Handler,
        getLogger,
        basicConfig,
        critical,
        debug,
        error,
        exception,
        fatal,
        info,
        warn,
        warning,
    )

from hierosoft.logging2 import (
    FATAL,
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET,
    utcnow,
)

to_log_level = {
    4: 10,  # logging.DEBUG
    3: 20,  # logging.INFO
    2: 30,  # logging.WARNING (logging default)
    # True: 30,  # logging.WARNING
    1: 40,  # logging.ERROR
    # False: 50,  # logging.ERROR
    0: 50,  # logging.CRITICAL
}  # NOTE: True and False are cast to int when used as keys!

verbosity_levels = [False, True, 0, 1, 2, 3, 4]

verbosity = 2  # 2 to mimic Python 3 logging default WARNING (30)
for _argi in range(1, len(sys.argv)):
    arg = sys.argv[_argi]
    if arg.startswith("--"):
        if arg == "--verbose":
            verbosity = 1
        elif arg == "--debug":
            verbosity = 2


def is_enclosed(value, start, end):
    if len(value) < len(start) + len(end):
        return False
    return value.startswith(start) and value.endswith(end)


def is_str_like(value):
    return type(value).__name__ in ("str", "bytes", "bytearray", "unicode")


pformat_preferred_quote = None  # < See quote under set_pformat_preferred_quote


def set_pformat_preferred_quote(quote):
    """Set the global pformat_preferred_quote

    Args:
        quote (str): Set pformat_preferred_quote to this. Defaults to
            adaptive ("'" if "'" not in value else '"' when
            pformat_preferred_quote is None).
    """
    global pformat_preferred_quote
    pformat_preferred_quote = quote


def pformat(value, quote_if_like_str=None, escape_if_like_str=None):
    """This is mostly like pformat from pprint except always on one line.

    Numbers are left as numbers even if quote_if_like_str is True, to
    avoid adding extra quotes. Use set pformat_preferred_quote to set
    the preferred quote.

    Args:
        value: any value that can convert to str. Values in
            an iterable will be processed resursively first.
        quote_if_like_str (Optional[bool]): Do not use this option, or
            your pformat calls will be incompatible with
            pprint.pformat--This option is only for recursion. Add
            quotes (not done recursively, since if iterable but not
            is_str_like, the last step which is converting from iterable
            to string adds quotes to all string values). Defaults to
            True.
        escape_if_like_str (Optional[bool]): Escape newlines and
            backspace to avoid various display issues (display the
            string in a way that helps debugging rather than original
            function). For example, change "\n" (literal newline, on
            character) to "\\n" (actually one backslash followed by
            newline). Defaults to True.

    Returns:
        str: string where only strings are quote_if_like_str (without
            leading b or u).
    """
    if escape_if_like_str is None:
        escape_if_like_str = True
    if quote_if_like_str is None:
        quote_if_like_str = True
    original_value = value
    enclosures = None
    if not is_str_like(value):
        # ^ unicode isn't normal in Python 3 so check typename not isinstance
        iterated = False
        try:
            parts = []
            enclosures = ("[", "]")
            if isinstance(enclosures, tuple):
                enclosures = ("(", ")")
            if hasattr(value, 'items'):
                if isinstance(value, OrderedDict):
                    parts = OrderedDict()
                else:
                    parts = {}
                for key, item in value.items():
                    parts[key] = pformat(item, quote_if_like_str=False)
                return parts
            for i, item in enumerate(value):
                iterated = True
                parts.append(pformat(item, quote_if_like_str=False))
                # Use append not '=' since tuple is not assignable
            if isinstance(value, tuple):
                value = tuple(parts)
            else:
                value = parts
        except TypeError:
            if iterated:
                raise
            # else it is not iterable, so do not try to fix elements
    if not quote_if_like_str:
        try:
            _ = len(value)
        except TypeError:
            # It is not str-like. To avoid adding quotes to non-str-like
            #   (number, bool, etc.) leave it as is
            #   (otherwise it will get quotes on list to str).
            return value
    value = str(value)
    # big_enclosures = ["OrderedDict(", ")"]
    if is_enclosed(value, "b'", "'") or is_enclosed(value, "u'", "'"):
        if quote_if_like_str:
            return value[1:]  # Only remove b or u not b'' etc.
        else:
            return value[2:-1]
    elif is_str_like(original_value):
        if escape_if_like_str:
            value = value.replace("\r", "\\r").replace("\n", "\\n")
            value = value.replace("\b", "\\b")
            value = value.replace("\t", "\\t")
        if quote_if_like_str:
            if pformat_preferred_quote is None:
                if '"' in value:
                    return "'%s'" % value.replace("'", "\\'")
                else:
                    return '"%s"' % value.replace('"', '\\"')
            else:
                # This is universal but isn't as nice since it will
                #   force escaped quotes. The case above is adaptive.
                quo = pformat_preferred_quote
                return '%s%s%s' % (quo, value.replace(quo, '\\'+quo), quo)
    # elif isinstance(value, OrderedDict)
    return value


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


def write4(arg):
    if verbosity < 4:
        return False
    sys.stderr.write(arg)
    sys.stderr.flush()
    return True


def echo0(*args, **kwargs):  # formerly prerr
    # This level is like logging.CRITICAL
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo1(*args, **kwargs):  # formerly debug
    # This level is like logging.ERROR
    if verbosity < 1:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo2(*args, **kwargs):  # formerly extra
    # This level is like logging.WARNING
    if verbosity < 2:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo3(*args, **kwargs):
    # This level is like logging.INFO
    if verbosity < 3:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo4(*args, **kwargs):
    # This level is like logging.DEBUG
    if verbosity < 4:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def get_verbosity():
    return verbosity


def set_verbosity(verbosity_level):
    """Set verbosity of the console output of the entire module.

    This affects any program(s) using the module.

    Args:
        verbosity_level (int): Level 0 to 3. Some granular decisions
            (any code using echo2) may appear on the console if 2 or
            higher.

    Raises:
        ValueError: If verbosity_level is not within bounds.
    """
    global verbosity
    if verbosity_level not in verbosity_levels:
        v_msg = verbosity_levels
        if isinstance(v_msg, str):
            v_msg = '"{}"'.format(v_msg)
        raise ValueError(
            "verbosity_levels must be one of {} not {}."
            "".format(verbosity_levels, v_msg)
        )
    verbosity = verbosity_level


def get_traceback(indent=""):
    """Get a formatted traceback.

    Args:
        indent (Optional[str]): Indent. Defaults to "".

    Returns:
        str: Traceback, usually multiple lines. Lines
            are delimited by "\n".
    """
    ex_type, ex, tb = sys.exc_info()
    msg = "{}{} {}:\n".format(indent, ex_type, ex)
    msg += traceback.format_exc()
    del tb
    return msg


def view_traceback(indent="", min_indent=None):
    """Write the traceback to stderr.

    Deprecations:
    min_indent keyword argument

    Args:
        min_indent (Optional[str]): indent each line of output this
            much.
    """
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


def to_syntax_error(path, line_n, msg, col=None):
    '''Convert the error to a syntax error
    that specifies the file and line number that has the bad syntax.

    Args:
        col (int, optional): is the character index relative to the
            start of the line, starting at 1 for compatibility with
            outputinspector (which will subtract 1 if using editors that
            start at 0).
    '''
    this_fmt = syntax_error_fmt

    if col is None:
        part = "{column}"
        remove_i = this_fmt.find(part)
        if remove_i > -1:
            suffix_i = remove_i + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:remove_i] + this_fmt[suffix_i:]
    if line_n is None:
        part = "{row}"
        remove_i = this_fmt.find(part)
        if remove_i > -1:
            suffix_i = remove_i + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:remove_i] + this_fmt[suffix_i:]
    return this_fmt.format(path=path, row=line_n, column=col, message=msg)
    # ^ Settings values not in this_fmt is ok.


def echo_SyntaxWarning(path, lineN, msg, col=None):
    msg = to_syntax_error(path, lineN, msg, col=col)
    echo0(msg)
    # ^ So the IDE can try to parse what path&line has an error.


def raise_SyntaxError(path, lineN, msg, col=None):
    echo_SyntaxWarning(path, lineN, msg, col=col)
    raise SyntaxError(msg)

def human_readable(bytes_size):
    """Convert bytes to smallest number in TB, GB, MB, or KB"""
    # NOTE: .format requires Python 2.6 or newer.
    endings = ["bytes", "KB", "MB", "GB", "TB"]
    ending_i = 0
    size = bytes_size
    while size >= 1024.0:
        if ending_i >= len(endings) - 1:
            # already on the largest denominator
            break
        ending_i += 1
        size /= 1024.0
    rounded = round(size, 1)
    # num_str = '%.1g' % (rounded)
    # %.1: 1 decimal
    # g: remove insignificant decimals
    # ^ for some reason returns exponential notation for 512.
    #   There is no way to round and remove insignificant decimals
    #   without Python 3.6, so for backward compatibility:
    if rounded == int(rounded):
        num_str = str(int(rounded))
    else:
        num_str = '%.1f' % (rounded)

    return "%s%s" % (num_str, endings[ending_i])