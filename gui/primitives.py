from __future__ import annotations
from typing import *
from abc import *
import math

from gui.graphics import Point, Bounds
from misc.util import *
from misc import default

class Renderable(ABC):
    referenceFactory = ReferenceFactory()

    def __init__(self):
        self._identifier = Renderable.referenceFactory.new()

    @property
    def identifier(self) -> ReferenceFactory.Reference:
        return self._identifier

    @identifier.setter
    def identifier(self, value: ReferenceFactory.Reference):
        pass

    def master(self):
        return self

    def move(self, position: Point):
        pass

    def position(self) -> Point:
        return Point(0, 0)

    def bounds(self) -> Bounds:
        return Bounds(Point(0, 0), Point(0, 0))

    def handles(self) -> [Point]:
        return []

    def handle(self, index: int, position: Point):
        pass

    def render(self, draw_list, offset: Point, scale: float):
        pass


class Primitive(Renderable):
    Parameter = Union[int, float, str]
    Parameters = List[Parameter]

    def __init__(self, name: Optional[str], arity: int, *parameters: Primitive.Parameter):
        super(Primitive, self).__init__()

        self.name: str = name
        self.arity: int = arity
        self.parameters: Primitive.Parameters = list(parameters)

    def __getitem__(self, item: int) -> Primitive.Parameter:
        return self.parameters[item]

    def __setitem__(self, key: int, value: Primitive.Parameter):
        self.parameters[key] = value

    def __str__(self) -> str:
        return "{}{}{}".format(
            self.name,
            format_list(self.parameters, str, default.tokens[default.primitive_begin], default.tokens[default.value_separator], default.tokens[default.primitive_end]),
            default.tokens[default.primitive_separator])

    def __repr__(self) -> str:
        return self.name + "/" + str(self.arity) + str(self.parameters)

    def __len__(self) -> int:
        return self.arity

    @property
    def master(self) -> Primitive:
        return self

    def as_list(self):
        return [self.name] + self.parameters

    @staticmethod
    def from_list(parameters: Primitive.Parameters):
        assert len(parameters) > 0
        name = parameters[0]
        arity = len(parameters) - 1
        for primitive in [Line, Rect, Circle, Vector]:
            if name == primitive.static_name():
                if arity not in primitive.static_arity():
                    return None
                return primitive(arity, *parameters[1:])

        return Primitive(name, arity, *parameters[1:])


class PrimitiveGroup(Renderable):
    Parameter = Union[Primitive, "PrimitiveGroup"]
    Parameters = List[Parameter]

    def __init__(self, *primitives: Union[Primitive, PrimitiveGroup]):
        super(PrimitiveGroup, self).__init__()

        self._arity: int = len(primitives)
        self.primitives: PrimitiveGroup.Parameters = list(primitives)
        self._master: Optional[Primitive] = None
        self._min_arity: Optional[int] = None
        self._max_arity: Optional[int] = None

    def __str__(self) -> str:
        return format_list(self.primitives, str, default.tokens[default.primitive_group_begin], '', default.tokens[default.primitive_group_end], ' ')

    def __repr__(self) -> str:
        return "{{{}}}".format(", ".join(map(repr, self.primitives)))

    def __getitem__(self, item: int) -> Union[Primitive, PrimitiveGroup]:
        return self.primitives[item]

    def __iter__(self):
        return self.primitives.__iter__()

    @property
    def master(self) -> Optional[Primitive]:
        return self._master

    @master.setter
    def master(self, value):
        self._master = value

    @property
    def max_arity(self) -> Optional[int]:
        return self._max_arity

    @property
    def min_arity(self) -> Optional[int]:
        return self._min_arity

    @property
    def arity(self):
        return self._arity

    def _update_min_arity(self, min_arity: int):
        if self._min_arity is None or min_arity < self._min_arity:
            self._min_arity = min_arity

    def _update_max_arity(self, arity: int):
        if self._max_arity is None or arity > self._max_arity:
            self._max_arity = arity

    def _recalculate_arity(self):
        self._min_arity = None
        self._max_arity = None
        for primitive in self.primitives:
            self._update_min_arity(primitive.master.arity)
            self._update_max_arity(primitive.master.arity)

    def append(self, parameter: PrimitiveGroup.Parameter):
        if self.arity == 0:
            self._master = parameter.master

        self._update_min_arity(parameter.master.arity)
        self._update_max_arity(parameter.master.arity)

        self.primitives.append(parameter)
        self._arity += 1

    def find(self, item: ReferenceFactory.Reference) -> Optional[PrimitiveGroup.Parameter]:
        for primitive in self.primitives:
            if primitive.identifier == item:
                return self

            if isinstance(primitive, PrimitiveGroup):
                result = primitive.find(item)

                if result is not None:
                    return result

        return None

    def move(self, position):
        for primitive in self.primitives:
            primitive.move(position)

    def position(self) -> Point:
        position = Point(0, 0)
        for primitive in self.primitives:
            position += primitive.position()

        return position / self.arity

    def bounds(self) -> Bounds:
        bounds = None
        for primitive in self.primitives:
            if bounds is None:
                bounds = primitive.bounds()
            else:
                bounds = bounds.expanded(primitive.bounds)
        return bounds

    def render(self, draw_list, offset, scale):
        self.bounds().render(draw_list, offset, scale, 10)
        for primitive in self.primitives:
            primitive.render(draw_list, offset, scale)


