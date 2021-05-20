from __future__ import annotations
from typing import *
from abc import *
import math

from gui.graphics import Point, Bounds
from misc.util import *
from misc import default

class Renderable(ABC):

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

    @abstractmethod
    def dsl(self, _depth: int = 0, _identifier: bool = False) -> str:
        pass

    def __len__(self) -> int:
        return 1


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

    def dsl(self, _depth: int = 0, _identifier: bool = False) -> str:
        return "{}{}{}{}{}".format(
            "\t" * _depth,
            "{}{}".format(default.tokens[default.identifier], self.identifier) if _identifier else "",
            self.name,
            format_list(self.parameters, str, default.tokens[default.primitive_begin], default.tokens[default.value_separator], default.tokens[default.primitive_end]),
            default.tokens[default.primitive_separator])

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

    def copy(self, reference_factory: ReferenceFactory) -> PrimitiveGroup.Parameter:
        return self.from_list(reference_factory.new(), self.name, self.parameters)

class PrimitiveGroup(Renderable):
    Parameter = Union[Primitive, "PrimitiveGroup"]
    Parameters = List[Parameter]

    def __init__(self, identifier: ReferenceFactory.Reference, *primitives: PrimitiveGroup.Parameter):
        super(PrimitiveGroup, self).__init__(identifier)

        self._arity: int = 0
        self.primitives: List[PrimitiveGroup.Parameter] = []
        self._master: Optional[Primitive] = None
        self._min_arity: Optional[int] = None
        self._max_arity: Optional[int] = None

        for primitive in primitives:
            self.append(primitive)

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

    def dsl(self, _depth: int = 0, _identifier: bool = False) -> str:
        return "{}{}\n{}\n{}".format(
            "\t" * _depth,
            default.tokens[default.primitive_group_begin],
            "\n".join([primitive.dsl(_depth + 1, _identifier) for primitive in self.primitives]),
            "\t" * _depth + default.tokens[default.primitive_group_end])

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

    def remove(self, *primitives: PrimitiveGroup.Parameter):
        for primitive in primitives:
            self.primitives.remove(primitive)

        self._master: Optional[Primitive] = None
        self._min_arity = None
        self._max_arity = None
        self._arity = 0

        for primitive in self.primitives:
            if self._arity == 0:
                self._master = primitive.master

            self._update_min_arity(primitive.master.arity)
            self._update_max_arity(primitive.master.arity)
            self._arity += 1

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

    def depth(self, item: ReferenceFactory.Reference) -> Optional[int]:
        if item == self.identifier:
            return 0

        for primitive in self.primitives:
            if primitive.identifier == item:
                return 1

            if isinstance(primitive, PrimitiveGroup):
                result = primitive.depth(item)

                if result is not None:
                    return result + 1

        return None

    def parent(self, item: ReferenceFactory.Reference) -> Optional[PrimitiveGroup.Parameter]:
        for primitive in self.primitives:
            if primitive.identifier == item:
                return self

            if isinstance(primitive, PrimitiveGroup):
                result = primitive.find(item)

                if result is not None:
                    return result

    def copy(self, reference_factory: ReferenceFactory) -> PrimitiveGroup.Parameter:
        primitives = [primitive.copy(reference_factory) for primitive in self.primitives]

        return PrimitiveGroup(reference_factory.new(), *primitives)

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

    def tikz(self):
        return "\n".join([primitive.tikz() for primitive in self.primitives])

