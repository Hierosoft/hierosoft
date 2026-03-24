# -*- coding: utf-8 -*-
import sys
# import numpy


def average_int(elements):
    total = 0
    for element in elements:
        total += element
    return int(round(total / len(elements)))


def rgba_tuple(int_pixel):
    """Convert from BGRA int to tuple.

    Args:
        int_pixel (int): an entire BGRA pixel

    Returns:
        tuple: r, g, b, a integers
    """
    return (
        (int_pixel >> 8) & 0xFF,  # R
        (int_pixel >> 16) & 0xFF,  # G
        int_pixel >> 24,  # B
        int_pixel & 0xFF,  # A
    )


def hex_pair(int_value):
    """Convert a byte to a hex pair.

    Args:
        int_value (int): A number 0-255.

    Returns:
        str: A string 2 characters long (such as '08' for int_value 8,
            or 'ff' for int_value 255).

    Raises:
        OverflowError: (Raised by to_bytes since called without length &
            order params and by default only allows 0-255) if "int too
            big to convert"
    """
    assert isinstance(int_value, int)
    value_bytes = int_value.to_bytes()  # if no length param limit is 1 byte
    return value_bytes.hex()


def hex_rgba(int_pixel):
    """Convert from BGRA int to tuple.

    Args:
        int_pixel (int): an entire BGRA pixel

    Returns:
        tuple: r, g, b, a integers
    """
    return (
        hex_pair((int_pixel >> 8) & 0xFF)  # R
        + hex_pair((int_pixel >> 16) & 0xFF)  # G
        + hex_pair(int_pixel >> 24)  # B
        + hex_pair(int_pixel & 0xFF)  # A
    )


def bgra_from_rgba_tuple(r, g, b, a):
    if r > 255:
        raise ValueError("a %s is too large (expected 0 to 255)" % r)
    if g > 255:
        raise ValueError("a %s is too large (expected 0 to 255)" % g)
    if b > 255:
        raise ValueError("a %s is too large (expected 0 to 255)" % b)
    if a > 255:
        raise ValueError("a %s is too large (expected 0 to 255)" % a)
    return (
        (b << 24) & (g << 16) & (r << 8) & a
    )


class OffscreenCanvas(object):
    def __init__(self, width, height):
        self._w = width
        self._h = height
        self._bpp = 32
        # self.buffer = numpy.empty(buffer_total, dtype=object)
        self._buffer = [0] * self.count

    @property
    def count(self):
        return self._w * self._h

    def sub_buffer(self, start_x, start_y, width, height):
        results = []
        y = start_y
        for rel_y in range(height):
            x = start_x
            for rel_x in range(width):
                results.append(self._buffer[width*y+x])
                x += 1
            y += 1
        return results

    def render(self, canvas, divisor=None, transparent=None):
        if divisor is None:
            divisor = 1
        if transparent is not None:
            if len(transparent) != 3:
                raise ValueError("3-color tuple is required")
        new_w = self._w / divisor
        new_h = self._h / divisor
        for dst_y in range(new_h):
            y = dst_y * divisor
            for dst_x in range(new_w):
                x = dst_x * divisor
                pixel = average_int(self.sub_buffer(x, y, divisor, divisor))
                # r, g, b, a = rgba_tuple(pixel)
                hex_color = hex_rgba(pixel)
                canvas.create_line(dst_x, dst_y, dst_x+x, dst_y,
                                   fill=hex_color)
                # ^ +1 since exclusive (draw one pixel in this case)


# from tkinter import Frame, Variable, Scrollbar, Text
# from tkinter.constants import VERTICAL, RIGHT, LEFT, BOTH, END, Y

if sys.version_info.major >= 3:  # imports differ
    import tkinter as tk
    from tkinter import ttk
else:
    # Python 2
    import Tkinter as tk  # type:ignore
    import ttk  # type:ignore


class TextExtension(ttk.Frame):
    """Extends Frame.  Intended as a container for a Text field.
    Better related data handling and has Y scrollbar.

    [CC BY 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
    Attribution:
    answered Oct 22, 2014 at 14:08
    Nicklas Börjesson

    edited Apr 11, 2023 at 17:23
    Piti Ongmongkolkul

    edited July 16, 2025
    by Poikilos (Jake Gustafson)
    """

    def __init__(self, master, textvariable=None, *args, **kwargs):
        if sys.version_info.major >= 3:
            super(TextExtension, self).__init__(master)
        else:
            ttk.Frame.__init__(self, master)
        # Init GUI

        self._y_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)

        self._text_widget = tk.Text(self, yscrollcommand=self._y_scrollbar.set,
                                    *args, **kwargs)
        self._text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self._y_scrollbar.config(command=self._text_widget.yview)
        self._y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if textvariable is not None:
            if not (isinstance(textvariable, tk.Variable)):
                raise TypeError("tkinter.Variable type expected, {} given."
                                .format(type(textvariable)))
            self._text_variable = textvariable
            self.var_modified()
            self._text_trace = self._text_widget.bind('<<Modified>>',
                                                      self.text_modified)
            self._var_trace = textvariable.trace("w", self.var_modified)

    def text_modified(self, *args):
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)
            self._text_variable.set(self._text_widget.get(1.0, 'end-1c'))
            self._var_trace = self._text_variable.trace("w", self.var_modified)
            self._text_widget.edit_modified(False)

    def var_modified(self, *args):
        self.set_text(self._text_variable.get())
        self._text_widget.edit_modified(False)

    def unhook(self):
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)

    def clear(self):
        self._text_widget.delete(1.0, tk.END)

    def set_text(self, _value):
        self.clear()
        if (_value is not None):
            self._text_widget.insert(tk.END, _value)

    def leaf_cget(self, key):
        self._text_widget.cget(key)

    def leaf_configure(self, **kwargs):
        self._text_widget.configure(**kwargs)

