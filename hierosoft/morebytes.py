# -*- coding: utf-8 -*-
from __future__ import print_function
import binascii
import os
import shutil
import sys
import re
import tempfile

from hierosoft import (
    echo0,
    echo1,
    echo2,
    write0,
)


BYTE_STR_TYPES = (bytes, bytearray)
if sys.version_info.major < 3:
    # In Python 2, str is same as bytes (not unicode)
    BYTE_STR_TYPES = (bytes, bytearray, str)


def crc16_buypass(data):
    """Calculate the hash using the CRC16 BUYPASS algorithm.

    by [Sz'](https://stackoverflow.com/users/2278704/sz)
    <https://stackoverflow.com/a/60604183>
    Mar 9, 2020 at 15:56

    Returns:
        int: An integer that can fit in a word (two bytes)
    """
    assert isinstance(data, (bytes))
    xor_in = 0x0000  # initial value
    xor_out = 0x0000  # final XOR value
    poly = 0x8005  # generator polinom (normal form)
    reg = xor_in
    for octet in data:
        # reflect in
        for i in range(8):
            top_bit = reg & 0x8000
            if octet & (0x80 >> i):
                top_bit ^= 0x8000
            reg <<= 1
            if top_bit:
                reg ^= poly
        reg &= 0xFFFF
        # reflect out
    return reg ^ xor_out


def crc16_modbus(data, offset=0, length=None):
    """Calculate the hash using the CRC16 MODBUS algorithm.

    answered May 1, 2019 at 8:16 by user11436151
    edited Feb 26, 2020 at 13:45 by Matphy
    https://stackoverflow.com/a/55933366

    Args:
        data (bytearray): _description_
        offset (int, optional): _description_. Defaults to 0.
        length (_type_, optional): _description_. Defaults to None.

    Returns:
        int: An integer that can fit in a word (two bytes)
    """
    assert isinstance(data, (bytes, bytearray))
    if length is None:
        length = len(data)
    if ((data is None) or (offset < 0) or (offset > len(data) - 1)
            and (offset + length > len(data))):
        return 0
    print("uzunluk=", len(data))
    print(data)
    crc = 0xFFFF
    for i in range(length):
        crc ^= data[offset + i]
        for j in range(8):
            print(crc)
            if ((crc & 0x1) == 1):
                print("bb1=", crc)
                crc = int((crc / 2)) ^ 40961
                print("bb2=", crc)
            else:
                crc = int(crc / 2)
    return crc & 0xFFFF


def crc16_ccit_false(data, offset=0, length=None):
    '''Python implementation of CRC-16/CCITT-FALSE

    (output matches CRC-16 button's CCITT-FALSE output on
    <https://crccalc.com/>).
    answered Apr 25, 2019 at 13:31
    CC BY-SA 4.0 Amin Saidani
    <https://stackoverflow.com/a/55850496/4541104>
    '''
    assert isinstance(data, (bytes, bytearray))
    if length is None:
        length = len(data)
    if ((data is None) or (offset < 0) or (offset > len(data) - 1)
            and (offset+length > len(data))):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0, 8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF


def to_hex(bytestring, delimiter=""):
    '''
    Represent the binary as an ASCII string of hexadecimal characters.
    in Python 3.5+, this isn't necessary a you can do:
    bytestring.hex(" "). Therefore, this function is only for
    backward compatibility.

    Sequential arguments:
    binary -- A "bytes" or "bytearray" object.

    Keyword arguments:
    delimiter -- Place this between each byte (each hex pair).
    '''
    assert isinstance(bytestring, BYTE_STR_TYPES)

    # import binascii
    if (delimiter is not None) and (len(delimiter) > 0):
        if sys.version_info.major >= 3:
            return " ".join(["{:02x}".format(x) for x in bytestring])
        else:
            return " ".join(["%02x" % ord(x) for x in bytestring])

    return binascii.hexlify(bytestring).decode('utf-8')  # no delimiter


def split_words(value):
    '''
    Split a 32-bit integer into two 16-bit values (but each in int
    form).

    Returns:
    A tuple of (HIWORD, LOWORD).
    '''
    return (value >> 16, value % 65536)


def endswith_bytes(haystack, needle):
    '''
    Check if a bytearray ends with another bytearray (needle).
    Alternatively, either haystack or needle can be bytes (A "bytes"
    object and "bytearray" object can be accurately compared as a whole
    or as a slice to the other type).

    This function exists to avoid exceptions when the length differs
    but to raise exceptions when the type differs. For example, if
    needle is accidentally an integer (such as the result of
    subscripting a bytearray) then the "len" function will raise an
    exception. If len was not called, the "==" case would never occur
    because bytearray haystack[-1] is never needle if needle is a
    bytearray because a subscripted bytearray results in an int!
    '''
    if not isinstance(haystack, type(needle)):
        raise TypeError(
            "Type mismatch: %s %s %s %s"
            % (type(haystack).__name__, haystack,
               type(needle).__name__, needle)
        )
    if len(needle) < 1:
        return ValueError("needle is blank")
    if len(haystack) < len(needle):
        return False
    return haystack[-len(needle):] == needle


