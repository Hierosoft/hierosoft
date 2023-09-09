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


def hexpair(int_value):
    """_summary_

    Args:
        int_value (_type_): _description_

    Returns:
        _type_: _description_

    Raises:
        OverflowError: (Raised by to_bytes since has no length, order
            params) if "int too big to convert"
    """
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
        hexpair((int_pixel >> 8) & 0xFF)  # R
        + hexpair((int_pixel >> 16) & 0xFF)  # G
        + hexpair(int_pixel >> 24)  # B
        + hexpair(int_pixel & 0xFF)  # A
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