import math

import imgui

from gui.graphics import Bounds, Point
from gui.primitives import PrimitiveGroup
from misc import util


class Canvas:
    handle_size = 5

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)

        self.primitives = PrimitiveGroup

        self.intersected_primitive = None
        self.intersected_point = None
        self.selected_primitives: [] = []
        self.selected_point = None
        self.selected_handle = None
        self.scale = 1

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

    def render(self, draw_list, offset, **kwargs):
        for index, primitive in enumerate(self.primitives):
            primitive.render(draw_list, offset, self.scale)

            if index == self.intersected_primitive:
                primitive.bounds().render(draw_list, offset, self.scale, Canvas.handle_size)

            if index == self.selected_primitive:
                primitive.bounds().render(draw_list, offset, self.scale)
                for handle in primitive.handles():
                    handle.render(draw_list, offset, self.scale)

        if "render_order" in kwargs:
            if kwargs["render_order"]:
                self.render_order(draw_list, offset)

    def render_order(self, draw_list, offset):
        for index in range(len(self.primitives) - 1):
            p0 = self.primitives[index].position()
            p1 = self.primitives[index + 1].position()
            draw_list.add_line(p0.x * self.scale + offset.x, p0.y * self.scale + offset.y, p1.x * self.scale + offset.x, p1.y * self.scale + offset.y, imgui.get_color_u32_rgba(0.9, 0.9, 0.9, 1.0))
            draw_list.add_circle_filled(p1.x * self.scale + offset.x, p1.y * self.scale + offset.y, 4 * self.scale, imgui.get_color_u32_rgba(0.9, 0.9, 0.9, 1.0))

    def render_grid(self, draw_list, offset, position_min, position_max, grid_step=64):
        for x in util.frange(math.fmod(offset.x, grid_step * self.scale), position_max.x - position_min.x, grid_step * self.scale):
            color = imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 0.2)
            if offset.x == x:
                color = imgui.get_color_u32_rgba(1, 1, 1, 1)
            draw_list.add_line(position_min.x + x, position_min.y, position_min.x + x, position_max.y, color)
        for y in util.frange(math.fmod(offset.y, grid_step * self.scale), position_max.y - position_min.y, grid_step * self.scale):
            color = imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 0.2)
            if offset.y == y:
                color = imgui.get_color_u32_rgba(1, 1, 1, 1)
            draw_list.add_line(position_min.x, position_min.y + y, position_max.x, position_min.y + y, color)

    def render_canvas(self, draw_list, position_min, position_max):
        draw_list.add_rect_filled(position_min.x, position_min.y, position_max.x, position_max.y,
                                  imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 1.0))
        draw_list.add_rect(position_min.x, position_min.y, position_max.x, position_max.y,
                           imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0))

    def render_cursor(self, draw_list, position):
        offset = 8
        draw_list.add_rect_filled(position.x - offset,
                                  position.y - offset / 5.0,
                                  position.x + offset,
                                  position.y + offset / 5.0,
                                  imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 1.0))
        draw_list.add_rect_filled(position.x - offset / 5.0,
                                  position.y - offset,
                                  position.x + offset / 5.0,
                                  position.y + offset,
                                  imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 1.0))

    def mouse_move(self, position):
        self.intersected_primitive = None
        self.intersected_point = position

        for index, primitive in enumerate(reversed(self.primitives)):
            if self.intersected_point in primitive.bounds() * self.scale:
                self.intersected_primitive = len(self.primitives) - index - 1
                break

    def mouse_drag(self, position):
        if self.selected_primitive is not None:
            primitive = self[self.selected_primitive]

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


    def mouse_release(self, position):
        self.selected_handle = None

    def reset_selection(self):
        self.selected_primitive = None
        self.intersected_primitive = None
        self.selected_handle = None