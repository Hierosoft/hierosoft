# -*- coding: utf-8 -*-
"""
Support Tk versions below 8.7 (alpha June 18, 2021)
that don't have SVG (such as in Python 2 or
some copies of Python 3 included with early macs).
- For Tk 8.7 or higher, you could use tksvg instead.

Why not use <https://github.com/TkinterEP/python-tksvg/tree/master>:
- Requires a C module (disadvantage due to cross-platform issues
  and potentiall requiring Dev Tools to install on mac)


Node's public members:
'appendChild', 'attributes', 'childNodes', 'cloneNode', 'firstChild',
'getAttribute', 'getAttributeNS', 'getAttributeNode',
'getAttributeNodeNS', 'getElementsByTagName', 'getElementsByTagNameNS',
'getInterface', 'getUserData', 'hasAttribute', 'hasAttributeNS',
'hasAttributes', 'hasChildNodes', 'insertBefore', 'isSameNode',
'isSupported', 'lastChild', 'localName', 'namespaceURI', 'nextSibling',
'nodeName', 'nodeType', 'nodeValue', 'normalize', 'ownerDocument',
'parentNode', 'prefix', 'previousSibling', 'removeAttribute',
'removeAttributeNS', 'removeAttributeNode', 'removeAttributeNodeNS',
'removeChild', 'replaceChild', 'schemaType', 'setAttribute',
'setAttributeNS', 'setAttributeNode', 'setAttributeNodeNS',
'setIdAttribute', 'setIdAttributeNS', 'setIdAttributeNode',
'setUserData', 'tagName', 'toprettyxml', 'toxml', 'unlink', 'writexml'

Attr (node.attributes[x])'s public members:
'appendChild', 'attributes', 'childNodes', 'cloneNode', 'firstChild',
'getInterface', 'getUserData', 'hasChildNodes', 'insertBefore', 'isId',
'isSameNode', 'isSupported', 'lastChild', 'localName', 'name',
'namespaceURI', 'nextSibling', 'nodeName', 'nodeType', 'nodeValue',
'normalize', 'ownerDocument', 'ownerElement', 'parentNode', 'prefix',
'previousSibling', 'removeChild', 'replaceChild', 'schemaType',
'setUserData', 'specified', 'toprettyxml', 'toxml', 'unlink', 'value'
"""
# from __future__ import annotations  # allows getter, setter, etc, but *postponed*:
#     still not in Python 2.7.17!
from __future__ import division  # workarounds are used, but import to be sure
from __future__ import print_function

import copy
import sys

from collections import OrderedDict

from xml.dom.minidom import (
    # parse,  # accepts a file handle
    parseString,
    # Node,  # such as to access static members
    Text,
)

from hierosoft import (  # noqa F401
    echo1,
)

from hierosoft.morebytes import (
    find_not_quoted,
    without_comments,
)


def echo0(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)
    return True


# from xml.etree import ElementTree


def str_to_viewBox(viewBoxStr):
    """Convert svg_node.attributes['viewBox'].value to float list.

    Returns:
        list[float]: left, top, width, height
    """
    viewBox = viewBoxStr.split()
    if len(viewBox) != 4:
        raise ValueError("viewBox must be 4 floats")
    for i, value in enumerate(viewBox):
        viewBox[i] = float(value)
    return viewBox