def startswith_bytes(haystack, needle):
    """Check if str, bytes, or bytearray startswith needle

    Args:
        haystack (Union[str,bytes,bytearray]): any string
        needle (Union[str,bytes,bytearray]): what to try to find in haystack
    """
    if not isinstance(haystack, type(needle)):
        raise TypeError(
            "Type mismatch: %s != %s (%s != %s)"
            % (type(haystack).__name__, type(needle).__name__,
               repr(haystack), repr(needle))
        )
    if len(needle) < 1:
        return ValueError("needle is blank")
    if len(haystack) < len(needle):
        return False
    return haystack[:len(needle)] == needle


def find_any(haystack, needles, start=0, end=None, whitespace_also=False):
    '''
    Keyword arguments:
    whitespace_also -- Also find whitespace.
    '''
    result = -1
    if end is None:
        end = len(haystack)
    for needle in needles:
        result = haystack.find(needle, start, end)
        if result > -1:
            break
    if whitespace_also:
        for i in range(start, end):
            if haystack[i:i+1].strip() != haystack[i:i+1]:
                # ^ slice, otherwise will be an int if is bytearray or
                #   bytes!
                if ((result < 0) or (i < result)):
                    result = i
                break
    return result


def find_any_not(haystack, needles, not_whitespace_either=False, start=0,
                 end=None):
    '''
    Sequential arguments:
    haystack -- The string to search.
    needles -- characters or phrases to skip (*not* count as match).

    Keyword arguments:
    not_whitespace_either -- If True, do not count whitespace as a
        match either.
    '''
    if end is None:
        end = len(haystack)
    pos = start - 1
    while pos < len(haystack):
        pos += 1
        if not_whitespace_either:
            if haystack[pos:pos+1].strip() != haystack[pos:pos+1]:
                # ^ must slice, otherwise will be int if bytearray or
                #   bytes!
                continue
        for needle in needles:
            if startswith_bytes(haystack[pos:], needle):
                pos += len(needle) - 1
                # ^ -1 since 1 will be added at start of next loop.
                #   For example, if startswith "REM " then set index
                #   from 4 to 3 and then it will continue after the
                #   " " after the +=1 at the top of the loop.
        return pos
    return -1


def startswith_any(haystack, needles):
    for needle in needles:
        if startswith_bytes(haystack.lstrip(), needle):
            return True
    return False


def no_b(text_bytes):
    """Remove the 3 characters b'' from encoded bytes.
    """
    text = str(text_bytes)
    if startswith_bytes(text, "b'") and startswith_bytes(text, "'"):
        return text[2:-1]  # remove leading "b'" & trailing "'"
    return text


