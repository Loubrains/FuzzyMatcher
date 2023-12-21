from controller import Controller
from fuzzy_ui import FuzzyUI
from data_model import DataModel
from file_manager import FileManager


def main():
    file_manager = FileManager()
    data_model = DataModel(file_manager)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()


if __name__ == "__main__":
    main()
