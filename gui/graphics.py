import math

import imgui

BUTTON_LEFT = 0
BUTTON_RIGHT = 1
BUTTON_MIDDLE = 2

class Point:
    def __init__(self, x: int, y: int):
        self.x = int(x)
        self.y = int(y)

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y

        return Point(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y

        return Point(x, y)

    def __len__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def render(self, draw_list, offset):
        draw_list.add_circle(self.x + offset.x, self.y + offset.y, 10, imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0))

class Dimension:
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Bounds:
    def __init__(self, min: Point, max: Point):
        self.min = min
        self.max = max

    @staticmethod
    def centered(point: Point, offset: int):
        offset_point = Point(offset, offset)
        min = point - offset_point
        max = point + offset_point

        return Bounds(min, max)

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

    def render(self, canvas, offset=0, color='red'):
        pass

    def clear(self, canvas):
        pass

    def __contains__(self, item):
        return self.min.x <= item.x <= self.max.x and self.min.y <= item.y <= self.max.y

class Canvas:
    handle_size = 5

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)

        self.primitives = []

        self.intersected_primitive = None
        self.intersected_point = None
        self.selected_primitive = None
        self.selected_point = None
        self.selected_handle = None
        self.dragging = False

    def __len__(self):
        return len(self.primitives)

    def __getitem__(self, item):
        return self.primitives[item]

    def __str__(self):
        return "\n".join(map(str, self.primitives))

    def __repr__(self):
        return "Canvas:" \
               "\nintersect = (" + self.intersected_primitive + ", " + self.intersected_point + ")" \
               "\nselect = (" + self.selected_primitive + ", " + self.selected_point + ")" + \
               "\nhandle = " + self.selected_handle + \
               "\nprimitives = [\n" + ",\n".join(map(repr, self.primitives)) + "\n]"

    def any(self, callback):
        for primitive in enumerate(self.primitives):
            if callback(primitive) is True:
                return True

        return False

    def all(self, callback):
        for primitive in enumerate(self.primitives):
            if callback(primitive) is False:
                return False

        return True

    def for_each(self, callback):
        for primitive in enumerate(self.primitives):
            callback(primitive)

    def render(self, draw_list, offset):
        for index, primitive in enumerate(self.primitives):
            primitive.render(draw_list, offset)

            if index == self.intersected_primitive:
                primitive.bounds().render(draw_list, offset)

            if index == self.selected_primitive:
                for handle in primitive.handles():
                    handle.render(draw_list, offset)

    def mouse_move(self, position):
        self.intersected_primitive = None
        self.intersected_point = position

        for index, primitive in enumerate(self.primitives):
            if self.intersected_point in primitive.bounds():
                self.intersected_primitive = index
                break

    def mouse_drag(self, position):
        if self.selected_primitive is not None:
            primitive = self[self.selected_primitive]

            if self.selected_handle is None:
                for index, handle in enumerate(primitive.handles()):
                    if self.intersected_point in Bounds.centered(handle, Canvas.handle_size):
                        self.selected_handle = index
                        break

            if self.selected_handle is None:
                current_position = primitive.position()
                relative_offset_x = self.selected_point.x - current_position.x
                relative_offset_y = self.selected_point.y - current_position.y
                new_x = self.intersected_point.x - relative_offset_x
                new_y = self.intersected_point.y - relative_offset_y

                primitive.move(Point(new_x, new_y))
            else:
                primitive.handle(self.selected_handle, self.intersected_point)

            self.selected_point = self.intersected_point

    def mouse_press(self, position):
        self.dragging = True
        self.selected_point = self.intersected_point

        if self.selected_primitive is not None:
            # Check first if a handle is selected
            primitive = self[self.selected_primitive]
            for index, handle in enumerate(primitive.handles()):
                if position in Bounds.centered(handle, Canvas.handle_size):
                    self.selected_handle = index
                    break
            else:
                self.selected_primitive = self.intersected_primitive
        else:
            # Update selected primitive
            self.selected_primitive = self.intersected_primitive


    def mouse_release(self, event):
        self.dragging = False
        self.selected_handle = None