class Byter:
    '''
    Edit a file regardless of those naggy old encodings. Detect the
    newline character on load, otherwise use the system's default.

    Public attributes:
    padded_assignment_operator -- Set padded_assignment_operator as
        anything you want as long as syntax is proper. New values will
        have this in between. For example, if the syntax allows spaces
        around the operator, padded_assignment_operator can be " = "
        where "=" is in assignment operators (Warning:
        padded_assignment_operator cannot have spaces in shell script
        and likely some other languages).
    '''
    # TODO: merge this code with newer rewrite_conf (may be more
    #   fault-tolerant)
    def __init__(self):
        self.path = None
        self.comment_marks = [b"#"]
        self.assignment_operators = [b":"]
        self.padded_assignment_operator = b":"
        self.newline = os.linesep.encode('utf-8')
        self.changes = 0

    def load(self, path):
        with open(path, 'rb') as ins:
            self.data = ins.read()
        self.cursor = 0
        self.path = path
        i = -1
        self.newline = None
        while True:
            i += 1
            if i >= len(self.data):
                break
            if self.data[i] == b'\r':
                if (i + 1) < len(self.data):
                    if self.data[i+1] == b'\n':
                        self.newline = b'\r\n'
                        break
                self.newline = b'\r'
                break
            elif self.data[i] == b'\n':
                self.newline = b'\n'
                break
        if self.newline is None:
            self.newline = os.linesep.encode('utf-8')
            echo0('[Byter load] No newline was detected in "{}".'
                  ' os.linesep {} will be used.'
                  ''.format(os.path.basename(path), self.newline))
        else:
            echo0('[Byter load] detected newline={}'
                  ''.format(self.newline))
        self.changes = 0

    def readline(self):
        '''
        Returns:
        A line including newline character(s), or "" if none left
        (Both cases match Python's file object behavior by design).
        '''
        if self.cursor >= len(self.data):
            return ""
        start_i = self.cursor
        data = self.data
        ender_i = None
        self.cursor -= 1
        while True:
            self.cursor += 1
            if self.cursor >= len(self.data):
                break
            i0 = self.cursor
            i1 = self.cursor + 1
            if i1 >= len(self.data):
                i1 = None
            if data[i0] == "\r":
                ender_i = i0 + 1  # + 1 to include it with exclusive slice
                if i1 is not None:
                    if data[i1] == "\n":
                        ender_i += 1
                    # else allow for os with \r only
                # else allow for os with \r only
                break
            elif data[i0] == "\n":
                # ok since already checked for \r\n above.
                ender_i = i0 + 1  # + 1 to include it with exclusive slice
                break
        if ender_i is None:
            ender_i = len(self.data)
        self.cursor = ender_i
        return self.data[start_i:ender_i]

    def seek(self, cursor):
        '''Set the cursor location in the file.'''
        if cursor < 0:
            raise IndexError("cursor={}".format(cursor))
        if cursor >= len(self.data):
            raise IndexError("cursor=%s, len=%s"
                             % (cursor, len(self.data)))
        self.cursor = cursor

    def seek_to_next_line(self):
        if self.cursor >= len(self.data):
            return
        while True:
            self.cursor += 1
            if self.cursor >= len(self.data):
                return
            if self.data[self.cursor] in [b'\r', b'\n']:
                if self.data[self.cursor] == b'\r':
                    if self.cursor + 1 < len(self.data):
                        if self.data[self.cursor+1] == b'\n':
                            self.cursor += 1
                            return
                        # else allow only 'r' newlines
                    # else allow only 'r' newlines
                return

    def _value_slice(self, name, value, allow_commented=False):
        prev_cursor = self.cursor
        aos = self.assignment_operators
        self.seek(0)
        if isinstance(name, str):
            name = name.encode("utf-8")
        if isinstance(value, str):
            value = value.encode("utf-8")
        slice_pair = None
        line_n = 0
        while True:
            line_n += 1  # Counting numbers start at 1.
            start_i = self.cursor
            line = self.readline()
            if not line:  # ""
                break
            next_line_i = start_i + len(line)
            comment_i = find_any(self.data, self.comment_marks, start=start_i,
                                 end=next_line_i)
            name_i = self.data.find(name, start_i, next_line_i)
            if name_i < 0:
                continue
            if ((comment_i > -1) and (comment_i < name_i)):
                if not allow_commented:
                    continue
            name_ender_i = name_i + len(name)
            if name_ender_i == len(self.data):
                slice_pair = (name_ender_i, name_ender_i)  # 0 chars
                break
            sign_i = find_any(self.data, aos, whitespace_also=True,
                              start=name_ender_i, end=next_line_i)
            if sign_i < 0:
                # There are more characters, so it is not really a
                #   match. For example, name was "x" but here is "x1"
                #   or something else before space or
                #   assignment_operator.
                continue
            endbefore_i = find_any(self.data, [b'\r', b'\n'],
                                   start=name_ender_i, end=next_line_i)
            if endbefore_i < 0:
                endbefore_i = len(self.data)
            if ((comment_i > -1) and (comment_i < endbefore_i)):
                endbefore_i = comment_i
            value_i = find_any_not(self.data, aos, not_whitespace_either=True,
                                   start=name_ender_i, end=endbefore_i)

            if value_i < 0:
                endbefore_near_i = endbefore_i
                if endbefore_near_i < 0:
                    endbefore_near_i = name_ender_i + 10
                if endbefore_near_i >= len(self.data):
                    endbefore_near_i = len(self.data)
                if (endbefore_near_i - name_ender_i) > 10:
                    endbefore_near_i = name_ender_i + 10
                echo0('File "{}", line {}: Warning: The name ended'
                      ' but the value did not start (near "{}")!'
                      ''.format(self.path, line_n,
                                no_b(self.data[name_ender_i:
                                               endbefore_near_i])))
                # ^ [1:] to remove "b" from "b' some text'"
                #   a bash-style
                slice_pair = (endbefore_i, endbefore_i)  # 0 chars
                # ^ Ok since is either before comment or newline
                break
            value_ender_i = find_any(self.data, [], whitespace_also=True,
                                     start=value_i, end=endbefore_i)
            # ^ [] to *only* find whitespace.
            if value_ender_i < 0:
                # It ends at the comment or end of file or newline.
                slice_pair = (value_i, endbefore_i)
                break
            # It ends at whitespace:
            slice_pair = (value_i, value_ender_i)
            break

        self.cursor = prev_cursor
        return slice_pair

    def set(self, name, value):
        if type(value).__name__ not in ['bytes', 'bytearray']:
            value = str(value).encode('utf-8')
        pao = self.padded_assignment_operator
        prev_cursor = self.cursor
        slice_pair = self._value_slice(name, value)
        commented = False
        if slice_pair is None:
            slice_pair = self._value_slice(name, value, allow_commented=True)
            if slice_pair is not None:
                self.cursor = slice_pair[1]
                self.seek_to_next_line()
                # If it is a comment, add it at the beginning of the
                # next line.
                slice_pair = (self.cursor, self.cursor)
        old_value = self.data[slice_pair[0]:slice_pair[1]]
        new = value
        if commented:
            # The slice was already placed at the end of the line.
            new = name + pao + value + self.newline
        if old_value != new:
            echo0('[set] changing {} to {}'.format(old_value, value))
            data = self.data
            self.data = data[:slice_pair[0]] + new + data[slice_pair[1]:]
            self.changes += 1
        if slice_pair[0] < prev_cursor:
            prev_cursor += len(new) - len(old_value)
        self.cursor = prev_cursor

    def save(self):
        if self.changes < 1:
            echo0("[Byter save] Warning:"
                  " There are no tracked changes (saving anyway).")
        with open(self.path, 'wb') as outs:
            outs.write(self.data)
            self.changes = 0


