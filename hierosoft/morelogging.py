# -*- coding: utf-8 -*-
'''
This submodule provides logging features such as for handling verbosity
and representation of data in human-readable form.

This module can't import hierosoft or it would be a circular dependency
(It would cause an incomplete module error and stop the program).
'''
from __future__ import print_function
import sys
import traceback
import os

from collections import OrderedDict

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0
MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

# import hierosoft.moreweb  # avoid this--circular import

if sys.version_info.major >= 3:
    import logging
    from logging import (
        Formatter,
        Logger,
        Handler,
        getLogger,
    )
else:
    # Polyfills for Python 2
    FORMAT_STYLES = ['%', '{', '$']
    class Formatter:
        def __init__(self, fmt=None, datefmt=None, style='%',
                     validate=True, defaults=None):
            # FIXME  validate=True, *, defaults=None):  what? (upstream code)
            if fmt is None:
                fmt = '%(message)s'
            self.fmt = fmt
            if style not in FORMAT_STYLES:
                raise ValueError("style was %s but should be one in %s"
                                 % (style, FORMAT_STYLES))
            self.style = style
            self.t = None
            if style == "$":
                import string
                self.t = string.Template(fmt)
            # region attributes in upstream not implemented here yet
            self.datefmt = datefmt
            self.validate = validate
            self.defaults = defaults
            # endregion attributes in upstream not implemented here yet

        def format(self, message):
            if self.style == "%":
                return self.fmt % {'message': message}
            elif self.style == "{":
                return self.fmt.format(message=message)
            elif self.style == "$":
                # such as "Error: $message in some method"
                return self.t.substitute(message=message)
            else:
                raise ValueError("style was %s but should be one in %s"
                                 % (self.style, FORMAT_STYLES))
    default_formatter = Formatter()

    class Logger:
        def __init__(self, name):
            self.name = name
            self.level = 30
            # region attributes in upstream not implemented here yet
            # (via logger = logging.getLogger(); dir(logger)
            #   in Python 3.11 on Windows)
            # self._cache = None
            self._log = sys.stderr
            self.disabled = False
            # self.filter
            # self.filters
            self.handlers = []
            # self.hasHandlers
            # self.manager
            # self.parent
            # self.propogate = True
            # ^ if propogate, pass events to higher level handlers too
            # self.root
            # endregion attributes in upstream not implemented here yet

        # region methods in upstream not implemented here yet
        # def addFilter(self, ):
        # def addHandler(self, ):
        # def callHandlers(self, ):
        # def findCaller(self, ):
        # def getChild(self, ):
        # def log(self, ):
        # def makeRecord(self, ):
        # def removeFilter(self, ):
        # def removeHandler(self, ):
        # endregion methods in upstream not implemented here yet

        def isEnabledFor(self, level):
            return False if level < self.level else True

        def handle(self, record):
            # TODO: make a record class??
            for handler in self.handlers:
                handler.format(record)
                handler.emit(record)
            # TODO: check own formatter instead of code below
            print(default_formatter.format(record), file=self._log)

        def getEffectiveLevel(self):
            if self.level >= CRITICAL:
                return CRITICAL
            if self.level >= ERROR:
                return ERROR
            if self.level >= WARNING:
                return WARNING
            if self.level >= INFO:
                return INFO
            if self.level >= DEBUG:
                return DEBUG
            return NOTSET

        def critical(self, msg):
            if CRITICAL < self.level:
                return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s\n" % msg)
            self._log.flush()

        def debug(self, msg):
            if DEBUG < self.level:
                return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s\n" % msg)
            self._log.flush()

        def error(self, msg):
            if ERROR < self.level:
                return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s\n" % msg)
            self._log.flush()

        def exception(self, ex):
            # if ERROR < self.level:
            #     return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s: %s\n" % (type(ex).__name__, ex))
            self._log.flush()

        def fatal(self, msg):
            # if ERROR < self.level:
            #     return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s" % (msg) + "\n")
            self._log.flush()

        def info(self, msg):
            if INFO < self.level:
                return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s" % (msg) + "\n")
            self._log.flush()

        def setLevel(self, level):
            self.level = level

        def warn(self, msg):
            print("<stdin>:1: DeprecationWarning:"
                  " The 'warn' method is deprecated, use 'warning' instead")
            self.warning(msg)

        def warning(self, msg):
            if WARNING < self.level:
                return
            # prefix = "" if self.name is None else "[%s] " % self.name
            self._log.write("%s" % (msg) + "\n")
            self._log.flush()

    class Handler:
        def __init__(self, level=NOTSET):
            raise NotImplementedError("Handler")
    loggers = {}
    # class logging:
    filename = None
    encoding = 'utf-8'

    def getLogger(self, name=None):
        logger = loggers.get(name)  # None is allowed (root of hierarchy)
        if logger is not None:
            return logger
        return Logger(name)

    def basicConfig(**kwargs):
        global filename
        global encoding
        string_keys = ['filename', 'encoding']
        for key, value in kwargs.items():
            if key in string_keys:
                if type(value).__name__ not in ("str", "unicode"):
                    # ^ Do not use isinstance, since unicode is not in Python 3
                    #   (every str is unicode)
                    raise TypeError("Expected str/unicode for %s but got %s %s"
                                    % (key, type(value).__name__, value))
            if key == "filename":
                filename = value
            elif key == "encoding":
                encoding = value


to_log_level = {
    3: 10,
    2: 20,
    1: 30,
    True: 30,
    0: 40,
    False: 40,
}

verbosity_levels = [False, True, 0, 1, 2, 3]

verbosity = 0
for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
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
        vMsg = verbosity_levels
        if isinstance(vMsg, str):
            vMsg = '"{}"'.format(vMsg)
        raise ValueError(
            "verbosity_levels must be one of {} not {}."
            "".format(verbosity_levels, vMsg)
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