class SVGSegment:
    """A collection of points.

    In SVG format, each command in a path node makes a separate Path.
    """
    PROPS = [
        'buffer',
        'bezier',
        'command',
        'quadratic',
        'smooth',
        '_vector_fmt',
    ]

    def __init__(self):
        self.buffer = []
        self.bezier = False
        self.command = None
        self.quadratic = False
        self.smooth = 0
        self.set_vector_fmt(["x", "y"])
        # All of these should be copied by copy()

    def to_dict(self, get_buffer=True):
        result = {}
        for name in type(self).PROPS:
            if not get_buffer and (name == 'buffer'):
                continue
            result[name] = getattr(self, name)
        return result

    def element(self, i, name):
        return self.buffer[
            i * len(self._vector_fmt)
            + self._vector_fmt.index(name)
        ]

    def __len__(self):
        """Magic (or dunder) method to determine (len(self))

        Returns:
            int: number of segments
        """
        if len(self.buffer) % len(self._vector_fmt) != 0:
            raise ValueError(
                "Buffer len %s should be divisible by vector_fmt %s: %s"
                % (len(self.buffer), self._vector_fmt, self.buffer)
            )
        return int(len(self.buffer) / len(self._vector_fmt))

    def location(self, i):
        return (
            self.element(i, "x"),
            self.element(i, "y")
        )

    def _location(self, i):
        return [
            self.element(i, "x"),
            self.element(i, "y")
        ]

    def _2D_to_index(self, index_times_2):
        """Get the internal index that corresponds to a 1D vector of pairs.

        Args:
            index_times_2 (int): index in your [x1,y1,x2,y2,...] output

        Returns:
            int: index inside of the buffer (skips everything but 'x' & 'y')
        """
        if sys.version_info.major >= 3:
            raise RuntimeError(
                "Set vector_fmt first to generate this method."
            )
        else:
            raise RuntimeError(
                "Call set_vector_fmt first to generate this method."
            )

    def get_vector_fmt(self):  # for Python 2
        return self._vector_fmt

    @property
    def vector_fmt(self):
        return self._vector_fmt

    def set_vector_fmt(self, vector_fmt):  # for Python 2
        self._vector_fmt = vector_fmt
        len_vector_fmt = len(vector_fmt)
        if 'x' not in vector_fmt:
            if 'y' not in vector_fmt:
                echo0("Warning, no x nor y in %s" % vector_fmt)
            else:
                echo0("Warning, no x in %s" % vector_fmt)
        elif 'y' not in vector_fmt:
            echo0("Warning, no y in %s" % vector_fmt)
        else:
            _x_i = vector_fmt.index('x')
            _y_i = vector_fmt.index('y')

        def fast_2D_to_index(index_times_2):
            """Hard-coded faster copy of _2D_to_index

            Needs late binding so use locals so they will change to latest
            definition.
            """
            index = int(index_times_2 / 2)
            if index_times_2 % 2 == 0:
                # echo0("Getting x (index=%s, len(vector_fmt)=%s, _x_i=%s)"
                #       % (index, len(vector_fmt), _x_i))
                # even numbers *and* 0 are X values in output buffer
                return index * len_vector_fmt + _x_i
            # echo0("Getting y (index=%s, len(vector_fmt)=%s, _y_i=%s)"
            #       % (index, len(vector_fmt), _y_i))
            return index * len_vector_fmt + _y_i
        self._2D_to_index = fast_2D_to_index
        assert len(vector_fmt) == len(self._vector_fmt)

    @vector_fmt.setter
    def vector_fmt(self, vector_fmt):
        # Requires `from __future__ import annotations` in Python 2
        #   (otherwise, "SVGSegment instance has no attribute '_vector_fmt'"
        #   occurs) so use set_vector_fmt if using Python 2.
        self.set_vector_fmt(vector_fmt)

    def buffer_2d(self):
        """Convert n-dimensional buffer to 2D buffer.

        Returns:
            list[float]: Length is len(self) * 2 since
                __len__ is overridden by
                int(len(self.buffer) / len(self._vector_fmt)
        """
        fn = self._2D_to_index
        # len(self) * 2 to simulate 2D output buffer
        #   (ok since __len__ is overridden. See `def __len__`` above)
        return [self.buffer[fn(i)] for i in range(len(self) * 2)]

    def copy(self):
        segment = SVGSegment()
        segment.buffer = copy.deepcopy(self.buffer)
        segment.bezier = self.bezier
        segment.quadratic = self.quadratic
        segment.smooth = self.smooth
        segment._vector_fmt = copy.deepcopy(self._vector_fmt)
        return segment

    def append_location(self, x, y):
        new_index = len(self)
        self.buffer += [0 for _ in self._vector_fmt]
        self.set_element(new_index, "x", x)
        self.set_element(new_index, "y", y)
        if len(self._vector_fmt) > 2:
            echo0("Warning: append_location only set x and y but has %s"
                  % self._vector_fmt)

    def connect_to_start(self):
        first = self.buffer[:len(self._vector_fmt)]
        self.buffer += first