# TODO: Make sure slicer/octoprint really adds the following G-code
#  progress commands (including in Klipper if has any effect):
'''
From the default config:
NOTES:
  - Time mode needs info from the G-code file such as the elapsed time
    or the remaining time. This info can be supplied as "M73 Rxx" G-code
    or as comment. Both must be generated by the slicer. If comment is
    used than "file_comment_parsing" has to be enabled for it to take
    effect. If that info is missing (comment or "M73 Rxx"), the progress
    source defaults to option 0 (file mode).
  - If "M73 Pxx" is present in the G-code file then file or time based
    progress modes will be overridden by that.

  Options: [File mode: 0, Time mode: 1]

prog_source:1
'''


QUOTE_MARKS = ('"', "'", "`")
QUOTE_MARKS_BYTES = (b"'", b'"', b'`')


def find_not_quoted(haystack, needle, start=None, end=None, quote_mark=None,
                    escape_mark="\\", already_in_quote=None,
                    allow_nested_quotes=True):
    """Find a string respecting quotes

    This function exists since regex fails at this on a misplaced quote
    (See <https://stackoverflow.com/a/26629680/4541104>, which is
    unusable regex due to that issue confirmed there).

    Redundant with pycodetool, but here to avoid dependencies when parsing conf
    files including desktop files.

    Args:
        haystack (string): Search in this
        needle (string): Search for this
        start (Optional[int]): Start looking here in haystack.
            Remember to tet already_in_quote if searching for the
            end quote by setting start to the index after the
            opening quote.
        end (Optional[int]): End looking here in haystack (exclusive).
        quote_mark (Optional[list[str]]): The quote mark. Defaults to
            QUOTE_MARKS (or QUOTE_MARKS_BYTES if haystack is bytes
            or bytearray *and* Python>=3 is being used).
        escape_mark (Optional[str]): Note that in some formats
            such as CSV, the escape character for " is another
            " before it!! Defaults to "\".
        already_in_quote (Optional[str]): Set this if a quote is
            already open at the start of haystack or before
            haystack[start].
    """
    prefix = "[find_not_quoted] "
    if not needle:  # Do *not* strip--Allow finding space.
        raise ValueError("needle must be a non-blank string")
    if not start:
        start = 0
    if start < 0 or start > len(haystack):
        raise ValueError('start was %s but len of "%s" is %s'
                         % (start, haystack, len(haystack)))
    elif start == len(haystack):
        # Allowed for edge cases (such as succinct code without checks)
        echo1('Warning: start was %s but len of "%s" is %s'
              % (start, haystack, len(haystack)))
        return -1
    if end is None:
        end = len(haystack)
    if start > end:
        raise ValueError("start=%s is greater than end=%s"
                         % (start, end))
    if end > len(haystack):
        raise ValueError("end=%s is greater than len(haystack)=%s"
                         % (end, len(haystack)))

    if quote_mark is not None:
        if not isinstance(quote_mark, (bytes, bytearray, str)):
            raise NotImplementedError(
                "Only bytes or str are implemented, not %s"
                % type(quote_mark).__name__
            )
        if ((already_in_quote is not None)
                and (already_in_quote != quote_mark)):
            echo0(prefix+'Warning: already_in_quote="%s" is not "%s"'
                  % (already_in_quote, quote_mark))
        quote_marks = [quote_mark]
    else:
        if (isinstance(quote_mark, (bytes, bytearray))
                and (sys.version_info.major >= 3)):
            quote_marks = QUOTE_MARKS_BYTES
        else:
            quote_marks = QUOTE_MARKS
        if ((already_in_quote is not None)
                and (already_in_quote not in quote_marks)):
            echo0(prefix+'Warning: already_in_quote=%s is not from %s'
                  % (already_in_quote, quote_marks))
    del quote_mark
    for _quote_mark in quote_marks:
        if not _quote_mark:
            raise ValueError("bad quote_mark=%s" % _quote_mark)
    in_quote = already_in_quote
    quote_stack = []
    if in_quote is not None:
        quote_stack.append(in_quote)
    # prev_ch = None
    # prev_ch_is_escaped = False
    echo2(prefix+'started at %s: "%s"' % (start, haystack[start:]))
    in_escape = None
    for index in range(start, end):
        if index + len(needle) > end:
            # The needle would end beyond the end.
            return -1
        if in_quote is not None:
            # already in quotes
            if ((haystack[index:index+len(in_quote)] == in_quote)
                    and (not in_escape)):
                in_quote = None
                quote_stack.pop()
                if allow_nested_quotes:
                    if len(quote_stack) > 0:
                        in_quote = quote_stack[-1]
                # Allow the endquote to be found as the
                #   result (*not* to be found if not)
                if not in_quote:
                    if haystack[index:index+len(needle)] == needle:
                        return index
        else:
            # not in quotes
            for quote_mark in quote_marks:
                if haystack[index:index+len(quote_mark)] == quote_mark:
                    if not in_escape:
                        # Only use unescaped quotes (if prev_ch is escape_mark
                        #   but is escaped, it doesn't escape this char)
                        in_quote = quote_mark
                        quote_stack.append(in_quote)
                        break
            # if in_quote is not None:  # start quote
            # If start quote is needle *or* any needle not in quotes,
            #   detect as needle (so no further conditions are necessary):
            if haystack[index:index+len(needle)] == needle:
                return index

        if in_escape:
            # prev_ch_is_escaped = True
            # encoded Python string stays escaped for entire \x00 but N/A here
            #   (code here is just to avoid escaped escape from escaping next)
            in_escape = None
        else:
            # prev_ch_is_escaped = False
            if haystack[index:index+len(escape_mark)] == escape_mark:
                in_escape = escape_mark
                # This char becoming prev_ch *is real* escape, not escaped one
                #   (so keep prev_ch_is_escaped = False)
        # prev_ch = haystack[index]
    return -1


