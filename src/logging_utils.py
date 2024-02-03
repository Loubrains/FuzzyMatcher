"""
This module provides utility functions for logging and debugging within the application. It includes functionality to set up logging configurations and to format various types of data for clear and concise logging.

Functions:
    setup_logging(): Configures the logging settings for the application. It specifies the log level, format, and output file. Additionally, it sets the log level for certain verbose third-party libraries to avoid cluttering the logs.

    format_and_log_data_for_debug(logger, attributes): Accepts a logger instance and a dictionary of attributes. It formats and logs the attributes based on their data types for improved readability in debugging. The function handles pandas DataFrames, dictionaries with various types of values, and other basic data types, ensuring that the logged information is concise and informative, especially for large or complex data structures.
    
Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
from typing import Any
import pandas as pd
import inspect


def setup_logging():
    """
    Sets up the logging configuration for the application. Initializes the logging with a specified format, log level, and output file.

    The logger's basic configuration is set to INFO level, and logs are formatted to include the timestamp, filename, line number, log level, and the log message.
    Logs are written to 'app.log' file. Also, the log level for the 'chardet' library is set to WARNING to avoid overly verbose logging.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        filename="app.log",
        filemode="w",
    )
    logging.getLogger("chardet").setLevel(logging.WARNING)

    logging.info("Logging initialized")


def format_and_log_data_for_debug(logger: logging.Logger, attributes: dict[str, Any]) -> None:
    """
    Formats various types of class attributes and logs them for debugging purposes.

    It handles pandas DataFrames, dictionaries, and other data types differently to provide clear and concise log messages. For large collections or data frames, it provides a summarized view to avoid cluttering the logs.

    Args:
        logger (logging.Logger): The logger instance used to log the messages.
        attributes (dict[str, Any]): A dictionary containing the attribute names and their values from a class instance.

        The method inspects each attribute and decides on a logging format based on its data type:
        - For pandas DataFrames, it logs the head of the DataFrame.
        - For dictionaries, it handles dictionaries of types differently from those with collection values.
        - For other data types, it logs the value directly.
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
