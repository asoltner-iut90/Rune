from core.window import Window
from core.workspace import Workspace


class ApplicationManager:
    def __init__(self, workspace: Workspace):
        self.applications: list[Window] = []
        self.workspace = workspace

    def add_application(self, application: Window):
        self.applications.append(application)
        self.workspace.add_window(application)