def without_comments(style_str, enclosures=None):
    """Get style_str without comments enclosed by enclosures.

    Args:
        style_str (str): any string
        enclosures (Union[list[str],tuple[str]], optional): Start and
            end. Defaults to ("/*", "*/") if None.

    Raises:
        SyntaxError: _description_

    Returns:
        _type_: _description_
    """
    if enclosures is None:
        if isinstance(style_str, (bytes, bytearray)):
            enclosures = (b"/*", b"*/")
            squo = b"'"
        else:
            enclosures = ("/*", "*/")
            squo = "'"
    starter = enclosures[0]
    ender = enclosures[1]
    while True:
        c_start = find_not_quoted(style_str, starter,
                                  quote_mark=squo,
                                  allow_nested_quotes=False)
        if c_start < 0:
            break
        c_end = find_not_quoted(style_str, ender, c_start+len(starter),
                                quote_mark=squo,
                                allow_nested_quotes=False)
        if c_end < 0:
            raise SyntaxError("style string has unclosed /*")
        style_str = style_str[:c_start] + style_str[c_end+len(ender):]

    return style_str


newlineBytesRE = re.compile(b"[\\r\\n]")
newlineStrRE = re.compile(r"[\r\n]")


def split_before_newlines(spacing_and_newline):
    """Split the line from the newline.

    Args:
        spacing_and_newline (Union[str,bytes,bytearray]): A string ending with
            newline or not.

    Returns:
        string: A tuple of (text, newline). If there is no
            text, the return is ("", newline) and if there is
            no newline, the return is (newline, "") where
            newline is blank if there is no newline.
    """
    if isinstance(spacing_and_newline, (bytes, bytearray)):
        newlineRE = newlineBytesRE
    else:
        newlineRE = newlineStrRE
    match = newlineRE.search(spacing_and_newline)
    if not match:
        return (spacing_and_newline, "")
    return (
        spacing_and_newline[:match.span()[0]],
        spacing_and_newline[match.span()[0]:]
    )


def keep_strip(value_and_spacing):
    """Split a string into spacing, non-spacing, spacing.

    Args:
        value (Union[str,bytes,bytearray]): Any string

    Returns:
        tuple[Union[str,bytes,bytearray]]: (same type as value)
            3-long tuple of spacing, non-spacing, and spacing
            (spacing in between ends is left intact).
            If value_and_spacing is only spacing, then the
            result is (value_and_spacing, "", "")
    """
    left_spacing_then_value = value_and_spacing.rstrip()
    if len(left_spacing_then_value) == 0:
        if isinstance(value_and_spacing, (bytes, bytearray)):
            return (value_and_spacing, b"", b"")
        return (value_and_spacing, "", "")
    right_spacing = value_and_spacing[
        (len(value_and_spacing)-(len(value_and_spacing)
                                 - len(left_spacing_then_value))):
    ]
    # ^ *Must* include "len(value_and_spacing)-" to account for
    #   the edge space when no space was removed (which would
    #   prevent slicing from end since 0 starts at beginning)
    value = left_spacing_then_value.strip()
    return (
        left_spacing_then_value[:len(left_spacing_then_value)-len(value)],
        value,
        right_spacing,
    )


spaceSignSpaceStrREs = {
    "=": re.compile(r"[^\S\r\n]*=[^\S\r\n]*"),
    ":": re.compile(r"[^\S\r\n]*:[^\S\r\n]*"),
}

spaceSignSpaceBytesREs = {
    b"=": re.compile(r"[^\S\r\n]*=[^\S\r\n]*".encode("utf-8")),
    b":": re.compile(r"[^\S\r\n]*:[^\S\r\n]*".encode("utf-8")),
}


