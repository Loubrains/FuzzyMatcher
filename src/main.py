import logging
from controller import Controller
from fuzzy_ui import FuzzyUI
from data_model import DataModel
from file_handler import FileHandler
from logging_utils import setup_logging


# def setup_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
#         filename="app.log",
#         filemode="w",
#     )
#     logging.getLogger("chardet").setLevel(logging.WARNING)

#     logging.info("Logging initialized")


def main():
    logging.info("Application starting")
    file_handler = FileHandler()
    data_model = DataModel(file_handler)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()
    logging.info("Application terminated")


if __name__ == "__main__":
    setup_logging()
    main()
