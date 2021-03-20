import math

from gui.primitives import Rect, Line, Circle
from parsing.atom_translator import Translator
from parsing.primitive_parser import Parser
from gui import util
from gui.graphics import Canvas, BUTTON_LEFT, BUTTON_RIGHT, Point
from imgui.integrations.glfw import GlfwRenderer
import OpenGL.GL as gl
import imgui
import glfw

from pattern.pattern import *
from pattern.search import Search

class Screen:
    def __init__(self, title, width, height):
        super(Screen, self).__init__()

        imgui.create_context()

        self.width = width
        self.height = height
        self.window = self.glfw_init(title, self.width, self.height)
        self.impl = GlfwRenderer(self.window)
        self.icanvas = Canvas()
        self.ocanvas = Canvas()

        self.show_ilp = False
        self.knowledge = ""
        self.query = ""
        self.query_results = []
        self.extrapolations = 1
        self.tolerance = 0.1

        self.camera_offset = imgui.Vec2(64 * 4.5, 64 * 2.65)
        self.itext = "rect(0, 0, 100, 100, 0).\nrect(100, 100, 100, 100, 0)."
        #self.itext = "rect(0, 0, 50, 50, 0).\nrect(50, 50, 100, 100, 0).\nrect(150, 150, 150, 150, 0).\nrect(300, 300, 200, 200, 0)."
        self.otext = ""

        self.reload_icanvas()

        self.consolas = imgui.get_io().fonts.add_font_from_file_ttf("res/Consolas.ttf", 20)
        self.impl.refresh_font_texture()
        imgui.get_io().config_flags |= imgui.CONFIG_DOCKING_ENABLE

    def glfw_init(self, title, width, height):
        if not glfw.init():
            print("Could not initialize GLFW")
            exit(1)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)

        window = glfw.create_window(width, height, title, None, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            print("Could not initialize GLFW window")
            exit(1)

        return window

    def should_close(self) -> bool:
        return glfw.window_should_close(self.window)

    def render(self):
        self.render_prepare()

        self.render_input()
        self.render_output()
        self.render_ilp()
        self.render_settings()

        self.render_end()

    def render_prepare(self):
        imgui.new_frame()

        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.set_next_window_position(0, 0)
        window_size = imgui.get_io().display_size
        imgui.set_next_window_size(window_size.x, window_size.y)

        window_flags = imgui.WINDOW_MENU_BAR | \
                       imgui.WINDOW_NO_DOCKING | \
                       imgui.WINDOW_NO_TITLE_BAR | \
                       imgui.WINDOW_NO_COLLAPSE | \
                       imgui.WINDOW_NO_RESIZE | \
                       imgui.WINDOW_NO_MOVE | \
                       imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS | \
                       imgui.WINDOW_NO_NAV_FOCUS

        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)
        imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(0, 0))
        imgui.begin("Editor", False, window_flags)
        imgui.pop_style_var(3)

        dockspace_id = imgui.get_id("DockSpace")
        imgui.dock_space(dockspace_id, 0, 0, 1 << 6)

        if imgui.begin_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.menu_item("Settings", "s")[0]:
                    self.show_ilp = True
                if imgui.menu_item("Exit", "esc")[0]:
                    glfw.set_window_should_close(self.window, True)
                imgui.end_menu()
            imgui.end_menu_bar()

    def render_ilp(self):
        if self.show_ilp:
            # Settings window
            _, self.show_ilp = imgui.begin("ILP", True)

            # Background knowledge
            imgui.label_text("##knowledge_label", "Background knowledge")
            imgui.push_font(self.consolas)
            _, self.knowledge = imgui.input_text_multiline("##knowledge_input", self.knowledge, 1000, -1, 0)
            imgui.pop_font()

            # Query
            imgui.label_text("##query_label", "Query")
            imgui.push_item_width(-1)
            imgui.push_font(self.consolas)
            _, self.query = imgui.input_text("##query_input", self.query, 100)
            imgui.pop_font()

            # Search button
            if imgui.button("Search", -1, 0):
                search = Search()
                if len(self.knowledge) > 0:
                    canvas_atoms, canvas_predicates = Translator.translate(self.icanvas.primitives)
                    knowledge_atoms, knowledge_predicates = Translator.translate(Parser.parse(self.knowledge), canvas_predicates)
                    query_atoms, query_predicates = Translator.translate(Parser.parse(self.query), knowledge_predicates)
                    if knowledge_atoms is not None and query_atoms is not None:
                        search.assertz(canvas_atoms)
                        search.assertz(knowledge_atoms)
                        self.query_results = search.query(query_atoms[0])

            # Search results
            imgui.label_text("##search_results", "Results")
            # for result in self.query_results:
            #     imgui.columns(2, "query_results_columns")
            #     imgui.separator()
            #     for key, value in result:
            #         imgui.text(key)
            #         imgui.next_column()
            #         imgui.text(value)
            #         imgui.next_column()
            #     imgui.columns(1)
            #     imgui.separator()
            imgui.push_font(self.consolas)
            imgui.text(str(self.query_results))
            imgui.pop_font()

            imgui.end()

    def render_settings(self):
        imgui.begin("Settings")
        _, self.extrapolations = imgui.drag_int("Extrapolations", self.extrapolations)
        _, self.tolerance = imgui.drag_float("Tolerance", self.tolerance)
        imgui.end()

    def render_input(self):
        imgui.begin("Input")
        imgui.dock_space("Input##Dockspace", 0, 0, 0)
        imgui.end()

        imgui.begin("Canvas##Input")
        self.render_icanvas()
        imgui.end()

        imgui.begin("Code##Input")
        self.render_itext()
        imgui.end()

    def render_output(self):
        imgui.begin("Output")
        imgui.dock_space("Output##Dockspace", 0, 0, 0)
        imgui.end()

        imgui.begin("Canvas##Output")
        self.render_ocanvas()
        imgui.end()

        imgui.begin("Code##Output")
        self.render_otext()
        imgui.end()

    def render_itext(self):
        imgui.push_font(self.consolas)
        changed, value = imgui.input_text_multiline("##itext", self.itext, len(self.itext) + 1000, -1, -1)
        if changed:
            self.itext = value
            self.reload_icanvas()
        imgui.pop_font()

    def render_otext(self):
        imgui.push_font(self.consolas)
        changed, value = imgui.input_text_multiline("##otext", self.otext, len(self.otext) + 1000, -1, -1)
        if changed:
            self.otext = value
            self.reload_ocanvas()
        imgui.pop_font()

    def render_ocanvas(self):
        io = imgui.get_io()
        draw_list = imgui.get_window_draw_list()

        position_min = imgui.get_cursor_screen_pos()
        size = imgui.get_content_region_available()
        position_max = imgui.Vec2(position_min.x + size.x, position_min.y + size.y)

        self.render_canvas(draw_list, position_min, position_max)
        self.render_grid(draw_list, position_min, position_max)

        origin = imgui.Vec2(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        mouse_position_in_canvas = imgui.Vec2(io.mouse_pos.x - origin.x, io.mouse_pos.y - origin.y)
        self.ocanvas.render(draw_list, origin)

    def render_icanvas(self):
        io = imgui.get_io()
        draw_list = imgui.get_window_draw_list()

        position_min = imgui.get_cursor_screen_pos()
        size = imgui.get_content_region_available()
        position_max = imgui.Vec2(position_min.x + size.x, position_min.y + size.y)

        # Render canvas
        self.render_canvas(draw_list, position_min, position_max)

        # Poll events
        imgui.invisible_button("##icanvas_button", size.x, size.y)
        left_pressed = imgui.is_item_clicked(BUTTON_LEFT)
        right_pressed = imgui.is_item_clicked(BUTTON_RIGHT)
        left_released = imgui.is_mouse_released(BUTTON_LEFT)
        right_released = imgui.is_mouse_released(BUTTON_RIGHT)
        left_dragging = imgui.is_mouse_dragging(BUTTON_LEFT)
        right_dragging = imgui.is_mouse_dragging(BUTTON_RIGHT)
        hovered = imgui.is_item_hovered()
        active = hovered and (imgui.is_mouse_down(BUTTON_LEFT) or imgui.is_mouse_down(BUTTON_RIGHT))

        # Update scroll
        if active and right_dragging:
            self.camera_offset = imgui.Vec2(self.camera_offset.x + io.mouse_delta.x, self.camera_offset.y + io.mouse_delta.y)

        # Update origin
        origin = imgui.Vec2(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        mouse_position_in_canvas = Point(io.mouse_pos.x - origin.x, io.mouse_pos.y - origin.y)

        # Update intersected
        if hovered:
            self.icanvas.mouse_move(mouse_position_in_canvas)

        # Mouse press event
        if left_pressed:
            self.icanvas.mouse_press(mouse_position_in_canvas)
        if left_dragging:
            self.icanvas.mouse_drag(mouse_position_in_canvas)
            self.reload_itext()
            self.update_ocanvas()
        if left_released:
            self.icanvas.mouse_release(mouse_position_in_canvas)

        # Context menu
        right_drag_delta = imgui.get_mouse_drag_delta(BUTTON_RIGHT)
        if right_released and right_drag_delta.x == 0 and right_drag_delta.y == 0:
            imgui.open_popup("context")
        if imgui.begin_popup("context"):
            if imgui.menu_item("Add line")[0]:
                self.icanvas.primitives.append(Line(
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    int(mouse_position_in_canvas.x + 25),
                    int(mouse_position_in_canvas.y + 25)))
                self.reload_itext()
            if imgui.menu_item("Add rectangle")[0]:
                self.icanvas.primitives.append(Rect(
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    50,
                    50))
                self.reload_itext()
            if imgui.menu_item("Add circle")[0]:
                self.icanvas.primitives.append(Circle(
                    3,
                    int(mouse_position_in_canvas.x),
                    int(mouse_position_in_canvas.y),
                    25))
                self.reload_itext()
            imgui.end_popup()

        imgui.push_clip_rect(position_min.x, position_min.y, position_max.x, position_max.y, True)

        # Render the grid and primitives
        self.render_grid(draw_list, position_min, position_max)

        # Render atoms
        self.icanvas.render(draw_list, origin)

        # Render cursor
        if hovered:
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)
            self.render_cursor(draw_list, io.mouse_pos)
        else:
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)

        imgui.pop_clip_rect()

    def render_canvas(self, draw_list, position_min, position_max):
        draw_list.add_rect_filled(position_min.x, position_min.y, position_max.x, position_max.y, imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 1.0))
        draw_list.add_rect(position_min.x, position_min.y, position_max.x, position_max.y, imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0))

    def render_cursor(self, draw_list, position):
        offset = 8
        io = imgui.get_io()
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

    def render_grid(self, draw_list, position_min, position_max, grid_step = 64):
        for x in util.frange(math.fmod(self.camera_offset.x, grid_step), position_max.x - position_min.x, grid_step):
            color = imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 0.2)
            if self.camera_offset.x == x:
                color = imgui.get_color_u32_rgba(1, 1, 1, 1)
            draw_list.add_line(position_min.x + x, position_min.y, position_min.x + x, position_max.y, color)
        for y in util.frange(math.fmod(self.camera_offset.y, grid_step), position_max.y - position_min.y, grid_step):
            color = imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 0.2)
            if self.camera_offset.y == y:
                color = imgui.get_color_u32_rgba(1, 1, 1, 1)
            draw_list.add_line(position_min.x, position_min.y + y, position_max.x, position_min.y + y, color)

    def render_end(self):
        imgui.end()

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        glfw.swap_interval(1)
        glfw.swap_buffers(self.window)

    def update(self):
        glfw.poll_events()
        self.impl.process_inputs()

        if imgui.is_key_pressed(glfw.KEY_ESCAPE):
            glfw.set_window_should_close(self.window, True)

        if imgui.is_key_pressed(glfw.KEY_S):
            self.show_ilp = True

        if imgui.get_io().mouse_wheel != 0:
            if imgui.get_io().key_ctrl:
                self.tolerance = util.clamp(self.tolerance + 0.1 * imgui.get_io().mouse_wheel, 0.0, 5.0)
                print("Tolerance: ", self.tolerance)
            else:
                self.extrapolations = util.clamp(int(self.extrapolations + imgui.get_io().mouse_wheel), 0, 20)
                print("Extrapolations: ", self.extrapolations)
            self.update_ocanvas()

    def close(self):
        self.impl.shutdown()
        glfw.terminate()

    def reload_icanvas(self):
        self.icanvas.primitives = Parser.parse(self.itext)

    def reload_ocanvas(self):
        self.ocanvas.primitives = Parser.parse(self.otext)

    def reload_itext(self):
        self.itext = str(self.icanvas)

    def reload_otext(self):
        self.otext = str(self.ocanvas)

    def update_ocanvas(self):
        self.ocanvas.primitives = self.icanvas.primitives.copy()

        if len(self.icanvas.primitives) > 1:
            primitive_name = self.icanvas[0].name
            primitive_arity = self.icanvas[0].arity
            primitives = [primitive for primitive in self.icanvas.primitives if primitive.name == primitive_name and primitive.arity == primitive_arity]

            parameters = [[] for i in range(self.extrapolations)]
            # patterns = [BFSOperatorPattern, LinearPattern]
            patterns = [BFSOperatorPattern, SinusoidalPattern]
            for index in range(primitive_arity):
                for pattern in patterns:
                    result = pattern.apply(primitives, index)
                    if result is not None:
                        for extrapolation in range(self.extrapolations):
                            parameters[extrapolation].append(result.next(primitives, extrapolation + 1))
                        break
                else:
                    self.reload_otext()
                    return

            for parameter in parameters:
                self.ocanvas.primitives.append(Parser.create_primitive(primitive_name, primitive_arity, parameter))

            self.reload_otext()