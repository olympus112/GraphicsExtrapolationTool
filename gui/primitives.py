from __future__ import annotations
from typing import *
from abc import *
import math

from gui.graphics import Point, Bounds
from misc.util import *
from misc import default

class Renderable(ABC):
    referenceFactory = ReferenceFactory()

    def __init__(self, identifier: ReferenceFactory.Reference):
        self._identifier = identifier

    @property
    def identifier(self) -> ReferenceFactory.Reference:
        return self._identifier

    @identifier.setter
    def identifier(self, value: ReferenceFactory.Reference):
        pass

    def master(self):
        return self

    def move(self, delta: Point):
        pass

    def position(self) -> Point:
        return Point(0, 0)

    def bounds(self) -> Bounds:
        return Bounds(Point(0, 0), Point(0, 0))

    def handles(self) -> [Point]:
        return []

    def handle(self, index: int, position: Point):
        pass

    def render(self, draw_list, offset: Point, scale: float, factor: float = 1.0):
        pass


class Primitive(Renderable):
    Parameter = Union[int, float, str]
    Parameters = List[Parameter]

    def __init__(self, identifier: ReferenceFactory.Reference, name: Optional[str], arity: int, *parameters: Primitive.Parameter):
        super(Primitive, self).__init__(identifier)

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

    def as_list(self) -> Primitive.Parameters:
        return [self.name] + self.parameters

    @staticmethod
    def from_list(identifier: ReferenceFactory.Reference, name: str, parameters: Primitive.Parameters):
        arity = len(parameters)
        for primitive in [Line, Rect, Circle, Vector]:
            if name == primitive.static_name():
                if arity not in primitive.static_arity():
                    return None

                return primitive(identifier, arity, *parameters)

        return Primitive(identifier, name, arity, *parameters)

    @staticmethod
    def static_arity() -> List[int]:
        pass

class PrimitiveGroup(Renderable):
    Parameter = Union[Primitive, "PrimitiveGroup"]
    Parameters = List[Parameter]

    def __init__(self, identifier: ReferenceFactory.Reference, *primitives: PrimitiveGroup.Parameter):
        super(PrimitiveGroup, self).__init__(identifier)

        self._arity: int = len(primitives)
        self.primitives: PrimitiveGroup.Parameters = [*primitives]
        self._master: Optional[Primitive] = None
        self._min_arity: Optional[int] = None
        self._max_arity: Optional[int] = None

    def __str__(self) -> str:
        return format_list(self.primitives, str, default.tokens[default.primitive_group_begin], '', default.tokens[default.primitive_group_end], ' ')

    def __repr__(self) -> str:
        return "{{{}}}".format(", ".join(map(repr, self.primitives)))

    def __getitem__(self, item: int) -> PrimitiveGroup.Parameter:
        return self.primitives[item]

    def __len__(self) -> int:
        return len(self.primitives)

    def __iter__(self):
        return self.primitives.__iter__()

    def __reversed__(self):
        return self.primitives.__reversed__()

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
    def arity(self) -> int:
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

    def reset(self):
        self._arity: int = 0
        self.primitives: PrimitiveGroup.Parameters = []
        self._master: Optional[Primitive] = None
        self._min_arity: Optional[int] = None
        self._max_arity: Optional[int] = None

    def append(self, parameter: PrimitiveGroup.Parameter):
        if self.arity == 0:
            self._master = parameter.master

        self._update_min_arity(parameter.master.arity)
        self._update_max_arity(parameter.master.arity)

        self.primitives.append(parameter)
        self._arity += 1

    def find(self, item: ReferenceFactory.Reference) -> Optional[PrimitiveGroup.Parameter]:
        if item == self.identifier:
            return self

        for primitive in self.primitives:
            if primitive.identifier == item:
                return primitive

            if isinstance(primitive, PrimitiveGroup):
                result = primitive.find(item)

                if result is not None:
                    return result

        return None

    def move(self, position: Point):
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
                bounds = bounds.expanded(primitive.bounds())
        return bounds

    def render(self, draw_list: Any, offset: Point, scale: float, factor: float = 1.0):
        self.bounds().render(draw_list, offset, scale, factor, 10)


