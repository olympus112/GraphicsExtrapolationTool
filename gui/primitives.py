from gui import util
from gui.graphics import Point, Bounds
import math
import imgui

class Primitive:
    def __init__(self, name, arity, *parameters):
        self.name = name
        self.arity = arity
        self.parameters = list(parameters)

    def __getitem__(self, item):
        return self.parameters[item]

    def __setitem__(self, key, value):
        self.parameters[key] = value

    def __str__(self):
        return self.name + ", ".join(map(str, self.parameters)).join(list("()")) + "."

    def __repr__(self):
        return self.name + "/" + str(self.arity) + str(self.parameters)

    def move(self, position):
        pass

    def position(self) -> Point:
        return Point(0, 0)

    def bounds(self) -> Bounds:
        return Bounds(Point(0, 0), Point(0, 0))

    def handles(self) -> [Point]:
        return []

    def handle(self, index, position):
        pass

    def render(self, draw_list, offset, scale):
        pass

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
            color = util.parse_color(self[4])
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
        min_x, max_x = util.minmax(self[0], self[2])
        min_y, max_y = util.minmax(self[1], self[3])
        dx, dy = max_x - min_x, max_y - min_y

        return Point(min_x + dx / 2.0, min_y + dy / 2.0)

    def bounds(self) -> Bounds:
        min_x, max_x = util.minmax(self[0], self[2])
        min_y, max_y = util.minmax(self[1], self[3])
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
            color = util.parse_color(self[4])
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
            color = util.parse_color(self[4])
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
            color = util.parse_color(self[3])
        else:
            color = imgui.get_color_u32_rgba(0.4, 0.6, 0.4, 0.8)

        draw_list.add_circle_filled(self[0] * scale + offset.x,
                                    self[1] * -scale + offset.y,
                                    self[2] * scale,
                                    color,
                                    30)