def _tokenize_conf_line(raw_line, allow_comment_after_value, sign=None,
                        comment_mark=None, path=None, lineN=None):
    # quote_mark=None):
    indent, line_strip, entire_line_end = keep_strip(raw_line)
    if len(line_strip) == 0:
        indent, line_end = split_before_newlines(raw_line)
        return [indent, None, None, None, None, None, line_end]

    if startswith_bytes(line_strip, comment_mark):
        post_comment_space, line_end = split_before_newlines(entire_line_end)
        comment = line_strip + post_comment_space
        return [indent, None, None, None, None, comment, line_end]
    if isinstance(raw_line, (bytes, bytearray)):
        spaceSignSpaceREs = spaceSignSpaceBytesREs
        # still a dict at this stage
    elif isinstance(raw_line, str):
        spaceSignSpaceREs = spaceSignSpaceStrREs
        # still a dict at this stage
    else:
        raise TypeError("Regex for %s is not implemented."
                        % type(raw_line).__name__)
    # See if there is precompiled regex for sign:
    spaceOpSpace = spaceSignSpaceREs.get(sign)
    if spaceOpSpace is None:
        echo0("Warning: performance may be slow"
              " due to no precompiled regex for %s"
              % repr(sign))
        spaceOpSpace = re.compile(type(sign)(r"[^\S\r\n]*")
                                  + re.escape(sign)
                                  + type(sign)(r"[^\S\r\n]*"))
    match = spaceOpSpace.search(line_strip)
    if not match:
        where = ""
        if path is not None:
            where = 'File "{}"'.format(path)
            if lineN is not None:
                where += ", line {}: ".format(lineN)
            else:
                where += ": "
        raise NotImplementedError(
            where+'The line was not understood as blank, comment,'
            ' nor `name{}value`'
            ''.format(sign)
        )
    sign_and_spacing = line_strip[match.span()[0]:match.span()[1]]
    name = line_strip[:match.span()[0]]
    rvalue = line_strip[match.span()[1]:]
    # NOTE: findall would find two if there are two sign in a row,
    #   and search only finds the first sign, so:
    if startswith_bytes(rvalue, sign):
        where = ""
        if path is not None:
            where = 'File "{}"'.format(path)
            if lineN is not None:
                where += ", line {}: ".format(lineN)
            else:
                where += ": "
        echo0(
            where+"Warning: extra sign directly after first '{}'"
            ''.format(sign)
        )

    value = None
    post_value_spacing = None
    comment = None
    line_end = None
    if allow_comment_after_value:
        comment_i = find_not_quoted(rvalue, comment_mark)
        if comment_i > -1:
            comment = rvalue[comment_i:]
            rvalue = rvalue[:comment_i]
            comment_spacing, line_end = split_before_newlines(entire_line_end)
            comment += comment_spacing
            _, value, post_value_spacing = keep_strip(rvalue)
            # ^ _ since there is no spacing before rvalue at this stage
            #   due to spaceSignSpace capturing it and placing it in
            #   sign_and_spacing

    if comment is None:
        _, value, __ = keep_strip(rvalue)
        if len(__) > 0:
            raise RuntimeError(
                "The first keep_strip call should have obtained post-value"
                " space when there is no comment but left '%s' in rvalue."
                "\n  line_strip=%s"
                "\n  name=%s"
                "\n  sign_and_spacing=%s"
                "\n  rvalue=%s"
                "\n  value=%s"
                "\n  comment=%s"
                "\n  line_end=%s"
                % (__, repr(line_strip),
                   repr(name), repr(sign_and_spacing),
                   repr(rvalue), repr(value),
                   repr(comment), repr(line_end))
            )
        post_value_spacing, line_end = split_before_newlines(entire_line_end)
    if None in (value, post_value_spacing, line_end):
        raise NotImplementedError(
            "None for one of: value=%s, post_value_spacing=%s, line_end=%s"
            % (value, post_value_spacing, line_end)
        )
    if len(_) > 0:
        raise RuntimeError(
            "spaceOpSpace should have obtained pre-value space"
            " but left '%s' in line_strip=%s"
            "\n  name=%s"
            "\n  sign_and_spacing=%s"
            "\n  rvalue=%s"
            "\n  value=%s"
            "\n  comment=%s"
            "\n  line_end=%s"
            % (_, repr(line_strip),
               repr(name), repr(sign_and_spacing),
               repr(rvalue), repr(value),
               repr(comment), repr(line_end))
        )

    return [indent, name, sign_and_spacing, value, post_value_spacing,
            comment, line_end]


def _tokenize_conf_line_bytes(raw_line, allow_comment_after_value, **kwargs):
    if kwargs.get('sign') is None:
        kwargs['sign'] = b"="
    if kwargs.get('comment_mark') is None:
        kwargs['comment_mark'] = b"#"
    return _tokenize_conf_line(raw_line, allow_comment_after_value, **kwargs)


