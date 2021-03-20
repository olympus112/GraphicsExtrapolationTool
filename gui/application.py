from gui.screen import Screen


class Application:
    def __init__(self):
        super(Application, self).__init__()
        self.screen = Screen("Editor", 1280, 720)

    def run(self):
        print("Running application")
        print("Started rendering")

        while not self.screen.should_close():
            self.screen.update()
            self.screen.render()

        self.screen.close()

        print("Closed application")

if __name__ == '__main__':
    application = Application()
    application.run()