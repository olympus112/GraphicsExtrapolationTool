from gui.primitives import *
from gui.graphics import BUTTON_LEFT, BUTTON_RIGHT, Point
from gui.canvas import Canvas
from imgui.integrations.glfw import GlfwRenderer
from datetime import datetime
from os import listdir
from os.path import isfile, join
import OpenGL.GL as gl
import imgui
import glfw

from parsing.lexer import Lexer
from parsing.pattern_parser import PatternParser
from parsing.primitive_parser import PrimitiveParser
from pattern.pattern import *


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
        self.opatterns = ""
        self.console = []

        self.show_file_loader = False
        self.show_file_saver = False
        self.text_cache = None
        self.filename_cache = ""
        self.default_path = "./res/examples/"

        self.show_ilp = False
        self.knowledge = ""
        self.query = ""
        self.query_results = []

        self.extrapolations = 2
        self.tolerance = 0.1
        self.found_patterns: Optional[InstancePattern] = None
        self.available_patterns = [ConstantPattern, LinearPattern, BFSOperatorPattern, PeriodicPattern, SinusoidalPattern]
        self.selected_patterns = [True for _ in self.available_patterns]
        self.render_order = False
        self.render_identifiers = False

        self.camera_offset = Point(64 * 4.5, 64 * 2.65)
        self.scale_index = 0

        self.itext_to_icanvas()
        self.consolas = imgui.get_io().fonts.add_font_from_file_ttf("res/consolas.ttf", 28)
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
                self.itext_to_all()

            if imgui.button("Choose example", -1):
                self.text_cache = None
                self.show_file_loader = False

            if imgui.button("Cancel", -1):
                self.itext = self.text_cache
                self.itext_to_all()
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
                # search = Search()
                # if len(self.knowledge) > 0:
                #     canvas_atoms, canvas_predicates = Translator.translate(self.icanvas.primitives)
                #     knowledge_atoms, knowledge_predicates = Translator.translate(PrimitiveParser.parse(self.knowledge),
                #                                                                  canvas_predicates)
                #     query_atoms, query_predicates = Translator.translate(PrimitiveParser.parse(self.query), knowledge_predicates)
                #     if knowledge_atoms is not None and query_atoms is not None:
                #         search.assertz(canvas_atoms)
                #         search.assertz(knowledge_atoms)
                #         self.query_results = search.query(query_atoms[0])
                pass

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

        any_changed = False
        for index, pattern in enumerate(self.available_patterns):
            changed, self.selected_patterns[index] = imgui.checkbox(str(pattern), self.selected_patterns[index])
            any_changed |= changed

        if len(self.opatterns) == 0 or len(self.otext) == 0:
            savings = "/"
        else:
            savings = round((1.0 - float(len(self.opatterns)) / float(len(self.otext))) * 100.0, 2)
        imgui.text("Space saving: {}%".format(savings))

        if any_changed:
            self.icanvas_to_all()

        if imgui.button("Extract constants", -1):
            if len(self.opatterns) != 0:
                constants, counter = Lexer.extract_constants(self.opatterns)
                self.opatterns = self.replace_constants(self.opatterns, constants, counter)
                self.opatterns_to_all()

        for entry in self.console:
            imgui.text_colored('{} (x{})'.format(entry[0], entry[1]), *entry[2])

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

        imgui.begin("Patterns##Output")
        self.render_opatterns()
        imgui.end()

    def render_itext(self):
        imgui.push_font(self.consolas)
        changed, value = imgui.input_text_multiline("##itext", self.itext, len(self.itext) + 1000, -1, -1)
        if changed:
            self.itext = value
            self.itext_to_all()
        imgui.pop_font()

    def render_otext(self):
        imgui.push_font(self.consolas)
        changed, value = imgui.input_text_multiline("##otext", self.otext, len(self.otext) + 1000, -1, -1)
        if changed:
            self.otext = value
            self.otext_to_ocanvas()
        imgui.pop_font()

    def render_opatterns(self):
        imgui.push_font(self.consolas)
        changed, value = imgui.input_text_multiline("##opatterns", self.opatterns, len(self.opatterns) + 1000, -1, -1)
        if changed:
            self.opatterns = value
            self.opatterns_to_all()
        imgui.pop_font()

    def render_ocanvas(self):
        io = imgui.get_io()
        draw_list = imgui.get_window_draw_list()

        position_min = Point(*imgui.get_cursor_screen_pos())
        size = imgui.get_content_region_available()
        position_max = Point(position_min.x + size.x, position_min.y + size.y)

        self.ocanvas.render_canvas(draw_list, position_min, position_max)
        self.ocanvas.render_grid(draw_list, self.camera_offset, position_min, position_max)

        origin = Point(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        _mouse_position_in_canvas = Point(io.mouse_pos.x - origin.x, io.mouse_pos.y - origin.y)

        try:
            self.ocanvas.render(draw_list, origin, render_order=self.render_order)
        except Exception as error:
            self.handle_error(error)

    def render_icanvas(self):
        io = imgui.get_io()
        draw_list = imgui.get_window_draw_list()

        position_min = imgui.get_cursor_screen_pos()
        size = imgui.get_content_region_available()
        position_max = Point(position_min.x + size.x, position_min.y + size.y)

        # Render canvas
        self.icanvas.render_canvas(draw_list, position_min, position_max)

        # Poll events
        imgui.invisible_button("##icanvas_button", size.x, size.y)
        left_double_clicked = imgui.is_mouse_double_clicked(BUTTON_LEFT)
        left_pressed = imgui.is_item_clicked(BUTTON_LEFT)
        left_released = imgui.is_mouse_released(BUTTON_LEFT)
        right_released = imgui.is_mouse_released(BUTTON_RIGHT)
        left_dragging = imgui.is_mouse_dragging(BUTTON_LEFT)
        right_dragging = imgui.is_mouse_dragging(BUTTON_RIGHT)
        hovered = imgui.is_item_hovered()
        active = hovered and (imgui.is_mouse_down(BUTTON_LEFT) or imgui.is_mouse_down(BUTTON_RIGHT))

        # Double click
        if left_double_clicked:
            self.icanvas.mouse_double()

        # Update scroll
        if active and right_dragging:
            self.camera_offset = Point(self.camera_offset.x + io.mouse_delta.x, self.camera_offset.y + io.mouse_delta.y)

        # Update origin
        origin = Point(position_min.x + self.camera_offset.x, position_min.y + self.camera_offset.y)
        mouse_position_in_canvas = Point(io.mouse_pos.x - origin.x, origin.y - io.mouse_pos.y)
        mouse_position_in_canvas = mouse_position_in_canvas / self.icanvas.scale

        # Update intersected
        if hovered:
            self.icanvas.mouse_move(mouse_position_in_canvas)

        # Mouse press event
        if left_pressed and hovered:
            self.icanvas.mouse_press(mouse_position_in_canvas, _control=imgui.get_io().key_ctrl)
        if left_dragging and hovered:
            self.icanvas.mouse_drag(mouse_position_in_canvas)
            self.icanvas_to_all()
        if left_released:
            self.icanvas.mouse_release(mouse_position_in_canvas)

        # Context menu
        right_drag_delta = imgui.get_mouse_drag_delta(BUTTON_RIGHT)
        if right_released and right_drag_delta.x == 0 and right_drag_delta.y == 0:
            imgui.open_popup("context")
        if imgui.begin_popup("context"):
            if imgui.menu_item("Add rectangle")[0]:
                self.icanvas.primitives.append(Rect(
                    self.icanvas.reference_factory.new(),
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    50,
                    50))
                self.icanvas_to_all()
            if imgui.menu_item("Add line")[0]:
                self.icanvas.primitives.append(Line(
                    self.icanvas.reference_factory.new(),
                    4,
                    int(mouse_position_in_canvas.x - 25),
                    int(mouse_position_in_canvas.y - 25),
                    int(mouse_position_in_canvas.x + 25),
                    int(mouse_position_in_canvas.y + 25)))
                self.icanvas_to_all()
            if imgui.menu_item("Add vector")[0]:
                self.icanvas.primitives.append(Vector(
                    self.icanvas.reference_factory.new(),
                    4,
                    int(mouse_position_in_canvas.x),
                    int(mouse_position_in_canvas.y),
                    45,
                    100))
                self.icanvas_to_all()
            if imgui.menu_item("Add circle")[0]:
                self.icanvas.primitives.append(Circle(
                    self.icanvas.reference_factory.new(),
                    3,
                    int(mouse_position_in_canvas.x),
                    int(mouse_position_in_canvas.y),
                    25))
                self.icanvas_to_all()
            if imgui.menu_item("Load file")[0]:
                self.show_file_loader = True
            imgui.end_popup()

        imgui.push_clip_rect(position_min.x, position_min.y, position_max.x, position_max.y, True)

        # Render the grid and primitives
        self.icanvas.render_grid(draw_list, self.camera_offset, position_min, position_max)

        # Render atoms
        self.icanvas.render(draw_list, origin, render_order=self.render_order, render_identifiers=self.render_identifiers)

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
            if imgui.is_key_pressed(glfw.KEY_P):
                self.show_ilp = not self.show_ilp
            if imgui.is_key_pressed(glfw.KEY_O):
                self.render_order = not self.render_order
            if imgui.is_key_pressed(glfw.KEY_I):
                self.render_identifiers = not self.render_identifiers
            if imgui.is_key_pressed(glfw.KEY_L):
                self.show_file_loader = not self.show_file_loader
            if imgui.is_key_pressed(glfw.KEY_S):
                self.show_file_saver = not self.show_file_saver
            if imgui.is_key_pressed(glfw.KEY_G):
                self.icanvas.group_selection()

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

            self.found_patterns_to_ocanvas()

    def close(self):
        self.impl.shutdown()
        glfw.terminate()

    def itext_to_icanvas(self):
        self.icanvas.reset()
        self.icanvas.primitives = PrimitiveParser.parse(self.itext, reference_factory=self.icanvas.reference_factory)
        self.icanvas.selected_group = self.icanvas.primitives.identifier

    def otext_to_ocanvas(self):
        self.ocanvas.reset()
        self.ocanvas.primitives = PrimitiveParser.parse(self.otext, reference_factory=self.ocanvas.reference_factory)
        self.ocanvas.selected_group = self.ocanvas.primitives.identifier

    def icanvas_to_itext(self):
        self.itext = str(self.icanvas)

    def ocanvas_to_otext(self):
        self.otext = str(self.ocanvas)

    def icanvas_to_found_patterns(self):
        self.found_patterns = Pattern.search_group_recursive(self.icanvas.primitives, self.available_patterns, self.tolerance)

    def found_patterns_to_opatterns(self):
        if self.found_patterns is not None:
            self.opatterns = str(self.found_patterns)
        else:
            self.opatterns = ""

    def opatterns_to_found_patterns(self):
        parser = PatternParser(self.opatterns)
        try:
            self.found_patterns = parser.parse()
        except Exception as error:
            self.found_patterns = None
            self.handle_error(error)

    def found_patterns_to_ocanvas(self):
        self.ocanvas.reset()

        if self.found_patterns is None:
            return

        master = self.icanvas.primitives.master
        if master is None:
            return

        primitives = Pattern.next([master], self.found_patterns, [self.extrapolations] * self.found_patterns.level, self.ocanvas.reference_factory)
        for primitive in primitives:
            if primitive is not None:
                self.ocanvas.primitives.append(primitive)

        self.ocanvas_to_otext()

    def icanvas_to_all(self):
        self.icanvas_to_itext()
        self.icanvas_to_found_patterns()
        self.found_patterns_to_opatterns()
        self.found_patterns_to_ocanvas()

    def itext_to_all(self):
        self.itext_to_icanvas()
        self.icanvas_to_found_patterns()
        self.found_patterns_to_opatterns()
        self.found_patterns_to_ocanvas()

    def opatterns_to_all(self):
        self.opatterns_to_found_patterns()
        self.found_patterns_to_ocanvas()

    def handle_error(self, error):
        error_str = str(error)
        if len(self.console) == 0 or self.console[-1][0] != error_str:
            self.console.append([error_str, 1, (1.0, 0.0, 0.0, 1.0)])
        else:
            self.console[-1][1] += 1

    def replace_constants(self, string: str, constants: List[Lexer.Token], counter: Dict[str, int]) -> str:
        new_vars: Dict[str, str] = dict()

        for token in reversed(constants):
            value = string[token.start : token.start + token.length]
            if counter[value] < 2:
                continue

            if value not in new_vars.keys():
                new_vars[value] = "var{}".format(len(new_vars))

            string = string[:token.start] + new_vars[value] + string[token.start + token.length:]

        new_var_code = ""
        for value, variable in new_vars.items():
            new_var_code += "${} = {}\n".format(variable, value)

        return new_var_code + string