class Rect(Primitive):

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Rect, self).__init__(identifier, Rect.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "rect"

    @staticmethod
    def static_arity() -> List[int]:
        return [4, 5]

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y

    def position(self) -> Point:
        x = self[0] + self[2] / 2
        y = self[1] + self[3] / 2
        return Point(x, y)

    def bounds(self) -> Bounds:
        return Bounds(Point(self[0], self[1]), Point(self[0] + self[2], self[1] + self[3]))

    def handles(self) -> List[Point]:
        return [Point(self[0] + self[2], self[1] + self[3])]

    def handle(self, index: int, position: Point):
        if index == 0:
            self[2] = int(position.x - self[0])
            self[3] = int(position.y - self[1])

    def render(self, draw_list: Any, offset: Point, scale: int, factor: float = 1.0):
        if self.arity == 5:
            color = parse_color(self[4], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        draw_list.add_rect_filled(self[0] * scale + offset.x,
                                  self[1] * -scale + offset.y,
                                  (self[0] + self[2]) * scale + offset.x,
                                  (self[1] + self[3]) * -scale + offset.y,
                                  color)


class Line(Primitive):

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Line, self).__init__(identifier, Line.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "line"

    @staticmethod
    def static_arity() -> List[int]:
        return [4, 5]

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y
        self[2] += delta.x
        self[3] += delta.y

    def position(self) -> Point:
        min_x, max_x = minmax(self[0], self[2])
        min_y, max_y = minmax(self[1], self[3])
        dx, dy = max_x - min_x, max_y - min_y

        return Point(min_x + dx / 2.0, min_y + dy / 2.0)

    def bounds(self) -> Bounds:
        min_x, max_x = minmax(self[0], self[2])
        min_y, max_y = minmax(self[1], self[3])
        return Bounds(Point(min_x, min_y), Point(max_x, max_y))

    def handles(self) -> List[Point]:
        return [Point(self[0], self[1]), Point(self[2], self[3])]

    def handle(self, index: int, position: Point):
        if index == 0:
            self[0] = int(position.x)
            self[1] = int(position.y)
        elif index == 1:
            self[2] = int(position.x)
            self[3] = int(position.y)

    def render(self, draw_list: Any, offset: Point, scale: float, factor: float = 1.0):
        if self.arity == 5:
            color = parse_color(self[4], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        draw_list.add_line(self[0] * scale + offset.x,
                           self[1] * -scale + offset.y,
                           self[2] * scale + offset.x,
                           self[3] * -scale + offset.y,
                           color)


class Vector(Primitive):

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Vector, self).__init__(identifier, Vector.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "vector"

    @staticmethod
    def static_arity() -> List[int]:
        return [4, 5]

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y

    def position(self) -> Point:
        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        return Bounds(
            Point(self[0], self[1]),
            Point(self[0] + self[3] * math.cos(math.radians(self[2])), self[1] + self[3] * math.sin(math.radians(self[2]))))

    def handles(self) -> List[Point]:
        return [Point(self[0], self[1]), Point(self[0] + self[3] * math.cos(math.radians(self[2])), self[1] + self[3] * math.sin(math.radians(self[2])))]

    def handle(self, index: int, position: Point):
        if index == 0:
            self[0] = int(position.x)
            self[1] = int(position.y)
        elif index == 1:
            delta = position - self.position()
            self[2] = int(math.degrees(math.atan2(delta.y, delta.x)))
            if self[2] < 0:
                self[2] += 180
            self[3] = int(delta.length())

    def render(self, draw_list: Any, offset: Point, scale: float, factor: float = 1.0):
        if self.arity == 5:
            color = parse_color(self[4], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        draw_list.add_line(self[0] * scale + offset.x,
                           self[1] * -scale + offset.y,
                           self[0] * scale + self[3] * math.cos(math.radians(self[2])) * scale + offset.x,
                           self[1] * -scale + self[3] * math.sin(math.radians(self[2])) * -scale + offset.y,
                           color)


class Circle(Primitive):

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Circle, self).__init__(identifier, Circle.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "circle"

    @staticmethod
    def static_arity() -> List[int]:
        return [3, 4]

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y

    def position(self) -> Point:
        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        min_x, min_y = self[0] - self[2], self[1] - self[2]
        max_x, max_y = self[0] + self[2], self[1] + self[2]

        return Bounds(Point(min_x, min_y), Point(max_x, max_y))

    def handles(self) -> List[Point]:
        return [Point(self[0] + self[2], self[1])]

    def handle(self, index: int, position: Point):
        if index == 0:
            self[2] = int((position - Point(self[0], self[1]).length()))

    def render(self, draw_list: Any, offset: Point, scale: float, factor: float = 1.0):
        if self.arity == 4:
            color = parse_color(self[3], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        draw_list.add_circle_filled(self[0] * scale + offset.x,
                                    self[1] * -scale + offset.y,
                                    self[2] * scale,
                                    color,
                                    30)