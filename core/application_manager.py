from core.application import Application
from core.workspace import Workspace


class ApplicationManager:
    def __init__(self, workspace: Workspace):
        self.applications: list[Application] = []
        self.workspace = workspace

    def add_application(self, application: Application):
        self.applications.append(application)
        self.workspace.add_window(application)