def arg_spec_to_vector_fmt(arg_spec):
    vector_fmt = []
    for arg in arg_spec:
        if arg == "location":
            vector_fmt += ["x", "y"]
        elif arg == "control1":
            vector_fmt += ["control1.x", "control1.y"]
        elif arg == "control2":
            vector_fmt += ["control2.x", "control2.y"]
        elif arg == "qcontrol":
            vector_fmt += ["qcontrol.x", "qcontrol.y"]
        elif arg == "x":
            # The parser needs to append prev_y to buffer!
            vector_fmt += ["x", "y"]
        elif arg == "y":
            # The parser needs to insert prev_x to buffer!
            vector_fmt += ["x", "y"]
        else:
            raise NotImplementedError("%s is not implemented"
                                      % arg)
    return vector_fmt


def str_to_style(style_str):
    style = OrderedDict()
    start = 0
    style_str = without_comments(style_str)
    # echo2("without_comments()=%s" % repr(style_str))
    while start < len(style_str):
        end = find_not_quoted(style_str, ";", start,
                              quote_mark="'",
                              allow_nested_quotes=False)
        value_end = end
        if end < 0:
            value_end = len(style_str)  # keep all if no ender
        # assignment operator index:
        ao_index = find_not_quoted(style_str, ":", start, value_end,
                                   quote_mark="'",
                                   allow_nested_quotes=False)
        if ao_index < 0:
            if style_str[start:].strip():
                echo0("Warning: stray %s in style=%s"
                      % (repr(style_str[start:]), repr(style_str)))
            break
        key = style_str[start:ao_index].strip()
        value = style_str[ao_index+1:value_end].strip()
        style[key] = value
        start = value_end + 1  # start next one *after* ";"
        #   or len() (in that case, len + 1 is ok since will end the loop)
    return style


def node_attr_or_style(node, key):
    """Get a node attribute or style, whichever is present.

    Args:
        node (Element): The xml.dom.minidom Element
        key (str): _description_

    Returns:
        str: value of attribute, style attribute, or None.
            style attribute overrides attribute.
    """
    fill = node.attributes.get(key)
    if fill is not None:
        fill = fill.value  # use str not Attr
        # echo0(prefix+"using fill=%s" % fill)
    style_str = node.attributes.get('style')
    if style_str is not None:
        style_str = style_str.value  # use str not Attr
    style = None
    if style_str:
        style = str_to_style(style_str)
    if style is not None:
        # style overrides html attribute
        fill = style.get(key)
    return fill


