from src.controller import Controller
from src.fuzzy_ui import FuzzyUI
from src.data_model import DataModel
from src.file_manager import FileManager


def main():
    file_manager = FileManager()
    data_model = DataModel(file_manager)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()


if __name__ == "__main__":
    main()