def _tokenize_conf_line_str(raw_line, allow_comment_after_value, **kwargs):
    if kwargs.get('sign') is None:
        kwargs['sign'] = "="
    if kwargs.get('comment_mark') is None:
        kwargs['comment_mark'] = "#"
    return _tokenize_conf_line(raw_line, allow_comment_after_value, **kwargs)


class AssignmentInfo:
    INDENT = 0
    NAME = 1
    SIGN_AND_SPACING = 2
    VALUE = 3
    POST_VALUE_SPACING = 4
    COMMENT = 5
    LINE_END = 6
    EMPTY = [None, None, None, None, None, None, None]
    # PARTS = EMPTY.copy()
    # ^ list has no attribute copy in Python 2, so:
    PARTS = EMPTY[:]
    PARTS[INDENT] = "indent"
    PARTS[NAME] = "name"
    PARTS[SIGN_AND_SPACING] = "sign_and_spacing"
    PARTS[VALUE] = "value"
    PARTS[POST_VALUE_SPACING] = "post_value_spacing"
    PARTS[COMMENT] = "comment"
    PARTS[LINE_END] = "line_end"
    PARTS_BYTES = []
    for __part in PARTS:
        PARTS_BYTES.append(__part.encode("utf-8"))

    def __init__(self):
        # behave as enum, but better since type can be checked.
        self.value = None

    @classmethod
    def set_by_name(cls, parts, name, value):
        if isinstance(name, (bytes, bytearray)):
            parts[cls.PARTS_BYTES.index(name)] = value
        else:
            parts[cls.PARTS.index(name)] = value

    @classmethod
    def get_by_name(cls, parts, name):
        if isinstance(name, (bytes, bytearray)):
            return parts[cls.PARTS_BYTES.index(name)]
        return parts[cls.PARTS.index(name)]


def tokenize_conf_line(raw_line, allow_comment_after_value, **kwargs):
    """Tokenize conf or *any* assignment line without spaces in var name.

    Uses consistent indices that indicate meaning of token.

    Args:
        raw_line (Union[str,bytes,bytearray]): A conf file line.
            Must be blank, comment, or assignment
            (*not* "[section_name]" format--preprocess those).
        allow_comment_after_value (bool): If True, a
            comment mark after the value will be processed.
        sign (Optional[Union[str,bytes,bytearray]]): The sign separating name
            from value.
        comment_mark (Optional[Union[str,bytes,bytearray]]): The mark that
            starts a comment.
        path (Optional[Union[str,bytes,bytearray]]): For syntax errors
            readable by the IDE, specify a file path where raw_line
            originated.
        lineN (Optional[Union[str,bytes,bytearray]]): For syntax error line
            numbers the IDE can jump to via click, specify a line number
            in path where the first line is 1.
        # quote_mark (Optional[Union[str,bytes,bytearray]]): If not . Defaults
        #     to QUOTE_MARKS.

    Returns:
        list[Union[str,bytes,bytearray]]: Parts of the line in consistent
            indices (last index is always right space *and* comment if any,
            including space left of comment if any)
            [indent,     name, sign_and_spacing, value, post_value_spacing,
            comment,  line_end]
            - where comment may contain whitespace or be only comment_mark
            - *or* if starts with comment after whitespace:
              [indent,     None, None,             None,  None,
              comment, line_end]
            - *or* if blank:
              [raw_line,   None, None,             None,  None,
              None, None]
    """
    if isinstance(raw_line, (bytes, bytearray)):
        # _tokenize_conf_line_bytes sets default arguments as bytes objects:
        return _tokenize_conf_line_bytes(raw_line, allow_comment_after_value,
                                         **kwargs)
    return _tokenize_conf_line_str(raw_line, allow_comment_after_value,
                                   **kwargs)


def tokenize_conf_line_as_dict(raw_line, allow_comment_after_value, **kwargs):
    """Process any assignment and return the results as a dict

    For documentation other than return see tokenize_conf_line.

    Returns:
        dict: A dict where each element of AssignmentInfo.PARTS is a key
            and each value is the literal chunk of raw_line (Therefore
            values are all strings or all bytes objects depending on the
            type of raw_line).
    """
    parts = tokenize_conf_line(raw_line, allow_comment_after_value, **kwargs)
    results = {}
    if len(AssignmentInfo.PARTS) != len(parts):
        raise NotImplementedError(
            "expected %s values from but got %s from tokenize_conf_line"
            % (len(AssignmentInfo.PARTS), len(parts))
        )
    for i, name in AssignmentInfo.PARTS:
        # Do *not* use PARTS_BYTES here, we just want
        #   values looked up by programmer not looked up by code.
        results[name] = parts[i]
    return results


