from Controller import Controller
from FuzzyUI import FuzzyUI
from DataModel import DataModel
from FileManager import FileManager


def main():
    file_manager = FileManager()
    data_model = DataModel(file_manager)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()


if __name__ == "__main__":
    main()
