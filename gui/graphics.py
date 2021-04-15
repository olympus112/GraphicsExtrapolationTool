import math
from typing import Union

import imgui

from misc import util

BUTTON_LEFT = 0
BUTTON_RIGHT = 1
BUTTON_MIDDLE = 2

class Point:
    def __init__(self, x: Union[int, float], y: Union[int, float]):
        self.x = x
        self.y = y

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y

        return Point(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y

        return Point(x, y)

    def __mul__(self, other):
        x = self.x * other
        y = self.y * other

        return Point(x, y)

    def __truediv__(self, other):
        x = self.x / other
        y = self.y / other

        return Point(x, y)

    def min(self, other):
        return Point(
            self.x if other.x > self.x else other.x,
            self.y if other.y > self.y else other.y,
        )

    def max(self, other):
        return Point(
            self.x if other.x < self.x else other.x,
            self.y if other.y < self.y else other.y,
        )

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def render(self, draw_list, offset, scale):
        draw_list.add_circle(
            self.x * scale + offset.x,
            self.y * -scale + offset.y,
            10,
            imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0))

class Dimension:
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Bounds:
    def __init__(self, min: Point, max: Point):
        self.min = min
        self.max = max

    def __mul__(self, other):
        min = self.min * other
        max = self.max * other

        return Bounds(min, max)

    def __truediv__(self, other):
        min = self.min / other
        max = self.max / other

        return Bounds(min, max)

    def __contains__(self, item):
        return self.min.x <= item.x <= self.max.x and self.min.y <= item.y <= self.max.y

    @staticmethod
    def centered(point: Point, offset: int):
        offset_point = Point(offset, offset)
        min = point - offset_point
        max = point + offset_point

        return Bounds(min, max)

    def expanded(self, other):
        return Bounds(
            self.min.min(other.min),
            self.max.max(other.max)
        )

    def min_x(self):
        return self.min.x

    def min_y(self):
        return self.min.y

    def max_x(self):
        return self.max.x

    def max_y(self):
        return self.max.y

    def width(self):
        return self.max.x - self.min.x

    def height(self):
        return self.max.y - self.min.y

    def render(self, draw_list, offset, scale, factor=1.0, margin=0):
        draw_list.add_rect(self.min.x * scale + offset.x - margin,
                           self.min.y * -scale + offset.y + margin,
                           self.max.x * scale + offset.x + margin,
                           self.max.y * -scale + offset.y - margin,
                           imgui.get_color_u32_rgba(0.9 * factor, 0.9 * factor, 0.9 * factor, 1.0))