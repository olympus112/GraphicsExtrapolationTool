from __future__ import annotations
from typing import *
import math

import imgui

from gui.graphics import Bounds, Point
from gui.primitives import PrimitiveGroup, Renderable
from misc import util
from misc.util import ReferenceFactory


class Selection:

    def __init__(self):
        self.renderables: Set[int] = set()

    def __str__(self) -> str:
        return str(self.renderables)

    def __repr__(self) -> str:
        return repr(self.renderables)

    def __contains__(self, item: int) -> bool:
        return item in self.renderables

    def __iter__(self):
        return self.renderables.__iter__()

    def __len__(self) -> int:
        return len(self.renderables)

    def select(self, renderable: int):
        self.renderables.clear()
        if renderable is not None:
            self.renderables.add(renderable)

    def toggle(self, renderable: int):
        if renderable is None:
            return
        if renderable in self.renderables:
            self.renderables.remove(renderable)
        else:
            self.renderables.add(renderable)

    def empty(self) -> bool:
        return len(self.renderables) == 0

    def is_single_selection(self) -> bool:
        return len(self.renderables) == 1

    def first(self):
        result, = self.renderables
        return result

    def reset(self):
        self.renderables.clear()


class Canvas:

    reference_factory: ReferenceFactory = ReferenceFactory()
    handle_size = 5

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)

        self.primitives: PrimitiveGroup = PrimitiveGroup(0)

        self.intersected_renderable: Optional[int] = None
        self.intersected_point: Optional[Point] = None

        self.selected_group: ReferenceFactory.Reference = self.primitives.identifier
        self.selected_renderables: Selection = Selection()
        self.selected_point: Optional[Point] = None
        self.selected_handle: Optional[int] = None

        self.scale: float = 1.0

    def __getitem__(self, item: int) -> PrimitiveGroup.Parameter:
        return self.primitives[item]

    def __str__(self) -> str:
        return "\n".join(map(str, self.primitives))

    def __repr__(self) -> str:
        return "Canvas:\nintersect=({}, {})\nselect=({}, {})\nhandle={}\nprimitives={}".format(
            self.intersected_renderable,
            self.intersected_point,
            self.selected_renderables,
            self.selected_point,
            self.selected_handle,
            self.primitives)

    def render(self, draw_list: Any, offset: Point, **kwargs):
        def render_renderable(
                renderable: Renderable,
                draw_list: Any,
                offset: Point,
                _child_of_selected_group: bool = False,
                _root: bool = False,
                _selected: bool = False,
                _intersected: bool = False,
                _render_identifiers: bool = False,
                _render_order: bool = False):

            if isinstance(renderable, PrimitiveGroup):
                if renderable.identifier == self.selected_group:
                    _child_of_selected_group = True
                    is_in_selected_group = True
                else:
                    is_in_selected_group = False

                for index, child in enumerate(renderable):
                    is_selected = is_in_selected_group and index in self.selected_renderables
                    is_intersected = is_in_selected_group and index == self.intersected_renderable
                    render_renderable(child, draw_list, offset, _child_of_selected_group=_child_of_selected_group, _selected=is_selected, _intersected=is_intersected, _render_order=_render_order, _render_identifiers=_render_identifiers)

                if is_in_selected_group:
                    if _render_order:
                        self.render_order(renderable, draw_list, offset)

            if not _root:
                factor = 1.0 if _child_of_selected_group else 0.5
                renderable.render(draw_list, offset, self.scale, factor)

                if _render_identifiers:
                    self.render_identifier(renderable, draw_list, offset, factor)

            if _intersected:
                renderable.bounds().render(draw_list, offset, self.scale, Canvas.handle_size)

            if _selected:
                renderable.bounds().render(draw_list, offset, self.scale)
                if self.selected_renderables.is_single_selection():
                    for handle in renderable.handles():
                        handle.render(draw_list, offset, self.scale)


        _render_order = kwargs['render_order'] if 'render_order' in kwargs else False
        _render_identifiers = kwargs['render_identifiers'] if 'render_identifiers' in kwargs else False
        render_renderable(self.primitives, draw_list, offset, _root=True, _render_order=_render_order, _render_identifiers=_render_identifiers)

    def render_identifier(self, renderable: Renderable, draw_list: Any, offset: Point, factor: float = 1.0):
        position = renderable.position()
        draw_list.add_text(
            position.x * self.scale + offset.x,
            position.y * -self.scale + offset.y,
            imgui.get_color_u32_rgba(factor, factor, factor, 1.0),
            str(renderable.identifier))

    def render_order(self, group: PrimitiveGroup, draw_list: Any, offset: Point):
        for index in range(len(group) - 1):
            p0 = group[index].position()
            p1 = group[index + 1].position()
            draw_list.add_line(
                p0.x * self.scale + offset.x,
                p0.y * -self.scale + offset.y,
                p1.x * self.scale + offset.x,
                p1.y * -self.scale + offset.y,
                imgui.get_color_u32_rgba(0.9, 0.9, 0.9, 1.0))
            draw_list.add_circle_filled(
                p1.x * self.scale + offset.x,
                p1.y * -self.scale + offset.y,
                4 * self.scale,
                imgui.get_color_u32_rgba(0.9, 0.9, 0.9, 1.0))

    def render_grid(self, draw_list, offset: Point, position_min: Point, position_max: Point, grid_step=64):
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

    def render_canvas(self, draw_list: Any, position_min: Point, position_max: Point):
        draw_list.add_rect_filled(position_min.x, position_min.y, position_max.x, position_max.y,
                                  imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 1.0))
        draw_list.add_rect(position_min.x, position_min.y, position_max.x, position_max.y,
                           imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0))

    def render_cursor(self, draw_list: Any, position: Point):
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

    def mouse_move(self, position: Point):
        self.intersected_renderable = None
        self.intersected_point = position

        group = self.primitives.find(self.selected_group)
        if group is None:
            print("Selected group not found {} {}", self.selected_group, self.primitives.identifier)
            return

        for index, primitive in enumerate(reversed(group)):
            if self.intersected_point in primitive.bounds() * self.scale:
                self.intersected_renderable = len(group) - index - 1
                break

    def mouse_drag(self, position: Point):
        if self.selected_renderables.empty():
            return

        group = self.primitives.find(self.selected_group)

        for selected_renderable in self.selected_renderables:
            primitive = group[selected_renderable]

            if self.selected_renderables.is_single_selection() and self.selected_handle is not None:
                primitive.handle(self.selected_handle, self.intersected_point)
            else:
                delta = position - self.selected_point

                primitive.move(delta)

        self.selected_point = self.intersected_point

    def mouse_press(self, position: Point, _control: bool = False):
        self.selected_point = self.intersected_point

        if self.selected_renderables.is_single_selection():
            # Check first if a handle is selected
            group = self.primitives.find(self.selected_group)

            primitive = group[self.selected_renderables.first()]
            for index, handle in enumerate(primitive.handles()):
                if position in Bounds.centered(handle, Canvas.handle_size):
                    self.selected_handle = index
                    break
            else:
                if _control:
                    self.selected_renderables.toggle(self.intersected_renderable)
                else:
                    self.selected_renderables.select(self.intersected_renderable)
        else:
            # Update selected primitive
            if _control:
                self.selected_renderables.toggle(self.intersected_renderable)
            else:
                self.selected_renderables.select(self.intersected_renderable)

    def mouse_double(self):
        if self.selected_renderables.is_single_selection():
            group = self.primitives.find(self.selected_group)
            primitive = group[self.selected_renderables.first()]
            if isinstance(primitive, PrimitiveGroup):
                self.selected_group = primitive.identifier
                self.reset_selection()
        else:
            self.selected_group = self.primitives.identifier

    def mouse_release(self, _position: Point):
        self.selected_handle = None

    def reset_selection(self):
        self.selected_renderables.reset()
        self.intersected_renderable = None
        self.selected_handle = None

    def reset(self):
        self.reference_factory.reset()
        self.primitives = PrimitiveGroup(-1)
        self.selected_group = -1
        self.reset_selection()

    def group_selection(self):
        current_group = self.primitives.find(self.selected_group)
        old_group_primitives = [primitive for primitive in current_group]
        new_group_primitives = [current_group[renderable] for renderable in self.selected_renderables]

        current_group.reset()
        for primitive in old_group_primitives:
            if primitive not in new_group_primitives:
                current_group.append(primitive)

        new_group = PrimitiveGroup(self.reference_factory.new(), *new_group_primitives)
        current_group.append(new_group)

        self.reset_selection()