class Rect(Primitive):
    @staticmethod
    def static_name():
        return "rect"

    @staticmethod
    def static_arity():
        return [4, 5]

    def __init__(self, arity, *parameters):
        assert arity in Rect.static_arity()
        super(Rect, self).__init__(Rect.static_name(), arity, *parameters)

    def move(self, position):
        self[0] = int(position.x - self[2] / 2)
        self[1] = int(position.y - self[3] / 2)

    def position(self) -> Point:
        x = self[0] + self[2] / 2
        y = self[1] + self[3] / 2
        return Point(x, y)

    def bounds(self) -> Bounds:
        return Bounds(Point(self[0], self[1]), Point(self[0] + self[2], self[1] + self[3]))

    def handles(self) -> [Point]:
        return [Point(self[0] + self[2], self[1] + self[3])]

    def handle(self, index, position):
        if index == 0:
            self[2] = int(position.x - self[0])
            self[3] = int(position.y - self[1])

    def render(self, draw_list, offset, scale):
        if self.arity == 5:
            color = parse_color(self[4])
        else:
            color = imgui.get_color_u32_rgba(0.4, 0.6, 0.4, 0.8)

        draw_list.add_rect_filled(self[0] * scale + offset.x,
                                  self[1] * -scale + offset.y,
                                  (self[0] + self[2]) * scale + offset.x,
                                  (self[1] + self[3]) * -scale + offset.y,
                                  color)


class Line(Primitive):
    @staticmethod
    def static_name():
        return "line"

    @staticmethod
    def static_arity():
        return [4, 5]

    def __init__(self, arity, *parameters):
        super(Line, self).__init__(Line.static_name(), arity, *parameters)

    def move(self, position):
        delta = self.position() - position

        self[0] -= delta.x
        self[1] -= delta.y
        self[2] -= delta.x
        self[3] -= delta.y

    def position(self) -> Point:
        min_x, max_x = minmax(self[0], self[2])
        min_y, max_y = minmax(self[1], self[3])
        dx, dy = max_x - min_x, max_y - min_y

        return Point(min_x + dx / 2.0, min_y + dy / 2.0)

    def bounds(self) -> Bounds:
        min_x, max_x = minmax(self[0], self[2])
        min_y, max_y = minmax(self[1], self[3])
        return Bounds(Point(min_x, min_y), Point(max_x, max_y))

    def handles(self) -> [Bounds]:
        return [Point(self[0], self[1]), Point(self[2], self[3])]

    def handle(self, index, position):
        if index == 0:
            self[0] = int(position.x)
            self[1] = int(position.y)
        elif index == 1:
            self[2] = int(position.x)
            self[3] = int(position.y)

    def render(self, draw_list, offset, scale):
        if self.arity == 5:
            color = parse_color(self[4])
        else:
            color = imgui.get_color_u32_rgba(0.4, 0.6, 0.4, 0.8)

        draw_list.add_line(self[0] * scale + offset.x,
                           self[1] * -scale + offset.y,
                           self[2] * scale + offset.x,
                           self[3] * -scale + offset.y,
                           color)


class Vector(Primitive):
    @staticmethod
    def static_name():
        return "vector"

    @staticmethod
    def static_arity():
        return [4, 5]

    def __init__(self, arity, *parameters):
        super(Vector, self).__init__(Vector.static_name(), arity, *parameters)

    def move(self, position):
        delta = self.position() - position

        self[0] -= delta.x
        self[1] -= delta.y

    def position(self) -> Point:
        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        return Bounds(
            Point(self[0], self[1]),
            Point(self[0] + self[3] * math.cos(math.radians(self[2])), self[1] + self[3] * math.sin(math.radians(self[2]))))

    def handles(self) -> [Point]:
        return [Point(self[0], self[1]), Point(self[0] + self[3] * math.cos(math.radians(self[2])), self[1] + self[3] * math.sin(math.radians(self[2])))]

    def handle(self, index, position):
        if index == 0:
            self[0] = int(position.x)
            self[1] = int(position.y)
        elif index == 1:
            delta = position - self.position()
            self[2] = int(math.degrees(math.atan2(delta.y, delta.x)))
            if self[2] < 0:
                self[2] += 180
            self[3] = int(delta.length())

    def render(self, draw_list, offset, scale):
        if self.arity == 5:
            color = parse_color(self[4])
        else:
            color = imgui.get_color_u32_rgba(0.4, 0.6, 0.4, 0.8)

        draw_list.add_line(self[0] * scale + offset.x,
                           self[1] * -scale + offset.y,
                           self[0] * scale + self[3] * math.cos(math.radians(self[2])) * scale + offset.x,
                           self[1] * -scale + self[3] * math.sin(math.radians(self[2])) * -scale + offset.y,
                           color)


class Circle(Primitive):
    @staticmethod
    def static_name():
        return "circle"

    @staticmethod
    def static_arity():
        return [3, 4]

    def __init__(self, arity, *parameters):
        assert arity in Circle.static_arity()
        super(Circle, self).__init__(Circle.static_name(), arity, *parameters)

    def move(self, position):
        self[0] = int(position.x)
        self[1] = int(position.y)

    def position(self) -> Point:
        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        min_x, min_y = self[0] - self[2], self[1] - self[2]
        max_x, max_y = self[0] + self[2], self[1] + self[2]

        return Bounds(Point(min_x, min_y), Point(max_x, max_y))

    def handles(self) -> [Point]:
        return [Point(self[0] + self[2], self[1])]

    def handle(self, index, position):
        if index == 0:
            self[2] = int((position - Point(self[0], self[1]).length()))

    def render(self, draw_list, offset, scale):
        if self.arity == 4:
            color = parse_color(self[3])
        else:
            color = imgui.get_color_u32_rgba(0.4, 0.6, 0.4, 0.8)

        draw_list.add_circle_filled(self[0] * scale + offset.x,
                                    self[1] * -scale + offset.y,
                                    self[2] * scale,
                                    color,
                                    30)