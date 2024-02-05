"""
This module provides utility functions for logging and debugging within the application.

Logs are written to 'app.log' file in the project root directory.

Functions:
    - setup_logging: Configures the logging settings for the application.
    - format_and_log_data_for_debug: Formats and logs attributes based on their data types for improved readability in debugging.
    
Main dependencies:
    - pandas: for data manipulation
    - inspect: for formatting log messages

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
from typing import Any
import pandas as pd
import inspect


def setup_logging():
    """
    Initializes logging with a specified format, log level, and output file. Logs are written to 'app.log' file.
    Also supresses noisy libraries.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        filename="app.log",
        filemode="w",
    )

    # Suppressing noisy libraries
    logging.getLogger("chardet").setLevel(logging.WARNING)

    logging.info("Logging initialized")


def format_and_log_data_for_debug(logger: logging.Logger, attributes: dict[str, Any]) -> None:
    """
    Formats various types of class attributes and logs them for debugging purposes.

    Args:
        logger (logging.Logger): The logger instance used to log the messages.
        attributes (dict[str, Any]): A dictionary containing the attribute names and their values from a class instance.

    The method inspects each attribute and decides on a logging format based on its data type:
        - For pandas DataFrames, it logs the head of the DataFrame.
        - For dictionaries:
            - If dictionary where values are types, it show everything.
            - If dictionary where keys have more than 10 values, it show keys and counts of values.
            - For any other dictionary, it just show the first 5 items.
        - For other data types, it logs the value directly.

    Usage:
        Can be used on specific variables, or can be used on all class attributes of a data model, like so:
        `logging_utils.format_and_log_data_for_debug(logger, vars(self))`
    """

    log_messages = ["Class attributes:\n"]
    for name, obj in attributes.items():
        if isinstance(obj, pd.DataFrame):
            # Handling dataframes, show head
            log_message = f"{name} (head):\n{obj.head()}"
        elif isinstance(obj, dict):
            if all(isinstance(v, type) for v in obj.values()):
                # Handling dictionaries of types, show all
                type_dict = dict(obj.items())
                log_message = f"{name} (dictionary of types):\n{type_dict}"
            elif any(len(v) > 10 for v in obj.values() if isinstance(v, (list, set, tuple, dict))):
                # For dictionaries whose keys have many values, show keys and their value counts
                summarized_dict = {
                    k: len(v) if isinstance(v, (list, set, tuple, dict)) else "Non-collection"
                    for k, v in obj.items()
                }
                log_message = f"{name} (some keys have many values, showing keys and counts):\n{summarized_dict}"
            else:
                # For other dictionaries, show the first few items
                limit = 5
                dict_head = dict(list(obj.items())[:limit])
                log_message = f"{name} (first {limit} items):\n{dict_head}"
        else:
            log_message = f"{name}:\n{obj}"

        log_messages.append(inspect.cleandoc(log_message) + "\n")

    logger.debug("\n".join(log_messages))
