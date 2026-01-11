# -*- coding: utf-8 -*-
'''
This submodule provides logging features such as for handling verbosity
and representation of data in human-readable form.

This module can't import hierosoft or it would be a circular dependency
(It would cause an incomplete module error and stop the program).
'''
from __future__ import print_function
from __future__ import division
import inspect
import re
import sys
import traceback
import os
import warnings

from collections import OrderedDict

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)

echo_stack_trace = None
echo_multiline = True

# frame is a namedtuple in Python 3, but tuple in Python 2:
# (frame, filename, lineno, function, context, index)
# so:
STACK_ELEMENT_FRAME_IDX = 0
STACK_ELEMENT_FUNCTION_IDX = 3

verbosity = 2  # 2 to mimic Python 3 logging default WARNING (30)

space_nospace_rc = re.compile(r'(\s*)(.*)')

log_path = "stderr.txt"  # None for no file-based logging
log_mode = "w"  # changed to "a" after first use.

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

# import hierosoft.moreweb  # avoid this--circular import


def set_echo_multiline(enable):
    global echo_multiline
    if enable not in (True, False):
        raise ValueError(
            "Expected True or False for enable, got {}".format(enable))
    echo_multiline = enable


def set_echo_stack_trace(enable):
    global echo_stack_trace
    if enable not in (True, False):
        raise ValueError(
            "Expected True or False for enable, got {}".format(enable))
    echo_stack_trace = enable


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

for _arg_i in range(1, len(sys.argv)):
    arg = sys.argv[_arg_i]
    if arg.startswith("--"):
        if arg == "--verbose":
            verbosity = 1
        elif arg == "--debug":
            verbosity = 2


def formatted_ex(ex):
    """Similar to traceback.format_exc but works on any not just current
    (traceback.format_exc only uses exception occurring, not argument!)
    """
    return "{}: {}".format(type(ex).__name__, ex)


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


def is_enclosed(value, start, end):
    if len(value) < len(start) + len(end):
        return False
    return value.startswith(start) and value.endswith(end)


def is_str_like(value):
    return type(value).__name__ in ("str", "bytes", "bytearray", "unicode")


emit_quote = None  # < See set_emit_quote's quote arg documentation


def set_emit_quote(quote):
    """Set the global emit_quote
    '"' is used if None (default).

    Args:
        quote (str): Set emit_quote to this. Defaults to
            adaptive ("'" if "'" not in value else '"' when
            emit_quote is None).
    """
    # formerly set_hr_repr_preferred_quote
    global emit_quote
    emit_quote = quote


