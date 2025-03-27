"""
The moresix module is an addendum to six (the Python 3 compatibility
module for Python 2, with features listed at
<https://six.readthedocs.io/>), and may serve as a source for code
contributions to six, so this file should be completely modular (able to
be copied anywhere and still work).

See also seven, a project that helps Python 2.7 code work on Python 2.5.

MIT License
"""
# Copyright (c) 2010-2024 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import sys

# endregion Polyfills that can be copied to other files
# (or use moresix.subprocess_run etc. explicitly to avoid that)
import subprocess

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError
    NotADirectoryError = OSError
    # ^ such as:
    #   "NotADirectoryError: [Errno 20] Not a directory: '...'" where
    #   "..." is a file and the call is os.listdir.

if sys.version_info.major >= 3:
    # from subprocess import run as subprocess_run

    # Globals used:
    # import subprocess
    from subprocess import CompletedProcess
    from subprocess import run as subprocess_run
else:
    class CompletedProcess:
        """This is a Python 2 substitute for the Python 3 class.
        This implementation endeavors to maintain feature parity with
        the Python 3 documentation:
        <https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess>
        """
        _custom_impl = True

        def __init__(self, args, returncode, stdout=None, stderr=None):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

        def check_returncode(self):
            if self.returncode != 0:
                err = subprocess.CalledProcessError(self.returncode,
                                                    self.args,
                                                    output=self.stdout)
                raise err
            return self.returncode

    def subprocess_run(*popenargs, **kwargs):
        '''subprocess.run substitute for Python 2
        CC BY-SA 4.0
        by Martijn Pieters
        https://stackoverflow.com/a/40590445
        and Poikilos
        '''
        this_input = kwargs.pop("input", None)
        check = kwargs.pop("handle", False)

        if this_input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not '
                                 'both be used.')
            kwargs['stdin'] = subprocess.PIPE

        process = subprocess.Popen(*popenargs, **kwargs)
        try:
            outs, errs = process.communicate(this_input)
        except Exception as ex:
            process.kill()
            process.wait()
            raise ex
        returncode = process.poll()
        # print("check: {}".format(check))
        # print("returncode: {}".format(returncode))
        if check and returncode:
            raise subprocess.CalledProcessError(returncode, popenargs,
                                                output=outs)
        return CompletedProcess(popenargs, returncode, stdout=outs,
                                stderr=errs)
    subprocess.run = subprocess_run

# endregion Polyfills that can be copied to other files


if sys.version_info.major < 3:
    import time


def datetime_timestamp(now, emulate_python2=False):
    """Convert a datetime object to a timestamp (seconds).
    A datetime instance does not have a timestamp method in Python 2.

    Args:
        now (datetime): Any datetime object such as
            datetime.datetime.now()
        emulate_python2 (bool, optional): Return a number rounded to
            nearest 1's place but still a float, like Python 2. Set to
            True to make output format identical on Python 3. Defaults
            to False.

    Returns:
        float: POSIX timestamp (number seconds passed since epoch),
            with decimal places (representing fractions of a second) if
            using Python 3 and emulate_python2 is False.
    """
    if sys.version_info.major >= 3:
        if emulate_python2:
            return float(round(now.timestamp()))
        return now.timestamp()  # more accurate (Python 3 only)
        # NOTE: "Naive datetime instances are assumed to represent
        #   local time and this method relies on the platform C
        #   mktime()"
        #   -<https://docs.python.org/3/library/datetime.html
        #    #datetime.datetime.timestamp>
        # otherwise:
        # now.replace(tzinfo=timezone.utc).timestamp()
    return time.mktime(now.timetuple())  # round in Python 2
    #   (accurate to the second) but still float
