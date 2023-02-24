# -*- coding: utf-8 -*-
from __future__ import print_function

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


def endswith_bytes(haystack, needle):
    '''
    Check if a bytearray ends with another bytearray (needle).

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