class MoreSVG(object):  # Must be new-style class (object) for get/set in Py 2
    """Process SVG data.

    This could almost be non-OO neatly except prev_x and prev_y may be used by
    relative (lowercase) SVG commands even when starting new path node.
    """
    def __init__(self):
        self.prev_x = None
        self.prev_y = None
        self.shapes = []  # in tkinter canvas, each shape remains changeable

    def _draw_svg_path(self, node, canvas, viewBox=None, fill=None,
                       constrain=None, pos=None, stroke=None,
                       stroke_width=None):
        """Draw a single path node (where node.tagName is "path").

        Example with attributes:
        ```XML
        <path
        id="path1001"
        fill="none"
        stroke="black"
        stroke-width="1"
        d="M 170.00,25.15            C 170.00,25.15 226.00,25.15 226.00,25.15
        226.00,25.15 334.00,25.15 334.00,25.15
        . . . Z"
        style="stroke-width:0.60471994;stroke-dasharray:none;
        stroke:none;fill:#ffffff;fill-opacity:1" />
        ```
        where ". . ." could be any number of coordinates, but some may be
        arguments for a letter command:

        - MoveTo: M, m
        - LineTo: L, l, H, h, V, v
        - Cubic Bezier Curve: C, c, S, s
        - Quadratic Bezier Curve: Q, q, T, t
        - Elliptical Arc Curve: A, a
        - ClosePath: Z, z
        -<developer.mozilla.org/en-US/docs/Web/SVG/Attribute/d#path_commands>

        Spec:

        For further documentation see draw_svg.

        Args:
            node (xml.dom.minidom.Node): A path node.
            viewBox (Iterable[float]): (left, top, width, height)
                The viewBox will be snapped to the constrained dimension
                (see constrain) of the canvas if there is a viewBox. If
                there is no viewBox, the locations in the SVG file will
                be taken literally. Either way, the canvas should be the
                shape of the viewBox or path(s) to avoid paths being
                cropped, unless constrain is set appropriately. This is
                usually generated by _draw_svg_root.
            fill (string): A Tk-compatible string such as "black" or
                "white". Defaults to node.attributes.get('fill') stroke
                from node.attributes.get('style') if available as per
                SVG spec, otherwise black (default in SVG spec).
            stroke (string): A Tk-compatible string such as "black" or
                "white". Defaults to node.attributes.get('stroke') or
                stroke from node.attributes.get('style') if available as
                per SVG spec, otherwise black (default in SVG spec).
            stroke_width (int): stroke_width in pixels. Defaults to
                node.attributes.get('stroke_width') or stroke_width from
                node.attributes.get('style') if available as per SVG
                spec, otherwise 1 (default in SVG spec).
        """
        prefix = "[_draw_svg_path] "  # noqa F841
        if node.tagName != "path":
            raise ValueError("This function can only draw a path node.")
        parts = node.attributes['d'].value.split()
        # prev_x & prev_y need to be preserved from path to path for relative
        constraints = ["width", "height"]
        if constrain is None:
            pass
            # constrain = "width"
        elif constrain not in constraints:
            raise ValueError('Constrain must be one of %s but is %s'
                             % (constraints, constrain))
        if viewBox is not None:
            if len(viewBox) != 4:
                raise ValueError("viewBox must be 4 floats")
            for i, value in enumerate(viewBox):
                if not isinstance(value, float):
                    echo0("Warning: viewBox should be float for speed")
                    viewBox[i] = float(value)
        if pos is not None:
            if len(pos) != 2:
                raise ValueError("pos must be 2 in length (x, y)")
            for coord in pos:
                if coord != int(coord):
                    raise ValueError("pos must be 2 integers (x, y), but was"
                                     % pos)
        x = None
        y = None
        segments = []  # buffer, buffer, buffer
        segment = SVGSegment()  # x1,y1,x2,y2,...

        stroke_width = None
        if fill is None:
            # Caller didn't override behavior, so use standard
            fill = node_attr_or_style(node, 'fill')
            if fill is None:
                fill = "black"
        if stroke is None:
            # Caller didn't override behavior, so use standard
            stroke = node_attr_or_style(node, 'stroke')
            if stroke is None:
                stroke = "black"
        if stroke_width is None:
            # Caller didn't override behavior, so use standard
            stroke_width = node_attr_or_style(node, 'stroke-width')
            if stroke_width is None:
                stroke_width = 1
            else:
                stroke_width = float(stroke_width)
        stroke_width = int(round(stroke_width))
        if stroke_width < 1:  # Make compatible with tk
            # TODO: Convert units to pixels first.
            stroke_width = 1
        fill_opacity = node_attr_or_style(node, "fill-opacity")
        if fill_opacity is not None:
            fill_opacity = float(fill_opacity)
        command = None
        relative = False
        argi = None  # argument index for current command, looping as per spec
        arg_spec = None  # argument name list
        new_segment = SVGSegment()
        sub_field_i = 0  # for tracing in syntax/parsing errors only
        for index in range(0, len(parts)):
            sub_field_i += 1
            part = parts[index]
            part_upper = part.upper()
            coords = part.split(",")
            is_command = True
            # See SVG spec:
            #   <developer.mozilla.org/en-US/docs/Web/SVG/Attribute/d>
            if part_upper == "M":
                # Move without closing (lowercase is relative,
                #   but that doesn't change the behavior of Z).
                arg_spec = ["location"]
                # previous line is cut before this
                #   automatically by code below since
                #   is_command so coord prior to M will
                #   be termination location of that segment.
            elif part_upper == "Z":
                # Close the shape (lowercase is relative,
                #   but that doesn't change the behavior of Z).
                if not segment.buffer:
                    echo0("Error in SVG: closed before start")
                else:
                    segment.connect_to_start()
                    # self.prev_x = segment.buffer[0]
                    # self.prev_y = segment.buffer[1]
                    # TODO: Do these count as previous??
                arg_spec = []  # No arguments
            elif part_upper == "L":
                # Line
                arg_spec = ["location"]
                new_segment.bezier = False
                new_segment.smooth = 0
            elif part_upper == "H":
                arg_spec = ["x"]
                new_segment.bezier = False
                new_segment.smooth = 0
            elif part_upper == "V":
                arg_spec = ["y"]
                new_segment.bezier = False
                new_segment.smooth = 0
            elif part_upper == "C":
                # Cubic bezier curve
                arg_spec = ["control1", "control2", "location"]
                new_segment.bezier = True
                new_segment.smooth = 1
            elif part_upper == "S":
                # Smooth cubic bezier curve
                # control1 is control2 of previous location.
                arg_spec = ["control2", "location"]
                new_segment.bezier = True
                new_segment.smooth = 1
            elif part_upper == "Q":
                # Quadratic bezier curve
                arg_spec = ["qcontrol", "location"]
                new_segment.bezier = True
                new_segment.quadratic = True
                new_segment.smooth = 1
            elif part_upper == "T":
                # Quadratic bezier curve
                arg_spec = ["location"]
                new_segment.bezier = False
                new_segment.quadratic = True
                new_segment.smooth = 1
            elif part_upper == "A":
                # Elliptical arc curve
                # TODO: generate arc
                arg_spec = ["r1", "r2", "angle", "large-arc-flag",
                            "sweep-flag", "location"]
                new_segment.bezier = False
                new_segment.quadratic = False
                new_segment.smooth = 1
            else:
                is_command = False
            if is_command:
                # Can have multiple segments such as: M C Z m c z
                #   in that order, where lowercase is relative
                segments.append(segment)
                new_segment._vector_fmt = arg_spec_to_vector_fmt(arg_spec)
                new_segment.command = part
                segment = new_segment.copy()
                argi = -1
                # Lowercase indicates arguments are relative.
                relative = part != part_upper
                if arg_spec:
                    command_upper = part_upper
                else:
                    # No arguments are allowed (such as for Z)
                    command_upper = None
                    command = None
                    # else has no args
                # else use the coord (fall through)
                #   and execute the command using the coord
                continue  # skip to the param(s)
            if arg_spec:
                argi += 1  # start at 0 (reset to -1 usually)
                if argi == len(arg_spec):
                    argi = 0
                elif argi > len(arg_spec):
                    raise NotImplementedError("argi overflow")
            else:
                continue
            x = None
            y = None
            arg = None
            if arg_spec[argi] in ["location", "control1", "control2",
                                  "qcontrol"]:
                x = float(coords[0])
                y = float(coords[1])
                if relative:
                    x = self.prev_x + x
                    y = self.prev_y + y
            elif arg_spec[argi] == "x":
                x = float(part)
                if relative:
                    x = self.prev_x + x
                y = self.prev_y
            elif arg_spec[argi] == "y":
                x = self.prev_x
                y = float(part)
                if relative:
                    y = self.prev_y + y
            else:
                arg = float(part)
            if arg:
                # It is not a coordinate pair
                segment.buffer.append(arg)
                continue
            if relative:
                if self.prev_x is None:
                    raise ValueError(
                        "Error in SVG syntax: %s in relative mode"
                        "before any points (command=%s) at subfield %s"
                        % (repr(coords), segment.command, sub_field_i)
                    )
            self.prev_x = x
            self.prev_y = y
            segment.buffer.append(x)
            segment.buffer.append(y)
            # end for part

        # Process the segments
        if len(segment.buffer) > 0:
            echo0("Warning, unterminated segment")
            segments.append(segment)
        if not pos:
            pos = (0, 0)
        scale = 1.0
        if viewBox:
            if constrain is None:
                pass
            elif constrain == "width":
                scale = (float(canvas.winfo_width())
                         / float(viewBox[2]-viewBox[0]))
            elif constrain == "height":
                scale = (float(canvas.winfo_height())
                         / float(viewBox[3]-viewBox[1]))
            else:
                raise ValueError(
                    'constrain should be "width" or "height" but was %s'
                    % constrain
                )
        for segment in segments:
            # NOTE: cyclic must be handled in the SVG itself
            #   (Z or z means draw line to start)
            # TODO: use node.attributes.get('stroke') (string such as "black")
            buffer2d = segment.buffer_2d()
            if len(buffer2d) < 1:
                # Avoid obscure tkinter error `cnf = args[-1]` fails on len 0
                continue
            elif len(buffer2d) < 4:
                # Avoid obscure tkinter error
                #   "wrong # coordinates: expected at least 4, got 2"
                echo0("Warning: skipped non-implemented"
                      " single point SVG command: %s"
                      % segment.to_dict(get_buffer=False))
                continue
            if viewBox:
                for x_i in range(0, len(buffer2d), 2):
                    y_i = x_i + 1
                    buffer2d[x_i] = int(round(
                        float(buffer2d[x_i] - viewBox[0] + pos[0]) * scale
                    ))
                    buffer2d[y_i] = int(round(
                        float(buffer2d[y_i] - viewBox[1] + pos[1]) * scale
                    ))
            if fill_opacity is None:
                if fill and fill != "none":
                    fill_opacity = 1.0
            if fill_opacity > .5:
                # create_polygon is filled
                self.shapes.append(
                    canvas.create_polygon(
                        *buffer2d,
                        fill=fill,
                        smooth=segment.smooth
                    )  # ^ Python 2 does not like trailing comma above.
                )
            else:
                if stroke == "none":
                    raise ValueError('There is no fill and stroke is "none".')
                # create_line is never filled
                self.shapes.append(
                    canvas.create_line(
                        *buffer2d,
                        fill=stroke,  # create_line never filled so fill is stroke
                        smooth=segment.smooth
                    )  # ^ Python 2 does not like trailing comma above.
                )

    def _draw_svg_root(self, root, canvas, constrain=None, pos=None):
        """Draw a Node assuming it is the svg root node.

        For documentation see draw_svg.
        """
        viewBoxAttr = root.attributes['viewBox']
        # echo0("Attr has: %s" % dir(viewBoxAttr))  # See module dostring
        viewBox = str_to_viewBox(viewBoxAttr.value)
        # for node in root.getElementsByTagName("path"):
        path_count = 0
        for node in root.childNodes:
            # ^ root.childNodes: may be Text object
            # if node.nodeType != Node.ELEMENT_NODE:
            #     continue
            if isinstance(node, Text):
                # has no attribute tagName
                pass
            elif node.tagName == "sodipodi:namedview":
                pass
            elif node.tagName == "defs":
                pass
            elif node.tagName == "path":
                path_count += 1
                self._draw_svg_path(
                    node,
                    canvas,
                    viewBox=viewBox,
                    constrain=constrain,
                    pos=pos,
                )
            else:
                echo0("Warning: unknown tag: %s" % node.tagName)
        if path_count < 1:
            echo0("Warning: 0 paths.")

    def draw_svg(self, data, canvas, constrain=None, pos=None):
        """Draw svg to canvas manually

        This method exists since it doesn't require Tk 8.7 (in alpha 2021).

        Args:
            data (bytes): svg data
            canvas (tk.Canvas): A Canvas or canvas-like object with at
                least .winfo_width(), .winfo_height(), and .create_line().
            constrain (string): "width" or "height" fit the image to
                width or height. This requires viewBox to be set in the
                SVG, otherwise constrain is ignored.
            pos (Iterable[int]): Position (in Canvas units, usually pixels)
                where the path should be drawn.
        """
        dom = parseString(data)
        done = False
        for root in dom.childNodes:
            # usually just one
            # print("node has: %s" % dir(root))  # See module dostring
            if type(root).__name__ == "DocumentType":
                continue
            if done:
                echo0("Warning got extra %s" % root.tagName)
            else:
                echo0("Using %s" % root.tagName)
            self._draw_svg_root(
                root,
                canvas,
                constrain=constrain,
                pos=pos,
            )
            done = True
