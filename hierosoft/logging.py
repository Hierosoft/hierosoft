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


def view_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    print("{}{} {}: ".format(indent, ex_type, ex), file=sys.stderr)
    traceback.print_tb(tb)
    del tb
    print("", file=sys.stderr)
