import logging
from typing import Any
import pandas as pd
import inspect


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        filename="app.log",
        filemode="w",
    )
    logging.getLogger("chardet").setLevel(logging.WARNING)

    logging.info("Logging initialized")


def format_and_log_data_for_debug(logger: logging.Logger, attributes: dict[str, Any]) -> None:
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
