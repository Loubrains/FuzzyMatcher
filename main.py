from Controller import Controller
from FuzzyUI import FuzzyUI
from DataModel import DataModel
from FileManager import FileManager

if __name__ == "__main__":
    data_model = DataModel()
    file_manager = FileManager()
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model, file_manager)
    user_interface.mainloop()