class Rect(Primitive):
    width = 50
    height = 50

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Rect, self).__init__(identifier, Rect.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "rect"

    @staticmethod
    def static_arity() -> List[int]:
        return [2, 3, 4, 5]

    def get_size(self) -> Tuple[Primitive.Parameter, Primitive.Parameter]:
        if self.arity == 2:
            width = Rect.width
            height = Rect.height
        elif self.arity == 3:
            width = self[2]
            height = self[2]
        else:
            width = self[2]
            height = self[3]

        return width, height

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y

    def position(self) -> Point:
        # width, height = self.get_size()
        #
        # x = self[0] + width / 2
        # y = self[1] + height / 2
        # return Point(x, y)

        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        width, height = self.get_size()

        # return Bounds(Point(self[0], self[1]), Point(self[0] + width, self[1] + height))

        return Bounds(Point(self[0] - width / 2.0, self[1] - height / 2.0), Point(self[0] + width / 2.0, self[1] + height / 2.0))

    def handles(self) -> List[Point]:
        width, height = self.get_size()

        # return [Point(self[0] + width, self[1] + height)]
        return [Point(self[0] + width / 2.0, self[1] + height / 2.0)]

    def handle(self, index: int, position: Point):
        if index == 0:
            if self.arity == 3:
                self[2] = (position - self.position()).length() * math.sqrt(2)
            elif self.arity > 3:
                self[2] = 2 * int(position.x - self[0])
                self[3] = 2 * int(position.y - self[1])

    def render(self, draw_list: Any, offset: Point, scale: int, factor: float = 1.0):
        if self.arity == 5:
            color = parse_color(self[4], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        width, height = self.get_size()
        # draw_list.add_rect_filled(self[0] * scale + offset.x,
        #                           self[1] * -scale + offset.y,
        #                           (self[0] + width) * scale + offset.x,
        #                           (self[1] + height) * -scale + offset.y,
        #                           color)
        draw_list.add_rect_filled((self[0] - width / 2.0) * scale + offset.x,
                                  (self[1] - height / 2.0) * -scale + offset.y,
                                  (self[0] + width / 2.0) * scale + offset.x,
                                  (self[1] + height / 2.0) * -scale + offset.y,
                                  color)

    def tikz(self) -> str:
        if self.arity == 5:
            r, g, b, a = parse_color_rgba(self[4], 1.0)
        else:
            r, g, b, a = default.r, default.g, default.b, default.a

        def f(c):
            return min(max(0, int(c * 255.0)), 255)

        bounds = self.bounds()
        return "\\draw [fill={{rgb, 255: red, {}; green, {}; blue, {}}}, draw opacity={}] ({}, {}) rectangle ({}, {});".format(
            f(r),
            f(g),
            f(b),
            a,
            bounds.min_x(),
            bounds.min_y(),
            bounds.max_x(),
            bounds.max_y()
        )

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

    def tikz(self):
        if self.arity == 5:
            r, g, b, a = parse_color_rgba(self[4], 1.0)
        else:
            r, g, b, a = default.r, default.g, default.b, default.a

        def f(c):
            return min(max(0, int(c * 255.0)), 255)

        bounds = self.bounds()
        return "\\draw [color={{rgb, 255: red, {}; green, {}; blue, {}}}, draw opacity={}] ({}, {}) -- ({}, {});".format(
            f(r),
            f(g),
            f(b),
            a,
            bounds.min_x(),
            bounds.min_y(),
            bounds.max_x(),
            bounds.max_y()
        )

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

    def tikz(self):
        if self.arity == 5:
            r, g, b, a = parse_color_rgba(self[4], 1.0)
        else:
            r, g, b, a = default.r, default.g, default.b, default.a

        def f(c):
            return min(max(0,int(c * 255.0)), 256)

        return "\\draw [-{{Triangle[width=8,length=10]}}][color={{rgb, 255: red, {}; green, {}; blue, {}}}, draw opacity={}] ({}, {}) -- ({}, {});".format(
            f(r),
            f(g),
            f(b),
            a,
            self.position().x,
            self.position().y,
            self[0] + self[3] * math.cos(math.radians(self[2])),
            self[1] + self[3] * math.sin(math.radians(self[2]))
        )

class Circle(Primitive):
    radius = 25

    def __init__(self, identifier: ReferenceFactory.Reference, arity: int, *parameters: Primitive.Parameter):
        super(Circle, self).__init__(identifier, Circle.static_name(), arity, *parameters)

    @staticmethod
    def static_name() -> str:
        return "circle"

    @staticmethod
    def static_arity() -> List[int]:
        return [2, 3, 4]

    def move(self, delta: Point):
        self[0] += delta.x
        self[1] += delta.y

    def position(self) -> Point:
        return Point(self[0], self[1])

    def bounds(self) -> Bounds:
        if self.arity < 3:
            radius = 25
        else:
            radius = self[2]

        min_x, min_y = self[0] - radius, self[1] - radius
        max_x, max_y = self[0] + radius, self[1] + radius

        return Bounds(Point(min_x, min_y), Point(max_x, max_y))

    def handles(self) -> List[Point]:
        if self.arity < 3:
            return []

        return [Point(self[0] + self[2], self[1])]

    def handle(self, index: int, position: Point):
        if self.arity < 3:
            return

        if index == 0:
            r = Point(self[0], self[1]).length()
            self[2] = int((position - Point(r, r)))

    def render(self, draw_list: Any, offset: Point, scale: float, factor: float = 1.0):
        if self.arity == 4:
            color = parse_color(self[3], factor)
        else:
            color = imgui.get_color_u32_rgba(default.r * factor, default.g * factor, default.b * factor, default.a)

        if self.arity < 3:
            radius = 25
        else:
            radius = self[2]

        draw_list.add_circle_filled(self[0] * scale + offset.x,
                                    self[1] * -scale + offset.y,
                                    radius * scale,
                                    color,
                                    30)

    def tikz(self):
        if self.arity == 4:
            r, g, b, a = parse_color_rgba(self[3], 1.0)
        else:
            r, g, b, a = default.r, default.g, default.b, default.a

        def f(c):
            return min(max(0,int(c * 255.0)), 255)

        if self.arity < 3:
            radius = 25
        else:
            radius = self[2]

        return "\\draw [fill={{rgb, 255: red, {}; green, {}; blue, {}}}, draw opacity={}] ({}, {}) circle ({});".format(
            f(r),
            f(g),
            f(b),
            a,
            self.position().x,
            self.position().y,
            radius
        )