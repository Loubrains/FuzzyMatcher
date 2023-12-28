import logging
from controller import Controller
from fuzzy_ui import FuzzyUI
from data_model import DataModel
from file_manager import FileManager


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        filename="app.log",
        filemode="w",
    )
    logging.getLogger("chardet").setLevel(logging.INFO)

    logging.info("Logging initialized")


def main():
    logging.info("Application starting")
    file_manager = FileManager()
    data_model = DataModel(file_manager)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()
    logging.info("Application terminated")


if __name__ == "__main__":
    setup_logging()
    main()
