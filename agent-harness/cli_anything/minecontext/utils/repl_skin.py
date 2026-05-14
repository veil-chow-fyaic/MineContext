class ReplSkin:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    def print_banner(self) -> None:
        print(f"{self.name} CLI-Anything harness v{self.version}")
        print("Type 'help' for commands, 'quit' to exit.")

    def prompt(self) -> str:
        return input(f"{self.name}> ")

    def info(self, message: str) -> None:
        print(message)
