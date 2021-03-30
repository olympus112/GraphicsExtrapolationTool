from gui.primitives import *
from parsing.atom_translator import Translator
from gui.graphics import Canvas, BUTTON_LEFT, BUTTON_RIGHT, Point
from imgui.integrations.glfw import GlfwRenderer
from datetime import datetime
from os import listdir
from os.path import isfile, join
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
        self.itext = ""
        self.otext = ""

        self.show_file_loader = False
        self.show_file_saver = False
        self.text_cache = None
        self.filename_cache = ""
        self.default_path = "./res/examples/"

        self.show_ilp = False
        self.knowledge = ""
        self.query = ""
        self.query_results = []

        self.extrapolations = 1
        self.tolerance = 0.1
        self.found_patterns = []
        self.available_patterns = [ConstantPattern, LinearPattern, BFSOperatorPattern, PeriodicPattern, SinusoidalPattern]
        self.selected_patterns = [True for _ in self.available_patterns]
        self.render_order = False

        self.camera_offset = imgui.Vec2(64 * 4.5, 64 * 2.65)
        self.scale_index = 0

        self.reload_icanvas()
        self.consolas = imgui.get_io().fonts.add_font_from_file_ttf("res/consolas.ttf", 20)
        self.impl.refresh_font_texture()
        glfw.maximize_window(self.window)
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
        self.render_file_loader()
        self.render_file_saver()

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
                if imgui.menu_item("Load", "l")[0]:
                    self.show_file_loader = True
                if imgui.menu_item("Save", "s")[0]:
                    self.show_file_saver = True
                if imgui.menu_item("Settings", "i")[0]:
                    self.show_ilp = True
                if imgui.menu_item("Exit", "esc")[0]:
                    glfw.set_window_should_close(self.window, True)
                imgui.end_menu()
            imgui.end_menu_bar()

    def render_file_saver(self):
        if self.show_file_saver:
            _, self.show_file_saver = imgui.begin("File saver", False)

            imgui.text_colored("Files are save in " + self.default_path, 0.5, 0.5, 0.5)
            imgui.separator()
            imgui.text("Filename")
            imgui.push_item_width(-1)
            _, self.filename_cache = imgui.input_text("##Filename_input", self.filename_cache, 100)

            if imgui.button("Save file", -1):
                if len(self.filename_cache) == 0:
                    self.filename_cache = datetime.now().strftime("%m%d%Y_%H%%S")
                path = self.default_path + self.filename_cache
                file = open(path, "w")
                file.write(self.itext)
                self.filename_cache = ""

                self.show_file_saver = False

            imgui.end()

    def render_file_loader(self):
        if self.show_file_loader:
            _, self.show_file_loader = imgui.begin("File loader", False)

            imgui.text_colored("Looking for files in " + self.default_path, 0.5, 0.5, 0.5)
            imgui.separator()
            imgui.text("Examples")
            files = [file for file in listdir(self.default_path) if isfile(join(self.default_path, file))]

            if self.text_cache is None:
                self.text_cache = self.itext

            imgui.push_item_width(-1)
            changed, selected_file_index = imgui.listbox("##Examples", -1, files)
            imgui.pop_item_width()
            imgui.separator()
            if changed:
                file = open(self.default_path + files[selected_file_index])
                text = file.read()
                file.close()

                self.itext = text
                self.reload_icanvas()
                self.update_ocanvas()

            if imgui.button("Choose example", -1):
                self.text_cache = None
                self.show_file_loader = False

            if imgui.button("Cancel", -1):
                self.itext = self.text_cache
                self.reload_icanvas()
                self.update_ocanvas()
                self.show_file_loader = False

            imgui.end()


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
                    knowledge_atoms, knowledge_predicates = Translator.translate(Parser.parse(self.knowledge),
                                                                                 canvas_predicates)
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

        imgui.text("mx: {}, my: {}".format(imgui.get_io().mouse_pos.x, imgui.get_io().mouse_pos.y))
        imgui.text("offset x: {}, offset y: {}".format(self.camera_offset.x, self.camera_offset.y))
        imgui.text("scale: {}".format(self.icanvas.scale))

        _, self.extrapolations = imgui.drag_int("Extrapolations", self.extrapolations)
        _, self.tolerance = imgui.drag_float("Tolerance", self.tolerance)

        patterns = [str(pattern) for pattern in self.found_patterns]
        imgui.listbox("Patterns", 0, patterns)
        any_changed = False
        for index, pattern in enumerate(self.available_patterns):
            changed, self.selected_patterns[index] = imgui.checkbox(str(pattern), self.selected_patterns[index])
            any_changed |= changed

        if any_changed:
            self.update_ocanvas()

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

        self.ocanvas.render_canvas(draw_list, position_min, position_max)
        self.ocanvas.render_grid(draw_list, self.camera_offset, position_min, position_max)

        origin = imgui.Vec2(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        mouse_position_in_canvas = imgui.Vec2(io.mouse_pos.x - origin.x, io.mouse_pos.y - origin.y)
        self.ocanvas.render(draw_list, origin, render_order=self.render_order)

    def render_icanvas(self):
        io = imgui.get_io()
        draw_list = imgui.get_window_draw_list()

        position_min = imgui.get_cursor_screen_pos()
        size = imgui.get_content_region_available()
        position_max = imgui.Vec2(position_min.x + size.x, position_min.y + size.y)

        # Render canvas
        self.icanvas.render_canvas(draw_list, position_min, position_max)

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
            self.camera_offset = imgui.Vec2(self.camera_offset.x + io.mouse_delta.x,
                                            self.camera_offset.y + io.mouse_delta.y)

        # Update origin
        origin = imgui.Vec2(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        mouse_position_in_canvas = Point(io.mouse_pos.x - origin.x, origin.y - io.mouse_pos.y)
        mouse_position_in_canvas = mouse_position_in_canvas / self.icanvas.scale

        # Update intersected
        if hovered:
            self.icanvas.mouse_move(mouse_position_in_canvas)

        # Mouse press event
        if left_pressed and hovered:
            self.icanvas.mouse_press(mouse_position_in_canvas)
        if left_dragging and hovered:
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
            if imgui.menu_item("Add rectangle")[0]:
                self.icanvas.primitives.append(Rect(
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    50,
                    50))
                self.reload_itext()
            if imgui.menu_item("Add line")[0]:
                self.icanvas.primitives.append(Line(
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    int(mouse_position_in_canvas.x + 25),
                    int(mouse_position_in_canvas.y + 25)))
                self.reload_itext()
            if imgui.menu_item("Add vector")[0]:
                self.icanvas.primitives.append(Vector(
                    4,
                    int(mouse_position_in_canvas.x),
                    int(mouse_position_in_canvas.y),
                    45,
                    100))
                self.reload_itext()
            if imgui.menu_item("Add circle")[0]:
                self.icanvas.primitives.append(Circle(
                    3,
                    int(mouse_position_in_canvas.x),
                    int(mouse_position_in_canvas.y),
                    25))
                self.reload_itext()
            if imgui.menu_item("Load file")[0]:
                self.show_file_loader = True
            imgui.end_popup()

        imgui.push_clip_rect(position_min.x, position_min.y, position_max.x, position_max.y, True)

        # Render the grid and primitives
        self.icanvas.render_grid(draw_list, self.camera_offset, position_min, position_max)

        # Render atoms
        self.icanvas.render(draw_list, origin, render_order=self.render_order)

        # Render cursor
        if hovered:
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)
            self.icanvas.render_cursor(draw_list, io.mouse_pos)
        else:
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)

        imgui.pop_clip_rect()

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

        if not imgui.get_io().want_capture_keyboard:
            if imgui.is_key_pressed(glfw.KEY_I):
                self.show_ilp = not self.show_ilp
            if imgui.is_key_pressed(glfw.KEY_O):
                self.render_order = not self.render_order
            if imgui.is_key_pressed(glfw.KEY_L):
                self.show_file_loader = not self.show_file_loader
            if imgui.is_key_pressed(glfw.KEY_S):
                self.show_file_saver = not self.show_file_saver

        # if not imgui.get_io().want_capture_mouse:
        if imgui.get_io().mouse_wheel != 0:
            if imgui.get_io().key_shift:
                self.tolerance = util.clamp(self.tolerance + 0.1 * imgui.get_io().mouse_wheel, 0.0, 5.0)
            elif imgui.get_io().key_ctrl:
                self.scale_index += 0.1 * imgui.get_io().mouse_wheel
                new_scale = self.scale_index + 1 if self.scale_index > 0 else math.exp(self.scale_index)
                self.icanvas.scale = new_scale
                self.ocanvas.scale = new_scale
            else:
                self.extrapolations = int(max(0, self.extrapolations + imgui.get_io().mouse_wheel))
            self.update_ocanvas()

    def close(self):
        self.impl.shutdown()
        glfw.terminate()

    def reload_icanvas(self):
        self.icanvas.reset_selection()
        self.icanvas.primitives = Parser.parse(self.itext)

    def reload_ocanvas(self):
        self.ocanvas.reset_selection()
        self.ocanvas.primitives = Parser.parse(self.otext)

    def reload_itext(self):
        self.itext = str(self.icanvas)

    def reload_otext(self):
        self.otext = str(self.ocanvas)

    def update_ocanvas(self):
        self.ocanvas.primitives = self.icanvas.primitives.copy()

        if len(self.icanvas.primitives) > 1:
            output_parameters, self.found_patterns = Pattern.search(self.icanvas.primitives, np.array(self.available_patterns)[self.selected_patterns], self.extrapolations, self.tolerance)

            if output_parameters is not None:
                for parameters in output_parameters:
                    self.ocanvas.primitives.append(Parser.create_primitive(parameters[0], len(parameters) - 1, parameters[1:]))

            self.reload_otext()
