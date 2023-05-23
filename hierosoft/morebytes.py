# -*- coding: utf-8 -*-
from __future__ import print_function
import binascii
import os
import sys

def echo0(*args):
    print(*args, file=sys.stderr)

# by [Sz'](https://stackoverflow.com/users/2278704/sz)
# <https://stackoverflow.com/a/60604183>
# Mar 9, 2020 at 15:56
def crc16_buypass(data: bytes):
    xor_in = 0x0000  # initial value
    xor_out = 0x0000  # final XOR value
    poly = 0x8005  # generator polinom (normal form)
    reg = xor_in
    for octet in data:
        # reflect in
        for i in range(8):
            topbit = reg & 0x8000
            if octet & (0x80 >> i):
                topbit ^= 0x8000
            reg <<= 1
            if topbit:
                reg ^= poly
        reg &= 0xFFFF
        # reflect out
    return reg ^ xor_out


# answered May 1, 2019 at 8:16 by user11436151
# edited Feb 26, 2020 at 13:45 by Matphy
# https://stackoverflow.com/a/55933366
def crc16_modbus(data : bytearray, offset=0, length=None):
    if length is None:
        length = len(data)
    if data is None or offset < 0 or offset > len(data) - 1 and offset + length > len(data):
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


def crc16_ccit_false(data : bytearray, offset=0, length=None):
    '''
    Python implementation of CRC-16/CCITT-FALSE
    (output matches CRC-16 button's CCITT-FALSE output on
    <https://crccalc.com/>).
    answered Apr 25, 2019 at 13:31
    CC BY-SA 4.0 Amin Saidani
    <https://stackoverflow.com/a/55850496/4541104>
    '''
    if length is None:
        length = len(data)
    if data is None or offset < 0 or offset > len(data)- 1 and offset+length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
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
    # import binascii
    if (delimiter is not None) and (len(delimiter) > 0):
        return " ".join(["{:02x}".format(x) for x in bytestring])

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
    if len(haystack) < len(needle):
        return False
    return haystack[-len(needle):] == needle



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


def find_any_not(haystack, needles, not_whitespace_either=False, start=0, end=None):
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
    pos = start -1
    while pos < len(haystack):
        pos += 1
        if not_whitespace_either:
            if haystack[pos:pos+1].strip() != haystack[pos:pos+1]:
                # ^ must slice, otherwise will be int if bytearray or
                #   bytes!
                continue
        for needle in needles:
            if haystack[pos:].startswith(needle):
                pos += len(needle) - 1
                # ^ -1 since 1 will be added at start of next loop.
                #   For example, if startswith "REM " then set index
                #   from 4 to 3 and then it will continue after the
                #   " " after the +=1 at the top of the loop.
        return pos
    return -1


def startswith_any(haystack, needles):
    for needle in needles:
        if haystack.lstrip().startswith(needle):
            return True
    return False


def no_b(text_bytes):
    text = str(text_bytes)
    if text.startswith("b'") and text.endswith("'"):
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
            raise IndexError("cursor={}, len={}".format(cursor, len(self.data)))
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
            comment_i = find_any(self.data, self.comment_marks, start=start_i, end=next_line_i)
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
            endbefore_i = find_any(self.data, [b'\r', b'\n'], start=name_ender_i, end=next_line_i)
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
                                no_b(self.data[name_ender_i:endbefore_near_i])))
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
# TODO: Make sure slicer/octoprint really adds these G-code progress
#  commands (including in Klipper if has any effect):
'''
From the default config:

# NOTES:
#   - Time mode needs info from the G-code file such as the elapsed time or the remaining time. This info
#     can be supplied as "M73 Rxx" G-code or as comment. Both must be generated by the slicer. If comment
#     is used than "file_comment_parsing" has to be enabled for it to take effect.
#     If that info is missing (comment or "M73 Rxx"), the progress source defaults to option 0 (file mode).
#   - If "M73 Pxx" is present in the G-code file then file or time based progress modes will be overriden
#     by that.
#
#   Options: [File mode: 0, Time mode: 1]
prog_source:1
'''

class ByteConf(Byter):
    '''
    See Byter. This subclass is the same for now.
    '''
    def __init__(self):
        Byter.__init__(self)
