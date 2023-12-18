from Controller import Controller
from FuzzyUI import FuzzyUI
from DataModel import DataModel
from FileManager import FileManager


def main():
    data_model = DataModel()
    file_manager = FileManager()
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model, file_manager)
    controller.run()


if __name__ == "__main__":
    main()