def hr_repr(value, quote_if_like_str=None, escape_if_like_str=None):
    """Human-readable repr is mostly like pformat from pprint
    except without newlines (existing ones get escaped).

    Numbers are left as numbers even if quote_if_like_str is True, to
    avoid adding extra quotes. Use set_emit_quote to set
    the preferred quote.

    Args:
        value: any value that can convert to str. Values in
            an iterable will be processed recursively first.
        quote_if_like_str (Optional[bool]): Do not use this option, or
            your hr_repr calls will be incompatible with
            (will have call signature different from)
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
    # formerly named pformat (same name as with pprint's pformat but
    #   different args so renamed)
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
                    parts[key] = hr_repr(item, quote_if_like_str=False)
                if isinstance(parts, OrderedDict):
                    return str(parts).replace("OrderedDict", "")[1:-1]
                return parts
            for i, item in enumerate(value):
                iterated = True
                parts.append(hr_repr(item, quote_if_like_str=False))
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
            if emit_quote is None:
                if '"' in value:
                    return "'%s'" % value.replace("'", "\\'")
                else:
                    return '"%s"' % value.replace('"', '\\"')
            else:
                # This is universal but isn't as nice since it will
                #   force escaped quotes. The case above is adaptive.
                quo = emit_quote
                return '%s%s%s' % (quo, value.replace(quo, '\\'+quo), quo)
    # elif isinstance(value, OrderedDict)
    return value


def write0(msg, traceback_start=2, stack_trace=True):
    """Write to stderr & flush but do not add a newline.

    Args:
        msg (str): Message for stderr
        traceback_start (int, optional): Where to start in the traceback
            (set automatically). Defaults to 2.
        stack_trace (bool, optional): Show the stack trace as a prefix
            in square brackets. Defaults to True.

    Returns:
        bool: Whether message is shown (always True, but returned to
            match behavior of other write functions).
    """
    return echo0(msg, traceback_start=traceback_start, add_newline=False,
                 stack_trace=stack_trace)


def write1(msg):
    if verbosity < 1:
        return False
    return write0(msg, traceback_start=3)


def write2(msg):
    if verbosity < 2:
        return False
    return write0(msg, traceback_start=3)


def write3(msg):
    if verbosity < 3:
        return False
    return write0(msg, traceback_start=3)


def write4(msg):
    if verbosity < 4:
        return False
    return write0(msg, traceback_start=3)


def _print(*args, **kwargs):
    global log_mode
    print(*args, **kwargs)
    if log_path is None:
        return True
    with open(log_path, log_mode) as stream:
        log_mode = "a"
        kwargs['file'] = stream
        print(*args, **kwargs)
    return True


def _write(msg):
    global log_mode
    sys.stderr.write(msg)
    if log_path is None:
        return True
    with open(log_path, log_mode) as stream:
        log_mode = "a"
        stream.write(msg)
    return True


def _flush():
    if log_path is None:
        sys.stderr.flush()
        return
    # else nothing to do (written in realtime)


def echo0_long(*args, **kwargs):  # formerly prerr
    """Show the message and abbreviated callstack
    Example output: "[__main__ loggingdemo.__init__ foo] Hi"
    where __main__ is Python __main__ and foo is the function
    that called echo0, and "Hi" is the message (args).

    For other purposes, logging2 replaces echo methods.

    For additional arguments, see print. kwargs['file'] defaults to
        sys.stderr.

    Args:
        traceback_start (int, optional): Where in the traceback to
            start. Reserved for use by other echo functions to skip
            themselves (start=2). Defaults to 1 (only skip echo0 itself).
        multiline (bool, optional): Write "  At: " then traceback on
            a separate line (False formats the traceback as a prefix in
            square brackets on the single line output). Defaults to
            echo_multiline (True since easier to notice actual message
            [as in args] if starts at beginning of line, and works
            well if write* was used on same line).
        stack_trace (bool, optional): Whether a stack trace
            (reversed traceback, most recent call last) should be shown.
            Defaults to global echo_stack_trace.
    """
    # This level is like logging.CRITICAL
    # logging.CRITICAL = 50
    if echo_stack_trace is None:
        echo_stack_trace = get_verbosity() >= 3
    stack_trace = kwargs.pop('stack_trace', echo_stack_trace)

    if not stack_trace:
        if 'file' not in kwargs:
            kwargs['file'] = sys.stderr
            # ^ this way prevents dup named arg in print
        print(*args, **kwargs)
        return

    multiline = kwargs.pop('multiline', echo_multiline)
    start = 1  # only skip self (keep caller)
    skip = kwargs.pop('traceback_start', None)  # default prevents KeyError
    if skip:
        start = int(skip)
    stack = inspect.stack()
    # current_frame = inspect.currentframe()
    # call_frame = inspect.getouterframes(current_frame, 2)
    # stack_str = ""
    prefix = ""
    line2 = None
    if len(stack) >= start + 1:
        # Show the callstack during print
        # for i in range(1, len(call_frame)):
        # [3] is caller_name (but works with older Python)
        # module = inspect.getmodule(call_frame[i]) # always "inspect"...
        # name = call_frame[i][3]
        # if not isinstance(name, str):
        # if module and hasattr(module, '__name__'):
        #     # name = name.__name__
        #     name = module.__name__
        # stack_str = name + " " + stack_str
        names = []
        # print("frame={}".format(frame))
        parent_i = 1
        index = parent_i - 1  # -1 since +1 is done right away
        for i, frame_info in enumerate(stack[parent_i:]):  # Skip self frame
            index += 1
            # Since stack[start:] misses grandparent name (probably
            #   since no parent), don't use skip start until info is gathered.
            # Get the module name for each frame
            frame = frame_info[STACK_ELEMENT_FRAME_IDX]
            function_name = frame_info[STACK_ELEMENT_FUNCTION_IDX]
            module = inspect.getmodule(frame)
            module_name = module.__name__ if module and hasattr(module, '__name__') else '<module>'
            # if module_name == "__main__" and hasattr(module, '__file__') and module.__file__:
            #     module_name = module.__file__
            # ^ doesn't work (__main__ is set below)
            # Prepend module name only if this frame is below the main script
            class_name = None
            if "self" in frame.f_locals:
                class_name = frame.f_locals["self"].__class__.__name__
            # Build the name with module, class (if any), and function
            if class_name:
                name = "{}.{}.{}".format(module_name, class_name, function_name)
            else:
                name = "{}.{}".format(module_name, function_name)
            # Prepend module name only for the parent of the main script
            if index < start:
                continue
            if i == len(stack) - 2:  # Main script frame
                names.append("__main__")
            elif i == len(stack) - 3:  # Parent of main script
                names.append(name)
            else:
                names.append(function_name)
        names_str = "{}".format(" ".join(reversed(names)))
        # Remove unnamed module, replace multiple-whitespace with " ":
        names_str = " ".join(
            names_str.replace(".<module>", "").replace("<module>", "")
            .split()
        )
        prefix = "[{}] ".format(names_str)
        if multiline:
            line2 = "  At: {}".format(names_str)
        elif not args:
            args = [prefix]
        else:
            if prefix not in args[0]:
                # Cast since tuple doesn't support item assignment:
                args = [prefix] + list(args)  # just keep others intact,
                #   since print takes almost anything (such as if a
                #   single arg is an iterable or other non-str)
                args = tuple(args)
    # Python 2 (without print_function) print >> sys.stderr, args
    if 'file' not in kwargs:
        kwargs['file'] = sys.stderr  # this way prevents dup named arg in print
    print(*args, **kwargs)
    if line2 and args and args[0]:
        print(line2, file=sys.stderr)
    return True


def echo0(*args, **kwargs):
    """Show the message and the most recent call in the callstack.

    Example output: "[__main__ foo] Hi"
    where __main__ is the Python __main__ and foo is the function
    that called echo0, and "Hi" is the message (args).

    Args:
        stack_trace (bool, optional): Whether a stack trace
            (reversed traceback, most recent call last) should be shown.
            Defaults to echo_stack_trace (True if log level is INFO or
            DEBUG on first call of echo0, otherwise False).
        traceback_start (int, optional): Where in the traceback to start
            (skip frames). Defaults to 1 (only skip echo0 itself).
        multiline (bool, optional): Write "  At: " then traceback on a
            separate line. Defaults to global echo_multiline, True since
            message (args) is readable if at beginning of line, and
            works well if write* was done on same line.
        add_newline (bool, optional): The line ends (Use print to
            sys.stderr rather than sys.stderr.write+flush). Defaults to
            True.
    """
    global echo_stack_trace
    if echo_stack_trace is None:
        echo_stack_trace = get_verbosity() >= 3

    add_newline = kwargs.pop('add_newline', True)
    stack_trace = kwargs.pop('stack_trace', echo_stack_trace)
    multiline = kwargs.pop("multiline", True)
    start = kwargs.pop("traceback_start", 1)
    if not stack_trace:
        if add_newline:
            if 'file' not in kwargs:
                kwargs['file'] = sys.stderr
                # ^ this way prevents dup named arg in print
            _print(*args, **kwargs)
        else:
            if args and args[0]:
                _write(args[0])
                _flush()
        return

    stack = inspect.stack()
    names_str = None
    line2 = None
    if len(stack) > start:
        frame_info = stack[start]
        frame = frame_info[STACK_ELEMENT_FRAME_IDX]
        function_name = frame_info[STACK_ELEMENT_FUNCTION_IDX]
        module = inspect.getmodule(frame)
        module_name = (
            module.__name__ if module and hasattr(module, "__name__") else "__main__"  # noqa:E501
        )
        class_name = (
            frame.f_locals["self"].__class__.__name__
            if "self" in frame.f_locals
            else None
        )
        if class_name:
            names_str = "{}.{}.{}".format(module_name, class_name,
                                          function_name)
        else:
            names_str = "{}.{}".format(module_name, function_name)

        if multiline:
            line2 = "  At: {}".format(names_str)
        else:
            prefix = "[{}]".format(names_str)
            if args and args[0]:
                # Get the tab & place it before the prefix
                #   (safe: not-found group(s) still return '' string)
                tab, no_tab = space_nospace_rc.match(args[0]).groups()
                args = (tab+prefix,) + (no_tab,) + args[1:]
            else:
                args = (prefix,) + args
            # print adds a *space* between sequential args.

    if add_newline:
        kwargs['file'] = sys.stderr
        _print(*args, **kwargs)
    else:
        if args and args[0]:
            _write(args[0])
            _flush()

    if line2 and args and args[0]:
        if add_newline:
            _print(line2, file=sys.stderr)
        # else line isn't over yet, so do not show line2
        #   (add_newline is expected later in client code
        #   if add_newline is False this time.)
    return True


def echo1(*args, **kwargs):  # formerly debug
    # This level is like logging.ERROR
    if verbosity < 1:
        return False
    kwargs['traceback_start'] = 2
    echo0(*args, **kwargs)
    return True


def echo2(*args, **kwargs):  # formerly extra
    # This level is like logging.WARNING
    if verbosity < 2:
        return False
    kwargs['traceback_start'] = 2
    echo0(*args, **kwargs)
    return True


def echo3(*args, **kwargs):
    # This level is like logging.INFO
    if verbosity < 3:
        return False
    kwargs['traceback_start'] = 2
    echo0(*args, **kwargs)
    return True


def echo4(*args, **kwargs):
    # This level is like logging.DEBUG
    if verbosity < 4:
        return False
    kwargs['traceback_start'] = 2
    echo0(*args, **kwargs)
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
