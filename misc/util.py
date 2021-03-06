from typing import Set

import imgui
import numpy as np

from pylo.language.commons import Constant

class ReferenceFactory:
    Reference = int

    def __init__(self):
        self._reference_counter: ReferenceFactory.Reference = -1
        self._free_references: Set[ReferenceFactory.Reference] = set()

    def new(self) -> Reference:
        if len(self._free_references) == 0:
            self._reference_counter += 1
            return self._reference_counter
        else:
            return self._free_references.pop()

    def release(self, reference: Reference):
        if reference < 0:
            return

        self._free_references.add(reference)

    def reserve(self, reference: Reference):
        if reference < 0:
            return

        if self._reference_counter < reference:
            for new_reference in range(self._reference_counter + 1, reference):
                self._free_references.add(new_reference)
        elif reference in self._free_references:
            self._free_references.remove(reference)
        else:
            print("Reference already used: {}", reference)

    def is_free(self, reference: Reference) -> bool:
        return reference > self._reference_counter or reference in self._free_references

    def reset(self):
        self._reference_counter = -1
        self._free_references.clear()

def frange(start, stop=None, step=None):
    # if set start=0.0 and step = 1.0 if not specified
    start = float(start)
    if stop is None:
        stop = start + 0.0
        start = 0.0
    if step is None:
        step = 1.0

    count = 0
    while True:
        temp = float(start + count * step)
        if step > 0 and temp >= stop:
            break
        elif step < 0 and temp <= stop:
            break
        yield temp
        count += 1

def minmax(a, b):
    if a < b:
        return a, b

    return b, a


def all_same(parameters, tolerance):
    return all(equal_tolerant(parameters[0], parameter, tolerance) for parameter in parameters)

def clamp(value, min, max):
    if value < min:
        return min
    if value > max:
        return max
    return value

class Tolerance:
    def __init__(self, absolute: float, relative: float):
        self.absolute = absolute
        self.relative = relative

def equal_tolerant(x: float, y: float, tolerance: Tolerance):
    if tolerance is None:
        return x == y

    return np.isclose(x, y, rtol=tolerance.relative, atol=tolerance.absolute)

def map_range(x, min_in, max_in, min_out, max_out):
    return (x - min_in) * (max_out - min_out) / (max_in - min_in) + min_out

def parse_color(color, factor):
    r, g, b, a = parse_color_rgba(color, factor)

    return imgui.get_color_u32_rgba(r * factor, g * factor, b * factor, a)

def parse_color_rgba(color, factor):
    r, g, b, a = 1.0, 1.0, 1.0, 1.0

    def hsv_to_rgb(h, s, v):
        if s == 0.0:
            v *= 255
            return v, v, v
        i = int(h * 6.)  # XXX assume int() truncates!
        f = (h * 6.) - i
        p, q, t = int(255 * (v * (1. - s))), int(255 * (v * (1. - s * f))), int(255 * (v * (1. - s * (1. - f))))
        v *= 255
        i %= 6
        if i == 0:
            return v, t, p
        if i == 1:
            return q, v, p
        if i == 2:
            return p, v, t
        if i == 3:
            return p, q, v
        if i == 4:
            return t, p, v
        if i == 5:
            return v, p, q

    default_a = 0.5
    if isinstance(color, (Constant, str)):
        if isinstance(color, Constant):
            color = color.name
        colors = {"r": (1.0, 0.0, 0.0), "g": (0.0, 1.0, 0.0), "b": (0.0, 0.0, 1.0)}
        if color in colors:
            (r, g, b), a = colors[color], default_a
        elif color.startswith("c_"):
            if len(color) == 8:
                (r, g, b), a = (float(int(color.lstrip("c_")[i:i+2], 16)) / 255.0 for i in (0, 2, 4)), default_a
            elif len(color) == 10:
                (r, g, b, a) = (float(int(color.lstrip("c_")[i:i+2], 16)) / 255.0 for i in (0, 2, 4, 6))
    elif isinstance(color, (int, float, np.integer)):
        if color <= 1:
            (r, g, b), a = tuple([x / 255.0 for x in hsv_to_rgb(color, 1.0, 1.0)]), default_a
        else:
            (r, g, b), a = tuple([x / 255.0 for x in hsv_to_rgb((color % 360.0) / 360.0, 1.0, 1.0)]), default_a
    else:
        print(color, type(color))

    return r, g, b, a
def print_methods(obj):
    print([method_name for method_name in dir(obj) if callable(getattr(obj, method_name))])

def print_attrs(obj):
    print([attr for attr in dir(obj)])

def format_list(_list, _format=str, _begin='[', _separator=',', _end=']', _outer_space='', _inner_space=' '):
    if len(_list) == 0:
        return _begin + _end

    return (_separator + _inner_space).join(list(map(_format, _list))).join([_begin + _outer_space, _outer_space + _end])

def imgui_property(text, widget=None, *args):
    imgui.text_unformatted(text)
    imgui.next_column()
    imgui.push_item_width(-1)
    if widget is not None:
        result = widget(*args)
    else:
        result = None
    imgui.next_column()

    return result

def imgui_title(text, newline=False):
    if newline:
        imgui_property("")
    imgui.text_colored(text, 0.46, 0.54, 0.8, 1.0)
    imgui.next_column()
    imgui.push_item_width(-1)
    imgui.next_column()

def imgui_properties_start():
    imgui.columns(2)

def imgui_properties_end():
    imgui.columns(1)
