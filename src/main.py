"""
This is the main entry point of the FuzzyMatcher application.

The script sets up logging, initializes the file handler, data model, user interface,
and controller, and starts the application loop.

Main dependencies:
    - `data_model`: Handles data manipulation and business logic for fuzzy matching and categorization.
    - `fuzzy_ui`: Manages the user interface and user interactions.
    - `controller`: Coordinates between the data model and the user interface, handling the application's workflow.
    - `file_handler`: Manages file operations like reading, saving, and exporting data.
    - `logging_utils`: Initializes logging and provides log formatting functionality. 

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
from controller import Controller
from fuzzy_ui import FuzzyUI
from data_model import DataModel
from file_handler import FileHandler
from logging_utils import setup_logging


def main():
    logger = logging.getLogger(__name__)
    logger.info("Application starting")
    file_handler = FileHandler()
    data_model = DataModel(file_handler)
    user_interface = FuzzyUI()
    controller = Controller(user_interface, data_model)
    controller.run()
    logger.info("Application terminated")


if __name__ == "__main__":
    setup_logging()
    main()