def rewrite_conf(sc_src_path, desktop_sc_path, metadata,
                 assignment_operator="=", none_string="",
                 allow_adding=True):
    """_summary_

    Args:
        sc_src_path (_type_): _description_
        desktop_sc_path (_type_): _description_
        metadata (_type_): _description_
        assignment_operator (str, optional): _description_. Defaults to "=".
        none_string (str, optional): _description_. Defaults to "".
        allow_adding (bool, optional): _description_. Defaults to True.

    Returns:
        dict: Either None or a dict of values not added.
    """
    line_end = None
    with open(desktop_sc_path, 'wb') as outs:
        done_keys = set()
        with open(sc_src_path, "rb") as ins:
            for line_orig in ins:
                indent, name, sign_and_spacing, value, right_spacing = \
                    tokenize_conf_line(
                        line_orig,
                        sign=assignment_operator,
                    )
                if line_end is None or (len(right_spacing) < len(line_end)):
                    line_end = right_spacing
                if name in metadata:
                    # instead of .get use "in"--allow value of None
                    new_value = metadata[name]
                    outs.write(indent + name + sign_and_spacing + new_value
                               + right_spacing)
                    # ^ right_spacing includes newline
                    done_keys.add(name)
                    continue
                outs.write(line_orig)
        if line_end is None:
            line_end = os.linesep
            echo0("Warning: newline detected; using os newline (length=%s)"
                  % len(line_end))
        not_added_data = None
        if not allow_adding:
            not_added_data = {}
        for key, value in metadata.items():
            if key not in done_keys:
                if allow_adding:
                    outs.write("%s=%s%s" % (key, value, line_end))
                else:
                    not_added_data[key] = value
        if allow_adding or (len(not_added_data) < 1):
            # already added everything either way
            return None
        echo0('File "%s": Warning: does not contain %s so not added to "%s"'
              ' (allow_adding=%s)'
              % (sc_src_path, not_added_data, desktop_sc_path, allow_adding))
        return not_added_data


def rewrite_conf_str(src, dst, changes={}):
    """Install a conf such as an XDG desktop shortcut with changes.

    This will be *redefined* if running in *Python 2* (see
    sys.version_info.major check).

    Args:
        src (string): The conf file to read.
        dst (string): The conf file to write or overwrite.
        changes (dict): A set of values to change by name. For any value
            that is None, the line will be removed!
    """
    # This function is redefined further down in the case of Python 2.
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'wb') as tmp:
            # ^ ensure still exists when moving
            write0("Generating temporary icon %s..." % path)
            # NOTE: tmp.name is just some number (int)!
            with open(src, "rb") as stream:
                for rawL in stream:  # noqa N406
                    signI = rawL.find(b'=')  # noqa N806
                    # commentI = rawL.find(b'#')
                    if rawL.strip().startswith(b"#"):
                        tmp.write(rawL)
                        continue
                    if rawL.strip().startswith(b"["):
                        tmp.write(rawL)
                        continue
                    if signI < 0:
                        tmp.write(rawL)
                        continue
                    key_bytes = rawL[:signI].strip()
                    key = key_bytes.decode("utf-8")
                    value = changes.get(key)
                    if key not in changes:
                        # The value wasn't changed so write it as-is
                        # echo0("%s not in %s" % (key, changes))
                        tmp.write(rawL)
                        continue
                    if value is None:
                        echo0("%s was excluded from the icon" % key)
                        continue
                    line = "%s=%s\n" % (key, value)
                    tmp.write(line.encode("utf-8"))
        shutil.copy(path, dst)
    finally:
        write0("removing tmp file...")
        os.remove(path)


if sys.version_info.major < 3:
    # Python 2 (strings are bytes)
    def rewrite_conf_str(src, dst, changes={}):  # noqa F811
        """Install a conf such as an XDG desktop shortcut with changes.

        See Python 3 implementation's docstring for more info.
        """
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as tmp:
                write0("Generating temporary icon %s..." % path)
                sys.stderr.flush()
                with open(src, "rb") as stream:
                    for rawL in stream:  # noqa N406
                        signI = rawL.find('=')  # noqa N806
                        # commentI = rawL.find('#')
                        if rawL.strip().startswith("#"):
                            tmp.write(rawL)
                            continue
                        if rawL.strip().startswith("["):
                            tmp.write(rawL)
                            continue
                        if signI < 0:
                            tmp.write(rawL)
                            continue
                        key_bytes = rawL[:signI].strip()
                        key = key_bytes
                        value = changes.get(key)
                        if key not in changes:
                            # The value wasn't changed so write it as-is
                            tmp.write(rawL)
                            continue
                        if value is None:
                            echo0("%s was excluded from the icon" % key)
                            continue
                        line = "%s=%s\n" % (key, value)
                        tmp.write(line)
            shutil.copy(path, dst)
        finally:
            write0("removing tmp file...")
            sys.stderr.flush()
            os.remove(path)


def ord_at(string, idx):
    if sys.version_info.major >= 3:
        return string[idx]  # In Python 3 it is already int
    return ord(string[idx])  # same as: struct.unpack(">B", string[idx])[0]


def chr_at(string, idx):
    if sys.version_info.major >= 3:
        return chr(string[idx])
    return string[idx]  # In Python 2 it is still str


class ByteConf(Byter):
    """
    See Byter. This subclass is the same for now.
    """
    def __init__(self):
        Byter.__init__(self)
