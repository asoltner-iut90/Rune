class Application:
    def __init__(self, icon:str, name:str, command:list[str]):
        assert len(icon) == 1 , "Icon must be a single character"
        self.icon = icon
        self.name = name
        self.command = command